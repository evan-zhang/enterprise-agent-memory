#!/usr/bin/env python3
"""
compress.py — 快照压缩脚本

用法:
    python compress.py --snapshot <snapshot_dir> [--output <out_dir>] [--llm] [--dry-run]

功能:
    Phase 1: 结构化提取（DECISIONS + state + LOG）
    Phase 2: 启发式过滤（删除 ACK 对、重复行）
    Phase 3: 可选 LLM 压缩（调用外部 LLM API）
    降级策略: 任何阶段失败保留 raw.md

压缩比目标: 原始内容 → 压缩后（启发式 ~50%，LLM ~80%）
"""

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── 日志配置 ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger("compress")


# ── 常量 ─────────────────────────────────────────────────────────────────────

ACK_PATTERNS = [
    re.compile(r"^\s*\[.*\]\s*>?\s*(OK|好|收到|明白了|Acknowledged|ACK|Confirmed|✅)\s*$", re.IGNORECASE),
    re.compile(r"^\s*OK\s*$", re.IGNORECASE),
    re.compile(r"^\s*ACK\s*$", re.IGNORECASE),
    re.compile(r"^\s*好\s*$", re.IGNORECASE),
    re.compile(r"^好的.*$", re.IGNORECASE),
    re.compile(r"^收到.*$", re.IGNORECASE),
    re.compile(r"^明白.*$", re.IGNORECASE),
    re.compile(r"^👍\s*$"),
    re.compile(r"^HEARTBEAT_OK\s*$", re.IGNORECASE),
    re.compile(r"^#\s*HEARTBEAT", re.IGNORECASE),
    re.compile(r"^NO_REPLY\s*$", re.IGNORECASE),
]

REPEAT_THRESHOLD = 3  # 连续重复行超过此阈值才删除

SECTION_HEADERS = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


# ── Phase 1: 结构化提取 ─────────────────────────────────────────────────────

def extract_structured(snapshot_dir: Path) -> dict:
    """从快照目录提取 DECISIONS、state、LOG。"""
    result = {
        "decisions": [],
        "state": None,
        "log": "",
        "meta": {},
    }

    # 读取 DECISIONS.md
    decisions_path = snapshot_dir / "DECISIONS.md"
    if decisions_path.exists():
        content = decisions_path.read_text(encoding="utf-8")
        result["decisions"] = extract_decision_items(content)

    # 读取 state.json
    state_path = snapshot_dir / "state.json"
    if state_path.exists():
        try:
            result["state"] = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("state.json 解析失败，跳过")

    # 读取 LOG.md
    log_path = snapshot_dir / "LOG.md"
    if log_path.exists():
        result["log"] = log_path.read_text(encoding="utf-8")

    result["meta"] = {
        "snapshot": snapshot_dir.name,
        "extractedAt": datetime.now(timezone.utc).isoformat(),
        "originalSize": sum(
            (snapshot_dir / f).stat().st_size
            for f in ["DECISIONS.md", "state.json", "LOG.md"]
            if (snapshot_dir / f).exists()
        ),
    }

    return result


def extract_decision_items(content: str) -> list[dict]:
    """从 DECISIONS.md 提取结构化条目。"""
    items = []
    lines = content.split("\n")
    date_pattern = re.compile(r"^[-*]?\s*\[(\d{4}-\d{2}-\d{2})\]\s*(.+)")
    for line in lines:
        m = date_pattern.match(line.strip())
        if m:
            items.append({"date": m.group(1), "text": m.group(2)})
    return items


# ── Phase 2: 启发式过滤 ──────────────────────────────────────────────────────

def filter_ack(lines: list[str]) -> list[str]:
    """删除 ACK 类确认消息（单向，不删除请求）。"""
    filtered = []
    for line in lines:
        is_ack = any(p.match(line) for p in ACK_PATTERNS)
        if is_ack:
            continue
        filtered.append(line)
    return filtered


def filter_repeats(lines: list[str], threshold: int = REPEAT_THRESHOLD) -> list[str]:
    """删除连续重复行（保留首次出现）。"""
    if not lines:
        return lines

    result = []
    count = 1
    prev = lines[0]
    result.append(prev)

    for line in lines[1:]:
        if line == prev:
            count += 1
            if count <= 2:  # 保留前两次
                result.append(line)
        else:
            if count > threshold:
                # 替换为省略提示
                result.append(f"... [以上 {count} 行重复内容已压缩] ...")
            result.append(line)
            prev = line
            count = 1

    return result


def filter_empty_blocks(lines: list[str]) -> list[str]:
    """删除连续的空行块（超过2行连续空白→压缩为2行）。"""
    result = []
    empty_count = 0
    for line in lines:
        if not line.strip():
            empty_count += 1
            if empty_count <= 2:
                result.append(line)
        else:
            if empty_count > 2:
                result.append("")  # 插入一个空行作为分隔
            result.append(line)
            empty_count = 0
    return result


def hash_content(content: str) -> str:
    """计算内容哈希。"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def deduplicate_by_hash(lines: list[str]) -> list[str]:
    """基于哈希去重，保留首次出现。"""
    seen = set()
    result = []
    for line in lines:
        h = hash_content(line)
        if h in seen:
            continue
        seen.add(h)
        result.append(line)
    return result


def heuristic_compress(content: str) -> str:
    """Phase 2: 启发式压缩。"""
    lines = content.split("\n")

    # 1. 过滤 ACK
    lines = filter_ack(lines)
    log.debug("ACK 过滤后: %d 行", len(lines))

    # 2. 去重（哈希）
    lines = deduplicate_by_hash(lines)
    log.debug("去重后: %d 行", len(lines))

    # 3. 过滤连续重复
    lines = filter_repeats(lines)
    log.debug("重复过滤后: %d 行", len(lines))

    # 4. 过滤空行块
    lines = filter_empty_blocks(lines)

    return "\n".join(lines)


# ── Phase 3: LLM 压缩 ────────────────────────────────────────────────────────

LLM_API_TEMPLATE = """请将以下项目日志压缩到原始长度的约 20%，保留所有关键信息。

要求：
1. 保留所有决策记录（DECISIONS）
2. 保留任务状态和进度信息
3. 删除所有确认类消息（ACK、OK、收到等）
4. 合并重复信息
5. 用一句话概括每段工作的结论

原文：
{content}

压缩后（保留结构）：
"""


def llm_compress(content: str, api_url: Optional[str] = None, model: str = "gpt-4") -> str:
    """Phase 3: 调用 LLM API 压缩（可选）。"""
    if not api_url:
        log.warning("未提供 LLM API URL，跳过 LLM 压缩")
        return content

    prompt = LLM_API_TEMPLATE.format(content=content)

    try:
        import urllib.request
        import urllib.error

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        log.warning("LLM 压缩失败: %s，回退到启发式压缩结果", e)
        raise


# ── 降级策略 ─────────────────────────────────────────────────────────────────

def save_raw(compressed_path: Path, original_content: str) -> Path:
    """保存原始内容到 raw.md（降级备份）。"""
    raw_path = compressed_path.parent / "raw.md"
    raw_path.write_text(original_content, encoding="utf-8")
    log.info("原始内容已备份: %s", raw_path)
    return raw_path


# ── 核心压缩流程 ─────────────────────────────────────────────────────────────

def compress_snapshot(
    snapshot_dir: Path,
    output_dir: Optional[Path] = None,
    use_llm: bool = False,
    llm_api_url: Optional[str] = None,
    llm_model: str = "gpt-4",
    dry_run: bool = False,
) -> dict:
    """
    完整压缩流程。
    返回统计信息 dict。
    """
    if not snapshot_dir.exists():
        raise FileNotFoundError(f"快照目录不存在: {snapshot_dir}")

    output_dir = output_dir or snapshot_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    original_size = 0
    phase1_data = {}

    # Phase 1: 结构化提取
    try:
        phase1_data = extract_structured(snapshot_dir)
        log.info("Phase 1 完成: 提取 DECISIONS %d 条, LOG %d 字符",
                 len(phase1_data.get("decisions", [])),
                 len(phase1_data.get("log", "")))
    except Exception as e:
        log.error("Phase 1 失败: %s", e)
        raise

    # 合并所有文本内容用于压缩
    all_text_parts = []

    # 加入 state 摘要
    if phase1_data.get("state"):
        st = phase1_data["state"]
        all_text_parts.append(f"## 项目状态\nstatus={st.get('status')}, stage={st.get('stage')}")
        resume = st.get("resume", {})
        if resume.get("nextAction"):
            all_text_parts.append(f"nextAction: {resume['nextAction']}")

    # 加入决策
    decisions = phase1_data.get("decisions", [])
    if decisions:
        all_text_parts.append("## 决策记录\n" + "\n".join(
            f"- [{d['date']}] {d['text']}" for d in decisions
        ))

    # 加入日志
    if phase1_data.get("log"):
        all_text_parts.append("## 执行日志\n" + phase1_data["log"])

    original_content = "\n\n".join(all_text_parts)
    original_size = len(original_content.encode("utf-8"))

    # Phase 2: 启发式压缩
    phase2_result = ""
    try:
        phase2_result = heuristic_compress(original_content)
        phase2_size = len(phase2_result.encode("utf-8"))
        ratio = (1 - phase2_size / max(original_size, 1)) * 100
        log.info("Phase 2 完成: %d → %d 字节 (压缩率: %.1f%%)", original_size, phase2_size, ratio)
    except Exception as e:
        log.error("Phase 2 失败: %s", e)
        # 降级：保存 raw.md
        compressed_path = output_dir / "compressed.md"
        if not dry_run:
            save_raw(compressed_path, original_content)
        raise

    # Phase 3: LLM 压缩（可选）
    final_content = phase2_result
    if use_llm and llm_api_url:
        try:
            final_content = llm_compress(phase2_result, api_url=llm_api_url, model=llm_model)
            llm_size = len(final_content.encode("utf-8"))
            ratio = (1 - llm_size / max(original_size, 1)) * 100
            log.info("Phase 3 完成: %d → %d 字节 (总压缩率: %.1f%%)", original_size, llm_size, ratio)
        except Exception as e:
            log.warning("Phase 3 LLM 压缩失败: %s，使用 Phase 2 结果", e)
            final_content = phase2_result

    # 写入结果
    compressed_path = output_dir / "compressed.md"
    if dry_run:
        log.info("[DRY-RUN] 跳过写入: %s", compressed_path)
        log.info("压缩后内容预览（前 300 字符）:\n%s", final_content[:300])
    else:
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(dir=output_dir, prefix=".compressed_tmp_", suffix=".md")
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(final_content)
            shutil.move(tmp_path, compressed_path)
            log.info("压缩结果已写入: %s", compressed_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    final_size = len(final_content.encode("utf-8"))
    return {
        "original_size": original_size,
        "final_size": final_size,
        "compression_ratio": round((1 - final_size / max(original_size, 1)) * 100, 1),
        "decisions_count": len(decisions),
        "phase2_only": not use_llm,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="快照压缩脚本")
    parser.add_argument("--snapshot", type=Path, required=True, help="快照目录路径")
    parser.add_argument("--output", type=Path, help="输出目录（默认同快照目录）")
    parser.add_argument("--llm", action="store_true", help="启用 LLM 压缩（Phase 3）")
    parser.add_argument("--llm-api-url", type=str, help="LLM API URL")
    parser.add_argument("--llm-model", type=str, default="gpt-4", help="LLM 模型名")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    return parser.parse_args()


def main():
    args = parse_args()

    log.info("快照目录: %s", args.snapshot.resolve())

    stats = compress_snapshot(
        snapshot_dir=args.snapshot,
        output_dir=args.output,
        use_llm=args.llm,
        llm_api_url=args.llm_api_url,
        llm_model=args.llm_model,
        dry_run=args.dry_run,
    )

    log.info("=" * 50)
    log.info("压缩统计:")
    log.info("  原始大小: %d 字节", stats["original_size"])
    log.info("  压缩后: %d 字节", stats["final_size"])
    log.info("  压缩率: %.1f%%", stats["compression_ratio"])
    log.info("  决策条数: %d", stats["decisions_count"])
    log.info("  仅 Phase2: %s", stats["phase2_only"])
    log.info("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("执行失败: %s", e)
        sys.exit(1)

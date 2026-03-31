#!/usr/bin/env python3
"""
update_index.py — 将 state.json 同步到 INDEX.md

用法:
    python update_index.py [--project-dir <path>] [--dry-run]

功能:
    1. 读取 state.json，映射 status/stage 到 INDEX.md
    2. 原子写入（临时文件 → 校验 → mv）
    3. 更新 state.json 的 updateCount 和 lastIndexSync

字段映射:
    state.json.status + stage  →  INDEX.md.status + stage
    DISCUSSING/TARGET          →  IDLE/TARGET
    READY/PLAN                 →  READY/PLAN
    RUNNING/EXECUTE            →  RUNNING/EXECUTE
    PAUSED/*                   →  PAUSED/*
    BLOCKED/*                  →  BLOCKED/*
    WAITING_USER/*             →  WAITING/*
    DONE/DONE                  →  DONE/DONE

依赖:
    Python 3.10+, 标准库 (json, pathlib, shutil, datetime)
"""

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── 日志配置 ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger("update_index")


# ── 字段映射 ───────────────────────────────────────────────────────────────

STATUS_MAP = {
    "DISCUSSING": "IDLE",
    "READY": "READY",
    "RUNNING": "RUNNING",
    "PAUSED": "PAUSED",
    "BLOCKED": "BLOCKED",
    "WAITING_USER": "WAITING",
    "DONE": "DONE",
}


def map_status(raw: str) -> str:
    """将 state.json 的 status 映射为 INDEX.md 的 status。"""
    return STATUS_MAP.get(raw, raw)


def map_stage(raw: str, status: str) -> str:
    """将 state.json 的 stage 映射为 INDEX.md 的 stage。

    规则:
    - DONE → DONE/DONE
    - PAUSED/BLOCKED/WAITING → 原样保留
    - 其他 → 仅当 status 和 stage 相等时保留，否则用 stage
    """
    if status == "DONE":
        return "DONE"
    if status in ("PAUSED", "BLOCKED", "WAITING"):
        return status
    return raw


# ── 核心逻辑 ───────────────────────────────────────────────────────────────

def load_state(state_path: Path) -> dict:
    """安全加载 state.json。"""
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log.error("state.json 不存在: %s", state_path)
        raise
    except json.JSONDecodeError as e:
        log.error("state.json JSON 解析失败: %s", e)
        raise


def generate_index(state: dict, project_id: str) -> str:
    """从 state.json 内容生成 INDEX.md 内容。"""
    raw_status = state.get("status", "DISCUSSING")
    raw_stage = state.get("stage", "TARGET")

    status = map_status(raw_status)
    stage = map_stage(raw_stage, status)

    resume = state.get("resume", {})
    next_action = resume.get("nextAction", "待定义")

    # 进度列表（从 state.meta.progress 或固定模板）
    progress_items = state.get("meta", {}).get("progress", [])

    # 关键决策（从 DECISIONS.md 读取或 state 中转存）
    decisions = state.get("meta", {}).get("decisions", [])

    # 阻塞项
    blocked = resume.get("currentBlocked", "") or state.get("meta", {}).get("blocked", "")

    updated_at = state.get("updatedAt", datetime.now(timezone.utc).isoformat())
    update_count = state.get("updateCount", 0)

    now_local = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 进度部分
    progress_lines = []
    if progress_items:
        for item in progress_items:
            done = "✅" if item.get("done") else "⏳" if item.get("in_progress") else "⬜"
            progress_lines.append(f"- {done} {item.get('text', '')}")
    else:
        progress_lines.append("- ⏳ 初始化项目")

    # 决策部分
    decision_lines = []
    if decisions:
        for d in decisions:
            decision_lines.append(f"- [{d.get('date', 'N/A')}] {d.get('text', '')}")
    else:
        decision_lines.append("- 暂无")

    # 阻塞项部分
    blocked_lines = []
    if blocked:
        blocked_lines.append(f"- {blocked}")
    else:
        blocked_lines.append("- 暂无")

    content = f"""# INDEX.md - {project_id}

## 元数据（系统维护，勿手动修改）

- stateRef: {updated_at}
- indexVersion: 1
- updateCount: {update_count}

## 项目状态（自动同步自 state.json）

- status: {status}
- stage: {stage}
- nextAction: {next_action}

## 快速导航

- **任务定义** → TASK.md
- **执行日志** → LOG.md
- **决策记录** → DECISIONS.md

## 当前进展

{"".join(f"{line}" for line in progress_lines)}

## 关键决策

{"".join(f"{line}" for line in decision_lines)}

## 阻塞项

{"".join(f"{line}" for line in blocked_lines)}
"""
    return content


def validate_index(content: str) -> bool:
    """校验生成的 INDEX.md 完整性。"""
    required = ["# INDEX.md", "## 元数据", "## 项目状态", "## 快速导航"]
    for field in required:
        if field not in content:
            log.warning("INDEX 缺少必需字段: %s", field)
            return False
    return True


def atomic_write(path: Path, content: str, dry_run: bool = False) -> None:
    """原子写入：临时文件 → 校验 → rename。"""
    if dry_run:
        log.info("[DRY-RUN] 跳过写入: %s", path)
        log.info("内容预览（前 200 字符）:\n%s", content[:200])
        return

    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".index_tmp_", suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)

        # 校验
        if not validate_index(content):
            log.error("INDEX 校验失败，拒绝写入")
            os.unlink(tmp_path)
            raise RuntimeError("INDEX 校验失败")

        # 原子替换
        shutil.move(tmp_path, path)
        log.info("INDEX.md 已更新: %s", path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def update_state_json(state_path: Path, dry_run: bool = False) -> None:
    """更新 state.json 的 updateCount 和 lastIndexSync。"""
    state = load_state(state_path)
    state["updateCount"] = state.get("updateCount", 0) + 1
    state["lastIndexSync"] = datetime.now(timezone.utc).isoformat()

    if dry_run:
        log.info("[DRY-RUN] 跳过 state.json 更新: %s", state_path)
        return

    tmp_fd, tmp_path = tempfile.mkstemp(dir=state_path.parent, prefix=".state_tmp_", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        shutil.move(tmp_path, state_path)
        log.info("state.json updateCount -> %d", state["updateCount"])
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="同步 state.json 到 INDEX.md")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="项目根目录（含 state.json 和 INDEX.md）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印内容，不写入文件",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    project_dir = args.project_dir.resolve()
    state_path = project_dir / "state.json"
    index_path = project_dir / "INDEX.md"

    log.info("项目目录: %s", project_dir)

    # 加载 state.json
    state = load_state(state_path)
    project_id = state.get("id", project_dir.name)

    # 生成并写入 INDEX.md
    content = generate_index(state, project_id)
    atomic_write(index_path, content, dry_run=args.dry_run)

    # 更新 state.json（自增 updateCount）
    if not args.dry_run:
        update_state_json(state_path, dry_run=args.dry_run)

    if args.dry_run:
        log.info("[DRY-RUN] 实际未修改任何文件")
        sys.exit(0)

    log.info("完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("执行失败: %s", e)
        sys.exit(1)

#!/usr/bin/env python3
from __future__ import annotations
"""
sop_handover.py — SOP 任务交接脚本

功能:
    - 验证 from-owner
    - 创建 HANDOVER.md（用模板）
    - 调用 sop_state.py 更新 status=HANDOVER_PENDING + 切换 owner
    - 追加 LOG.md
    - 同步 INDEX.md

用法:
    python sop_handover.py --instance-path <path> \
        --from-owner evan --to-owner zelda --reason "轮换" --next-steps "继续执行"
    python sop_handover.py --instance-path <path> \
        --from-owner evan --to-owner zelda --reason "轮换" --next-steps "继续执行" --dry-run
"""


import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── 日志配置 ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger("sop_handover")

SCRIPT_DIR = Path(__file__).parent


# ── 状态读取 ─────────────────────────────────────────────────────────────────

def load_state(instance_path: Path) -> dict:
    state_file = instance_path / "state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"state.json 不存在: {state_file}")
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 验证 ─────────────────────────────────────────────────────────────────────

def validate_from_owner(instance_path: Path, from_owner: str) -> None:
    state = load_state(instance_path)
    current_owner = state.get("owner", "")
    if from_owner != current_owner:
        raise ValueError(
            f"交接失败：from-owner={from_owner} 与当前 owner={current_owner} 不一致"
        )


# ── 创建 HANDOVER.md ────────────────────────────────────────────────────────

def create_handover_file(
    instance_path: Path,
    from_owner: str,
    to_owner: str,
    reason: str,
    next_steps: str,
    dry_run: bool = False,
) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state = load_state(instance_path)
    instance_id = state.get("id", instance_path.name)
    title = state.get("title", "")

    content = f"""# HANDOVER.md - {instance_id}

---
- **实例 ID**：{instance_id}
- **任务标题**：{title}
- **文档状态**：DRAFT
- **版本**：v1.0
- **创建时间**：{timestamp}
- **mode**：{state.get('mode', 'lite')}
---

## 交接信息

- **交出方**：{from_owner}
- **接入方**：{to_owner}
- **交接时间**：{timestamp}
- **交接原因**：{reason}

## 后续步骤

{next_steps}

## 交接检查清单

- [ ] 已完成当前阶段的所有任务
- [ ] 已更新 state.json 状态
- [ ] 已在 LOG.md 记录关键操作
- [ ] 已向新负责人说明背景和上下文

---

*交接时间: {timestamp}*
"""
    handover_path = instance_path / "HANDOVER.md"

    if dry_run:
        log.info("[DRY-RUN] 将创建/更新: %s", handover_path)
        return handover_path

    tmp_fd, tmp_path = tempfile.mkstemp(dir=instance_path, prefix=".handover_tmp_", suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        shutil.move(tmp_path, handover_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    log.info("已创建: %s", handover_path)
    return handover_path


# ── 追加交接记录到 LOG.md ──────────────────────────────────────────────────

def append_handover_to_log(
    instance_path: Path,
    from_owner: str,
    to_owner: str,
    reason: str,
    dry_run: bool = False,
) -> None:
    log_file = instance_path / "LOG.md"
    if not log_file.exists():
        return
    if dry_run:
        log.info("[DRY-RUN] 将追加交接记录到 LOG.md")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n| {timestamp} | HANDOVER | {from_owner} → {to_owner} | {reason} |\n"

    content = log_file.read_text(encoding="utf-8")
    tmp_fd, tmp_path = tempfile.mkstemp(dir=instance_path, prefix=".log_tmp_", suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content + entry)
        shutil.move(tmp_path, log_file)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    log.info("已追加交接记录到 LOG.md")


# ── 同步 INDEX.md ──────────────────────────────────────────────────────────

def sync_index(instance_path: Path, dry_run: bool = False) -> None:
    if dry_run:
        log.info("[DRY-RUN] 跳过 INDEX.md 同步")
        return

    update_script = SCRIPT_DIR / "update_index.py"
    result = subprocess.run(
        [sys.executable, str(update_script), "--project-dir", str(instance_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.warning("INDEX.md 同步失败: %s", result.stderr)


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="SOP 任务交接")
    parser.add_argument("--instance-path", required=True, help="实例目录路径")
    parser.add_argument("--from-owner", required=True, help="当前负责人")
    parser.add_argument("--to-owner", required=True, help="新负责人")
    parser.add_argument("--reason", required=True, help="交接原因")
    parser.add_argument("--next-steps", required=True, help="后续步骤")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    return parser.parse_args()


def main():
    args = parse_args()
    instance_path = Path(args.instance_path).resolve()

    if not instance_path.exists():
        log.error("实例目录不存在: %s", instance_path)
        sys.exit(1)

    try:
        # 1. 验证 from-owner
        validate_from_owner(instance_path, args.from_owner)
        log.info("✓ from-owner 验证通过")

        # 2. 创建 HANDOVER.md
        create_handover_file(
            instance_path, args.from_owner, args.to_owner,
            args.reason, args.next_steps, dry_run=args.dry_run,
        )

        # 3. 追加交接记录到 LOG.md
        append_handover_to_log(
            instance_path, args.from_owner, args.to_owner,
            args.reason, dry_run=args.dry_run,
        )

        # 4. 调用 sop_state.py 更新状态和 owner
        sop_state_script = SCRIPT_DIR / "sop_state.py"
        cmd = [
            sys.executable, str(sop_state_script),
            "--instance-path", str(instance_path),
            "--status", "HANDOVER_PENDING",
            "--owner", args.to_owner,
            "--reason", f"交接: {args.reason}",
            "--confirm",
        ]
        if args.dry_run:
            cmd.append("--dry-run")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"sop_state.py 执行失败: {result.stderr.strip()}")
        log.info("✓ 已更新状态为 HANDOVER_PENDING")

        # 5. 同步 INDEX.md
        sync_index(instance_path, dry_run=args.dry_run)

        log.info("交接完成: %s → %s", args.from_owner, args.to_owner)

    except Exception as e:
        log.error("交接失败: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

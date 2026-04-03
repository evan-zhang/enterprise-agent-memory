#!/usr/bin/env python3
from __future__ import annotations
"""
sop_state.py — SOP 状态管理脚本

在 EAM state 基础上增加确认门禁和语义化操作。

功能:
    - 确认单门禁: checklistConfirmed=false 时拒绝进 RUNNING
    - 多轮确认计数: confirmCount ≥ 3 输出 INTERVENTION_REQUIRED
    - 语义化操作: pause/resume/shelve/restart/wait-user/reviewed
    - 高风险操作确认: DONE/ARCHIVED/UPGRADED/owner变更需 --confirm
    - 每次 update 后调用 update_index.py 同步

用法:
    python sop_state.py --instance-path <path> --status RUNNING
    python sop_state.py --instance-path <path> --action pause --reason "等反馈"
    python sop_state.py --instance-path <path> --action increment-confirm
    python sop_state.py --instance-path <path> --status DONE --confirm
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
log = logging.getLogger("sop_state")

# ── 常量 ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent

STATUS_CHOICES = [
    "DISCUSSING", "READY", "RUNNING", "REVIEWING", "WAITING_USER",
    "BLOCKED", "PAUSED", "ON_HOLD", "CANCELLED", "DONE", "ARCHIVED",
    "HANDOVER_PENDING", "UPGRADED",
]

STAGE_CHOICES = ["TARGET", "PLAN", "CHECKLIST", "EXECUTE", "ARCHIVE", "DONE"]

HIGH_RISK_STATUSES = {"DONE", "ARCHIVED", "UPGRADED"}


# ── 状态读写（原子操作）─────────────────────────────────────────────────────

def load_state(instance_path: Path) -> dict:
    state_file = instance_path / "state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"state.json 不存在: {state_file}")
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(instance_path: Path, state: dict, dry_run: bool = False) -> None:
    if dry_run:
        log.info("[DRY-RUN] 跳过 state.json 写入: %s", instance_path / "state.json")
        return

    state_file = instance_path / "state.json"
    tmp_fd, tmp_path = tempfile.mkstemp(dir=instance_path, prefix=".state_tmp_", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        shutil.move(tmp_path, state_file)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ── LOG 追加 ────────────────────────────────────────────────────────────────

def append_log_entry(
    instance_path: Path,
    stage: str,
    operation: str,
    reason: str | None,
    detail: str,
    dry_run: bool = False,
) -> None:
    log_file = instance_path / "LOG.md"
    if not log_file.exists():
        return
    if dry_run:
        log.info("[DRY-RUN] 将追加日志: %s | %s | %s", operation, detail, reason or "N/A")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = reason or "N/A"
    entry = f"\n| {timestamp} | {stage} | {operation} | {detail}; 原因: {note} |\n"

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


# ── INDEX 同步 ──────────────────────────────────────────────────────────────

def sync_index(instance_path: Path, dry_run: bool = False) -> None:
    """调用 update_index.py 同步 INDEX.md。"""
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


# ── 语义化操作映射 ─────────────────────────────────────────────────────────

def apply_action(action: str, current_reason: str | None) -> tuple[str, str | None, str | None]:
    """语义化操作 → (new_status, reason_override, blocked_clear)。"""
    mapping = {
        "pause": ("PAUSED", current_reason or "暂停", None),
        "resume": ("RUNNING", current_reason or "恢复执行", None),
        "shelve": ("ON_HOLD", current_reason or "搁置", None),
        "restart": ("RUNNING", current_reason or "重启执行", ""),
        "wait-user": ("WAITING_USER", current_reason or "等待用户", None),
        "reviewed": ("RUNNING", current_reason or "复核通过", None),
    }
    if action in mapping:
        return mapping[action]
    raise ValueError(f"不支持的 action: {action}")


# ── 门禁 ────────────────────────────────────────────────────────────────────

def ensure_checklist_completed(state: dict) -> None:
    """确认单门禁：checklistConfirmed=false 时拒绝进入 RUNNING。"""
    if not state.get("checklistConfirmed", False):
        raise PermissionError("执行前确认单未完成，禁止进入 RUNNING")


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="SOP 状态管理")
    parser.add_argument("--instance-path", required=True, help="实例目录路径")
    parser.add_argument("--status", choices=STATUS_CHOICES, help="目标状态")
    parser.add_argument("--stage", choices=STAGE_CHOICES, help="目标阶段")
    parser.add_argument("--owner", help="新负责人")
    parser.add_argument("--reason", help="操作原因")
    parser.add_argument("--waiting-for", help="等待用户的事项（配合 wait-user 使用）")
    parser.add_argument(
        "--action",
        choices=["pause", "resume", "shelve", "restart", "wait-user", "reviewed", "increment-confirm"],
        help="语义化操作",
    )
    parser.add_argument("--confirm", action="store_true", help="显式确认高风险操作")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    return parser.parse_args()


def main():
    args = parse_args()
    instance_path = Path(args.instance_path).resolve()

    if not instance_path.exists():
        log.error("实例目录不存在: %s", instance_path)
        sys.exit(1)

    try:
        state = load_state(instance_path)
        old_status = state.get("status", "DISCUSSING")
        old_stage = state.get("stage", "TARGET")
        old_owner = state.get("owner", "")
        now = datetime.now(timezone.utc).isoformat()

        # ── increment-confirm 特殊处理 ──
        if args.action == "increment-confirm":
            state["confirmCount"] = state.get("confirmCount", 0) + 1
            count = state["confirmCount"]
            state["updatedAt"] = now
            save_state(instance_path, state, dry_run=args.dry_run)
            append_log_entry(instance_path, old_stage, "INCREMENT_CONFIRM",
                             args.reason, f"confirmCount: {count}", dry_run=args.dry_run)
            sync_index(instance_path, dry_run=args.dry_run)
            log.info("✓ confirmCount: %d", count)
            if count >= 3:
                intervention = {
                    "type": "INTERVENTION_REQUIRED",
                    "reason": "多轮未达成一致",
                    "instanceId": state.get("id", ""),
                    "confirmCount": count,
                }
                print(json.dumps(intervention, ensure_ascii=False))
            return

        # ── 计算目标状态 ──
        new_status = args.status if args.status else old_status
        new_stage = args.stage if args.stage else old_stage
        reason = args.reason

        # 语义化操作映射
        if args.action in ("pause", "resume", "shelve", "restart", "wait-user", "reviewed"):
            new_status, reason_override, blocked_clear = apply_action(args.action, reason)
            if reason_override is not None and reason is None:
                reason = reason_override
            if blocked_clear == "":
                state["resume"] = state.get("resume", {})
                state["resume"]["currentBlocked"] = ""

        # wait-user 时更新 waitingFor
        if args.action == "wait-user" and args.waiting_for:
            state["resume"] = state.get("resume", {})
            state["resume"]["waitingFor"] = args.waiting_for
            state["resume"]["nextAction"] = f"等待用户: {args.waiting_for}"

        # ── 进入 RUNNING 前门禁 ──
        if new_status == "RUNNING":
            ensure_checklist_completed(state)

        # ── 高风险门禁 ──
        owner_changed = bool(args.owner and args.owner != old_owner)
        high_risk = owner_changed or (new_status in HIGH_RISK_STATUSES)
        if high_risk and not args.confirm:
            log.error("高风险操作需要显式确认，请加 --confirm 参数")
            sys.exit(1)

        # ── 更新 state ──
        state["status"] = new_status
        state["stage"] = new_stage
        state["updatedAt"] = now
        if args.owner:
            state["owner"] = args.owner
        if reason is not None:
            state["reason"] = reason

        save_state(instance_path, state, dry_run=args.dry_run)

        # ── 追加日志 ──
        owner_detail = ""
        if args.owner and args.owner != old_owner:
            owner_detail = f"; owner: {old_owner} → {args.owner}"
        detail = f"status: {old_status} → {new_status}; stage: {old_stage} → {new_stage}{owner_detail}"
        append_log_entry(
            instance_path, new_stage,
            args.action.upper() if args.action else "UPDATE_STATE",
            reason, detail, dry_run=args.dry_run,
        )

        # ── 同步 INDEX ──
        sync_index(instance_path, dry_run=args.dry_run)

        log.info("✓ 状态已更新: %s / %s", new_status, new_stage)
        if owner_changed:
            log.info("✓ Owner 已切换: %s → %s", old_owner, args.owner)

    except PermissionError as e:
        log.error("门禁拒绝: %s", e)
        sys.exit(1)
    except ValueError as e:
        log.error("参数错误: %s", e)
        sys.exit(1)
    except Exception as e:
        log.error("执行失败: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

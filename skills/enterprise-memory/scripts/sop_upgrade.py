#!/usr/bin/env python3
from __future__ import annotations
"""
sop_upgrade.py — SOP Lite→Full 升级脚本

功能:
    - 验证 mode=lite 且 status 不是 DONE/ARCHIVED
    - TASK.md 插入继承声明
    - LOG.md 标记 [继承自Lite]
    - 从 templates/full/ 创建 PLAN.md / DECISIONS.md / ARTIFACTS.md
    - 更新 state.json: mode=full, upgradedFrom, status=DISCUSSING
    - 创建快照
    - 同步 INDEX.md

用法:
    python sop_upgrade.py --instance-path <path> --reason "复杂度超预期"
    python sop_upgrade.py --instance-path <path> --reason "复杂度超预期" --dry-run
"""


import argparse
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

# ── 日志配置 ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger("sop_upgrade")

SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "references" / "templates"


# ── 状态读写 ─────────────────────────────────────────────────────────────────

def load_state(instance_path: Path) -> dict:
    state_file = instance_path / "state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"state.json 不存在: {state_file}")
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(instance_path: Path, state: dict, dry_run: bool = False) -> None:
    if dry_run:
        log.info("[DRY-RUN] 跳过 state.json 写入")
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


# ── 验证 ─────────────────────────────────────────────────────────────────────

def validate_lite_instance(state: dict) -> None:
    """验证：必须是 Lite 模式，且 status 非 DONE/ARCHIVED。"""
    if state.get("mode") != "lite":
        raise ValueError(
            f"实例 {state.get('id')} 的 mode={state.get('mode')}，不是 lite，无法升级。\n"
            "sop_upgrade.py 只允许对 Lite 实例使用。"
        )
    if state.get("status") in ("DONE", "ARCHIVED"):
        raise ValueError(
            f"实例 {state.get('id')} 的 status={state.get('status')}，已完成或已归档，无法升级。\n"
            "只能对进行中的 Lite 实例执行升级。"
        )


# ── TASK.md 继承声明 ─────────────────────────────────────────────────────────

def inject_inheritance_declaration(
    task_file: Path,
    instance_id: str,
    reason: str,
    dry_run: bool = False,
) -> None:
    """在 TASK.md 元数据块之后、第一个 ## 标题之前插入继承声明区。"""
    if not task_file.exists():
        log.warning("TASK.md 不存在，跳过继承声明注入")
        return

    if dry_run:
        log.info("[DRY-RUN] 将在 TASK.md 插入继承声明")
        return

    content = task_file.read_text(encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    declaration = f"""## 继承声明

- **升级自**：{instance_id}
- **升级时间**：{now}
- **升级原因**：{reason}
- **继承文件**：TASK.md、LOG.md

> 原 Lite 实例：[{instance_id}]()

"""

    # 找到元数据块结束位置
    meta_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if meta_match:
        insert_pos = meta_match.end()
        new_content = content[:insert_pos] + "\n" + declaration + content[insert_pos:]
    else:
        new_content = declaration + content

    # 更新 mode 标记
    new_content = new_content.replace("mode**：lite", "mode**：full")

    # 原子写入
    tmp_fd, tmp_path = tempfile.mkstemp(dir=task_file.parent, prefix=".task_tmp_", suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(new_content)
        shutil.move(tmp_path, task_file)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    log.info("已更新 TASK.md（插入继承声明，mode→full）")


# ── LOG.md 标记继承 ──────────────────────────────────────────────────────────

def tag_log_as_inherited(
    log_file: Path,
    instance_id: str,
    dry_run: bool = False,
) -> None:
    """LOG.md 所有内容行前加 [继承自Lite] 标记。"""
    if not log_file.exists():
        log.warning("LOG.md 不存在，跳过继承标记")
        return

    if dry_run:
        log.info("[DRY-RUN] 将在 LOG.md 标记 [继承自Lite]")
        return

    content = log_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    marked_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("---") and not stripped.startswith("#") and not stripped.startswith("*"):
            if stripped.startswith("|"):
                cell_content = stripped.strip("|")
                is_separator = not any(c.isalnum() for c in cell_content)
                if is_separator:
                    marked_lines.append(line)
                else:
                    marked_lines.append(line.replace("|", "| [继承自Lite]", 1))
            else:
                marked_lines.append(line)
        else:
            marked_lines.append(line)

    separator = f"\n\n---\n*升级为 Full 模式 | {now} | 原实例: {instance_id}*\n\n"
    new_content = "\n".join(marked_lines) + separator
    new_content = new_content.replace("mode**：lite", "mode**：full")

    # 原子写入
    tmp_fd, tmp_path = tempfile.mkstemp(dir=log_file.parent, prefix=".log_tmp_", suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(new_content)
        shutil.move(tmp_path, log_file)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    log.info("已更新 LOG.md（标记为继承，mode→full）")


# ── 创建 Full 文档 ──────────────────────────────────────────────────────────

def create_full_documents(
    instance_path: Path,
    instance_id: str,
    title: str,
    owner: str,
    dry_run: bool = False,
) -> None:
    """从 templates/full/ 创建 PLAN.md / DECISIONS.md / ARTIFACTS.md。"""
    now = datetime.now(timezone.utc).isoformat()

    full_templates = {
        "PLAN-template.md": "PLAN.md",
        "DECISIONS-template.md": "DECISIONS.md",
        "ARTIFACTS-template.md": "ARTIFACTS.md",
    }

    full_dir = TEMPLATES_DIR / "full"
    for tpl_name, target_name in full_templates.items():
        tpl_path = full_dir / tpl_name
        if not tpl_path.exists():
            log.warning("模板文件不存在: %s", tpl_path)
            continue

        content = tpl_path.read_text(encoding="utf-8")
        content = (
            content.replace("{{id}}", instance_id)
            .replace("{{title}}", title)
            .replace("{{owner}}", owner)
            .replace("{{createdAt}}", now)
        )

        target_path = instance_path / target_name
        if dry_run:
            log.info("[DRY-RUN] 将创建: %s", target_path)
            continue

        tmp_fd, tmp_path = tempfile.mkstemp(dir=instance_path, prefix=f".{target_name}_tmp_", suffix=".md")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(content)
            shutil.move(tmp_path, target_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        log.info("已创建: %s", target_path)


# ── 追加升级日志 ─────────────────────────────────────────────────────────────

def append_upgrade_log(
    instance_path: Path,
    instance_id: str,
    reason: str,
    dry_run: bool = False,
) -> None:
    log_file = instance_path / "LOG.md"
    if not log_file.exists():
        return
    if dry_run:
        log.info("[DRY-RUN] 将追加升级记录到 LOG.md")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n| {timestamp} | UPGRADE | 升级为 Full 模式 | OK | reason: {reason} |\n"

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


# ── 快照 ─────────────────────────────────────────────────────────────────────

def create_snapshot(instance_path: Path, dry_run: bool = False) -> None:
    """调用 EAM 底座创建快照。"""
    if dry_run:
        log.info("[DRY-RUN] 跳过快照创建")
        return

    switch_script = SCRIPT_DIR / "switch_project.py"
    # 用 Python import 方式调用 create_snapshot
    sys.path.insert(0, str(SCRIPT_DIR))
    from switch_project import create_snapshot as _create_snapshot
    _create_snapshot(instance_path)
    log.info("快照已创建")


# ── INDEX 同步 ──────────────────────────────────────────────────────────────

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
    parser = argparse.ArgumentParser(description="SOP Lite→Full 升级")
    parser.add_argument("--instance-path", required=True, help="Lite 实例目录路径")
    parser.add_argument("--reason", required=True, help="升级原因")
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
        instance_id = state.get("id", instance_path.name)
        title = state.get("title", "")
        owner = state.get("owner", "")

        # 1. 验证
        log.info("验证 Lite 实例: %s ...", instance_id)
        validate_lite_instance(state)
        log.info("✓ 验证通过")

        # 2. TASK.md 插入继承声明
        task_file = instance_path / "TASK.md"
        inject_inheritance_declaration(task_file, instance_id, args.reason, dry_run=args.dry_run)

        # 3. LOG.md 标记继承
        log_file = instance_path / "LOG.md"
        tag_log_as_inherited(log_file, instance_id, dry_run=args.dry_run)

        # 4. 创建 Full 专有文档
        create_full_documents(instance_path, instance_id, title, owner, dry_run=args.dry_run)

        # 5. 更新 state.json
        now = datetime.now(timezone.utc).isoformat()
        state["mode"] = "full"
        state["status"] = "DISCUSSING"
        state["upgradedFrom"] = instance_id
        state["confirmCount"] = 0
        state["updatedAt"] = now
        state["reason"] = args.reason
        state["resume"] = {
            "lastCompleted": "",
            "currentBlocked": "",
            "waitingFor": "",
            "nextAction": "补充 PLAN.md 执行计划",
        }
        state["sopFiles"] = {
            "lite": ["TASK.md", "LOG.md", "RESULT.md", "HANDOVER.md"],
            "full": ["PLAN.md", "DECISIONS.md", "ARTIFACTS.md"],
        }
        save_state(instance_path, state, dry_run=args.dry_run)
        log.info("✓ 已更新 state.json（mode=full, status=DISCUSSING, upgradedFrom set）")

        # 6. 创建快照
        create_snapshot(instance_path, dry_run=args.dry_run)

        # 7. 追加升级日志
        append_upgrade_log(instance_path, instance_id, args.reason, dry_run=args.dry_run)

        # 8. 同步 INDEX.md
        sync_index(instance_path, dry_run=args.dry_run)

        log.info("升级完成: %s (lite → full)", instance_id)
        log.info("状态已重置为 DISCUSSING，请补充 PLAN.md 执行计划")

    except ValueError as e:
        log.error("验证失败: %s", e)
        sys.exit(1)
    except Exception as e:
        log.error("执行失败: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

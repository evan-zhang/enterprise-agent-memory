#!/usr/bin/env python3
from __future__ import annotations
"""
sop_init.py — SOP 实例初始化脚本

在 EAM 项目基础上应用 SOP 模板。复用 EAM 底座 switch_project.py 创建项目，
然后扩展 state.json 的 SOP 字段并应用模板文件。

用法:
    python sop_init.py --title "任务标题" --mode lite --owner evan
    python sop_init.py --title "任务标题" --mode full --owner evan --description "描述"
    python sop_init.py --title "任务标题" --mode lite --owner evan --dry-run
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
log = logging.getLogger("sop_init")

# ── 常量 ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "references" / "templates"


# ── 模板变量替换 ─────────────────────────────────────────────────────────────

def apply_template(template_path: Path, variables: dict[str, str]) -> str:
    """读取模板文件并替换变量。"""
    content = template_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def apply_templates(
    project_dir: Path,
    mode: str,
    variables: dict[str, str],
    dry_run: bool = False,
) -> list[str]:
    """应用模板文件到项目目录，返回创建的文件名列表。"""
    created_files: list[str] = []

    # Lite 四件套（所有模式共有）
    lite_templates = {
        "TASK-template.md": "TASK.md",
        "LOG-template.md": "LOG.md",
        "RESULT-template.md": "RESULT.md",
        "HANDOVER-template.md": "HANDOVER.md",
    }

    lite_dir = TEMPLATES_DIR / "lite"
    for tpl_name, target_name in lite_templates.items():
        tpl_path = lite_dir / tpl_name
        if not tpl_path.exists():
            log.warning("模板文件不存在: %s", tpl_path)
            continue

        content = apply_template(tpl_path, variables)
        # 替换 mode 标记
        content = content.replace("mode**：lite", f"mode**：{mode}")

        target_path = project_dir / target_name
        if dry_run:
            log.info("[DRY-RUN] 将创建: %s", target_path)
        else:
            # 原子写入
            tmp_fd, tmp_path = tempfile.mkstemp(dir=project_dir, prefix=f".{target_name}_tmp_", suffix=".md")
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    f.write(content)
                shutil.move(tmp_path, target_path)
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
            log.info("已创建: %s", target_path)

        created_files.append(target_name)

    # Full 额外三件套
    if mode == "full":
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

            content = apply_template(tpl_path, variables)

            target_path = project_dir / target_name
            if dry_run:
                log.info("[DRY-RUN] 将创建: %s", target_path)
            else:
                tmp_fd, tmp_path = tempfile.mkstemp(dir=project_dir, prefix=f".{target_name}_tmp_", suffix=".md")
                try:
                    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                        f.write(content)
                    shutil.move(tmp_path, target_path)
                except Exception:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    raise
                log.info("已创建: %s", target_path)

            created_files.append(target_name)

    return created_files


# ── 核心逻辑 ───────────────────────────────────────────────────────────────

def sop_init(
    title: str,
    mode: str = "lite",
    owner: str = "",
    description: str = "",
    dry_run: bool = False,
) -> Path | None:
    """创建 SOP 实例。

    1. 调用 EAM 底座 switch_project.py --new 创建项目
    2. 扩展 state.json 的 SOP 字段
    3. 应用模板文件
    4. 同步 INDEX.md
    """
    # 生成 slug name（用于目录名）
    name = title.replace(" ", "-")[:50] if title else "untitled"

    # Step 1: 调用 EAM 底座创建项目
    switch_script = SCRIPT_DIR / "switch_project.py"
    cmd = [
        sys.executable, str(switch_script),
        "--new", "--name", name, "--description", description,
    ]
    if dry_run:
        cmd.append("--dry-run")

    log.info("调用 EAM 底座创建项目: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("EAM 底座创建项目失败: %s", result.stderr)
        return None

    # 解析项目目录
    output_lines = result.stdout.strip().split("\n")
    project_dir_str = None
    for line in output_lines:
        if "完成:" in line:
            project_dir_str = line.split("完成:")[-1].strip()
            break

    if not project_dir_str:
        log.error("无法解析项目目录路径")
        return None

    project_dir = Path(project_dir_str)
    if not project_dir.exists():
        log.error("项目目录不存在: %s", project_dir)
        return None

    log.info("EAM 项目已创建: %s", project_dir)

    # Step 2: 扩展 state.json 的 SOP 字段
    state_path = project_dir / "state.json"
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    now = datetime.now(timezone.utc).isoformat()
    state.update({
        "source": "sop",
        "mode": mode,
        "owner": owner,
        "title": title,
        "deadline": "",
        "reason": "",
        "checklistConfirmed": False,
        "confirmCount": 0,
        "upgradedFrom": "",
        "sopFiles": {
            "lite": ["TASK.md", "LOG.md", "RESULT.md", "HANDOVER.md"],
            "full": ["PLAN.md", "DECISIONS.md", "ARTIFACTS.md"] if mode == "full" else [],
        },
    })
    state["updatedAt"] = now

    # Step 3: 应用模板文件（覆盖底座创建的基础文件）
    variables = {
        "id": state["id"],
        "title": title,
        "owner": owner,
        "createdAt": now,
    }
    created_files = apply_templates(project_dir, mode, variables, dry_run=dry_run)

    if not dry_run:
        # 原子写入更新后的 state.json
        tmp_fd, tmp_path = tempfile.mkstemp(dir=project_dir, prefix=".state_sop_tmp_", suffix=".json")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            shutil.move(tmp_path, state_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        log.info("state.json SOP 字段已扩展")

        # Step 4: 同步 INDEX.md
        update_script = SCRIPT_DIR / "update_index.py"
        sync_result = subprocess.run(
            [sys.executable, str(update_script), "--project-dir", str(project_dir)],
            capture_output=True, text=True,
        )
        if sync_result.returncode != 0:
            log.warning("INDEX.md 同步失败: %s", sync_result.stderr)
        else:
            log.info("INDEX.md 已同步")

    log.info("SOP 实例已创建: %s (mode=%s, owner=%s)", state["id"], mode, owner)
    return project_dir


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="SOP 实例初始化")
    parser.add_argument("--title", required=True, help="任务标题")
    parser.add_argument("--mode", choices=["lite", "full"], default="lite",
                        help="实例模式：lite（四件套）或 full（七件套）")
    parser.add_argument("--owner", default="", help="负责人")
    parser.add_argument("--description", default="", help="项目描述")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    return parser.parse_args()


def main():
    args = parse_args()

    project_dir = sop_init(
        title=args.title,
        mode=args.mode,
        owner=args.owner,
        description=args.description,
        dry_run=args.dry_run,
    )

    if project_dir is None:
        sys.exit(1)

    if args.dry_run:
        log.info("[DRY-RUN] 以上操作未实际执行")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("执行失败: %s", e)
        sys.exit(1)

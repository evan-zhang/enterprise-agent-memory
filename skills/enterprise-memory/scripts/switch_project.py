#!/usr/bin/env python3
"""
switch_project.py — 项目切换脚本（切出 + 切入）

用法:
    切入项目:
        python switch_project.py --enter --project-id <id>
        python switch_project.py --enter --keyword <关键词>

    切出项目:
        python switch_project.py --exit [--project-dir <path>]

    搜索项目:
        python switch_project.py --search <关键词>

    新建项目:
        python switch_project.py --new --name <项目名> --description <描述>

    列表项目:
        python switch_project.py --list

功能:
    切出: 保存当前项目状态 + 创建快照 + 更新 INDEX
    切入: /new + 读取目标项目 + 自检 + 输出摘要
    搜索: 按 ID/名称匹配项目

全局记忆层位置: ~/projects/
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
log = logging.getLogger("switch_project")


# ── 常量 ─────────────────────────────────────────────────────────────────────

PROJECTS_ROOT = Path.home() / ".openclaw" / "EAM-projects"
GLOBAL_INDEX = PROJECTS_ROOT / "GLOBAL-INDEX.md"
CURRENT_POINTER = PROJECTS_ROOT / "current-project.json"
ARCHIVE_DIR = PROJECTS_ROOT / "archive"


def ensure_dirs():
    """确保全局记忆层目录存在。"""
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ── 状态读写 ─────────────────────────────────────────────────────────────────

def load_state(project_dir: Path) -> dict | None:
    path = project_dir / "state.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def save_state(project_dir: Path, state: dict) -> None:
    path = project_dir / "state.json"
    tmp_fd, tmp_path = tempfile.mkstemp(dir=project_dir, prefix=".state_tmp_", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        shutil.move(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def read_current_pointer() -> dict | None:
    if not CURRENT_POINTER.exists():
        return None
    try:
        with open(CURRENT_POINTER, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def write_current_pointer(project_id: str, project_path: Path) -> None:
    data = {
        "projectId": project_id,
        "projectPath": str(project_path.resolve()),
        "switchedAt": datetime.now(timezone.utc).isoformat(),
    }
    tmp_fd, tmp_path = tempfile.mkstemp(dir=PROJECTS_ROOT, prefix=".current_project_tmp_", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(tmp_path, CURRENT_POINTER)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ── 快照 ─────────────────────────────────────────────────────────────────────

def create_snapshot(project_dir: Path, dry_run: bool = False) -> Path | None:
    """创建项目快照目录 snapshot/<timestamp>/。"""
    snapshot_dir = project_dir / "snapshot"
    snapshot_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = snapshot_dir / timestamp

    if dry_run:
        log.info("[DRY-RUN] 跳过快照创建: %s", snap)
        return snap

    snap.mkdir(exist_ok=True)

    # 快照核心文件
    files_to_copy = ["state.json", "INDEX.md", "LOG.md", "TASK.md", "DECISIONS.md"]
    for fname in files_to_copy:
        src = project_dir / fname
        if src.exists():
            shutil.copy2(src, snap / fname)

    log.info("快照已创建: %s", snap)
    return snap


# ── 搜索 ─────────────────────────────────────────────────────────────────────

def search_projects(keyword: str) -> list[dict]:
    """按 ID 或名称模糊搜索项目。"""
    results = []
    if not PROJECTS_ROOT.exists():
        return results

    kw = keyword.lower()
    for proj_dir in sorted(PROJECTS_ROOT.iterdir()):
        if not proj_dir.is_dir():
            continue
        if proj_dir.name in (GLOBAL_INDEX.name, CURRENT_POINTER.name, ARCHIVE_DIR.name, "archive"):
            continue

        state = load_state(proj_dir)
        if not state:
            continue

        proj_id = state.get("id", proj_dir.name)
        proj_name = state.get("name", "")

        if (kw in proj_id.lower()) or (kw in proj_name.lower()):
            results.append({
                "id": proj_id,
                "name": proj_name,
                "path": str(proj_dir.resolve()),
                "status": state.get("status", "UNKNOWN"),
                "stage": state.get("stage", "UNKNOWN"),
                "updatedAt": state.get("updatedAt", ""),
            })

    return results


def list_projects() -> list[dict]:
    """列出所有项目。"""
    return search_projects("")


# ── 切出 ─────────────────────────────────────────────────────────────────────

def exit_project(project_dir: Path, dry_run: bool = False) -> None:
    """切出当前项目：保存状态 + 创建快照 + 更新 INDEX。"""
    state = load_state(project_dir)
    if not state:
        log.error("无法读取 state.json，退出")
        raise RuntimeError("state.json not found")

    # 更新状态为 PAUSED
    if state.get("status") not in ("DONE",):
        state["status"] = "PAUSED"
        state["updatedAt"] = datetime.now(timezone.utc).isoformat()

    if not dry_run:
        save_state(project_dir, state)

    # 创建快照
    create_snapshot(project_dir, dry_run=dry_run)

    # 调用 update_index 同步 INDEX.md
    if not dry_run:
        from update_index import main as update_index_main
        # 重新调用（通过子进程避免 import 顺序问题）
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "update_index.py"), "--project-dir", str(project_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log.warning("update_index.py 执行失败: %s", result.stderr)

    log.info("切出完成: %s", project_dir.name)


# ── 切入 ─────────────────────────────────────────────────────────────────────

def enter_project(project_id: str | None = None, keyword: str | None = None, dry_run: bool = False) -> Path | None:
    """切入目标项目。"""
    # 搜索匹配项目
    if keyword:
        results = search_projects(keyword)
        if not results:
            log.error("未找到匹配项目: %s", keyword)
            return None
        if len(results) > 1:
            log.info("找到多个匹配项目:")
            for r in results:
                log.info("  [%s] %s (%s) - %s", r["id"], r["name"], r["status"], r["path"])
            # 取第一个
            chosen = results[0]
        else:
            chosen = results[0]
    elif project_id:
        proj_dir = None
        for d in PROJECTS_ROOT.iterdir():
            if not d.is_dir():
                continue
            state = load_state(d)
            if state and state.get("id") == project_id:
                proj_dir = d
                break
        if not proj_dir:
            log.error("未找到项目: %s", project_id)
            return None
        chosen = {"id": project_id, "name": state.get("name", ""), "path": str(proj_dir.resolve()),
                  "status": state.get("status", ""), "stage": state.get("stage", "")}
    else:
        log.error("必须指定 --project-id 或 --keyword")
        return None

    proj_path = Path(chosen["path"])
    state = load_state(proj_path)

    # 自检
    issues = []
    for fname in ["state.json", "INDEX.md", "TASK.md"]:
        if not (proj_path / fname).exists():
            issues.append(f"缺少文件: {fname}")

    if issues:
        log.warning("项目自检发现问题:\n  " + "\n  ".join(issues))

    # 输出摘要
    log.info("=" * 60)
    log.info("项目: %s (%s)", chosen["name"], chosen["id"])
    log.info("状态: %s / %s", chosen["status"], chosen["stage"])
    log.info("路径: %s", chosen["path"])
    if state:
        resume = state.get("resume", {})
        log.info("上次完成: %s", resume.get("lastCompleted", "N/A"))
        log.info("下一步: %s", resume.get("nextAction", "N/A"))
        if resume.get("waitingFor"):
            log.info("等待: %s", resume.get("waitingFor"))
    log.info("=" * 60)

    if not dry_run:
        # 更新全局指针
        write_current_pointer(chosen["id"], proj_path)
        log.info("已切换到项目: %s", chosen["name"])
    else:
        log.info("[DRY-RUN] 跳过全局指针更新")

    return proj_path


# ── 新建项目 ─────────────────────────────────────────────────────────────────

def new_project(name: str, description: str = "", dry_run: bool = False) -> Path:
    """新建项目目录并初始化。"""
    ensure_dirs()

    today = datetime.now().strftime("%Y%m%d")
    # 查找当天序号
    existing = [d for d in PROJECTS_ROOT.iterdir() if d.is_dir() and d.name.startswith(f"SOP-{today}")]
    seq = len(existing) + 1

    project_id = f"SOP-{today}-{seq:03d}-{name}"
    project_dir = PROJECTS_ROOT / project_id

    if project_dir.exists():
        log.error("项目目录已存在: %s", project_dir)
        raise FileExistsError(project_dir)

    if not dry_run:
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "snapshot").mkdir(exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()
        state = {
            "id": project_id,
            "name": name,
            "status": "DISCUSSING",
            "stage": "TARGET",
            "createdAt": now,
            "updatedAt": now,
            "updateCount": 0,
            "lastIndexSync": None,
            "resume": {
                "lastCompleted": "",
                "currentBlocked": "",
                "waitingFor": "",
                "nextAction": "",
            },
            "meta": {
                "description": description,
                "progress": [],
                "decisions": [],
                "blocked": "",
            },
        }
        save_state(project_dir, state)

        # 生成 INDEX.md
        from update_index import main as update_index_main
        # 用子进程调用
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "update_index.py"), "--project-dir", str(project_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log.warning("update_index.py 初始化失败: %s", result.stderr)

        # 创建基础文件
        for fname in ["TASK.md", "LOG.md", "DECISIONS.md"]:
            (project_dir / fname).write_text(f"# {fname.replace('.md','')} - {project_id}\n\n", encoding="utf-8")

        # 更新全局指针
        write_current_pointer(project_id, project_dir)

    log.info("项目已创建: %s", project_id)
    return project_dir


# ── 更新 GLOBAL-INDEX ─────────────────────────────────────────────────────────

def update_global_index(dry_run: bool = False) -> None:
    """更新全局索引。"""
    projects = list_projects()

    lines = [
        "# GLOBAL-INDEX.md",
        "",
        "## 项目列表",
        "",
        "| ID | 名称 | 状态 | 阶段 | 更新 |",
        "|---|---|---|---|---|",
    ]

    for p in projects:
        updated = p.get("updatedAt", "")[:10] if p.get("updatedAt") else "N/A"
        lines.append(f"| {p['id']} | {p['name']} | {p['status']} | {p['stage']} | {updated} |")

    lines.append("")
    lines.append(f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    content = "\n".join(lines)

    if dry_run:
        log.info("[DRY-RUN] 跳过 GLOBAL-INDEX.md 更新")
        return

    if not GLOBAL_INDEX.exists():
        GLOBAL_INDEX.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(dir=PROJECTS_ROOT, prefix=".global_index_tmp_", suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        shutil.move(tmp_path, GLOBAL_INDEX)
        log.info("GLOBAL-INDEX.md 已更新，共 %d 个项目", len(projects))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="项目切换脚本")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--enter", action="store_true", help="切入项目")
    group.add_argument("--exit", action="store_true", help="切出当前项目")
    group.add_argument("--search", type=str, metavar="KEYWORD", help="搜索项目")
    group.add_argument("--new", action="store_true", help="新建项目")
    group.add_argument("--list", action="store_true", help="列出所有项目")

    parser.add_argument("--project-id", type=str, help="项目 ID（切入时）")
    parser.add_argument("--keyword", type=str, help="搜索关键词")
    parser.add_argument("--name", type=str, help="项目名称（新建时）")
    parser.add_argument("--description", type=str, default="", help="项目描述（新建时）")
    parser.add_argument("--project-dir", type=Path, help="项目目录（切出时）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dirs()

    if args.list:
        projects = list_projects()
        if not projects:
            log.info("暂无项目")
        else:
            log.info("项目列表 (%d):", len(projects))
            for p in projects:
                log.info("  [%s] %s — %s / %s (更新: %s)",
                         p["id"], p["name"], p["status"], p["stage"],
                         p.get("updatedAt", "")[:10] if p.get("updatedAt") else "N/A")

    elif args.search:
        results = search_projects(args.search)
        if not results:
            log.info("未找到匹配项目: %s", args.search)
        else:
            for r in results:
                log.info("[%s] %s — %s / %s", r["id"], r["name"], r["status"], r["stage"])

    elif args.new:
        if not args.name:
            log.error("新建项目需要 --name")
            sys.exit(1)
        proj_dir = new_project(args.name, args.description, dry_run=args.dry_run)
        log.info("完成: %s", proj_dir)

    elif args.enter:
        proj_dir = enter_project(project_id=args.project_id, keyword=args.keyword, dry_run=args.dry_run)
        if proj_dir is None:
            sys.exit(1)

    elif args.exit:
        project_dir = args.project_dir or Path.cwd()
        exit_project(project_dir, dry_run=args.dry_run)

    else:
        log.error("请指定操作: --enter | --exit | --search | --new | --list")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("执行失败: %s", e)
        sys.exit(1)

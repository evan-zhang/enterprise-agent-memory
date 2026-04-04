#!/usr/bin/env python3
"""
task_registry.py — Task Registry core operations
create / get / list / stop / update / output
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

TASKS_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "tasks"
INDEX_FILE = TASKS_DIR / "index.json"

def _ensure_dir():
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    (TASKS_DIR / "logs").mkdir(exist_ok=True)
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("{}", encoding="utf-8")

def _load_index() -> dict:
    _ensure_dir()
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))

def _save_index(index: dict):
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

def _task_file(task_id: str) -> Path:
    return TASKS_DIR / f"{task_id}.json"

def _log_file(task_id: str) -> Path:
    return TASKS_DIR / "logs" / f"{task_id}.md"

def create(name: str, context: dict = None, openclaw_task_id: str = None) -> dict:
    """Create a new task entry."""
    _ensure_dir()
    task_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    task = {
        "id": task_id,
        "openclawTaskId": openclaw_task_id,
        "name": name,
        "status": "created",
        "createdAt": now,
        "updatedAt": now,
        "result": None,
        "error": None,
        "context": context or {}
    }
    _task_file(task_id).write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    # Log creation
    log_path = _log_file(task_id)
    log_path.write_text(f"# Task: {name} ({task_id})\n\n## Log\n\n### {datetime.now().strftime('%H:%M')} - Created\n- Context: {json.dumps(context or {})}\n", encoding="utf-8")
    # Update index
    index = _load_index()
    index[task_id] = {"name": name, "status": "created", "openclawTaskId": openclaw_task_id}
    _save_index(index)
    return task

def get(task_id: str) -> Optional[dict]:
    """Get task by ID."""
    path = _task_file(task_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def list(status_filter: str = None) -> list:
    """List all tasks, optionally filtered by status."""
    _ensure_dir()
    index = _load_index()
    tasks = []
    for task_id, info in index.items():
        if status_filter and info.get("status") != status_filter:
            continue
        task = get(task_id)
        if task:
            tasks.append(task)
    return tasks

def stop(task_id: str) -> Optional[dict]:
    """Mark task as stopped."""
    return update(task_id, {"status": "stopped"})

def update(task_id: str, updates: dict) -> Optional[dict]:
    """Update task fields."""
    task = get(task_id)
    if not task:
        return None
    task.update(updates)
    task["updatedAt"] = datetime.now().isoformat()
    _task_file(task_id).write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    # Update index
    index = _load_index()
    if task_id in index:
        index[task_id]["status"] = task["status"]
        _save_index(index)
    # Append to log
    log_path = _log_file(task_id)
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else f"# Task: {task['name']} ({task_id})\n\n## Log\n"
    existing += f"\n### {datetime.now().strftime('%H:%M')} - Updated: {list(updates.keys())}\n"
    if "status" in updates:
        existing += f"- Status → {updates['status']}\n"
    if "result" in updates:
        existing += f"- Result: {json.dumps(updates.get('result'), ensure_ascii=False)[:200]}\n"
    if "error" in updates:
        existing += f"- Error: {updates.get('error')}\n"
    log_path.write_text(existing, encoding="utf-8")
    return task

def output(task_id: str) -> Optional[dict]:
    """Get task output/result."""
    task = get(task_id)
    if not task:
        return None
    return {"output": task.get("result"), "status": task["status"], "error": task.get("error")}

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else "unnamed"
        ctx = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(create(name, ctx)))
    elif cmd == "get":
        print(json.dumps(get(sys.argv[2])))
    elif cmd == "list":
        print(json.dumps(list()))
    elif cmd == "stop":
        print(json.dumps(stop(sys.argv[2])))
    elif cmd == "output":
        print(json.dumps(output(sys.argv[2])))
    else:
        print(f"Unknown cmd: {cmd}")

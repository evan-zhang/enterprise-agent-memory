#!/usr/bin/env python3
"""
memory_sync.py -- 定期记忆同步脚本
用法: python memory_sync.py [--base-path ~/.openclaw/workspace] [--dry-run]
"""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_MAX_LINES = 200
MEMORY_MAX_BYTES = 25_000

def get_memory_stats(memory_md: Path) -> dict:
    """检查 MEMORY.md 状态"""
    if not memory_md.exists():
        return {"exists": False, "lines": 0, "bytes": 0}
    content = memory_md.read_text(encoding="utf-8")
    lines = content.count("\n") + 1
    bytes_ = len(content.encode("utf-8"))
    return {"exists": True, "lines": lines, "bytes": bytes_, "over_limit": lines >= MEMORY_MAX_LINES or bytes_ >= MEMORY_MAX_BYTES}

def archive_old_entries(memory_dir: Path, verbose: bool = True):
    """归档低优先级的旧条目（简化版：检查 MEMORY.md 行数）"""
    memory_md = memory_dir / "MEMORY.md"
    archive_dir = memory_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    stats = get_memory_stats(memory_md)
    if not stats["exists"] or not stats["over_limit"]:
        return False
    
    # 读取当前内容
    content = memory_md.read_text(encoding="utf-8")
    
    # 简单策略：检查是否超过200行，如果是，截断并归档
    lines = content.split("\n")
    if len(lines) > MEMORY_MAX_LINES:
        # 保留前 180 行（留 buffer）
        kept = lines[:180]
        archived = lines[180:]
        
        # 写入归档文件
        today = datetime.now().strftime("%Y-%m-%d")
        archive_file = archive_dir / f"MEMORY-archive-{today}.md"
        existing = archive_file.read_text(encoding="utf-8") if archive_file.exists() else ""
        archive_file.write_text(existing + "\n".join(archived), encoding="utf-8")
        
        # 重写 MEMORY.md
        memory_md.write_text("\n".join(kept) + f"\n\n> ⚠️ 归档了 {len(archived)} 行到 {archive_file.name}", encoding="utf-8")
        
        if verbose:
            print(f"  📦 归档 {len(archived)} 行到 {archive_file.name}")
        return True
    return False

def update_heartbeat_state(memory_dir: Path):
    """更新 heartbeat-state.json"""
    state_file = memory_dir / "heartbeat-state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
    else:
        state = {"lastMemorySync": None, "lastDistillation": None, 
                  "lastWorkspaceScan": None, "memorySyncCount": 0, "lastChecks": {}}
    
    state["lastMemorySync"] = datetime.now().isoformat()
    state["memorySyncCount"] = state.get("memorySyncCount", 0) + 1
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def sync(base_path: Path, dry_run: bool = False, verbose: bool = True):
    """执行记忆同步"""
    memory_dir = base_path / "memory"
    memory_md = base_path / "MEMORY.md"
    
    if dry_run:
        stats = get_memory_stats(memory_md)
        print(f"[dry-run] MEMORY.md: {stats['lines']} 行, {stats['bytes']} bytes")
        print(f"[dry-run] 需要归档: {stats.get('over_limit', False)}")
        return
    
    # 1. 检查 MEMORY.md 大小
    archived = archive_old_entries(memory_dir, verbose)
    
    # 2. 更新状态
    update_heartbeat_state(memory_dir)
    
    if verbose:
        print(f"✅ 记忆同步完成 (count: {json.loads((memory_dir / 'heartbeat-state.json').read_text())['memorySyncCount']})")

def main():
    parser = argparse.ArgumentParser(description="Agent Memory 记忆同步")
    parser.add_argument("--base-path", default=str(Path.home() / ".openclaw" / "workspace"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    sync(Path(args.base_path), dry_run=args.dry_run)

if __name__ == "__main__":
    main()

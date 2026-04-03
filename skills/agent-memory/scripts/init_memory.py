#!/usr/bin/env python3
"""
init_memory.py -- Initialize agent-memory memory system目录结构
用法: python init_memory.py [--base-path ~/.openclaw/workspace]
"""
import argparse
import json
from pathlib import Path

def init_memory_system(base_path: Path, verbose: bool = True):
    """Create complete memory system directory structure"""
    
    memory_dir = base_path / "memory"
    dirs = [
        memory_dir / "user",
        memory_dir / "feedback", 
        memory_dir / "project",
        memory_dir / "ref",
        memory_dir / "logs",
        memory_dir / "archive",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"  [OK] {d.relative_to(base_path)}")
    
    # 创建 MEMORY.md 索引文件
    memory_md = base_path / "MEMORY.md"
    if not memory_md.exists():
        memory_md.write_text(
            "# MEMORY.md -- Memory Index\n\n"
            "> Schema v2026.4.3 | Last updated: (today)\n\n"
            "## Topics\n\n"
            "_(none yet)_\n"
        )
        if verbose:
            print(f"  [OK] MEMORY.md (index)")
    
    # 创建 heartbeat-state.json
    heartbeat_state = memory_dir / "heartbeat-state.json"
    if not heartbeat_state.exists():
        state = {
            "lastMemorySync": None,
            "lastDistillation": None,
            "lastWorkspaceScan": None,
            "memorySyncCount": 0,
            "lastChecks": {
                "email": None,
                "calendar": None,
                "weather": None
            }
        }
        heartbeat_state.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        if verbose:
            print(f"  [OK] memory/heartbeat-state.json")
    
    if verbose:
        print(f"\n✅ 记忆系统初始化完成: {memory_dir}")
    
    return memory_dir

def main():
    parser = argparse.ArgumentParser(description="Initialize agent-memory memory system")
    parser.add_argument("--base-path", default=str(Path.home() / ".openclaw" / "workspace"),
                        help="工作空间根目录")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    args = parser.parse_args()
    
    base_path = Path(args.base_path).expanduser()
    init_memory_system(base_path, verbose=not args.quiet)

if __name__ == "__main__":
    main()

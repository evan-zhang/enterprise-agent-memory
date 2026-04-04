#!/usr/bin/env python3
"""
test_all.py — 完整测试：验证 enterprise-agent-memory 安装是否正确
Run this on a freshly installed agent to verify all components work.

Usage: python3 test_all.py
"""
import sys
import json
import subprocess
from pathlib import Path

def run(cmd, desc):
    """Execute a command and report result."""
    print(f"\n{'='*60}")
    print(f"TEST: {desc}")
    print(f"CMD:  {cmd}")
    print('-' * 60)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        out = result.stdout.strip() if result.stdout else ""
        err = result.stderr.strip() if result.stderr else ""
        if result.returncode == 0:
            print(f"✅ PASS (exit 0)")
            if out:
                print(f"Output: {out[:300]}")
            return True
        else:
            print(f"❌ FAIL (exit {result.returncode})")
            if out:
                print(f"Output: {out[:300]}")
            if err:
                print(f"Error: {err[:300]}")
            return False
    except Exception as e:
        print(f"❌ FAIL (exception: {e})")
        return False

def check_file(path, desc):
    """Check if a file exists."""
    print(f"\n{'='*60}")
    print(f"CHECK: {desc}")
    print(f"Path: {path}")
    exists = Path(path).exists()
    if exists:
        print(f"✅ EXISTS")
        return True
    else:
        print(f"❌ MISSING")
        return False

def main():
    workspace = Path.home() / ".openclaw" / "workspace"
    skills_dir = workspace / "skills"
    passed = 0
    failed = 0

    print("=" * 60)
    print("enterprise-agent-memory 完整测试")
    print("=" * 60)

    # 1. 目录结构检查
    print("\n\n[阶段 1] 目录结构检查")
    checks = [
        (workspace / "TOOLS.md", "TOOLS.md"),
        (skills_dir / "agent-memory" / "SKILL.md", "agent-memory SKILL.md"),
        (skills_dir / "enterprise-memory" / "SKILL.md", "enterprise-memory SKILL.md"),
        (skills_dir / "task-registry" / "SKILL.md", "task-registry SKILL.md"),
        (skills_dir / "task-registry" / "scripts" / "task_registry.py", "task_registry.py"),
        (skills_dir / "tool-router" / "SKILL.md", "tool-router SKILL.md"),
        (skills_dir / "tool-router" / "scripts" / "tool_router.py", "tool_router.py"),
        (skills_dir / "permission" / "SKILL.md", "permission SKILL.md"),
    ]
    for path, desc in checks:
        if check_file(str(path), desc):
            passed += 1
        else:
            failed += 1

    # 2. Tool Router 测试
    print("\n\n[阶段 2] Tool Router 测试")
    tr_script = skills_dir / "tool-router" / "scripts" / "tool_router.py"
    if tr_script.exists():
        tests = [
            (f'python3 {tr_script} route "帮我搜索最新的AI新闻"', "中文搜索路由"),
            (f'python3 {tr_script} route "search for weather"', "英文搜索路由"),
            (f'python3 {tr_script} route "帮我运行一个shell命令"', "exec 路由"),
            (f'python3 {tr_script} route "读取文件"', "文件读取路由"),
        ]
        for cmd, desc in tests:
            if run(cmd, desc):
                passed += 1
            else:
                failed += 1
    else:
        print("❌ tool_router.py 不存在，跳过 Tool Router 测试")
        failed += 4

    # 3. Task Registry 测试
    print("\n\n[阶段 3] Task Registry 测试")
    tr_script = skills_dir / "task-registry" / "scripts" / "task_registry.py"
    if tr_script.exists():
        # list
        if run(f'python3 {tr_script} list', "Task List（当前应为空）"):
            passed += 1
        else:
            failed += 1

        # create
        result = subprocess.run(
            f'python3 {tr_script} create "测试任务" \'{{"test": true}}\'',
            shell=True, capture_output=True, text=True
        )
        task_id = None
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                task_id = data.get("id")
            except:
                pass
        if task_id:
            print(f"✅ PASS — 创建成功，task_id={task_id}")
            passed += 1
            # get
            if run(f'python3 {tr_script} get {task_id}', "Task Get"):
                passed += 1
            else:
                failed += 1
            # update
            if run(f'python3 {tr_script} update {task_id} \'{{"status": "completed"}}\'', "Task Update"):
                passed += 1
            else:
                failed += 1
            # delete (cleanup)
            if run(f'python3 {tr_script} delete {task_id}', "Task Delete"):
                passed += 1
            else:
                failed += 1
        else:
            print(f"❌ FAIL — 创建失败，无法获取 task_id")
            failed += 4
    else:
        print("❌ task_registry.py 不存在，跳过 Task Registry 测试")
        failed += 5

    # 4. Memory 目录检查
    print("\n\n[阶段 4] Memory 目录检查")
    memory_dir = workspace / "memory"
    if memory_dir.exists():
        print(f"✅ PASS — memory/ 目录存在")
        passed += 1
    else:
        print(f"❌ FAIL — memory/ 目录不存在（运行 init_memory.py 初始化）")
        failed += 1

    # 5. TOOLS.md 内容检查
    print("\n\n[阶段 5] TOOLS.md 内容检查")
    tools_md = workspace / "TOOLS.md"
    if tools_md.exists():
        content = tools_md.read_text()
        has_tools = "web_search" in content and "exec" in content and "read" in content
        if has_tools:
            print(f"✅ PASS — TOOLS.md 包含工具条目")
            passed += 1
        else:
            print(f"❌ FAIL — TOOLS.md 缺少工具条目")
            failed += 1
    else:
        print(f"❌ FAIL — TOOLS.md 不存在")
        failed += 1

    # 汇总
    print("\n\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    total = passed + failed
    print(f"通过: {passed}/{total}")
    print(f"失败: {failed}/{total}")
    if failed == 0:
        print("\n🎉 全部通过！安装成功。")
        return 0
    else:
        print(f"\n⚠️  {failed} 项失败，请检查上方输出。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

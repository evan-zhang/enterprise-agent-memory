#!/usr/bin/env python3
"""
tool_router.py — Tool routing based on TOOLS.md
route(task) / lookup(name) / list_by_category() / list_by_risk()
"""
import json
import re
from pathlib import Path

TOOLS_MD = Path.home() / ".openclaw" / "workspace" / "TOOLS.md"
TOOLS_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "tools"

# Fallback: look in skill directory
if not TOOLS_MD.exists():
    TOOLS_MD = Path(__file__).parent / ".." / ".." / ".." / "TOOLS.md"
    if not TOOLS_MD.exists():
        TOOLS_MD = Path("/etc/placeholder")  # will trigger error below

if not TOOLS_MD.exists():
    raise FileNotFoundError(
        f"TOOLS.md not found at {Path.home()/.openclaw/workspace/TOOLS.md} or in skill directory. "
        "Run: cp TOOLS.md ~/.openclaw/workspace/TOOLS.md"
    )

# Routing keywords → tool name
KEYWORD_ROUTES = {
    "web_search": ["搜索", "找一下", "查一下", "最新消息", "search", "google"],
    "read": ["看文件", "读文件", "打开", "读取", "cat", "view file"],
    "write": ["创建文件", "新建文件", "写文件", "创建", "new file"],
    "edit": ["修改", "编辑", "改一下", "edit", "change"],
    "exec": ["运行", "执行", "终端", "shell", "命令行", "run", "execute"],
    "memory_search": ["记得", "之前说过", "记忆", "memory", "remember"],
    "cron": ["定时任务", "设置提醒", "cron", "schedule"],
    "gateway": ["配置", "重启", "检查设置", "config", "restart"],
    "sessions_spawn": ["派生子任务", "后台运行", "spawn", "subagent"],
    "web_fetch": ["抓取页面", "获取网页内容", "fetch", "scrape"],
    "browser": ["浏览器", "打开网页", "截图", "browser", "open url"],
    "message": ["发消息", "发送", "通知", "message", "send"],
}

def parse_tools_md() -> dict:
    """Parse TOOLS.md into tool metadata dict."""
    content = TOOLS_MD.read_text(encoding="utf-8")
    tools = {}
    current = None
    for line in content.split("\n"):
        line = line.rstrip()
        if line.startswith("### "):
            current = line[4:].strip()
            tools[current] = {"name": current, "category": "", "risk_level": "", "permission": "", "description": "", "status": "active"}
        elif current and line.startswith("- **"):
            if "**：" in line or "**:" in line:
                # Parse key: value
                key_end = line.index("**：") if "**：" in line else line.index("**:")
                key = line[2:key_end]
                val = line[key_end+3:].strip()
                key_map = {
                    "category": "category", "risk_level": "risk_level",
                    "permission": "permission", "description": "description",
                    "status": "status", "notes": "notes"
                }
                if key in key_map:
                    tools[current][key_map[key]] = val
    return tools

def route(task: str) -> list:
    """
    Given a natural language task, return recommended tools.
    Returns list of {tool, confidence, reason}.
    """
    tools = parse_tools_md()
    task_lower = task.lower()
    candidates = []
    
    # Keyword matching
    for tool_name, keywords in KEYWORD_ROUTES.items():
        if tool_name not in tools:
            continue
        for kw in keywords:
            if kw.lower() in task_lower:
                candidates.append({
                    "tool": tool_name,
                    "confidence": "high",
                    "reason": f"Keyword match: '{kw}'",
                    "risk_level": tools[tool_name].get("risk_level", ""),
                    "permission": tools[tool_name].get("permission", ""),
                })
                break
    
    # Deduplicate
    seen = set()
    unique = []
    for c in candidates:
        if c["tool"] not in seen:
            seen.add(c["tool"])
            unique.append(c)
    
    return unique[:5]

def lookup(name: str) -> dict:
    """Get tool metadata by name."""
    tools = parse_tools_md()
    return tools.get(name, None)

def list_by_category(category: str) -> list:
    """List all tools in a category."""
    tools = parse_tools_md()
    return [t for t in tools.values() if t.get("category") == category]

def list_by_risk(risk_level: str) -> list:
    """List all tools at a given risk level."""
    tools = parse_tools_md()
    return [t for t in tools.values() if t.get("risk_level") == risk_level]

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "route"
    args = sys.argv[2:]
    if cmd == "route":
        result = route(" ".join(args))
    elif cmd == "lookup":
        result = lookup(args[0]) if args else None
    elif cmd == "list_by_category":
        result = list_by_category(args[0]) if args else []
    elif cmd == "list_by_risk":
        result = list_by_risk(args[0]) if args else []
    else:
        result = {"error": f"Unknown cmd: {cmd}"}
    print(json.dumps(result, indent=2, ensure_ascii=False))

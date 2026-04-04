#!/usr/bin/env python3
"""
log_tool_exception.py — 记录工具异常到 memory/tools-log/
"""
import argparse
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "tools-log"

def main():
    parser = argparse.ArgumentParser(description="Log tool exception")
    parser.add_argument("--tool", required=True, help="Tool name")
    parser.add_argument("--reason", required=True, help="Exception reason")
    parser.add_argument("--detail", default="", help="Optional detail")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}.md"

    entry = f"- **{args.tool}** | {args.reason} | {datetime.now().strftime('%H:%M:%S')} | {args.detail}\n"

    if log_file.exists():
        content = log_file.read_text()
        if "## 异常日志" not in content:
            content = "## 异常日志\n\n| 工具 | 原因 | 时间 | 详情 |\n|------|------|------|------|\n" + content
        log_file.write_text(content + entry)
    else:
        log_file.write_text(f"## 异常日志 — {today}\n\n| 工具 | 原因 | 时间 | 详情 |\n|------|------|------|------|\n{entry}")

    print(f"Logged to {log_file}")

if __name__ == "__main__":
    main()

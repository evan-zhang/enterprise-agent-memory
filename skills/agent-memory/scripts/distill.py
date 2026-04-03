#!/usr/bin/env python3
"""
distill.py -- 夜间蒸馏脚本
将 KAIROS 日志中的重要条目蒸馏到 topic 文件
用法: python distill.py [--base-path ~/.openclaw/workspace] [--days 3]
"""
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

def get_recent_logs(memory_dir: Path, days: int = 3) -> list:
    """获取最近 N 天的 KAIROS 日志"""
    logs_dir = memory_dir / "logs"
    if not logs_dir.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for log_file in logs_dir.rglob("*.md"):
        # 解析日期：logs/YYYY/MM/YYYY-MM-DD.md
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})\.md$", str(log_file))
        if not match:
            continue
        y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
        file_date = datetime(y, m, d)
        if file_date >= cutoff:
            recent.append(log_file)
    
    return sorted(recent)

def extract_significant_entries(log_files: list) -> list:
    """从日志中提取重要条目（简化版：所有非标题行）"""
    entries = []
    for lf in log_files:
        content = lf.read_text(encoding="utf-8")
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            # 跳过空行、标题、分隔线
            if not line or line.startswith("#") or line.startswith("--") or line.startswith("*") or ":" not in line:
                continue
            # 保留有意义的内容行
            if len(line) > 20:  # 过滤太短的行
                entries.append({"source": lf.name, "content": line})
    return entries

def write_topic_file(dir_path: Path, name: str, topic_type: str, entries: list):
    """写入 topic 文件"""
    dir_path.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w]", "-", name.lower())[:50]
    file_path = dir_path / f"{slug}.md"
    
    today = datetime.now().strftime("%Y-%m-%d")
    frontmatter = f"""--
name: {name}
type: {topic_type}
tags: [distilled]
created: {today}
updated: {today}
importance: medium
--

# {name}

## 来自 KAIROS 日志

"""
    for e in entries[:20]:  # 最多20条
        frontmatter += f"- {e['content']}\n"
    
    frontmatter += f"\n--\n*蒸馏自: {', '.join(set(e['source'] for e in entries))}*\n"
    
    file_path.write_text(frontmatter, encoding="utf-8")
    return file_path

def distill(base_path: Path, days: int = 3, verbose: bool = True):
    """执行夜间蒸馏"""
    memory_dir = base_path / "memory"
    
    # 1. 扫描最近日志
    log_files = get_recent_logs(memory_dir, days)
    if verbose:
        print(f"  扫描 {len(log_files)} 个日志文件...")
    
    # 2. 提取重要条目
    entries = extract_significant_entries(log_files)
    if verbose:
        print(f"  发现 {len(entries)} 条可能值得蒸馏的条目")
    
    if not entries:
        return
    
    # 3. 按类型简单分类（这里用关键词，实际可更复杂）
    project_entries = [e for e in entries if any(k in e['content'].lower() for k in ["项目", "project", "任务", "task"])]
    user_entries = [e for e in entries if any(k in e['content'].lower() for k in ["偏好", "preference", "喜欢", "喜欢"])]
    feedback_entries = [e for e in entries if any(k in e['content'].lower() for k in ["反馈", "feedback", "错误", "修复"])]
    
    created = []
    
    if project_entries:
        p = write_topic_file(memory_dir / "project", "近期项目记录", "project", project_entries)
        created.append(f"project/{p.name}")
    if user_entries:
        p = write_topic_file(memory_dir / "user", "用户偏好记录", "user", user_entries)
        created.append(f"user/{p.name}")
    if feedback_entries:
        p = write_topic_file(memory_dir / "feedback", "反馈记录", "feedback", feedback_entries)
        created.append(f"feedback/{p.name}")
    
    # 4. 更新 heartbeat-state.json
    state_file = memory_dir / "heartbeat-state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
    else:
        state = {}
    state["lastDistillation"] = datetime.now().isoformat()
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    
    if verbose:
        print(f"✅ 蒸馏完成，创建 {len(created)} 个 topic 文件")
        for c in created:
            print(f"  • {c}")

def main():
    parser = argparse.ArgumentParser(description="Agent Memory 夜间蒸馏")
    parser.add_argument("--base-path", default=str(Path.home() / ".openclaw" / "workspace"))
    parser.add_argument("--days", type=int, default=3, help="扫描最近N天日志")
    args = parser.parse_args()
    
    distill(Path(args.base_path), days=args.days)

if __name__ == "__main__":
    main()

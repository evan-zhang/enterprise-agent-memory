#!/usr/bin/env python3
"""
register_tools.py -- Auto-register tools from skill SKILL.md into TOOLS.md

Usage:
  python3 register_tools.py skill-name          # register
  python3 register_tools.py --unregister skill # unregister
  python3 register_tools.py --list             # list registered tools
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
TOOLS_MD = WORKSPACE / "TOOLS.md"
TOOLS_DIR = WORKSPACE / "memory" / "tools"
SKILL_DIR = WORKSPACE / "skills"


def parse_frontmatter(content):
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        block = fm_match.group(1)
        # Parse tools_provided manually
        tools = []
        in_tools = False
        current = {}
        for line in block.split('\n'):
            if line.startswith('tools_provided:'):
                in_tools = True
                continue
            if in_tools:
                if line.startswith('  - name:'):
                    if current:
                        tools.append(current)
                    current = {'name': line.split('name:')[1].strip()}
                elif ':' in line and in_tools:
                    key = line.split(':')[0].strip()
                    val = ':'.join(line.split(':')[1:]).strip().strip('"').strip("'")
                    if key in ('category', 'risk_level', 'permission', 'description', 'channels', 'status'):
                        current[key] = val
        if current:
            tools.append(current)
        return tools
    return []


def parse_tools_md():
    if not TOOLS_MD.exists():
        return {}
    content = TOOLS_MD.read_text(encoding='utf-8')
    tools = {}
    current_cat = None
    for line in content.split('\n'):
        SKIP_CATS = {'Tool Metadata Schema', 'Tool Lifecycle'}
        if line.startswith('## '):
            # Format: "## category -- description"
            # Skip non-category sections
            parts = line.lstrip('## ').split('--')
            current_cat = parts[0].strip()
            if current_cat not in SKIP_CATS:
                tools[current_cat] = []
            else:
                current_cat = None
        elif line.startswith('### '):
            tool_name = line.lstrip('# ').strip()
            if current_cat:
                tools[current_cat].append({'name': tool_name, 'category': current_cat,
                    'risk_level': '', 'permission': '', 'description': '', 'status': 'active'})
    return tools


def merge_tool(tools, tool_meta, category):
    name = tool_meta.get('name', '')
    if not name:
        return
    tools[category] = [t for t in tools.get(category, []) if t.get('name') != name]
    tools[category].append(tool_meta)


def write_tools_md(tools):
    cat_names = {
        'search': 'search -- Search Tools',
        'file': 'file -- File Operations',
        'exec': 'exec -- Execution Tools',
        'memory': 'memory -- Memory Tools',
        'system': 'system -- System Tools',
        'network': 'network -- Network Tools',
    }
    lines = [
        "# TOOLS.md -- Tool Registry",
        "---",
        f"type: tool-registry",
        f"updated: {datetime.now().strftime('%Y-%m-%d')}",
        "---",
        "",
        "## Tool Metadata Schema",
        "",
        "| Field | Description |",
        "|-------|-------------|",
        "| name | Tool name |",
        "| category | Category (search/file/exec/network/memory/system) |",
        "| risk_level | Risk level (low/medium/high/critical) |",
        "| permission | Permission (read/write/exec/admin) |",
        "| description | What the tool does |",
        "| channels | Where it works (Telegram/Discord/Web/ALL) |",
        "| status | Status (active/deprecated/disabled) |",
        "",
        "## Tool Lifecycle",
        "",
        "| Status | Description |",
        "|--------|-------------|",
        "| active | Available for use |",
        "| deprecated | Not recommended |",
        "| disabled | Cannot be used |",
        "",
    ]
    for cat, cat_tools in tools.items():
        if not cat_tools:
            continue
        lines.append(f"## {cat_names.get(cat, cat)}")
        lines.append("")
        for t in cat_tools:
            lines.append(f"### {t['name']}")
            for key in ['category', 'risk_level', 'permission', 'description', 'channels', 'status']:
                val = t.get(key, '')
                if val:
                    lines.append(f"- **{key}**: {val}")
            lines.append("")
    TOOLS_MD.write_text('\n'.join(lines), encoding='utf-8')


def create_lifecycle(tool_meta):
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    tool_file = TOOLS_DIR / f"{tool_meta['name']}.json"
    data = {
        'name': tool_meta['name'],
        'category': tool_meta.get('category', ''),
        'risk_level': tool_meta.get('risk_level', ''),
        'permission': tool_meta.get('permission', ''),
        'description': tool_meta.get('description', ''),
        'channels': tool_meta.get('channels', 'ALL'),
        'status': tool_meta.get('status', 'active'),
        'registered_at': datetime.now().isoformat(),
        'skill': tool_meta.get('skill', ''),
        'log': []
    }
    tool_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def log_event(tool_name, event, detail=''):
    tool_file = TOOLS_DIR / f"{tool_name}.json"
    if tool_file.exists():
        data = json.loads(tool_file.read_text(encoding='utf-8'))
        data['log'].append({'time': datetime.now().isoformat(), 'event': event, 'detail': detail})
        tool_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def normalize_skill_path(skill_name):
    if skill_name.startswith('skill-'):
        return SKILL_DIR / skill_name
    return SKILL_DIR / f"skill-{skill_name}"


def do_register(skill_name):
    skill_path = normalize_skill_path(skill_name)
    if not skill_path.exists():
        print(f"Error: Skill not found: {skill_path}")
        return

    print(f"\n[REGISTER] {skill_name}")
    print(f"  path: {skill_path}")

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"  Error: SKILL.md not found")
        return

    tools_meta = parse_frontmatter(skill_md.read_text(encoding='utf-8'))
    if not tools_meta:
        print(f"  [WARN] No tools_provided found - skipping")
        return

    print(f"  Found {len(tools_meta)} tools: {[t.get('name') for t in tools_meta]}")

    tools = parse_tools_md()
    for tm in tools_meta:
        tm['skill'] = skill_name
        cat = tm.get('category', 'system')
        if cat not in tools:
            tools[cat] = []
        merge_tool(tools, tm, cat)
        create_lifecycle(tm)
        log_event(tm['name'], 'registered', f'from skill {skill_name}')
        print(f"  [OK] {tm['name']} -> {cat}")

    write_tools_md(tools)
    total = sum(len(v) for v in tools.values())
    print(f"\n  TOOLS.md updated ({total} tools total)")


def do_unregister(skill_name):
    skill_path = normalize_skill_path(skill_name)
    if not skill_path.exists():
        print(f"Error: Skill not found: {skill_path}")
        return

    print(f"\n[UNREGISTER] {skill_name}")
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"  Error: SKILL.md not found")
        return

    tools_meta = parse_frontmatter(skill_md.read_text(encoding='utf-8'))
    tools = parse_tools_md()
    removed = 0
    for tm in tools_meta:
        name = tm.get('name', '')
        cat = tm.get('category', '')
        if cat in tools:
            before = len(tools[cat])
            tools[cat] = [t for t in tools[cat] if t.get('name') != name]
            if len(tools[cat]) < before:
                removed += 1
                log_event(name, 'unregistered', f'from skill {skill_name}')

    if removed:
        write_tools_md(tools)
        print(f"  Removed {removed} tools, TOOLS.md updated")
    else:
        print(f"  Nothing to unregister")


def do_list():
    tools = parse_tools_md()
    print(f"\n[TOOLS] Total: {sum(len(v) for v in tools.values())} tools across {len(tools)} categories")
    for cat, cat_tools in tools.items():
        print(f"\n  {cat} ({len(cat_tools)} tools):")
        for t in cat_tools:
            status = t.get('status', 'active')
            skill = t.get('skill', 'unknown')
            print(f"    {t['name']} [{status}] <- {skill}")


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--list' in args:
        args.remove('--list')
        do_list()
    elif '--unregister' in args:
        args.remove('--unregister')
        if not args:
            print("Error: specify skill name")
            sys.exit(1)
        do_unregister(args[0])
    else:
        if not args:
            print(__doc__)
            print("\nUsage:")
            print("  python3 register_tools.py skill-name          # register")
            print("  python3 register_tools.py --unregister name # unregister")
            print("  python3 register_tools.py --list            # list all")
            sys.exit(1)
        do_register(args[0])

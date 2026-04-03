---
name: zelda-memory
description: "Structured long-term memory system for agents. Use when: starting a new session and you need context from past sessions; User says something important about preferences feedback or project context; you need to recall information from previous sessions; managing an ongoing project across multiple sessions; checking what you knew about a topic in previous conversations. Provides MEMORY.md index, four memory types, KAIROS daily logs, frontmatter schema, heartbeat maintenance, nightly distillation and workspace scanning. Activate whenever continuity of context matters."
---

# agent-memory — 记忆系统

## What This Skill Provides

A complete structured memory system that gives agents persistent, cross-session context. Modeled after Claude Code's `memdir` architecture but adapted for OpenClaw agents.

## Architecture

```
MEMORY.md          ← 索引文件（最多 200 行 / 25KB），指向 topic 文件
memory/
  user/            ← 用户偏好和习惯
  feedback/        ← 纠偏记录
  project/         ← 项目上下文
  ref/             ← 外部系统引用
  logs/            ← KAIROS append-only daily logs (logs/YYYY/MM/YYYY-MM-DD.md)
  archive/         ← MEMORY.md 溢出归档
memory/heartbeat-state.json  ← 同步状态追踪
```

## Quick Start

### First Time Setup

```bash
python3 ~/.openclaw/workspace/skills/agent-memory/scripts/init_memory.py
```

Or manually create the directory structure if you prefer not to run scripts.

### Session Startup (read in this order)

1. `SOUL.md` → who am I
2. `USER.md` → who is the human
3. `MEMORY.md` → long-term memory index
4. `memory/logs/YYYY/MM/YYYY-MM-DD.md` → today's KAIROS log (create if missing)
5. `memory/logs/YYYY/MM/YYYY-MM-DD.md` → yesterday's log (if exists)
6. `memory/heartbeat-state.json` → sync state

Then: search `memory_search` for topic files relevant to current conversation.

### When to Write Memories

| Situation | Write to | Example |
|----------|----------|---------|
| User expresses preference | `memory/user/` | "I prefer vim" |
| User corrects you | `memory/feedback/` | "You misunderstood, actually…" |
| Project context discovered | `memory/project/` | "This project needs IE compatibility" |
| External system info | `memory/ref/` | API key location, service config |
| Important decision made | Today's KAIROS log | Append to `memory/logs/YYYY/MM/YYYY-MM-DD.md` |

## Memory Writing Rules

### Four Memory Types

```
user/       — Who the human is, their preferences, habits
feedback/   — Corrections, guidance, things to avoid
project/   — Project context not derivable from code
ref/       — External systems (API docs, credentials, services)
```

### Frontmatter Required (every topic file)

```yaml
---
name: Human-readable title
type: user | feedback | project | ref
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
importance: low | medium | high
---
```

### MEMORY.md Index Rules

- **Update** MEMORY.md when adding/removing topic files
- **Do NOT update** MEMORY.md when just editing topic file content (update the file's `updated` field instead)
- **Hard limit**: 200 lines AND 25KB — whichever hits first triggers archiving
- **Archive low-importance entries** to `memory/archive/` when approaching limits

### KAIROS Daily Log (append-only)

Path: `memory/logs/YYYY/MM/YYYY-MM-DD.md`

Format:
```markdown
# YYYY-MM-DD

## HH:MM - Event Title
- Description
- Key decision
- Follow-up action
```

**Rule**: Append only. Never edit past entries. Create date-named files.

## Maintenance (Heartbeat Integration)

Every heartbeat, check `memory/heartbeat-state.json`:

```python
import json
state = json.load(open("memory/heartbeat-state.json"))
if state.get("lastMemorySync") is None or \
   hours_since(state["lastMemorySync"]) > 4:
    # Run: python scripts/memory_sync.py
```

Nightly distillation (02:00-03:00 local):
```python
if is_between("02:00", "03:00") and \
   hours_since(state.get("lastDistillation", 0)) > 12:
    # Run: python scripts/distill.py
```

Workspace scan (every 3rd sync):
```python
if state.get("memorySyncCount", 0) % 3 == 0 and \
   hours_since(state.get("lastWorkspaceScan", 0)) > 8:
    # Scan workspace for new/modified files worth remembering
```

## Key Patterns

### Proactive Retrieval (before answering)
```
User: "继续上次那个项目"
→ memory_search("上次 项目")
→ Found: memory/project/my-project.md
→ Load context, then proceed
```

### Writing a New Memory
```
User: "我喜欢用 zsh，不用 bash"
→ Determine type: user
→ Write to: memory/user/shell-preference.md (with frontmatter)
→ Update MEMORY.md index
→ Log to today's KAIROS: "User 偏好 zsh"
```

### Tool Selection (using TOOLS.md)
```
Before using exec: consult TOOLS.md for risk_level and permission
Before searching: consult TOOLS.md for search tool options
```

## References

- **Memory types**: See `references/memory-types.md` for detailed type descriptions
- **Frontmatter**: See `references/frontmatter.md` for schema spec
- **Startup workflow**: See `references/startup-workflow.md` for complete procedure

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/init_memory.py` | Initialize directory structure (first time) |
| `scripts/memory_sync.py` | Regular memory sync and MEMORY.md archiving |
| `scripts/distill.py` | Nightly distillation of KAIROS logs to topic files |

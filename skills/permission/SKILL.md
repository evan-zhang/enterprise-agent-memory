---
name: skill-permission
description: Permission system for agents. Use when: calling a tool with risk_level=high or critical; executing commands that modify files or state; performing actions that require explicit authorization. Provides permission level definitions, checking rules, and audit logging. Convention-based (agent self-enforces), not code-enforced. Activate before every tool call involving exec/write/admin operations.
---

# skill-permission — Permission System

## Overview

Four-level permission model. Convention-based — the agent self-enforces at reasoning time, not at execution time.

## Permission Levels

| Level | Name | Description | Auto-approve |
|-------|------|------------|-------------|
| `read` | Read | Non-destructive reads | ✅ Always |
| `write` | Write | File modifications | ✅ With task context |
| `exec` | Execute | Shell commands | ⚠️ Requires task context |
| `admin` | Admin | Gateway-level operations | ❌ Always confirm |

## Permission Check

Before every tool call:

```
1. Look up tool's permission level from TOOLS.md
2. Check if current context has sufficient permission
3. If insufficient: STOP, ask owner
4. If sufficient: proceed, log to memory/tools-log/
```

## When to Stop and Ask

Stop and ask owner when:
- `risk_level = critical` AND no clear task context
- `permission = admin` regardless of context
- Tool call would modify files outside `~/.openclaw/workspace/`
- External communication (email, social media)

## Audit Logging

Log to `memory/tools-log/YYYY-MM-DD.md`:

```
| tool | permission | decision | reason | time |
|------|------------|----------|--------|------|
| exec | admin | DENIED | no task context | 14:30 |
| exec | exec | APPROVED | task: read log | 14:31 |
```

## Risk Level Mapping

| risk_level | permission | Action |
|------------|------------|--------|
| low | read | Auto-approve |
| medium | write | Task context required |
| high | exec | Explicit task context |
| critical | admin | Always ask owner |

## Hard Stops

These always require owner confirmation:
- `rm -rf` or `dd` commands
- Modifying `~/.ssh/` or system config
- Sending external communications
- Gateway restart with `--force`

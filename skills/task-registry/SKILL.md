---
name: skill-task-registry
description: Task Registry for agents. Use when: creating, tracking, or managing sub-tasks spawned via sessions_spawn; checking status of background tasks; updating task state; stopping tasks; listing active tasks. Provides create/get/list/stop/update/output operations for agent-internal task tracking. Integrates with OpenClaw tasks via task ID mapping. Activate when managing multi-task workflows or background agents.
---

# skill-task-registry — Task Registry

## Overview

Task Registry tracks agent-internal sub-tasks, mapping OpenClaw task IDs to agent context.

**Key principle**: Task Registry wraps OpenClaw native tasks, it does NOT replace them. Namespace isolation ensures no conflict.

## Architecture

```
memory/tasks/
  {task-id}.json     # Per-task metadata
  index.json          # Task ID → context mapping
  logs/
    {task-id}.md      # Per-task execution log
```

## Data Model

```json
{
  "id": "task-uuid",
  "openclawTaskId": "openclaw-task-id",
  "name": "task name",
  "status": "created|running|completed|failed|stopped",
  "createdAt": "ISO timestamp",
  "updatedAt": "ISO timestamp",
  "result": {},
  "error": null,
  "context": {}
}
```

## Operations

### Task.create(name, context?)

Create a new task entry before spawning.

```python
Task.create("analyze CLAUDE CODE source", {"project": "claude-code"})
```

### Task.get(id)

Retrieve task by ID.

```python
task = Task.get("task-uuid")
# Returns full task JSON or None
```

### Task.list()

List all tasks (optionally filtered by status).

```python
Task.list()                   # All tasks
Task.list(status="running")   # Filtered
```

### Task.stop(id)

Mark task as stopped.

```python
Task.stop("task-uuid")
```

### Task.update(id, updates)

Update task fields (status, result, error).

```python
Task.update("task-uuid", {"status": "completed", "result": {...}})
```

### Task.output(id)

Get task output/result.

```python
Task.output("task-uuid")
# Returns {"output": ..., "status": ...}
```

## Integration with OpenClaw Tasks

OpenClaw tasks are managed via `openclaw tasks list/show/cancel`. Task Registry wraps them:

- When spawning a sub-agent: `Task.create()` → store context
- When sub-agent completes: `Task.update(id, {"status": "completed", "result": ...})`
- When stopping: `Task.stop(id)` (maps to `openclaw tasks cancel`)

## Logging

Append task events to `memory/tasks/logs/{id}.md`:

```markdown
# Task: {name} ({id})

## Log

### HH:MM - Created
- Context: {...}

### HH:MM - Status changed: running → completed
- Result: {...}
```

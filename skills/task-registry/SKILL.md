---
name: skill-task-registry
description: "Task Registry for agents. Use when: creating, tracking, or managing sub-tasks spawned via sessions_spawn; checking status of background tasks; updating task state; stopping tasks; listing active tasks. Provides create/get/list/stop/update/output operations for agent-internal task tracking. Integrates with OpenClaw tasks via task ID mapping. Activate when managing multi-task workflows or background agents."
tools_provided:
  - name: task_registry
    category: system
    risk_level: medium
    permission: write
    description: "Task lifecycle management: create/get/list/stop/update/output"
    channels: ALL
    status: active
---

# skill-task-registry — Task Registry

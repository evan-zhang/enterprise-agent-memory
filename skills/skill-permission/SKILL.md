---
name: skill-permission
description: "Permission system for agents. Use when: calling a tool with risk_level=high or critical; executing commands that modifying files or state; performing actions that require explicit authorization. Provides permission level definitions, checking rules, and audit logging. Convention-based (agent self-enforces), not code-enforced. Activate before every tool call involving exec/write/admin operations."
tools_provided:
  - name: permission_check
    category: system
    risk_level: low
    permission: read
    description: "Four-level permission check: read/write/exec/admin with convention-based enforcement"
    channels: ALL
    status: active
---

# skill-permission — Permission System

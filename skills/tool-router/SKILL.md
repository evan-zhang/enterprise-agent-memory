---
name: skill-tool-router
description: "Tool routing for agents. Use when: deciding which tool to use for a given task; checking if a tool is available; verifying tool metadata before calling; resolving tool name conflicts. Provides tool lookup, keyword-based routing, and metadata verification. Activate before every tool call."
tools_provided:
  - name: tool_router
    category: system
    risk_level: low
    permission: read
    description: "Semantic tool routing by task description: route/lookup/list_by_category/list_by_risk"
    channels: ALL
    status: active
---

# skill-tool-router — Tool Routing

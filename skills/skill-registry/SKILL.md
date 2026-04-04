# SKILL.md — skill-registry

> Tool Registry Skill for Zelda — 提供工具路由和元数据查询能力。

---
name: skill-registry
description: Zelda 工具注册表 Skill，支持工具元数据查询、语义路由辅助、异常日志记录。
updated: 2026-04-03
owner: zelda
tools_provided:
  - name: log_tool_exception
    category: system
    risk_level: low
    permission: write
    description: "Log tool exceptions to memory/tools-log/YYYY-MM-DD.md"
    channels: ALL
    status: active
---

## 工具

### registry_lookup

按类别或风险等级查询已注册工具。

```
registry_lookup --category search --risk low
registry_lookup --all
```

### route_hint

给定用户查询，返回最可能匹配的工具名称和理由。

```
route_hint "帮我搜索一下最新的 AI 新闻"
route_hint "读取 /root/.openclaw/workspace/MEMORY.md"
```

### log_tool_exception

记录工具调用异常（失败/超时/未预期结果）到 `memory/tools-log/YYYY-MM-DD.md`。

```
log_tool_exception --tool exec --reason "timeout" --detail "ls /root timed out after 30s"
```

---

## 技术实现

- 工具元数据来源：`~/.openclaw/workspace/TOOLS.md`
- 异常日志目录：`~/.openclaw/workspace/memory/tools-log/`
- 日志格式：按日滚动，仅记录失败/超时

---
name: skill-tool-router
description: Tool routing for agents. Use when: deciding which tool to use for a given task; checking if a tool is available; verifying tool metadata before calling; resolving tool name conflicts. Provides tool lookup, keyword-based routing, and metadata verification. Activate before every tool call.
---

# skill-tool-router — Tool Routing

## Overview

Given a natural language task description, return recommended tools with reasoning.

## Usage

### route(task_description)

Input: 自然语言任务描述
Output: 推荐工具列表 + 理由

```
route("帮我搜索一下最新的 AI 新闻")
route("读取 MEMORY.md 的内容")
route("帮我把这些文件整理一下")
```

### lookup(tool_name)

Check if a tool exists and return its metadata.

```
lookup("web_search")
lookup("exec")
```

### list_by_category(category)

List all tools in a category.

```
list_by_category("search")
list_by_category("exec")
list_by_category("file")
```

### list_by_risk(risk_level)

List all tools at a given risk level.

```
list_by_risk("low")
list_by_risk("critical")
```

## Routing Logic

1. Parse task description for keywords
2. Match against TOOLS.md Tool Routes table
3. If no keyword match, fall back to semantic search
4. Return top 3 candidates with confidence scores

## Confidence Scores

| Score | Meaning |
|-------|---------|
| high | Exact keyword match |
| medium | Category match |
| low | Semantic similarity |

## Tool Metadata

When choosing a tool, verify:
1. Tool exists (not deprecated/disabled)
2. Risk level is appropriate for the task
3. Permission level is available in current context

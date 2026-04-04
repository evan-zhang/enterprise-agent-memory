# TOOLS.md -- Tool Registry
---
updated: 2026-04-04
---

## Tool Metadata Schema

| Field | Description |
|-------|-------------|
| name | Tool name |
| category | Category |
| risk_level | Risk (low/medium/high/critical) |
| permission | Permission (read/write/exec/admin) |
| status | active/deprecated/disabled |

## system -- System Tools

### eam_init
- **category**: system
- **risk_level**: medium
- **permission**: write
- **description**: Initialize a new EAM project (creates SOP directory structure)
- **status**: active

### eam_switch
- **category**: system
- **risk_level**: medium
- **permission**: write
- **description**: Switch active EAM project
- **status**: active

### eam_compress
- **category**: system
- **risk_level**: medium
- **permission**: write
- **description**: Compress old KAIROS logs and archive snapshots
- **status**: active

### permission_check
- **category**: system
- **risk_level**: low
- **permission**: read
- **description**: Four-level permission check: read/write/exec/admin with convention-based enforcement
- **status**: active

### task_registry
- **category**: system
- **risk_level**: medium
- **permission**: write
- **description**: Task lifecycle management: create/get/list/stop/update/output
- **status**: active

### tool_router
- **category**: system
- **risk_level**: low
- **permission**: read
- **description**: Semantic tool routing by task description: route/lookup/list_by_category/list_by_risk
- **status**: active

### register_tools
- **category**: system
- **risk_level**: medium
- **permission**: write
- **description**: Tool registration CLI: discover/list/register/register-all across gateway and agent layers
- **status**: active

### log_tool_exception
- **category**: system
- **risk_level**: low
- **permission**: write
- **description**: Log tool exceptions to memory/tools-log/YYYY-MM-DD.md
- **channels**: ALL
- **status**: active

## memory -- Memory Tools

### memory_init
- **category**: memory
- **risk_level**: medium
- **permission**: write
- **description**: Initialize memory directory structure (user/feedback/project/ref/logs/archive)
- **status**: active

### memory_sync
- **category**: memory
- **risk_level**: medium
- **permission**: write
- **description**: Sync and update MEMORY.md index with latest topic files
- **status**: active

### memory_distill
- **category**: memory
- **risk_level**: medium
- **permission**: write
- **description**: Nightly distillation: scan KAIROS logs, create/update topic files
- **status**: active

## openclaw

### web_search

### read

### write

### edit

### exec

### cron

### sessions_spawn

### message

### web_fetch

### browser

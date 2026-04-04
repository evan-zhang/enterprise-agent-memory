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

## memory -- Memory Tools

### memory_init
- **category**: memory
- **risk_level**: medium
- **permission**: write
- **description**: Initialize memory directory structure (user/feedback/project/ref/logs/archive)
- **channels**: ALL
- **status**: active

### memory_sync
- **category**: memory
- **risk_level**: medium
- **permission**: write
- **description**: Sync and update MEMORY.md index with latest topic files
- **channels**: ALL
- **status**: active

### memory_distill
- **category**: memory
- **risk_level**: medium
- **permission**: write
- **description**: Nightly distillation: scan KAIROS logs, create/update topic files
- **channels**: ALL
- **status**: active

## openclaw -- OpenClaw Native Tools

### web_search
- **category**: search
- **risk_level**: low
- **permission**: read
- **description**: Web search via DuckDuckGo
- **channels**: ALL
- **status**: active

### read
- **category**: file
- **risk_level**: medium
- **permission**: read
- **description**: Read file contents
- **channels**: ALL
- **status**: active

### write
- **category**: file
- **risk_level**: high
- **permission**: write
- **description**: Create or overwrite files
- **channels**: ALL
- **status**: active

### edit
- **category**: file
- **risk_level**: high
- **permission**: write
- **description**: Precise text replacement
- **channels**: ALL
- **status**: active

### exec
- **category**: exec
- **risk_level**: critical
- **permission**: exec
- **description**: Execute shell commands
- **channels**: ALL
- **status**: active

### cron
- **category**: system
- **risk_level**: medium
- **permission**: admin
- **description**: Manage Gateway cron jobs and wake events
- **channels**: ALL
- **status**: active

### sessions_spawn
- **category**: system
- **risk_level**: high
- **permission**: admin
- **description**: Spawn sub-agent or ACP coding session
- **channels**: ALL
- **status**: active

### message
- **category**: system
- **risk_level**: high
- **permission**: exec
- **description**: Send messages via channel plugins
- **channels**: ALL
- **status**: active

### web_fetch
- **category**: network
- **risk_level**: low
- **permission**: read
- **description**: Fetch URL content (HTML to markdown)
- **channels**: ALL
- **status**: active

### browser
- **category**: network
- **risk_level**: medium
- **permission**: read
- **description**: Control browser (snapshot/actions/open)
- **channels**: ALL
- **status**: active

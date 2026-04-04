# TOOLS.md — Zelda 工具注册表

> **注**：本文件是 Zelda 的 Tool Registry，记录所有可用工具的元数据。支持语义路由和权限上下文过滤。

---
type: tool-registry
updated: 2026-04-04
owner: shared
---

## 工具元数据 Schema

每个工具条目包含：
- **name**：工具名称
- **category**：工具类别（search/file/exec/network/memory/system）
- **risk_level**：风险等级（low/medium/high/critical）
- **permission**：权限模式（read/write/exec/admin）
- **description**：工具描述（用于语义路由匹配）
- **channels**：可用 channel（Telegram/Discord/Web/ALL）
- **status**：工具状态（active/deprecated/disabled）

## 工具生命周期

> 工具注册表采用 per-tool 文件结构：memory/tools/{tool-name}.json

| 状态 | 说明 |
|------|------|
| `active` | 可用，正常调用 |
| `deprecated` | 不推荐，仍可用 |
| `disabled` | 禁用，不可调用 |

## search — 搜索工具

### web_search
- **category**：search
- **risk_level**：low
- **permission**：read
- **description**：网络搜索，基于 DuckDuckGo，返回标题/URL/摘要
- **channels**：ALL
- **status**：active
- **notes**：主力搜索工具，免费不占 ZAI 配额

### ZAI_MCP_web_search
- **category**：search
- **risk_level**：low
- **permission**：read
- **description**：ZAI Web Search MCP，走 Coding Plan 配额
- **channels**：ALL
- **status**：disabled
- **notes**：ZAI MCP 工具调用被拒绝（Prototype 计划权限问题），暂不可用

## file — 文件操作工具

### read
- **category**：file
- **risk_level**：medium
- **permission**：read
- **description**：读取文件内容，支持大文件截断（2000行/50KB）
- **channels**：ALL
- **status**：active

### write
- **category**：file
- **risk_level**：high
- **permission**：write
- **description**：创建或覆盖文件，自动创建父目录
- **channels**：ALL
- **status**：active
- **notes**：破坏性操作——覆盖已有文件时不留痕

### edit
- **category**：file
- **risk_level**：high
- **permission**：write
- **description**：精确文本替换，需要精确匹配原文本
- **channels**：ALL
- **status**：active
- **notes**：非破坏性编辑，推荐优先使用

## exec — 执行工具

### exec
- **category**：exec
- **risk_level**：critical
- **permission**：exec
- **description**：执行 shell 命令，支持 PTY 模式
- **channels**：ALL
- **status**：active
- **notes**：危险工具。破坏性命令（rm -rf/dd）需要明确任务上下文。按 TPR 授权原则执行。

## memory — 记忆工具

### memory_search
- **category**：memory
- **risk_level**：low
- **permission**：read
- **description**：语义搜索 MEMORY.md 和 memory/*.md
- **channels**：ALL
- **status**：active

### memory_get
- **category**：memory
- **risk_level**：low
- **permission**：read
- **description**：安全读取记忆文件片段，按行号范围
- **channels**：ALL
- **status**：active

## system — 系统工具

### cron
- **category**：system
- **risk_level**：medium
- **permission**：admin
- **description**：管理 Gateway cron 任务和唤醒事件
- **channels**：ALL
- **status**：active

### gateway
- **category**：system
- **risk_level**：critical
- **permission**：admin
- **description**：重启 Gateway、配置检查、应用配置
- **channels**：ALL
- **status**：active

### sessions_spawn
- **category**：system
- **risk_level**：high
- **permission**：admin
- **description**：派生独立 sub-agent 或 ACP coding session
- **channels**：ALL
- **status**：active

### message
- **category**：system
- **risk_level**：high
- **permission**：exec
- **description**：跨 channel 发送消息和管理
- **channels**：ALL
- **status**：active
- **notes**：对外通信，发送前通知 Evan

## network — 网络工具

### web_fetch
- **category**：network
- **risk_level**：low
- **permission**：read
- **description**：抓取 URL 内容（HTML→markdown/text），最大截断 50KB
- **channels**：ALL
- **status**：active

### browser
- **category**：network
- **risk_level**：medium
- **permission**：read
- **description**：控制浏览器（status/start/stop/snapshot/actions）
- **channels**：ALL
- **status**：active

## Tool Routes — 语义路由参考

| 工具名 | 触发关键词 |
|--------|-----------|
| web_search | 搜索、找一下、查一下、最新消息 |
| read | 看文件、读文件、打开 |
| write | 创建文件、新建文件，写文件 |
| edit | 修改、编辑、改一下 |
| exec | 运行、执行、终端、shell |
| memory_search | 记得、之前说过、记忆 |
| cron | 定时任务、设置提醒 |
| gateway | 配置、重启、检查设置 |
| sessions_spawn | 派生子任务、后台运行 |
| web_fetch | 抓取页面、获取网页内容 |
| browser | 浏览器、打开网页、截图 |

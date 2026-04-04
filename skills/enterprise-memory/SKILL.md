---
name: enterprise-memory
version: 1.2.1
description: EAM 规范（Enterprise Agent Memory）企业级 Agent 记忆体系。当用户提到 EAM、企业级记忆、全局项目、项目列表、项目状态、切换项目、查看项目、记忆体系、跨项目共享、全局记忆层时自动加载。提供项目级隔离、状态同步、快照压缩能力。
metadata:
  openclaw:
    requires:
      bins: [python3]
      python: ">=3.10"
homepage: https://github.com/evan-zhang/enterprise-agent-memory
tools_provided:
  - name: eam_init
    category: system
    risk_level: medium
    permission: write
    description: "Initialize a new EAM project (creates SOP directory structure)"
    channels: ALL
    status: active
  - name: eam_switch
    category: system
    risk_level: medium
    permission: write
    description: "Switch active EAM project"
    channels: ALL
    status: active
  - name: eam_compress
    category: system
    risk_level: medium
    permission: write
    description: "Compress old KAIROS logs and archive snapshots"
    channels: ALL
    status: active
---

# SKILL.md — enterprise-memory

## 项目信息

- **GitHub**: https://github.com/evan-zhang/enterprise-agent-memory
- **ClawHub**: https://clawhub.ai/evan-zhang/enterprise-memory
- **问题反馈**: https://github.com/evan-zhang/enterprise-agent-memory/issues
- **规范名称**: EAM 规范 (Enterprise Agent Memory)

## 触发词

```
EAM                          ← 识别 EAM 规范
企业级记忆                   ← 识别 EAM 规范
/切换项目 <关键词>
/新建项目 <项目名>
/项目列表
/项目搜索 <关键词>
SOP                          ← 识别 SOP 流程
新建SOP                      ← 创建 SOP 实例
创建任务                     ← 创建 SOP 实例
快速任务                     ← SOP Lite 模式
完整SOP                      ← SOP Full 模式
SOP Lite / SOP Full         ← 模式选择
任务交接                     ← SOP 交接流程
升级任务                     ← SOP Lite→Full 升级
```

## 描述

**EAM 规范**（Enterprise Agent Memory）企业级 Agent 记忆体系 Skill，内置 SOP 执行流程能力。

当用户提到以下内容时自动加载：EAM、企业级记忆、全局项目、项目列表、项目状态、切换项目、查看项目、记忆体系、记住项目、跨项目共享、全局记忆层、SOP、新建SOP、创建任务、快速任务、完整SOP、任务交接、升级任务。

核心路径：`~/.openclaw/EAM-projects/` 是所有全局项目的存储位置。

提供项目级隔离、状态同步、快照压缩能力，以及 SOP 流程管理（确认门禁、多轮确认、Lite/Full 模式、任务交接、模式升级）。

---

## 核心能力

### 1. AI 适配 + 代码校验

**核心思路**：约束 + 校验 + AI 生成

```
用户请求 → LLM 理解约束 → 生成结构化文件 → 代码校验 → 成功/失败
```

**分工原则**：
| 分工 | 负责 |
|------|------|
| 理解语义 | LLM |
| 生成文件 | LLM |
| 格式校验 | 代码 |
| 冲突处理 | prompt + warn |

### 2. 项目创建（AI 适配）

当用户说"创建项目"时，使用以下 Prompt 模板：

```
SYSTEM_PROMPT = """
你是 enterprise-memory 项目创建的适配层。

## 底座约束（HARD，必须符合）
- id 格式：SOP-{日期}-{序号}-{名称}
  示例：SOP-20260402-01-HarnessEngineering
- status 枚举：DISCUSSING | READY | RUNNING | REVIEWING | WAITING_USER | PAUSED | BLOCKED | ON_HOLD | CANCELLED | DONE | ARCHIVED | HANDOVER_PENDING | UPGRADED
- stage 枚举：TARGET | PLAN | CHECKLIST | EXECUTE | ARCHIVE | DONE
- mode：lite | full
- source：sop | manual | import

## 软约束（LLM 理解）
- title：1-100 字符的项目标题
- owner：用户名
- resume.nextAction：下一步操作

## 方法论语义（来自 {methodology_name}）
{methodology_semantics}

## 输出要求
生成符合底座约束的 state.json 内容。
"""
```

### 3. 字段映射

| state.json status | 底座值 | INDEX.md 值 | 语义 |
|------------------|--------|------------|------|
| DISCUSSING | DISCUSSING | IDLE | 讨论中 |
| READY | READY | READY | 已确认 |
| RUNNING | RUNNING | RUNNING | 执行中 |
| REVIEWING | REVIEWING | REVIEWING | 复核中 |
| WAITING_USER | WAITING_USER | WAITING | 等待用户 |
| PAUSED | PAUSED | PAUSED | 已暂停 |
| BLOCKED | BLOCKED | BLOCKED | 被阻塞 |
| ON_HOLD | ON_HOLD | ON_HOLD | 搁置 |
| CANCELLED | CANCELLED | CANCELLED | 已取消 |
| DONE | DONE | DONE | 已完成 |
| ARCHIVED | ARCHIVED | ARCHIVED | 已归档 |
| HANDOVER_PENDING | HANDOVER_PENDING | HANDOVER | 交接中 |
| UPGRADED | UPGRADED | UPGRADED | 已升级 |

### 4. 校验层

**关键字段（必须校验）**：
- `id`：格式 `^SOP-\d{8}-\d{2}-[\w-]+$`
- `status`：枚举值
- `stage`：枚举值
- `createdAt`：ISO8601 格式

**非关键字段（警告）**：
- `title`：非空 + 长度
- `owner`：非空

---

## 全局记忆层结构

```
~/.openclaw/EAM-projects/
├── GLOBAL-INDEX.md              # 全局项目索引
├── CHARTER.md                   # 项目宪章（约束定义）
├── current-project.json         # 当前项目指针
├── SOP-{日期}-{序号}-{名称}/    # 项目目录
│   ├── state.json              # 项目状态（含 SOP 扩展字段）
│   ├── INDEX.md                # 项目索引
│   ├── TASK.md                 # 任务定义
│   ├── LOG.md                  # 执行日志
│   ├── RESULT.md               # 结果留痕（Lite/Full）
│   ├── HANDOVER.md             # 交接文档（Lite/Full）
│   ├── PLAN.md                 # 执行计划（仅 Full）
│   ├── DECISIONS.md            # 决策记录（仅 Full）
│   ├── ARTIFACTS.md            # 产物清单（仅 Full）
│   └── snapshot/               # 快照目录
└── archive/                    # 归档目录
```

---

## 命令参考

### 项目创建（EAM 底座）
```bash
python scripts/switch_project.py --new --name <项目名> --description <描述>
```

### SOP 实例创建
```bash
# Lite 模式（四件套）
python scripts/sop_init.py --title "任务标题" --mode lite --owner <负责人>

# Full 模式（七件套）
python scripts/sop_init.py --title "任务标题" --mode full --owner <负责人> --description "描述"

# 预览模式
python scripts/sop_init.py --title "任务标题" --mode lite --owner <负责人> --dry-run
```

### SOP 状态管理
```bash
# 直接设置状态
python scripts/sop_state.py --instance-path <path> --status RUNNING

# 语义化操作
python scripts/sop_state.py --instance-path <path> --action pause --reason "等反馈"
python scripts/sop_state.py --instance-path <path> --action resume
python scripts/sop_state.py --instance-path <path> --action shelve --reason "优先级降低"
python scripts/sop_state.py --instance-path <path> --action restart
python scripts/sop_state.py --instance-path <path> --action wait-user --waiting-for "确认部署"
python scripts/sop_state.py --instance-path <path> --action reviewed

# 多轮确认计数
python scripts/sop_state.py --instance-path <path> --action increment-confirm

# 高风险操作（需 --confirm）
python scripts/sop_state.py --instance-path <path> --status DONE --confirm
python scripts/sop_state.py --instance-path <path> --status ARCHIVED --confirm
python scripts/sop_state.py --instance-path <path> --owner <new_owner> --confirm
```

### SOP 交接
```bash
python scripts/sop_handover.py --instance-path <path> \
    --from-owner <当前负责人> --to-owner <新负责人> \
    --reason "交接原因" --next-steps "后续步骤"
```

### SOP 升级（Lite → Full）
```bash
python scripts/sop_upgrade.py --instance-path <path> --reason "升级原因"
```

### 项目切换（EAM 底座）
```bash
# 切出
python scripts/switch_project.py --exit --project-dir <path>

# 切入
python scripts/switch_project.py --enter --keyword <关键词>

# 列表（支持 source 过滤）
python scripts/switch_project.py --list
python scripts/switch_project.py --list --source sop

# 搜索
python scripts/switch_project.py --search <关键词>
```

### INDEX 同步
```bash
python scripts/update_index.py --project-dir <path>
python scripts/update_index.py --project-dir <path> --dry-run
```

### 快照压缩
```bash
python scripts/compress.py --snapshot <snapshot_dir>
python scripts/compress.py --snapshot <snapshot_dir> --dry-run
```

---

## 实现要求

- Python 3.9+（使用 `from __future__ import annotations`）
- 所有写入使用原子操作（临时文件 → 校验 → rename）
- 完善的错误处理和日志
- 每个脚本支持 `--dry-run`
- 导入路径：相对于项目根目录
- 向后兼容：旧项目无 SOP 字段不影响

---

## 安全警告

**LLM 压缩数据外泄风险**

`compress.py` 支持可选的 LLM 压缩功能。如果启用：
- 会将项目内容 POST 到指定的 API 端点
- 项目数据会传输到外部服务器
- 请确认 API 端点可信后再启用

建议在生产环境中谨慎使用此功能。

---

## 目录结构

```
enterprise-memory/
├── scripts/
│   ├── switch_project.py      # EAM 底座：项目切换/创建
│   ├── update_index.py        # EAM 底座：INDEX 同步
│   ├── compress.py            # EAM 底座：快照压缩
│   ├── __init__.py
│   ├── sop_init.py            # SOP: 实例初始化
│   ├── sop_state.py           # SOP: 状态管理
│   ├── sop_handover.py        # SOP: 任务交接
│   └── sop_upgrade.py         # SOP: Lite→Full 升级
├── references/
│   ├── sop-lite-guide.md      # SOP Lite 使用指南
│   ├── sop-full-guide.md      # SOP Full 使用指南
│   ├── shared/
│   │   ├── state-machine.md   # 状态机定义
│   │   ├── confirm-protocol.md # 确认协议
│   │   └── upgrade-rules.md   # 升级规则
│   └── templates/
│       ├── lite/
│       │   ├── TASK-template.md
│       │   ├── LOG-template.md
│       │   ├── RESULT-template.md
│       │   └── HANDOVER-template.md
│       └── full/
│           ├── PLAN-template.md
│           ├── DECISIONS-template.md
│           └── ARTIFACTS-template.md
├── SKILL.md
├── CHARTER.md
└── docs/
```

---

## 版本

- Phase 1: 2026-03-31
- Phase 1.1: 2026-04-02（AI 适配方案）
- **v2.0: 2026-04-02（吸收 CMS-SOP，统一 SOP 能力）**
  - 统一 state.json schema（EAM + SOP 扩展字段）
  - 新增 4 个 SOP 脚本（sop_init / sop_state / sop_handover / sop_upgrade）
  - 扩展 STATUS_MAP（13 个状态）
  - 迁移模板和参考文档
  - Python 3.9+ 兼容

---

## Web 搜索与数据抓取能力

### 触发词

```
联网搜索                    ← 触发 web_search
读取网页                    ← 触发 jina.ai
抓取数据                   ← 触发 Firecrawl
浏览器操作                 ← 触发 agent-browser
```

### 数据抓取工具矩阵

| 工具 | 用途 | 成本 | 使用方式 |
|------|------|------|----------|
| **jina.ai** | 读取任意网页 | 免费 | `curl -s "https://r.jina.ai/[URL]"` |
| **agent-reach** | 搜索14个平台 | 免费 | Skill 触发词 |
| **agent-browser** | 浏览器自动化 | 免费 | Skill 触发词 |
| **Firecrawl** | 数据提取/RAG | 免费500积分起 | API 调用 |

### 工具选择决策树

```
收到任务
│
├─ 封闭平台/头条/微信？
│   └─ → jina.ai（curl）
│
├─ 社交媒体搜索？（推特/Reddit/微博）
│   └─ → agent-reach
│
├─ 需要填表/登录/复杂交互？
│   └─ → agent-browser
│
├─ 批量数据提取/RAG？
│   └─ → Firecrawl
│
└─ 简单读取网页？
    └─ → jina.ai
```

### 快速使用

#### 1. jina.ai（首选，最快）

```bash
curl -s "https://r.jina.ai/[URL]"
```

示例：
```bash
curl -s "https://r.jina.ai/https://toutiao.com/article/12345"
```

#### 2. agent-reach（平台搜索）

触发词示例：
- "搜一下最近的AI新闻"
- "搜索推特上的xxx"
- "读取这个GitHub仓库"

#### 3. agent-browser（复杂交互）

触发词示例：
- "帮我登录这个网站"
- "填表并提交"
- "截图这个页面"

#### 4. Firecrawl（专业数据提取）

```python
from firecrawl import Firecrawl
app = Firecrawl(api_key='your-key')
data = app.scrape(url='https://example.com')
```

### 医疗/医药研究场景

| 需求 | 推荐工具 |
|------|---------|
| 靶点搜索 | agent-reach + jina.ai |
| 专利分析 | jina.ai + Firecrawl |
| 文献调研 | jina.ai + Tavily |
| 社交媒体讨论 | agent-reach |

### Browser-Gateway 架构

对于需要登录的收费网站，可部署 Browser-Gateway：

```
用户 → OpenClaw Agent → Playwright MCP → Chrome（已登录）→ 收费网站
```

特点：
- Mac Mini 独占登录
- 单一会话管理
- 排队队列处理并发

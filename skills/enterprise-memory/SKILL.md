# SKILL.md — enterprise-memory

## 项目信息

- **GitHub**: https://github.com/evan-zhang/enterprise-agent-memory
- **ClawHub**: https://clawhub.com/evan-zhang/enterprise-memory
- **问题反馈**: https://github.com/evan-zhang/enterprise-agent-memory/issues
- **规范名称**: EAM 规范 (Enterprise Agent Memory)

## 触发词

```
EAM                          ← 识别 EAM 规范
企业级记忆                  ← 识别 EAM 规范
/e切换项目 <关键词>
/新建项目 <项目名>
/项目列表
/项目搜索 <关键词>
```

## 描述

**EAM 规范**（Enterprise Agent Memory）企业级 Agent 记忆体系 Skill。

当用户提到以下内容时自动加载：EAM、企业级记忆、全局项目、项目列表、项目状态、切换项目、查看项目、记忆体系、记住项目、跨项目共享、全局记忆层。

核心路径：`~/.openclaw/EAM-projects/` 是所有全局项目的存储位置。

提供项目级隔离、状态同步、快照压缩能力。

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
- status 枚举：DISCUSSING | READY | RUNNING | PAUSED | BLOCKED | DONE
- stage 枚举：TARGET | PLAN | CHECKLIST | EXECUTE | ARCHIVE | DONE
- mode：lite | full

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

| state.json status | 底座值 | CMS SOP 语义 |
|------------------|--------|-------------|
| DISCUSSING | DISCUSSING | 讨论中 |
| READY | READY | 已确认 |
| RUNNING | RUNNING | 执行中 |
| PAUSED | PAUSED | 已暂停 |
| BLOCKED | BLOCKED | 被阻塞 |
| DONE | DONE | 已完成 |

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
├── CHARTER.md                  # 项目宪章（约束定义）
├── current-project.json        # 当前项目指针
├── SOP-{日期}-{序号}-{名称}/   # 项目目录
│   ├── state.json             # 项目状态
│   ├── INDEX.md               # 项目索引
│   ├── TASK.md               # 任务定义
│   ├── LOG.md                # 执行日志
│   ├── DECISIONS.md         # 决策记录
│   └── snapshot/             # 快照目录
└── archive/                  # 归档目录
```

---

## 命令参考

### 项目创建
```bash
python skills/enterprise-memory/scripts/switch_project.py --new --name <项目名> --description <描述>
```

### 项目切换
```bash
# 切出
python skills/enterprise-memory/scripts/switch_project.py --exit --project-dir <path>

# 切入
python skills/enterprise-memory/scripts/switch_project.py --enter --keyword <关键词>

# 列表
python skills/enterprise-memory/scripts/switch_project.py --list

# 搜索
python skills/enterprise-memory/scripts/switch_project.py --search <关键词>
```

### INDEX 同步
```bash
python skills/enterprise-memory/scripts/update_index.py --project-dir <path>
python skills/enterprise-memory/scripts/update_index.py --project-dir <path> --dry-run
```

### 快照压缩
```bash
python skills/enterprise-memory/scripts/compress.py --snapshot <snapshot_dir>
python skills/enterprise-memory/scripts/compress.py --snapshot <snapshot_dir> --dry-run
```

---

## 实现要求

- Python 3.10+
- 所有写入使用原子操作（临时文件 → 校验 → rename）
- 完善的错误处理和日志
- 每个脚本支持 `--dry-run`
- 导入路径：相对于项目根目录

---

## 版本

- Phase 1: 2026-03-31
- Phase 1.1: 2026-04-02（AI 适配方案）

# SKILL.md — enterprise-memory

## 触发词

```
/切换项目 <关键词>
/新建项目 <项目名>
/项目列表
/项目搜索 <关键词>
```

## 描述

企业级 Agent 记忆体系 Skill（Phase 1）。提供项目级隔离、状态同步、快照压缩能力。

## 核心能力

### 1. INDEX 自动同步

触发条件：
- 修改 `state.json` 时自动调用 `update_index.py`
- 任何状态变更必须同步更新 INDEX.md

命令：
```bash
python skills/enterprise-memory/scripts/update_index.py --project-dir <path>
python skills/enterprise-memory/scripts/update_index.py --project-dir <path> --dry-run
```

字段映射：
| state.json status | INDEX.md status |
|------------------|-----------------|
| DISCUSSING | IDLE |
| RUNNING | RUNNING |
| PAUSED | PAUSED |
| BLOCKED | BLOCKED |
| DONE | DONE |

### 2. 项目切换

切出（保存当前项目）：
```bash
python skills/enterprise-memory/scripts/switch_project.py --exit --project-dir <path>
python skills/enterprise-memory/scripts/switch_project.py --exit --project-dir <path> --dry-run
```

切入（加载目标项目）：
```bash
python skills/enterprise-memory/scripts/switch_project.py --enter --keyword <关键词>
python skills/enterprise-memory/scripts/switch_project.py --enter --project-id <ID>
python skills/enterprise-memory/scripts/switch_project.py --enter --keyword <关键词> --dry-run
```

搜索项目：
```bash
python skills/enterprise-memory/scripts/switch_project.py --search <关键词>
python skills/enterprise-memory/scripts/switch_project.py --list
```

新建项目：
```bash
python skills/enterprise-memory/scripts/switch_project.py --new --name <项目名> --description <描述>
```

### 3. 快照压缩

```bash
python skills/enterprise-memory/scripts/compress.py --snapshot <snapshot_dir>
python skills/enterprise-memory/scripts/compress.py --snapshot <snapshot_dir> --llm --llm-api-url <url>
python skills/enterprise-memory/scripts/compress.py --snapshot <snapshot_dir> --dry-run
```

Phase 1: 结构化提取（DECISIONS + state + LOG）
Phase 2: 启发式过滤（ACK 对、重复行）
Phase 3: 可选 LLM 压缩

降级策略：失败时保留 `raw.md`

## 全局记忆层结构

```
~/projects/
├── GLOBAL-INDEX.md         # 全局项目索引
├── current-project.json    # 当前项目指针
├── SOP-{日期}-{序号}-{名称}/
│   ├── state.json          # 项目状态
│   ├── INDEX.md            # 项目索引
│   ├── TASK.md             # 任务定义
│   ├── LOG.md              # 执行日志
│   ├── DECISIONS.md        # 决策记录
│   └── snapshot/           # 快照目录
└── archive/                # 归档目录
```

## 实现要求

- Python 3.10+
- 所有写入使用原子操作（临时文件 → 校验 → rename）
- 完善的错误处理和日志
- 每个脚本支持 `--dry-run`
- 导入路径：相对于项目根目录

## Phase 2 预告

- 触发词增强：对话中的自动上下文保存
- 跨项目经验沉淀
- 定期压缩任务

## 版本

- Phase 1: 2026-03-31

# 企业级 Agent 记忆体系 - 项目宪章

**版本**：1.0
**日期**：2026-04-02
**状态**：DRAFT

---

## 一、概述

本宪章定义了 enterprise-memory 底座的核心约束，是所有工作方法论的基准。

---

## 二、项目结构

### 2.1 目录结构

```
EAM-projects/                           # 项目根目录
├── CHARTER.md                    # 本宪章
├── GLOBAL-INDEX.md              # 全局索引
├── SOP-{日期}-{序号}-{名称}/   # 项目目录
│   ├── state.json             # 项目状态
│   ├── INDEX.md               # 项目索引
│   ├── TASK.md                # 任务定义
│   ├── LOG.md                 # 执行日志
│   ├── DECISIONS.md          # 决策记录
│   └── snapshot/              # 快照
└── archive/                   # 归档
```

### 2.2 命名规范

| 元素 | 格式 | 示例 |
|------|------|------|
| 项目 ID | `SOP-{YYYYMMDD}-{NN}-{名称}` | `SOP-20260402-001-HarnessEngineering` |
| 日期 | `YYYYMMDD` | `20260402` |
| 序号 | `NN`（两位数字） | `01`, `02` |
| 名称 | 中文/英文/混排 | `HarnessEngineering` |

---

## 三、state.json 规范

### 3.1 必填字段

```json
{
  "id": "SOP-20260402-001-HarnessEngineering",
  "title": "项目标题",
  "mode": "lite | full",
  "owner": "用户名",
  "status": "DISCUSSING | READY | RUNNING | PAUSED | BLOCKED | DONE",
  "stage": "TARGET | PLAN | CHECKLIST | EXECUTE | ARCHIVE | DONE",
  "createdAt": "ISO8601 时间",
  "updatedAt": "ISO8601 时间"
}
```

### 3.2 可选字段

```json
{
  "deadline": "ISO8601 时间 | 空",
  "reason": "原因描述 | 空",
  "blockedReason": "阻塞原因 | 空",
  "checklistConfirmed": "true | false",
  "confirmCount": 0,
  "upgradedFrom": "父项目ID | 空",
  "resume": {
    "lastCompleted": "最后完成项",
    "currentBlocked": "当前阻塞",
    "waitingFor": "等待中",
    "nextAction": "下一步操作"
  },
  "meta": {
    "methodology": "cms-sop | lite | 其他",
    "decisions": ["决策列表"]
  }
}
```

### 3.3 status 枚举值

| status | 说明 | 映射 |
|--------|------|------|
| `DISCUSSING` | 讨论中 | 初始状态 |
| `READY` | 就绪 | 准备开始 |
| `RUNNING` | 运行中 | 执行中 |
| `PAUSED` | 暂停 | 暂停 |
| `BLOCKED` | 阻塞 | 被阻塞 |
| `DONE` | 完成 | 已完成 |

### 3.4 stage 枚举值

| stage | 说明 | 映射 |
|--------|------|------|
| `TARGET` | 目标定义 | 初始阶段 |
| `PLAN` | 计划制定 | 规划阶段 |
| `CHECKLIST` | 确认清单 | 确认阶段 |
| `EXECUTE` | 执行实施 | 执行阶段 |
| `ARCHIVE` | 归档 | 归档阶段 |
| `DONE` | 完成 | 最终阶段 |

---

## 四、硬约束（必须校验）

以下约束必须通过代码校验：

### 4.1 ID 格式

```
正则：^SOP-\d{8}-\d{2}-[\w-]+$
示例：SOP-20260402-01-HarnessEngineering
```

### 4.2 status 枚举

```
允许值：DISCUSSING, READY, RUNNING, PAUSED, BLOCKED, DONE
```

### 4.3 stage 枚举

```
允许值：TARGET, PLAN, CHECKLIST, EXECUTE, ARCHIVE, DONE
```

### 4.4 时间格式

```
格式：ISO8601
示例：2026-04-02T12:00:00+08:00
```

---

## 五、软约束（AI 理解）

以下约束由 LLM 理解和生成：

### 5.1 title 规范

```
长度：1-100 字符
内容：描述项目的简短标题
```

### 5.2 mode 规范

| mode | 说明 |
|------|------|
| `lite` | 轻量模式（简化流程） |
| `full` | 完整模式（标准流程） |

### 5.3 语义映射

| CMS SOP 语义 | 底座值 |
|-------------|--------|
| 讨论中 | DISCUSSING |
| 已确认 | READY |
| 执行中 | RUNNING |
| 已暂停 | PAUSED |
| 被阻塞 | BLOCKED |
| 已完成 | DONE |

---

## 六、校验规则

### 6.1 关键字段（必须校验）

| 字段 | 校验类型 |
|------|---------|
| `id` | 格式 + 唯一性 |
| `status` | 枚举值 |
| `stage` | 枚举值 |
| `createdAt` | ISO8601 格式 |
| `updatedAt` | ISO8601 格式 |

### 6.2 非关键字段（警告）

| 字段 | 校验类型 |
|------|---------|
| `title` | 非空 + 长度 |
| `owner` | 非空 |
| `mode` | 枚举值 |

---

## 七、方法论注册

### 7.1 内置方法论

| 方法论 | 说明 |
|--------|------|
| `cms-sop` | CMS SOP 六阶段方法论 |
| `lite` | 轻量方法论 |

### 7.2 外部方法论

外部方法论可通过适配层注册，格式：

```json
{
  "name": "方法论名称",
  "version": "1.0.0",
  "semantics": {
    "状态映射": {...},
    "阶段映射": {...}
  }
}
```

---

## 八、版本

- **宪章版本**：1.0
- **底座版本**：1.0
- **约束格式版本**：1.0

---

*最后更新：2026-04-02*

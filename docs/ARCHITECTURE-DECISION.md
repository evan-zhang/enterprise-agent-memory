# 架构决策：Skill + 全局记忆层

## 问题

企业级 Agent 记忆体系应该以什么形式交付？
- 作为独立 Agent？
- 作为 Skill？

## 决策

**方案 C：Skill + 全局记忆层**

### 架构

```
┌─────────────────────────────────────┐
│  Agent A（Discord DM）              │
│  ┌───────────────────────────────┐  │
│  │ enterprise-memory-skill       │  │
│  │  - 触发逻辑（SKILL.md）        │  │
│  │  - Python 脚本                │  │
│  └───────────────────────────────┘  │
│           ↓ 读写                      │
└─────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  全局记忆层            │
        │  ~/.openclaw/EAM-projects/          │
        │  - 所有项目数据        │
        │  - 跨 Agent 共享       │
        └───────────────────────┘
                    ↑
┌─────────────────────────────────────┐
│  Agent B（Telegram DM）             │
│  ┌───────────────────────────────┐  │
│  │ enterprise-memory-skill       │  │
│  └───────────────────────────────┘  │
│           ↓ 读写                      │
└─────────────────────────────────────┘
```

### 核心概念

**Skill（能力层）**：
- 定义：Agent 的能力扩展包
- 内容：触发逻辑 + Python 脚本 + 模板
- 职责：识别意图、调用脚本、格式化输出
- 特点：轻量、可复用、不存储数据

**全局记忆层（数据层）**：
- 定义：统一的存储位置
- 位置：`~/.openclaw/EAM-projects/`
- 内容：所有项目的 INDEX.md、state.json、snapshot 等
- 特点：跨 Agent 共享、单一真相源

---

## 理由

### 为什么不是独立 Agent？

**缺点**：
- 分裂体验：工作在 Agent A，记忆在 Agent B
- 需要绑定额外 Bot
- 无法复用：每个用户需要独立 Agent

### 为什么不是纯 Skill？

**缺点**：
- 记忆隔离：每个 Agent 的数据独立
- 无法跨 Agent 共享项目

### 为什么是 Skill + 全局记忆层？

**优点**：
- **灵活性**：Skill 可以附加到任何 Agent
- **统一性**：全局记忆层保证数据一致
- **简洁性**：不需要额外 Agent 和 Bot
- **可扩展**：可以叠加其他 Skill

---

## 类比

```
Skill = App（应用）
全局记忆层 = iCloud（云存储）
Agent = 设备（手机/平板/电脑）

任何设备安装 App 后，都能访问同一份云存储数据。
```

---

## 实现

### Skill 位置

```
~/.openclaw/EAM-projects/enterprise-agent-memory/skills/enterprise-memory/
├── SKILL.md
├── scripts/
│   ├── update_index.py
│   ├── switch_project.py
│   └── compress.py
└── references/
    └── templates/
```

### 全局记忆层位置

```
~/.openclaw/EAM-projects/
├── GLOBAL-INDEX.md
├── current-project.json
├── SOP-20260330-001-TPR/
│   ├── state.json
│   ├── INDEX.md
│   └── ...
└── archive/
```

### 访问协议

任何 Agent 加载 `enterprise-memory-skill` 后：
1. 自动读取 `~/.openclaw/EAM-projects/current-project.json` 获取当前项目
2. 读写 `~/.openclaw/EAM-projects/{project-id}/` 下的文件
3. 更新 `~/.openclaw/EAM-projects/GLOBAL-INDEX.md`

---

## 决策记录

| 时间 | 决策 | 备选方案 | 理由 |
|------|------|---------|------|
| 2026-03-31 | Skill + 全局记忆层 | 独立 Agent / 纯 Skill | 灵活 + 统一 + 简洁 |

---

*最后更新：2026-03-31*

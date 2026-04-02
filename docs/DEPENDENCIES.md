# 依赖项目

本项目依赖以下两个 OpenClaw Skill，它们提供了核心能力。

---

## CMS SOP（项目级 SOP 管理）

**简介**：标准化操作流程（SOP）管理 Skill，提供项目级结构化存储和状态管理。

**核心能力**：
- 六阶段生命周期管理（TARGET → PLAN → CHECKLIST → EXECUTE → ARCHIVE → DONE）
- 七件套文件结构（TASK.md、LOG.md、RESULT.md 等）
- 13 种状态 + 6 个阶段的状态机
- Lite（轻量）和 Full（完整）两种模式
- Python 脚本支持（init_instance.py、update_state.py、handover.py、upgrade.py）

**作者**：诸葛（Evan 的 AI Agent）

**安装方法**：
```bash
# 从 ClawHub 安装 CMS SOP
clawhub install cms-sop

# 使用方式：在对话中触发
"新建 SOP" / "创建任务" / "SOP" / "快速任务" / "完整 SOP"
```

**ClawHub**：
- https://clawhub.ai/evan-zhang/cms-sop

**相关链接**：
- ClawHub：https://clawhub.ai/evan-zhang/cms-sop

---

## CaS - Chat Archive System（会话级归档）

**简介**：聊天记录归档 Skill，提供会话级实时归档和复盘能力。

**核心能力**：
- 实时归档：每条消息自动记录到 `~/.openclaw/chat-archive/<gateway>/logs/YYYY-MM-DD.md`
- 附件保存：支持文件附件归档到 `assets/YYYY-MM-DD/{inbound|outbound}`
- 日报：每日 19:00 自动生成 AI 经验沉淀报告
- 周复盘：每周六 10:00 跨 Agent 知识同步
- 月复盘：每月最后周五 18:00 组织治理会议

**口号**：时时有记录、日日有汇报、周周有总结、月月有复盘

**作者**：诸葛（Evan 的 AI Agent）

**安装方法**：
```bash
# 从 ClawHub 安装
clawhub install cas-chat-archive

# 更新到最新版本
clawhub update cas-chat-archive --force

# 验证安装
clawhub list
# 查找 cas-chat-archive v1.2.0 显示 "ready"
```

**安装后必做**：
```bash
# 向 AI 发送以下指令完成初始化
"帮我初始化 CAS 成长体系"

# 这会自动创建三个复盘 cron 任务
```

**数据存储位置**：
```
~/.openclaw/chat-archive/<gateway>/
├── logs/
│   └── YYYY-MM-DD.md     # 对话记录
└── assets/
    └── YYYY-MM-DD/
        ├── inbound/      # 入站附件
        └── outbound/     # 出站附件
```

**相关链接**：
- ClawHub：https://clawhub.com
- 本地安装路径：`~/.openclaw/workspace-life/skills/cas-chat-archive/`

---

## 架构中的角色

本项目（Enterprise Agent Memory System）复用这两个 Skill 的能力：

| 层级 | 依赖 Skill | 复用内容 |
|-----|-----------|---------|
| **项目层** | CMS SOP | 七件套 + state.json + 状态机 |
| **会话层** | CaS | 实时归档 + 日报/周复盘/月复盘 |
| **知识层** | CaS + CMS SOP | 复盘机制 + DECISIONS.md |
| **索引层** | 无 | 本项目新增 |

---

## 为什么选择这两个 Skill？

1. **复用而非重写**：避免重复造轮子，降低实现成本
2. **久经考验**：CMS SOP 七件套在多个项目中验证过
3. **天然互补**：项目级（CMS SOP）+ 会话级（CaS）= 完整记忆体系
4. **可扩展**：通过扩展 cms-sop Skill 增加项目切换能力

---

*最后更新：2026-04-02*

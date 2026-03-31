# Enterprise Agent Memory System

企业级 Agent 记忆体系 - 让 AI 像人一样记忆、切换、沉淀

## 项目状态

**当前阶段**：设计完成，待实现（CHECKLIST 阶段）

**设计文档**：
- [设计总结](docs/DESIGN-SUMMARY.md) - 1 页纸快速了解
- [完整设计](docs/DESIGN-FULL.md) - 详细的架构和组件设计
- [审核报告](docs/REVIEW.md) - 三轮审核的问题和改进
- [方法论](docs/METHODOLOGY.md) - 本项目使用的方法论
- [依赖项目](docs/DEPENDENCIES.md) - 依赖的 Skill 及安装方法
- [架构决策](docs/ARCHITECTURE-DECISION.md) - Skill vs Agent 的选择
- [CHECKLIST 决策](docs/CHECKLIST.md) - 执行前的四个关键决策

## 核心问题

员工工作不是串行的，是多任务交替推进：
- 任务 A 做到一半 → 暂存 → 切换到任务 B
- 任务 B 做到一半 → 暂存 → 切回任务 A
- 切换时上下文丢失或混乱

## 解决方案

**类人记忆体系**：
- 统一存储（所有记忆在一个地方）
- 按需提取（能从海量记忆中快速提取某个项目的内容）
- 经验沉淀（跨项目的共有知识能提炼、复用）

**四层架构**：
```
项目层（CMS SOP）→ 会话层（CaS）→ 知识层（复盘）→ 索引层（搜索）
```

## 核心设计原则

1. **AI 为主，用户为辅** — 自动更新，自动保存
2. **强绑定强制机制** — 关键操作必须触发同步
3. **原子性保障** — 临时写 → 校验 → 原子替换
4. **降级策略** — 压缩失败保留完整数据
5. **简化优先** — 放弃过度设计（DAG/RAG）
6. **Skill + 全局记忆层** — 能力与数据分离，跨 Agent 共享

## 方法论

本项目使用 **CMS SOP 六阶段方法论**：

```
TARGET → PLAN → CHECKLIST → EXECUTE → ARCHIVE → DONE
```

详见 [方法论文档](docs/METHODOLOGY.md)。

### 当前阶段

**PLAN 完成 → CHECKLIST 待开始**

- ✅ 目标定义
- ✅ 架构设计
- ✅ 子 Agent 审核（3 轮）
- ⏳ 确认是否执行
- ⏳ 实现代码
- ⏳ 测试验证

## 目录结构

```
enterprise-agent-memory/
├── README.md               # 项目简介
├── project-state.json      # 项目状态（CMS SOP）
├── docs/                   # 设计文档
│   ├── METHODOLOGY.md      # 方法论
│   ├── DESIGN-SUMMARY.md   # 设计总结
│   ├── DESIGN-FULL.md      # 完整设计
│   ├── DEPENDENCIES.md     # 依赖 Skill
│   ├── DECISIONS.md        # 决策记录
│   └── REVIEW.md           # 审核报告
├── scripts/                # 实现脚本（待开发）
├── skills/                 # ClawHub Skill（待发布）
└── tests/                  # 测试（待开发）
```

## 审核结论

**CONDITIONAL_PASS**
- 5 个 Blocker 已修复 4 个
- 核心方案可行，实现复杂度可控
- 建议用 5 个真实项目跑 2 周压测

## 下一步

1. **CHECKLIST 阶段**：确认是否执行、执行范围
2. **EXECUTE 阶段**：实现三个核心脚本
   - `update_project_index.py`
   - `switch_project.py`
   - `compress_snapshot.py`
3. **TEST 阶段**：2 周压力测试
4. **RELEASE 阶段**：发布到 ClawHub

## 参与贡献

详见 [方法论文档](docs/METHODOLOGY.md)，了解如何参与本项目。

## License

MIT

---

*创建时间：2026-03-31*
*当前阶段：PLAN 完成，CHECKLIST 待开始*

# EAM Global Index

> EAM = Enterprise Agent Memory 项目管理系统
> 编码规则：SOP-YYYYMMDD-XXXX-项目名（XXXX为4位连续序号，不按日期重置）
> 下一个序号：0016

---

## 项目索引

| ID | 项目名 | 状态 |
|----|--------|------|
| 0001 | EAM-SOP-Merge | DONE |
| 0002 | Claude-Code-源码泄露事件分析 | DONE |
| 0003 | claude-code-leak | DONE |
| 0004 | agent-tool-system | DONE |
| 0005 | memory-system | GRV v1.1 |
| 0006 | hook-system | GRV v1.1 |
| 0007 | compaction-system | GRV v1.1 |
| 0008 | permission-system | GRV v1.1 |
| 0009 | subagent-system | GRV v1.1 |
| 0010 | task-system | GRV v1.1 |
| 0011 | skills-system | GRV v1.1 |
| 0012 | team-system | GRV v1.1 |
| 0013 | kairos-system | GRV v1.1 |
| 0014 | file-state-system | GRV v1.0 |
| 0015 | agent-architecture | GRV v1.0 |

## 最近更新

- 0015 agent-architecture: 2026-04-04 新建
- 0005-0014: 2026-04-04 GRV v1.1 修订
- 0004 agent-tool-system: 2026-04-04 完成
- 编码规则重构：3位按日重置 → 4位全局连续

## 编码规则（2026-04-04 更新）

格式：`SOP-YYYYMMDD-XXXX-项目英文名`

- 序号全局连续，不按日期重置
- 下一个新建项目：0016
- 4位序号，不足补零

## 项目状态说明

| 状态 | 含义 |
|------|------|
| DISCUSSING | 需求分析中 |
| GRV | GRV 审批中 |
| READY | 准备开始实现 |
| IN_PROGRESS | 实现中 |
| DONE | 已完成 |

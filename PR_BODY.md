## Summary

吸收 CMS-SOP 执行流程规范到 EAM，统一为 v2.0。

Closes #2

## 核心设计决策

- **D1**: 唯一 Skill、唯一目录（`~/.openclaw/EAM-projects/`）、唯一 Schema
- **D2**: EAM 底座不动，SOP 作为扩展层
- **D3**: 合并不是搬运（复用 EAM 底座创建项目，然后扩展 SOP 字段）
- **D4**: 目录命名统一为 `SOP-{日期}-{序号}-{名称}`
- **D5**: CMS-SOP 废弃

## Changes

### Prereq: Python 3.9 兼容
- 所有脚本头部添加 `from __future__ import annotations`

### M1: 统一 Schema + STATUS_MAP
- `switch_project.py`：`new_project()` 追加 10 个 SOP 扩展字段默认值
- `update_index.py`：STATUS_MAP 从 7 扩展到 13 个状态
- `switch_project.py`：`search_projects()` / `list_projects()` 支持 `source` 参数过滤

### M2: sop_init.py (283 lines)
- 调用 EAM 底座创建项目 → 扩展 SOP 字段 → 应用模板文件 → 同步 INDEX
- 支持 `--title` / `--mode` (lite|full) / `--owner` / `--dry-run`

### M3: sop_state.py (286 lines)
- 确认单门禁（`checklistConfirmed=false` → 拒绝 RUNNING）
- 多轮确认计数（`confirmCount ≥ 3` → INTERVENTION_REQUIRED）
- 6 个语义化操作（pause/resume/shelve/restart/wait-user/reviewed）
- 高风险操作需 `--confirm`
- 每次更新后自动同步 INDEX.md

### M4: sop_handover.py (248 lines) + sop_upgrade.py (393 lines)
- 交接：验证 owner → 创建 HANDOVER.md → 切换 owner → 更新状态
- 升级：验证 lite → 插入继承声明 → 标记 LOG → 创建 Full 文件 → 创建快照

### M5: 模板和参考文档
- Lite 模板 4 个（TASK/LOG/RESULT/HANDOVER）
- Full 模板 3 个（PLAN/DECISIONS/ARTIFACTS）
- SOP Lite/Full 使用指南
- 共享文档（状态机/确认协议/升级规则）

### M6: SKILL.md 更新
- 新增 SOP 触发词（SOP/新建SOP/创建任务/快速任务/完整SOP/任务交接/升级任务）
- 完整命令参考（含 --dry-run 示例）
- 目录结构文档
- Python 3.9+ 兼容性声明

### M7: 测试
- `tests/test_sop.py`：14 个新测试
  - Schema + STATUS_MAP 完整性
  - 向后兼容（旧 state 无 SOP 字段）
  - Source 过滤
  - 确认单门禁
  - 多轮确认阈值
  - 语义化操作映射
  - 升级校验

## Test Results

```
31 tests passed (17 original + 14 new SOP tests)
Python 3.9.2 compatible
```

## File Stats

```
21 files changed, 2024 insertions(+), 42 deletions(-)
```

## Backward Compatibility

旧 EAM 项目（无 SOP 字段）在新代码下完全正常工作：
- `state.get("mode")` → None（不影响逻辑）
- `state.get("checklistConfirmed", False)` → False（不影响逻辑）
- INDEX 生成、项目列表、搜索、切换全部兼容

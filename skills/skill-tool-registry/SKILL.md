---
name: skill-tool-registry
description: 工具自动注册系统。当安装新 skill 时，用这个来注册工具到 TOOLS.md 并创建生命周期文件。其他 Agent 安装新 skill 后也应该运行此脚本。提供 register_tools.py，支持注册（install）和注销（uninstall）两种模式。
---

# skill-tool-registry — 工具注册系统

## 作用

新 skill 安装后，自动从其 SKILL.md 读取 `tools_provided` 元数据，注册到 TOOLS.md 并创建 per-tool 生命周期文件。

## 使用方式

### 安装 skill 后注册工具
```bash
python3 ~/.openclaw/workspace/skills/skill-tool-registry/scripts/register_tools.py skill-name
```

### 卸载 skill 时注销工具
```bash
python3 ~/.openclaw/workspace/skills/skill-tool-registry/scripts/register_tools.py --unregister skill-name
```

### 查看当前所有已注册工具
```bash
python3 ~/.openclaw/workspace/skills/skill-tool-registry/scripts/register_tools.py --list
```

## Skill 需提供的元数据格式

在 skill 的 SKILL.md 顶部添加 YAML frontmatter：

```yaml
---
tools_provided:
  - name: task_registry
    category: system
    risk_level: medium
    permission: write
    description: Task 生命周期管理（创建/查询/更新/停止）
    channels: ALL
    status: active
---
```

## 数据结构

### TOOLS.md（集中注册表）
- 路径：`~/.openclaw/workspace/TOOLS.md`
- 内容：所有已注册工具的 metadata
- 由 register_tools.py 自动维护，人工不直接编辑

### Per-tool 生命周期文件
- 路径：`~/.openclaw/workspace/memory/tools/{tool-name}.json`
- 内容：工具状态 + 操作日志
- 记录：注册/禁用/启用/注销事件

### 生命周期状态
| 状态 | 说明 |
|------|------|
| `active` | 可用 |
| `deprecated` | 不推荐 |
| `disabled` | 禁用 |

## 工具路由集成

register_tools.py 会更新 TOOLS.md，之后 tool_router.py 就能自动路由到新工具。

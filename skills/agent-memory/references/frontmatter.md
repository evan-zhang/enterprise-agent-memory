# Frontmatter Schema 规范

## 完整 Schema

每个 topic 文件必须包含以下 frontmatter 字段：

```yaml
---
name: 人类可读的标题
type: user | feedback | project | ref
tags: [标签1, 标签2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
importance: low | medium | high
---
## 正文内容
```

## 字段说明

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `name` | ✅ | 简短描述，用于 MEMORY.md 索引引用 | "User 编辑器偏好" |
| `type` | ✅ | 四类之一，决定文件存放目录 | `user`, `feedback`, `project`, `ref` |
| `tags` | ✅ | 用于 memory_search 语义匹配 | `[preference, editor]` |
| `created` | ✅ | 首次创建日期 | `2026-04-03` |
| `updated` | ✅ | 最后更新日期 | `2026-04-03` |
| `importance` | ✅ | 决定归档优先级 | `low`, `medium`, `high` |

## type 字段合法值

| 值 | 目录 | 说明 |
|----|------|------|
| `user` | `memory/user/` | 用户偏好和身份 |
| `feedback` | `memory/feedback/` | 纠偏和反馈 |
| `project` | `memory/project/` | 项目上下文 |
| `ref` | `memory/ref/` | 外部系统引用 |

## importance 字段

| 值 | 归档优先级 | 说明 |
|----|-----------|------|
| `high` | 最后归档 | 核心记忆，绝对保留 |
| `medium` | 中等 | 重要，但不紧急 |
| `low` | 最先归档 | 参考性质，过期可删 |

## KAIROS 日志 Frontmatter

KAIROS 日志使用简化格式：

```markdown
# YYYY-MM-DD Daily Log

## HH:MM - 事件标题
- 事件描述
- 关键决策
```

KAIROS 日志不需要完整 frontmatter，但建议顶部包含日期。

## 错误示例

❌ 缺少 type：
```yaml
---
name: User 的习惯
tags: [preference]
---
```

❌ type 值不合法：
```yaml
---
name: User 的习惯
type: preference  # ❌ 应该是 user
---
```

❌ 缺少 importance：
```yaml
---
name: User 的习惯
type: user
tags: [preference]
created: 2026-04-03
updated: 2026-04-03
# ❌ 缺少 importance
---
```

## 正确示例

```yaml
---
name: User 编辑器偏好
type: user
tags: [editor, preference, vim]
created: 2026-04-03
updated: 2026-04-03
importance: high
---

## 偏好详情
- 主力编辑器：vim
- 终端偏好：zsh + tmux
```

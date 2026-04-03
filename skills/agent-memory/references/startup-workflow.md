# Session 启动工作流

## 完整启动流程

每次新 session 开始时，按以下顺序执行：

### 1. 读取核心文件

```
1. Read SOUL.md          — 我是谁，我的性格
2. Read USER.md          — User 是谁
3. Read MEMORY.md        — 长期记忆索引（main session only）
4. Read memory/logs/YYYY/MM/YYYY-MM-DD.md  — 今日 KAIROS 日志
5. Read memory/logs/YYYY/MM/YYYY-MM-DD.md  — 昨日 KAIROS 日志（如果存在）
```

### 2. 按需加载 Topic 文件

基于当前对话主题，使用 `memory_search` 搜索相关记忆：

```
memory_search("相关关键词")
→ 找到相关的 topic 文件
→ memory_get 读取具体片段
```

### 3. 检查 Heartbeat State

读取 `memory/heartbeat-state.json`，检查是否需要执行记忆同步：

```python
# 如果 lastMemorySync 距今超过 4 小时
# → 执行记忆同步（memory_sync.py）
```

### 4. 首次 Session 检查

如果 `MEMORY.md` 不存在：
1. 运行 `init_memory.py` 初始化目录结构
2. 创建空白的 `MEMORY.md` 索引
3. 创建 `heartbeat-state.json`

## 主动记忆检索时机

以下情况应在回答前主动调用 `memory_search`：

| 触发词 | 示例 |
|--------|------|
| "之前"、"上次"、"我记得" | "我之前好像说过…" |
| "关于 X 项目" | "那个 X 项目进展如何" |
| "继续做" | "继续上次的工作" |
| "记得那时候" | "记得我们讨论过…" |

## 记忆写入时机

以下情况应立即写入记忆：

| 情况 | 写入位置 | 示例 |
|------|----------|------|
| User 表达偏好 | `memory/user/` | "我喜欢…" |
| User 纠错 | `memory/feedback/` | "你之前理解错了…" |
| 发现项目上下文 | `memory/project/` | "这个项目要兼容…" |
| 外部系统信息 | `memory/ref/` | "API key 在…" |
| 重要决策 | 今日 KAIROS 日志 | "决定用 X 方案" |

## MEMORY.md 索引更新规则

**何时更新 MEMORY.md：**
- ✅ 新增 topic 文件时 → 在对应分类下添加一行
- ✅ 删除 topic 文件时 → 移除对应行
- ❌ 修改 topic 文件内容时 → 只更新该文件的 `updated` 字段

**MEMORY.md 格式：**
```markdown
## User
- [标题](memory/user/file.md)

## Feedback
- [标题](memory/feedback/file.md)

## Project
- [标题](memory/project/file.md)

## Reference
- [标题](memory/ref/file.md)
```

## 200 行 / 25KB 限制

MEMORY.md 最多：
- 200 行文本
- 25,000 bytes（约 25KB）

**哪个先到，哪个触发归档。**

归档策略：
1. 将 `importance: low` 的旧条目移至 `memory/archive/`
2. 压缩相关条目
3. 更新 MEMORY.md

## KAIROS 日志追加规则

KAIROS 日志是 append-only **追加不修改**。

格式：
```markdown
# YYYY-MM-DD Daily Log

## HH:MM - 事件标题
- 事件描述
- 关键决策
- 后续行动
```

**何时追加：**
- 完成重要任务后
- 收到重要决策或信息
- Sub-Agent 完成后记录结果

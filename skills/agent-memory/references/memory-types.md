# 四类记忆详解

## 概述

记忆系统将信息分为四类，每类有明确的用途、写入时机和存储位置。

## user — 用户偏好

**目录**：`memory/user/`

**用途**：存储用户的个人偏好、习惯和身份信息。这是关于"用户是谁"的知识。

**何时写入**：
- 用户明确表达偏好时（"我喜欢用 vim"、"请叫我 Evan"）
- 发现用户的习惯时（"每次都是先问再做"）
- 用户提供个人信息时

**示例**：
```markdown
# user/preferred-editor.md
---
name: User 编辑器偏好
type: user
tags: [editor, preference]
created: 2026-04-03
updated: 2026-04-03
importance: high
---

## 内容
- 喜欢用 vim
- 偏好中文界面
```

## feedback — 反馈与纠偏

**目录**：`memory/feedback/`

**用途**：记录用户的纠正、反馈和教训。这是关于"用户对我说过什么不对"的知识。

**何时写入**：
- 用户纠正错误时（"你之前理解错了，实际上应该是…"）
- 用户表达不满时（"你每次都这样回答不太好"）
- 用户给出指导时（"以后遇到这种情况你应该先…"）

**示例**：
```markdown
# feedback/2026-04-03-tpr-framework.md
---
name: TPR 框架引入
type: feedback
date: 2026-04-03
resolved: false
tags: [tpr, framework]
created: 2026-04-03
updated: 2026-04-03
importance: high
---

## 事件
User 引入了 TPR 框架来管理复杂任务。

## User 的具体要求
- 事前最大授权
- 遇到判断不了的问题主动停下
- 事后复盘纠偏
```

## project — 项目上下文

**目录**：`memory/project/`

**用途**：存储项目相关的背景知识，这些信息不能从代码本身推导出来。

**何时写入**：
- 开始新项目时
- 发现项目相关的重要上下文时
- 项目有特殊要求或约束时

**示例**：
```markdown
# project/my-project.md
---
name: My Project
type: project
project: my-project
tags: [project, context]
created: 2026-04-03
updated: 2026-04-03
importance: high
---

## 项目背景
- 需要兼容 Python 3.8+
- 客户要求所有输出为中文
- 截止日期：2026-05-01
```

## ref — 外部参考

**目录**：`memory/ref/`

**用途**：存储外部系统的引用信息（API 文档、服务配置等）。

**何时写入**：
- 发现重要的外部系统配置时
- 记录 API key 位置时
- 记录第三方服务凭证时

**示例**：
```markdown
# ref/github-api.md
---
name: GitHub API 配置
type: ref
system: github
tags: [api, github, credentials]
created: 2026-04-03
updated: 2026-04-03
importance: medium
---

## API Endpoint
https://api.github.com

## Token 位置
~/.config/gh/hosts.yml

## Rate Limit
5000 req/hour (authenticated)
```

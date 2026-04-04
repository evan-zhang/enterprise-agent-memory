# 安装指南 - enterprise-agent-memory

## 完整安装命令

```bash
# 1. 克隆 repo
git clone https://github.com/evan-zhang/enterprise-agent-memory.git
cd enterprise-agent-memory

# 2. 复制所有 skill 到 workspace
cp -r skills/* ~/.openclaw/workspace/skills/

# 3. 复制 TOOLS.md 到 workspace 根目录（tool-router 依赖此文件）
cp TOOLS.md ~/.openclaw/workspace/TOOLS.md

# 4. 初始化记忆目录
python3 ~/.openclaw/workspace/skills/agent-memory/scripts/init_memory.py

# 5. 验证
python3 ~/.openclaw/workspace/skills/skill-task-registry/scripts/task_registry.py list
```

## 目录结构说明

```
~/.openclaw/workspace/
├── skills/
│   ├── agent-memory/       ← 记忆系统（init_memory.py 在这里）
│   ├── enterprise-memory/  ← EAM 框架
│   ├── task-registry/      ← Task 生命周期管理
│   ├── tool-router/        ← 工具语义路由
│   └── permission/         ← 权限约定
├── TOOLS.md                ← 工具元数据注册表（tool-router 依赖）
└── memory/                 ← 记忆数据目录（init 后生成）
```

## 验证三个核心能力

```bash
# 能力1：工具路由
python3 ~/.openclaw/workspace/skills/skill-tool-router/scripts/tool_router.py route "帮我搜索最新的AI新闻"

# 能力2：任务注册
python3 ~/.openclaw/workspace/skills/skill-task-registry/scripts/task_registry.py create "测试任务" '{"test": true}'

# 能力3：查看权限约定
cat ~/.openclaw/workspace/skills/skill-permission/SKILL.md
```

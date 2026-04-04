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
```

## 自动测试（推荐）

安装完成后，运行自动化测试脚本：

```bash
cd enterprise-agent-memory
python3 test_all.py
```

测试覆盖：
- 目录结构（9 项文件检查）
- Tool Router 路由（4 项）
- Task Registry 全生命周期（5 项）
- Memory 目录初始化
- TOOLS.md 内容完整性

预期结果：`全部通过` → 🎉 安装成功

---

## 手动单项测试

如果不想跑自动脚本，也可以逐项验证：

```bash
# 1. 验证 skills 目录
ls ~/.openclaw/workspace/skills/
# 应看到：agent-memory enterprise-memory task-registry tool-router permission

# 2. 验证 TOOLS.md
ls ~/.openclaw/workspace/TOOLS.md

# 3. 验证 memory 目录（init 后）
ls ~/.openclaw/workspace/memory/
# 应看到：user/ feedback/ project/ ref/ logs/

# 4. 工具路由测试
python3 ~/.openclaw/workspace/skills/tool-router/scripts/tool_router.py route "帮我搜索最新的AI新闻"
# 预期：返回 web_search

# 5. Task 创建测试
python3 ~/.openclaw/workspace/skills/task-registry/scripts/task_registry.py list
# 预期：返回 []

python3 ~/.openclaw/workspace/skills/task-registry/scripts/task_registry.py create "测试" '{"demo": true}'
# 预期：返回 {"status": "created", "id": "xxx", ...}
```

## 目录结构说明

```
~/.openclaw/workspace/
├── skills/
│   ├── agent-memory/       ← 记忆系统
│   ├── enterprise-memory/  ← EAM 框架
│   ├── task-registry/      ← Task 生命周期管理
│   ├── tool-router/        ← 工具语义路由
│   └── permission/         ← 权限约定
├── TOOLS.md                ← 工具元数据注册表
└── memory/                 ← 记忆数据目录（init 后生成）
```

## 验证三个核心能力

```bash
# 能力1：工具路由
python3 ~/.openclaw/workspace/skills/tool-router/scripts/tool_router.py route "帮我搜索最新的AI新闻"

# 能力2：任务注册
python3 ~/.openclaw/workspace/skills/task-registry/scripts/task_registry.py create "测试任务" '{"test": true}'

# 能力3：查看权限约定
cat ~/.openclaw/workspace/skills/skill-permission/SKILL.md
```

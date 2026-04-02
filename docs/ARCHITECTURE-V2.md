# 企业级 Agent 记忆体系 - 架构设计 v2

**版本**：v2.0
**日期**：2026-04-02
**状态**：DRAFT

---

## 一、核心定位

### 1.1 底层框架

企业级 Agent 记忆体系（enterprise-memory）是一个**通用的底层框架**，用于：
- 项目隔离与发现
- 跨 Agent 记忆共享
- 统一的项目状态管理

### 1.2 可插拔架构

enterprise-memory 采用"**可插拔的工作方法论系统**"：
- 底层框架固定
- 工作方法可替换
- Agent 自主选择

---

## 二、三种安装组合

| 安装组合 | 结果 |
|---------|------|
| **enterprise-memory** | 底层框架原生结构 |
| **enterprise-memory + cms-sop** | cms-sop 成为默认工作方法 |
| **cms-sop（单独）** | 按 cms-sop 自身规范执行 |

### 2.1 说明

- **enterprise-memory** 是可选的底层框架
- **cms-sop** 可以独立于 enterprise-memory 工作
- 安装 enterprise-memory 后，cms-sop 成为推荐的工作方法

---

## 三、架构分层

```
┌─────────────────────────────────────────┐
│           enterprise-memory             │
│           （底层框架）                  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │    项目隔离与发现               │   │  ← 核心能力（始终存在）
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │    适配层（Adapter）           │   │  ← 方法论集成接口
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │    工作方法论                   │   │  ← 可替换（cms-sop 或其他）
│  │    （默认：cms-sop）           │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 四、方法论适配层

### 4.1 核心概念

适配层（Adapter）是将外部方法论集成到 enterprise-memory 的桥梁：

- **单向集成**：方法论更新不影响适配层
- **独立维护**：方法论保持独立
- **即插即用**：新方法论只需写适配层

### 4.2 CMS SOP 适配

CMS SOP 是一个独立 Skill，可以：
- 独立于 enterprise-memory 使用
- 通过适配层集成到 enterprise-memory

**适配内容**：

| 适配项 | 说明 |
|--------|------|
| **存储路径** | CMS SOP 的 `sop-instances/` → `~/projects/` |
| **state.json 格式** | 映射到统一格式 |
| **触发词** | 让 CMS SOP 指令能触发 enterprise-memory |
| **索引格式** | 统一 INDEX.md 格式 |

### 4.3 外部方法论扩展

将来可以集成其他工作方法论：
- 只需开发适配层代码
- 方法论本身无需修改
- 不影响 enterprise-memory 核心

---

## 五、与其他 Skill 的关系

### 5.1 依赖的 Skill

| Skill | 关系 | 说明 |
|-------|------|------|
| **cms-sop** | 可选依赖 | 推荐的工作方法论 |
| **cas-chat-archive** | 可选依赖 | 会话级归档 |

### 5.2 独立性

- **enterprise-memory 不强制依赖任何 Skill**
- 所有依赖都是可选的
- 不安装依赖时，enterprise-memory 使用原生结构

---

## 六、安装与配置

### 6.1 安装方式

```bash
# 安装主框架
clawhub install enterprise-memory

# 安装 cms-sop（可选，推荐）
clawhub install cms-sop
```

### 6.2 目录结构

```
~/.openclaw/
├── projects/                    ← 全局项目目录（用户可配置）
│   ├── CHARTER.md            ← 项目宪章（定义项目规范）
│   ├── GLOBAL-INDEX.md      ← 全局索引
│   ├── SOP-{日期}-{序号}-{名称}/  ← 具体项目
│   └── archive/              ← 归档目录
└── skills/
    └── enterprise-memory/     ← 主框架
```

### 6.3 路径配置

项目目录路径可通过环境变量或配置文件修改：

```bash
# 默认路径
export ENTERPRISE_MEMORY_ROOT=~/.openclaw/projects/

# 可配置为任意路径
export ENTERPRISE_MEMORY_ROOT=/your/custom/path/
```

**设计原则**：
- 路径可配置，便于用户自定义
- 默认使用 `~/.openclaw/projects/`
- 兼容不同部署环境

---

## 七、与 CMS SOP 的集成

### 7.1 集成方式

CMS SOP 通过适配层集成到 enterprise-memory：

```
用户："用 SOP 方法创建项目"
     ↓
enterprise-memory 接收请求
     ↓
调用 CMS SOP 适配层
     ↓
CMS SOP 在项目目录中创建 SOP 结构
     ↓
更新 GLOBAL-INDEX.md
```

### 7.2 文件映射

| CMS SOP 文件 | enterprise-memory 文件 |
|-------------|----------------------|
| `sop-instances/SOP-xxx/TASK.md` | `projects/SOP-xxx/TASK.md` |
| `sop-instances/SOP-xxx/LOG.md` | `projects/SOP-xxx/LOG.md` |
| `sop-instances/SOP-xxx/state.json` | `projects/SOP-xxx/state.json` |

---

## 八、设计原则

1. **最小化核心**：enterprise-memory 核心保持最小
2. **方法论独立**：工作方法论不依赖 enterprise-memory
3. **适配层隔离**：方法论更新不影响核心
4. **即插即用**：新方法论易于集成
5. **向后兼容**：不影响现有单独使用的 Skill

---

## 九、待确认问题

- [x] 适配层的技术实现方案
- [x] CMS SOP 适配层的具体接口
- [ ] 版本协调机制
- [x] 配置管理方式

---

## 十、适配层接口设计

### 10.1 适配层职责

适配层负责：
1. **路径映射**：将方法论的存储路径映射到 enterprise-memory 的项目目录
2. **格式转换**：将方法论的状态格式转换为统一格式
3. **索引同步**：确保方法论的文件变更能同步到 GLOBAL-INDEX.md

### 10.2 适配层接口

每个适配层需要实现以下接口：

```python
class MethodAdapter:
    def __init__(self, projects_root: str):
        self.projects_root = projects_root
    
    def create_project(self, name: str, method: str) -> dict:
        """创建项目，返回项目路径"""
        pass
    
    def sync_index(self, project_id: str) -> bool:
        """同步项目索引到 GLOBAL-INDEX.md"""
        pass
    
    def get_project_state(self, project_id: str) -> dict:
        """获取项目状态"""
        pass
    
    def update_project_state(self, project_id: str, state: dict) -> bool:
        """更新项目状态"""
        pass
```

### 10.3 CMS SOP 适配层实现

```python
class CMSSOPAdapter(MethodAdapter):
    """CMS SOP 方法论适配层"""
    
    def create_project(self, name: str, method: str = "cms-sop") -> dict:
        """创建项目时，自动应用 CMS SOP 结构"""
        # 1. 在 projects_root 创建项目目录
        # 2. 初始化 state.json（统一格式）
        # 3. 初始化 TASK.md, LOG.md 等
        pass
    
    def sync_index(self, project_id: str) -> bool:
        """同步 CMS SOP 文件到 GLOBAL-INDEX.md"""
        # 读取 state.json
        # 映射到统一格式
        # 更新 GLOBAL-INDEX.md
        pass
```

### 10.4 触发词设计

| 触发词 | 作用域 | 说明 |
|--------|---------|------|
| `enterprise-memory:创建项目` | 全局 | 通过 enterprise-memory 创建 |
| `sop:创建项目` | cms-sop | 直接调用 cms-sop |
| `全局项目列表` | enterprise-memory | 列出所有项目 |
| `sop:项目列表` | cms-sop | 列出 SOP 项目 |

**设计原则**：
- 前缀区分作用域（如 `enterprise-memory:` 或 `sop:`）
- 避免与 cms-sop 原生触发词冲突
- 支持在 enterprise-memory 中直接调用 cms-sop 能力

---

## 十、相关文档

- [ARCHITECTURE-DECISION.md](ARCHITECTURE-DECISION.md) - 架构决策记录
- [METHODOLOGY.md](METHODOLOGY.md) - 方法论定义
- [DEPENDENCIES.md](DEPENDENCIES.md) - 依赖说明

---

*最后更新：2026-04-02*

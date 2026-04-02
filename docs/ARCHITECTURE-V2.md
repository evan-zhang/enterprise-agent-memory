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
│  │    约束定义层                   │   │  ← 约束文档（定义需要什么）
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │    AI 适配层                    │   │  ← LLM 理解 + 生成
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │    工作方法论                   │   │  ← 可替换（cms-sop 或其他）
│  │    （默认：cms-sop）           │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 四、核心设计：AI 适配 + 代码校验

### 4.1 核心思路

底座定义约束 + 方法论定义语义 + LLM 自动桥接

```
用户请求 → LLM 理解约束 → 生成结构化文件 → 代码校验 → 成功/失败
```

### 4.2 分工原则

| 分工 | 负责 |
|------|------|
| **理解语义** | LLM |
| **生成文件** | LLM |
| **格式校验** | 代码 |
| **冲突处理** | prompt + warn |

### 4.3 不需要的

- ❌ 复杂的适配层代码
- ❌ 版本精确匹配
- ❌ 自动降级逻辑

### 4.4 需要的

- ✅ 清晰的约束文档
- ✅ 关键字段校验
- ✅ LLM 生成能力

---

## 五、方法论适配层

### 5.1 适配方式：AI 适配 + 代码校验

**核心思路**：约束 + 校验 + AI 生成

### 5.2 约束分层

```markdown
## 硬约束（必须校验）
- id 格式：SOP-{日期}-{序号}-{名称}
- status 枚举：DISCUSSING | RUNNING | PAUSED | BLOCKED | DONE
- stage 枚举：TARGET | PLAN | CHECKLIST | EXECUTE | ARCHIVE | DONE

## 软约束（AI 理解）
- stage 推荐值：TARGET | PLAN | CHECKLIST | EXECUTE | ARCHIVE | DONE
- 语义映射：DISCUSSING → IDLE
```

### 5.3 Prompt 模板

```python
SYSTEM_PROMPT = """
你是 {methodology_name} 方法论的适配层。
底座要求：{constraints}
方法论语义：{semantics}

生成符合底座约束的 {output_format}。
"""
```

### 5.4 输出校验层

```python
def validate(output, schema):
    """关键字段代码校验，非关键字段提示"""
    for field in schema.required:
        if not validate_format(output[field], schema[field]):
            raise ValidationError(f"字段 {field} 格式错误")
    # 非关键字段可以 warn 但不阻断
```

---

## 六、与其他 Skill 的关系

### 6.1 依赖的 Skill

| Skill | 关系 | 说明 |
|-------|------|------|
| **cms-sop** | 可选依赖 | 推荐的工作方法论 |
| **cas-chat-archive** | 可选依赖 | 会话级归档 |

### 6.2 独立性

- **enterprise-memory 不强制依赖任何 Skill**
- 所有依赖都是可选的
- 不安装依赖时，enterprise-memory 使用原生结构

---

## 七、安装与配置

### 7.1 安装方式

```bash
# 安装主框架
clawhub install enterprise-memory

# 安装 cms-sop（可选，推荐）
clawhub install cms-sop
```

### 7.2 目录结构

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

### 7.3 路径配置

项目目录路径可通过环境变量或配置文件修改：

```bash
# 默认路径
export ENTERPRISE_MEMORY_ROOT=~/.openclaw/EAM-projects/

# 可配置为任意路径
export ENTERPRISE_MEMORY_ROOT=/your/custom/path/
```

**设计原则**：
- 路径可配置，便于用户自定义
- 默认使用 `~/.openclaw/EAM-projects/`
- 兼容不同部署环境

---

## 八、与 CMS SOP 的集成

### 8.1 集成方式

CMS SOP 通过 AI 适配层集成到 enterprise-memory：

```
用户："用 SOP 方法创建项目"
     ↓
enterprise-memory 接收请求
     ↓
LLM 理解 CMS SOP 语义
     ↓
LLM 生成符合 enterprise-memory 约束的 state.json
     ↓
代码校验关键字段
     ↓
更新 GLOBAL-INDEX.md
```

### 8.2 文件映射

| CMS SOP 文件 | enterprise-memory 文件 |
|-------------|----------------------|
| `sop-instances/SOP-xxx/TASK.md` | `projects/SOP-xxx/TASK.md` |
| `sop-instances/SOP-xxx/LOG.md` | `projects/SOP-xxx/LOG.md` |
| `sop-instances/SOP-xxx/state.json` | `projects/SOP-xxx/state.json` |

---

## 九、设计原则

1. **最小化核心**：enterprise-memory 核心保持最小
2. **方法论独立**：工作方法论不依赖 enterprise-memory
3. **AI 适配优先**：能通过 LLM 理解的就不写代码
4. **代码校验兜底**：关键字段必须校验
5. **向后兼容**：不影响现有单独使用的 Skill

---

## 十、版本协调机制

### 10.1 简化方案：SemVer + 接口协议 + 单适配层

- enterprise-memory 声明接口协议版本
- cms-sop 声明实现的协议版本
- 一个适配层覆盖多个方法论版本
- **启动时校验 > 自动降级**（失败要明确）

### 10.2 版本声明格式

```markdown
## 底座版本声明
底座版本: 1.0
约束格式版本: 1.0

## 方法论版本声明
方法论: cms-sop
版本: 1.0
语义版本: 1.0
```

### 10.3 风险缓解

| 风险 | 缓解措施 |
|------|----------|
| AI 理解不稳定 | 提供清晰约束 + few-shot 示例 |
| 关键操作缺乏校验 | 代码校验关键字段 |
| 多方法论冲突 | prompt 中明确优先级 |
| 输出不一致 | 约束具体化 + 输出后自动校验 |

---

## 十一、相关文档

- [ARCHITECTURE-DECISION.md](ARCHITECTURE-DECISION.md) - 架构决策记录
- [METHODOLOGY.md](METHODOLOGY.md) - 方法论定义
- [DEPENDENCIES.md](DEPENDENCIES.md) - 依赖说明

---

*最后更新：2026-04-02*

# TASK.md - SOP-20260330-001

---
- **实例 ID**：SOP-20260330-001
- **任务标题**：企业级 Agent 记忆体系设计
- **负责人**：evan
- **文档状态**：DRAFT
- **版本**：v1.0
- **创建时间**：2026-03-30T22:29:29.559089
- **最后更新**：2026-03-31T06:15:00
- **mode**：full
---

## 任务目标

设计一套"类人记忆体系"的 Agent 使用架构，实现：
1. 多任务交替推进不丢失上下文
2. 任务级信息流可快速定位和切换
3. 跨任务经验可沉淀复用

## 背景

### 真实场景
- 员工工作不是串行的，是多任务交替推进
- 任务 A 做到一半需要暂存，切换到任务 B
- 任务 B 做到一半可能又要切回任务 A
- 切换时不希望上下文混乱或丢失

### 现有问题
- 多 Agent 方案：信息隔离但记忆碎片化
- 单 Agent 方案：记忆统一但信息流混乱

### 核心洞察
- 用户不需要物理隔离，需要逻辑隔离
- AI 记忆应该像人一样：统一存储 + 按需提取 + 经验沉淀

## 范围

### 包含
- 目标定义和需求分析
- 架构方案设计（目录隔离 + 全局索引）
- 技术可行性评估
- 实现路径规划

### 不包含
- 具体代码实现
- OpenClaw 源码改造

## 成功标准

- [ ] 明确"类人记忆体系"的三层结构设计
- [ ] 确定项目级目录隔离方案
- [ ] 确定全局索引/RAG 实现方式
- [ ] 验证"切换项目 = 切换目录 + load 索引"的可行性
- [ ] 设计跨项目经验库机制

## 架构方案（v2 - 整合 CMS SOP + CaS）

### 三层架构

| 层级 | 能力来源 | 核心职责 | 关键文件/机制 |
|-----|---------|---------|--------------|
| **项目层** | CMS SOP | 项目隔离、状态管理、暂存恢复 | 七件套 + state.json |
| **会话层** | CaS | 实时归档、对话记录、快照 | logs/*.md + assets/ |
| **知识层** | CaS + CMS SOP | 经验沉淀、跨项目共享 | 周复盘、月复盘、EXPERIENCE-POOL.md |

### 项目层（CMS SOP）

**项目根目录**：`~/projects/`

**命名规范**：所有项目必须有编号，格式为 `SOP-{日期}-{序号}-{名称}`

```
projects/
├── SOP-20260330-001-企业级Agent记忆体系/
│   ├── state.json         # 项目状态（status/stage/resume）
│   ├── INDEX.md           # 项目索引（AI 记忆入口）
│   ├── TASK.md            # 任务定义
│   ├── LOG.md             # 执行日志
│   ├── RESULT.md          # 结果产出
│   ├── HANDOVER.md        # 交接记录
│   ├── PLAN.md            # 执行计划（Full 模式）
│   ├── DECISIONS.md       # 决策记录（Full 模式）
│   └── ARTIFACTS.md       # 产出物清单（Full 模式）
├── SOP-20260331-002-TPR框架设计/
│   └── ...
├── SOP-20260401-003-日常备忘/
│   └── ...
└── GLOBAL-INDEX.md        # 全局索引（跨项目检索）
└── EXPERIENCE-POOL.md     # 经验库（跨项目沉淀）
└── current-project.json   # 当前项目指针
```

**current-project.json 结构**：
```json
{
  "projectId": "SOP-20260330-001",
  "projectPath": "~/projects/SOP-20260330-001-企业级Agent记忆体系",
  "switchedAt": "2026-03-31T06:50:00"
}
```

**state.json 结构**：
```json
{
  "id": "project-A",
  "status": "PAUSED",
  "stage": "EXECUTE",
  "resume": {
    "lastCompleted": "完成数据分析模块",
    "currentBlocked": "",
    "waitingFor": "",
    "nextAction": "继续设计 API 接口"
  }
}
```

### 会话层（CaS）

- 实时归档：每条消息记录到 `~/.openclaw/chat-archive/<gateway>/logs/YYYY-MM-DD.md`
- 快照保存：切出项目时，将当前会话上下文压缩保存到项目目录
- 渐进式加载：切入项目时，先加载 INDEX.md，按需加载完整上下文

### 知识层（CaS + CMS SOP）

- **日报**（每日 19:00）：AI 经验沉淀，更新当日项目的 LEARNING.md
- **周复盘**（每周六 10:00）：跨项目知识同步，更新 EXPERIENCE-POOL.md
- **月复盘**（每月最后周五 18:00）：组织治理，清理过期项目，归档完成项目

### 切换项目流程

```
切出项目 A：
1. AI 自动更新 INDEX.md
2. 保存 state.json（status=PAUSED, resume=当前进度）
3. 可选：压缩当前会话上下文 → snapshot/

切入项目 B：
1. /new 清空上下文
2. 读取 B/state.json + INDEX.md
3. AI 输出项目进展摘要
4. 等待用户指令：
   - "继续" → 加载 resume.nextAction，开始工作
   - "回顾" → 加载 snapshot/，恢复完整上下文
   - 具体问题 → 按需加载相关文档
```

### 核心原则

- **AI 为主，用户为辅**：INDEX 自动更新，状态自动保存，经验自动提炼
- **渐进式加载**：先轻量（INDEX），后重量（snapshot）
- **类人记忆**：统一存储 + 按需提取 + 经验沉淀

## cms-sop Skill 扩展计划

### 新增触发词
- "切换到"/"切到"/"switch" + 关键词（项目 ID/名称）
- "新建项目"/"创建项目"

### 新增脚本
- `scripts/switch_project.py` — 项目切换逻辑
  - `--keyword`：搜索关键词
  - `--project-id`：精确匹配
  - 输出：匹配结果或切换确认

### 新增能力
1. **新建项目**：复用 init_instance.py，路径改为 ~/projects/
2. **搜索项目**：遍历目录，匹配 ID/名称/INDEX.md 内容
3. **切换项目**：串联切出（保存）+ 切入（加载）流程

### current-project.json
位置：`~/projects/current-project.json`
作用：记录当前项目指针，session 启动时读取

---

---

## INDEX.md 更新机制（v3 - 审核后改进）

### 审核结论
**CONDITIONAL_PASS** — 经子 Agent 严格审核，发现 4 个 Blocker 级问题。

### Blocker 问题及解决方案

| Blocker | 问题 | 解决方案 |
|--------|-----|---------|
| **字段体系不兼容** | state.json 用 `DISCUSSING/TARGET`，INDEX.md 用 `RUNNING/EXECUTE` | 统一以 state.json 为事实源，INDEX.md 只做展示映射 |
| **触发条件依赖 AI 自觉** | 没有"关键操作 → INDEX 同步"的强绑定 | 建立强绑定机制，两者绑定为同一操作 |
| **无原子性保护** | 并发写入或会话中断会导致 INDEX.md 损坏 | 临时写 → 校验 → mv，引入 indexUpdateCount |
| **切出触发器模糊** | 单会话内完成所有操作时，切出触发器永不激活 | 切入时强制自检，而非依赖切出 |

### state.json → INDEX.md 字段映射表

| state.json status | state.json stage | INDEX.md status | INDEX.md stage |
|-------------------|------------------|-----------------|----------------|
| DISCUSSING | TARGET | IDLE | TARGET |
| READY | PLAN | READY | PLAN |
| RUNNING | EXECUTE | RUNNING | EXECUTE |
| PAUSED | * | PAUSED | * |
| BLOCKED | * | BLOCKED | * |
| WAITING_USER | * | WAITING | * |
| DONE | DONE | DONE | DONE |

> INDEX.md 的 status/stage **仅做展示**，所有状态变更必须通过修改 state.json 触发。

### INDEX.md 结构（v3）

```markdown
# INDEX.md - SOP-20260330-001

## 元数据（系统维护，勿手动修改）
- stateRef: 2026-03-31T07:15:00  # state.json.updatedAt 快照
- indexVersion: 3                 # INDEX 结构版本
- updateCount: 5                  # 更新计数器

## 项目状态（自动同步自 state.json）
- status: RUNNING
- stage: EXECUTE
- nextAction: 设计快照压缩策略

## 快速导航
- **任务定义** → TASK.md
- **执行日志** → LOG.md
- **决策记录** → DECISIONS.md
- **产出物** → ARTIFACTS.md

## 当前进展
- ✅ 目标定义（2026-03-30）
- ✅ 架构设计（2026-03-31）
- 🔄 INDEX 自动更新逻辑（进行中）
- ⏳ 快照压缩策略

## 关键决策
- 2026-03-31: 采用 CMS SOP + CaS 整合方案
- 2026-03-31: 项目必须有 ID，统一命名规范
- 2026-03-31: 统一 status/stage 字段体系

## 阻塞项
- 无
```

### 强绑定机制

**原则**：INDEX.md 更新不是"可选优化"，是"关键操作的必需副作用"。

| 触发操作 | 必须执行的动作 |
|---------|--------------|
| 修改 state.json.status | 同步更新 INDEX.md.status |
| 修改 state.json.stage | 同步更新 INDEX.md.stage |
| 新增 DECISIONS.md 条目 | 同步更新 INDEX.md.关键决策 |
| 修改 state.json.resume | 同步更新 INDEX.md.nextAction |
| 切出项目（PAUSED） | 全量同步 INDEX.md |

**实现方式**：封装为单一脚本 `update_project_index.py`，任何状态变更操作都调用此脚本。

```python
# update_project_index.py
def sync_index(state_path, index_path):
    # 1. 读取 state.json
    state = read_json(state_path)

    # 2. 原子写入 INDEX.md.tmp
    index_content = generate_index(state)
    write_file(index_path + ".tmp", index_content)

    # 3. 校验完整性
    if not validate_index(index_path + ".tmp"):
        raise Error("INDEX 校验失败")

    # 4. 原子替换
    os.rename(index_path + ".tmp", index_path)

    # 5. 更新 state.json.updateCount
    state["updateCount"] += 1
    state["lastIndexSync"] = now()
    write_json(state_path, state)
```

### 切入时强制自检流程

```
切入项目 B：
1. 读取 B/state.json
2. 读取 B/INDEX.md 元数据
3. 自检：
   - state.json.updatedAt > INDEX.md.stateRef？
     - 是 → 强制同步 INDEX.md
   - state.json.updateCount != INDEX.md.updateCount？
     - 不等 → 报警告，提示可能存在同步失败
4. 输出项目进展摘要
5. 等待用户指令
```

### 原子性保护

1. **临时文件写入**：先写 `.tmp`，校验通过后 `mv`
2. **更新计数器**：state.json 和 INDEX.md 都维护 updateCount，切入时对比
3. **时间戳快照**：INDEX.md 记录 stateRef（state.json.updatedAt 快照），切入时比对

### 遗漏的触发条件（已补充）

| 触发条件 | 处理方式 |
|---------|---------|
| 文件缺失或损坏 | 切入时自检，若关键文件缺失则报警 |
| 长时间无进展（>24h） | 可选：心跳检查时输出警告 |
| 外部直接修改 state.json | 切入时通过 updatedAt 检测并强制同步 |
| 新增重要文档 | 手动触发或通过 Skill 识别 |

---

## 快照压缩策略（v2 - 审核后改进）

### 审核结论
**CONDITIONAL_PASS** — 经子 Agent 严格审核，发现 5 个 Blocker 级问题。

### Blocker 问题及解决方案

| Blocker | 问题 | 解决方案 |
|--------|-----|---------|
| **DAG summarization 过于复杂** | 因果关系推断、相似合并工程上不可靠 | 简化为"结构化提取 + 启发式过滤 + 可选 LLM" |
| **80% 压缩率会丢信息** | 试错过程、推导上下文会被删除 | 保留 raw.md 原始对话作为安全网 |
| **无快照写入原子性** | 磁盘满、进程被 kill 会导致损坏 | 临时目录写入 → rename → 更新 metadata |
| **无压缩失败降级** | LLM 超时/返回非法格式时无兜底 | 失败时保留完整快照，打 compressionFailed 标记 |
| **切出检测依赖 AI 自觉** | AI 可能不感知切出时机 | 改为系统级事件或 state.json.lastSwitchOutAt |

### 触发时机（不变）

| 触发条件 | 说明 |
|---------|-----|
| **切出项目时** | 每次切换项目时自动快照 |
| **最小间隔 30 分钟** | 防止频繁切换导致大量快照 |
| **每日归档（23:00）** | 即使没切换，每天自动快照（兜底） |

### 保留策略（不变）

- **最近 10 个快照**：完整保留
- **时间衰减**：
  - 最近 7 天：全部保留
  - 8-30 天：每天保留 1 个
  - >30 天：每周保留 1 个
- **最大快照数**：30 个

### 存储结构（v2 - 增加 raw.md）

```
snapshot/
├── metadata.json          # 快照元数据（含 contentHash、compressionFailed）
├── latest -> 2026-03-31T07-15/  # 软链接
├── 2026-03-31T07-15/
│   ├── index.md           # 轻量快照（INDEX.md 副本）
│   ├── summary.md         # 压缩后的对话摘要
│   ├── state.json         # state.json 副本
│   └── raw.md             # 原始对话完整副本（安全网）
└── archive/               # 归档快照（>30 天）
    └── 2026-03/
```

### 压缩算法（v2 - 简化为三阶段）

**放弃完整 DAG summarization，改用可验证的规则集**：

```
Phase 1: 结构化提取（确定性，非 LLM）
├── 从 DECISIONS.md 提取决策列表 ✅
├── 从 state.json 提取 status/stage 变更历史 ✅
└── 从 LOG.md 提取里程碑事件 ✅

Phase 2: 启发式过滤（非严格 DAG）
├── 识别重复内容：连续重复的消息对，删除重复
└── 识别噪音：用户 ACK（"好"/"OK"）+ AI 确认，成对删除

Phase 3: LLM 摘要（仅用于剩余自由文本）
├── 剩余内容 < 20KB 时才调用
├── 摘要结果与 Phase 1 结构化数据合并
└── 失败时保留完整快照（降级）
```

**核心原则**：Phase 1 是确定性的，可验证、可回溯；LLM 只处理无法结构化的部分。

### 压缩失败降级策略

```python
def compress_snapshot(snapshot):
    try:
        # Phase 1 + 2：确定性处理
        structured = extract_structured(snapshot)
        filtered = heuristic_filter(snapshot)

        # Phase 3：LLM 摘要（可选）
        if filtered.sizeKB > 20:
            summary = llm_summarize(filtered)
        else:
            summary = filtered

        # 校验压缩结果
        if summary.sizeKB > snapshot.sizeKB * 0.25:
            return snapshot  # 压缩后反而变大，降级
        if not summary.keyNodes:
            return snapshot  # 摘要失败，降级

        return summary

    except Exception as e:
        log_warning(f"Compression failed: {e}")
        return snapshot  # 异常时降级，保留完整快照
```

### 快照写入原子性

```
1. 写入临时目录 snapshot/.tmp/2026-03-31T07-15/
2. 写入完成后校验完整性（index.md + summary.md + state.json + raw.md）
3. rename 到正式路径 snapshot/2026-03-31T07-15/
4. 更新 metadata.json（同样原子）
5. 更新软链接 latest
```

### 快照校验

每次快照后立即验证：
1. 目录完整性（四个文件都存在）
2. state.json 可被解析
3. summary.md 非空
4. 计算 contentHash，存入 metadata

恢复时：比对 contentHash，不一致则告警并拒绝恢复。

### metadata.json（v2）

```json
{
  "snapshots": [
    {
      "id": "2026-03-31T07-15",
      "createdAt": "2026-03-31T07:15:00",
      "type": "switch-out",
      "sizeKB": 12,
      "contentHash": "sha256:abc123...",
      "compressionRatio": 0.78,
      "compressionFailed": false,
      "turnCount": 45,
      "keyNodes": [
        {"type": "decision", "summary": "采用 CMS SOP + CaS"},
        {"type": "milestone", "summary": "完成 INDEX 设计"}
      ]
    }
  ],
  "retentionPolicy": {
    "maxSnapshots": 30,
    "minInterval": "30m",
    "keepDaily": 7,
    "keepWeekly": 4
  }
}
```

### 恢复策略

```
用户说："回顾"
  ↓
AI 读取 snapshot/latest/metadata.json
  ↓
检查 compressionFailed 标记：
  - true → 直接加载 raw.md（完整上下文）
  - false → 加载 summary.md（压缩上下文）
  ↓
输出项目进展摘要
  ↓
用户说："继续深入"
  ↓
按需加载 raw.md 或历史快照
```

---

## 全局索引（v1 - 简化版）

### 需求分析

**真实场景**：
- 活跃项目：~10 个，经常跟踪和查看
- 历史项目：成百上千，但封存后极少访问
- 核心需求：在活跃项目中快速找到信息

**结论**：RAG/向量库是**过度设计**，维护成本高，收益低。

### 简化方案

**GLOBAL-INDEX.md**：只列出活跃项目

```markdown
# GLOBAL-INDEX.md

## 活跃项目（按最后更新排序）
| 项目 ID | 名称 | 状态 | 最后更新 | 下一步 |
|--------|-----|------|---------|-------|
| SOP-20260330-001 | 企业级 Agent 记忆体系 | RUNNING | 2026-03-31 | 设计快照压缩 |
| SOP-20260331-002 | TPR 框架设计 | PAUSED | 2026-03-31 | 等待审核 |

## 归档项目（>30 天无更新或 status=ARCHIVED）
- 存放在 archive/ 目录
- 需要时手动指定项目 ID 访问
```

### 跨项目搜索

```
用户说："找一下关于 TPR 的项目"
  ↓
AI 遍历活跃项目的 INDEX.md
  ↓
关键词匹配（名称 + 关键决策 + nextAction）
  ↓
返回匹配结果
```

### 历史项目访问

```
用户说："查一下去年的 SOP-20250101-001"
  ↓
AI 直接读取 archive/SOP-20250101-001/
  ↓
不需要全局索引，直接指定路径
```

### 更新时机

| 事件 | 更新内容 |
|-----|---------|
| 新建项目 | 添加到 GLOBAL-INDEX.md |
| 项目状态变更 | 更新 GLOBAL-INDEX.md |
| 项目归档（>30 天无更新） | 移到 archive/，从活跃列表移除 |
| 周复盘 | 全量扫描，清理过期项目 |

---

## 待解决问题

1. ~~**/switch 命令**~~ ✅ 已决定：扩展 cms-sop Skill
2. ~~**INDEX.md 自动更新逻辑**~~ ✅ 已改进：v3 方案（强绑定 + 强制自检 + 原子性）
3. ~~**快照压缩策略**~~ ✅ 已改进：v2 方案（简化算法 + 降级策略 + 原子性）
4. ~~**全局索引/RAG**~~ ✅ 已简化：放弃 RAG，纯文本搜索 + 归档机制

**所有核心问题已解决。**

---

## 整体架构回顾

### 三层架构

| 层级 | 能力来源 | 核心职责 | 关键文件/机制 |
|-----|---------|---------|--------------|
| **项目层** | CMS SOP | 项目隔离、状态管理、暂存恢复 | 七件套 + state.json |
| **会话层** | CaS | 实时归档、对话记录、快照 | logs/*.md + snapshot/ |
| **知识层** | CaS + CMS SOP | 经验沉淀、跨项目共享 | 周复盘、月复盘、EXPERIENCE-POOL.md |
| **索引层** | 纯文本 | 跨项目搜索、项目发现 | GLOBAL-INDEX.md |

### 目录结构（完整版）

```
projects/
├── GLOBAL-INDEX.md           # 全局索引（活跃项目列表）
├── EXPERIENCE-POOL.md        # 经验库（跨项目沉淀）
├── current-project.json      # 当前项目指针
├── SOP-20260330-001-企业级Agent记忆体系/
│   ├── state.json            # 项目状态（事实源）
│   ├── INDEX.md              # 项目索引（AI 记忆入口）
│   ├── TASK.md               # 任务定义
│   ├── LOG.md                # 执行日志
│   ├── DECISIONS.md          # 决策记录
│   ├── RESULT.md             # 结果产出
│   ├── ARTIFACTS.md          # 产出物清单
│   ├── HANDOVER.md           # 交接记录
│   └── snapshot/             # 快照目录
│       ├── metadata.json
│       ├── latest -> 2026-03-31T07-15/
│       └── 2026-03-31T07-15/
│           ├── index.md
│           ├── summary.md
│           ├── state.json
│           └── raw.md        # 原始对话（安全网）
├── SOP-20260331-002-TPR框架设计/
│   └── ...
└── archive/                  # 归档项目（>30 天无更新）
    └── 2025/
        └── ...
```

### 核心设计原则

1. **AI 为主，用户为辅**：INDEX 自动更新，状态自动保存，经验自动提炼
2. **渐进式加载**：先轻量（INDEX），后重量（snapshot/raw）
3. **类人记忆**：统一存储 + 按需提取 + 经验沉淀
4. **强绑定强制机制**：关键操作必须触发 INDEX 同步，不依赖 AI 自觉
5. **原子性保障**：临时写 → 校验 → 原子替换，避免损坏
6. **降级策略**：压缩失败保留完整快照，不丢数据
7. **简化优先**：放弃复杂方案（DAG/RAG），用可验证的规则集

### 项目切换流程（完整版）

```
切出项目 A：
1. 检查距离上次快照是否 > 30 分钟
2. 创建快照（原子写入）：
   - 提取结构化数据（Phase 1）
   - 启发式过滤（Phase 2）
   - 可选 LLM 压缩（Phase 3）
   - 失败时保留完整快照（降级）
3. 更新 state.json（status=PAUSED, resume=当前进度）
4. 强制同步 INDEX.md
5. 更新 current-project.json

切入项目 B：
1. /new 清空上下文
2. 读取 current-project.json（确认当前项目）
3. 读取 B/state.json + B/INDEX.md
4. 自检：
   - state.json.updatedAt > INDEX.md.stateRef？
     - 是 → 强制同步 INDEX.md
   - snapshot/metadata.json 中的 compressionFailed？
     - true → 加载 raw.md
     - false → 加载 summary.md
5. 输出项目进展摘要
6. 等待用户指令：
   - "继续" → 加载 resume.nextAction，开始工作
   - "回顾" → 加载 snapshot/，恢复完整上下文
   - 具体问题 → 按需加载相关文档
```

---

## 决策记录

| 时间 | 决策内容 | 备选方案 | 选择理由 |
|------|----------|----------|----------|
| 2026-03-31 | 采用"目录隔离 + 全局索引"架构 | 多 Agent 物理隔离 | 更接近人的记忆模式，避免碎片化 |
| 2026-03-31 | 整合 CMS SOP + CaS | 自研新系统 | 复用现有能力，减少开发成本 |
| 2026-03-31 | AI 为主，用户为辅 | 用户手动维护 | 降低用户负担，提升体验 |
| 2026-03-31 | 项目切换能力扩展到 cms-sop | 新建 project-switch Skill | 是 cms-sop 的内在能力，保持一致性 |
| 2026-03-31 | 统一 status/stage 字段体系 | 两套独立体系 | 以 state.json 为事实源，INDEX.md 只做展示 |
| 2026-03-31 | INDEX 更新强绑定到关键操作 | AI 自主判断时机 | 避免依赖 AI 自觉，建立客观强制机制 |
| 2026-03-31 | 切入时强制自检而非依赖切出 | 切出时兜底更新 | 切出触发器定义模糊，切入自检更可靠 |
| 2026-03-31 | 快照压缩简化为三阶段 | 完整 DAG summarization | DAG 过于复杂不可靠，改用可验证规则集 |
| 2026-03-31 | 保留 raw.md 原始对话 | 只保留压缩摘要 | 确保摘要可验证，压缩失败有安全网 |
| 2026-03-31 | 压缩失败降级保留完整快照 | 直接报错 | 不丢数据优于压缩失败 |
| 2026-03-31 | 放弃 RAG，纯文本搜索 | 向量数据库 + embedding | 活跃项目少，历史项目极少访问，过度设计 |

---

*最后更新: 2026-03-31T07:35:00*

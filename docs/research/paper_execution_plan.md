# LabscriptAI Dry更新的方案

将 LabscriptAI 推向可投稿 NBT 论文：优先论文证据；从NBT审稿人回复来看审稿人想要：

1. 一个能用的、democratize 且SOTA合成生物学自动化的工具
2. 湿实验的检验+安全且负责，别给他们惹事
3. 落到文章细节：**正文**重画 Figure 1、新增 Table 1（系统级对比）、新增 Extended Data Figure（真机 runtime + memory）；**补充材料**仅 Table S1 + Table S2A/S2B；其余进 Methods/Data files（见 [`paper_deliverables.md`](paper_deliverables.md)）

[图片]

---

## 1. 定位

叙事：LabscriptAI = 模型无关、**一个 agent loop** 的液体处理自动化系统。用户在命令行里直接对话；同一个 agent 根据任务进入 `author` 或 `run` 状态。`author` 负责 NL → 三件套 protocol package；`run` 负责读真机/仿真状态、解释错误、给恢复建议。所有动作都走同一个 gatekeeper、同一套十个工具、同一份 trace / memory 口径，形成从意图到可审查包再到真机恢复与经验复用的闭环。

Here we introduce LabscriptAI, a state-grounded automation agent for synthetic biology that closes the loop from natural-language intent to validated execution by coupling protocol synthesis, simulation-based verification, physical-state monitoring, bounded runtime recovery, and reusable episodic memory.

[图片]

| 论断 | 证明 | 证据 | 混淆风险 |
| --- | --- | --- | --- |
| 编写 | 意图生成可运行协议 | 仿真基准 | 只看修复后 100% 易过拟合 |
| 实验质量 | 生物学与操作合理 | 专家 + 审稿智能体 | 仿真过 ≠ 科学合理 |
| 运行时执行 | 真实物理异常处理 | 真机基准 + 视频 | 无指标像个案 |

## 2. 论文最小产出

原则：正文讲 **系统能力**（可检查、可恢复、可复用），不把 benchmark 日志塞进主表；定量细节进 SI 两张编号表 + Methods/Data files。旧 SI 完整 Prompt 附录删减。

索引：[`paper_deliverables.md`](paper_deliverables.md)

### 2.1 正文（Main）

| 产出 | 要点 | 通过标准 |
| --- | --- | --- |
| **Figure 1** | 一个 Agent：CLI/TUI 对话入口；`author` / `run` 两个状态；gatekeeper；十个工具；skill library；memory store；统一 trace | 三条主线可读；不与 Table 1 重复罗列指标 |
| **Table 1** | 系统级对比：frontier LLM、coding agent、文献/官方工具、LabscriptAI | 回答 Barbara「existing LLM automation tools」；列克制，见 §8.1 |
| **Extended Data Fig. X** | 真机 runtime recovery（≥3 paired case）+ memory 两回合（≥1 case） | 支撑「不是只会写代码」；逐案例明细不进正文 |

配套：**Video 1**（缺吸头等恢复对比）、**Video 2**（memory 回合 1 vs 2），挂 ExtFig 或 SI。

### 2.2 补充材料（仅两张编号表）

| 产出 | 要点 |
| --- | --- |
| **Table S1** | 固定 base model × scaffold（90 题）；证明 scaffold 贡献，非模型红利 |
| **Table S2A** | External community generalization（66 题，分 subset） |
| **Table S2B** | LabFlow IR portability sanity（5–10 题，多 backend compile） |

### 2.3 不单独编号的材料（Methods / Data）

- Baseline manifest（模型 ID、API 日期、prompt hash、预算、工具权限）→ `supplementary/baseline_manifest.csv`
- Runtime 逐案例 → `supplementary/runtime_cases.csv`（原「S4」）
- Capability matrix 短文（原「S5」，Discussion 用）
- 90 题逐题多维评分、hold-out 清单

证据数字：[`authoring_benchmark_results.md`](authoring_benchmark_results.md)。实现状态：[`rollout_12_status.md`](rollout_12_status.md)。

## 3. 四层证据栈

| 基准 | 单位 | 环境 | 核心问题 | 指标示例 |
| --- | --- | --- | --- | --- |
| 编写 | NL → 协议包 | 本地 + code simulate | 能否产出可运行、可审查、可由人类 setup 的协议包？ | simulation pass、first-pass、best-of-budget、attempts、wall time、token、tool calls、`simulator_calls`、`skill_loads`（见 `benchmark_taxonomy`）、expert score |
| 运行时 + memory | 执行中物理异常、同类失败第二回合 | Flex/OT-2 优先，其他平台作为可选扩展；传感器/视觉/日志按证据等级标注 | 能否检测并处理真实偏差，并把一次失败变成下次更早规避？ | 恢复、硬停、人工介入、恢复时间、第二回合是否改进 |
| 外部社区验证 | 公开协议/教程 → 协议包 | Opentrons Protocol Library / OpenPlant 抽样 | 是否能泛化到真实社区协议，而不是只会自定义题？ | package pass rate、simulation pass、setup clarity |
| 跨平台 sanity | 标准移液任务 → 最小 IR → 多 backend compile | Opentrons + PyLabRobot-style action，Autoprotocol export 可选 | 任务表示是否可迁移到 Hamilton/Tecan/Opentrons 概念？ | IR valid、backend compile、unsupported reason |

勿只报「X/90」：须含严格首轮/预算、修复收敛、专家分、真机恢复、经验复用。

投稿口径不能把 runtime/memory 藏进 external/IR 副表。主线证据应是「编写 + 运行时恢复 + memory」三件套；Table S2A/S2B 只作泛化与可移植性旁证。

**分数主张拆分（投稿必守）**：

- **Authoring FP/BoB**（Table 1、S1）：来自 `labscriptai-authoring`（当前 freeze：`authoring-light`），**不是** `labscriptai-full` 端到端 90 题分数。
- **Runtime / Memory**（Table 1 摘要列、ExtFig）：来自真机/trace case study，**独立**于 90 题 composite。
- **External / IR**（S2A/S2B）：泛化与可移植性旁证，**不**替代 runtime 主线。

---

## 4. 智能体核心：一个 loop + 十个工具

[图片]

**新的代码口径**：不要再讲成两个独立 loop。LabscriptAI 是一个命令行对话 agent，内部只有一个 `while true + gatekeeper + tools` 主循环。`author` 和 `run` 是两个状态，不是两个产品。

`author` 状态产出三件套 execution package（`protocol.py`、`setup_card.html`、`manifest.json`，其中 `manifest.json` 记录工具权限与预算）；`run` 状态只读机器人/仿真状态、解析错误、提出恢复候选。模型在任何状态下都只提出受限 tool call，经 gatekeeper 后才可触达 simulator、只读 robot 观测或受控 run control。旧七件套只作为 legacy 兼容。详细实现与开工顺序见 `runtime_build_plan.md`。

代码策略：核心 agent loop 采用轻量 Python 自研，不把通用 coding agent 框架（如大型 TS monorepo）作为主线依赖。`earendil-works/pi` 等可作为 **外部 baseline** 对照。论文贡献仍须落在实验状态、gatekeeper、十个稳定工具、trace、真机恢复与经验复用。

**实现状态（2026-05-21）**：MCP bridge、shadow recovery benchmark、memory MVP、PyLabRobot IR proof 已落地（`rollout_12_status.md`）。详见 `runtime_build_plan.md` §2.1。

**论文未宣称**：90 题 `labscriptai-full` 全流程分数；默认真机自动 recovery（P4 controlled adapter）；Hamilton/Tecan 物理执行。真机 ExtFig 证据与 authoring freeze 分开填报。

| 组件 | 要点 | 通过 |
| --- | --- | --- |
| 单一 agent loop | observe → load skill/memory → candidate tool call → gatekeeper → execute → trace → continue/stop | author/run 两种状态都走同一套流程 |
| `author` 状态 | 文件读写、validate、simulate、protocol search、skill load；输出三件套 + trace | 首轮与预算内指标可比对 Claude Code 等基线 |
| `run` 状态 | robot inspect、error parse、recovery suggest、gated run control、memory | 真机/离线 case 每步有事件日志与状态轨迹 |
| gatekeeper | 每个 tool call 都先检查权限、状态、安全边界 | 模型不可绕过门控直驱硬件 |
| 十个工具 | `package.read_write`、`package.validate`、`package.simulate`、`robot.inspect`、`run.control`、`error.parse`、`recovery.suggest`、`skill.search_load`、`memory.read_write`、`protocol.search` | 工具名稳定，底层实现可逐步替换 |
| 经验库 | 案例记忆的 md/json | 第二回合先查经验，避免重复失败 |

近期 loop 强化采用三步，不直接把模型放到无限权限真机控制位：

| 步骤 | 交付 | 目的 | 风险边界 |
| --- | --- | --- | --- |
| 1 | `robot_http` read-only adapter | robot status、run history、module status、parse_error 进入 Python trace | 只读，不移动 |
| 2 | live recovery shadow benchmark | 模型候选恢复动作与 MCP `suggest_recovery_action` 对比 | **已实现**（shadow）；不执行恢复 |
| 3 | controlled recovery adapter | 未来白名单低风险 `execute_protocol_recovery` 分支进入 loop | **未接通**；须在 shadow 稳定后，gatekeeper + MCP contract 双重通过；高风险人工确认 |

Agent 详细开工方案见 `runtime_build_plan.md`；P0-P5 权限与当前实现状态见 `permission_matrix.md`。

---

## 5. 编程benchmark扩展（55→90 题）

- 须能区分直连 LLM / 编程智能体 / LabscriptAI。目标直接定为 90 题，不再以 70 题作为主目标。
- 题库继承规则：保留历史 55 题作为 `T001-T055`，复用其历史结果作为 continuity baseline；新增 35 题作为 `T056-T090`，专门承担区分强 coding agent（例如 Claude Code best-of-budget 满分后仍需拉开差异）的任务。
- 旧 55 题不简单原样重跑：需要补齐 package 交付要求、score schema、层级标签和 hold-out 标记，但题面主体、历史编号、历史分数映射要保留。
- 90 题按论文分析分组设计：L1 基础协议生成 15 · L2 资源规划 15 · L3 防污染与实验质量 15 · L4 真实生物协议 20 · L5 动态/条件约束 15 · L6 包交付与审查 10。注意：当前 active manifest `benchmarks/authoring/tasks.yaml` 是 schema `0.3`、difficulty-only，L1-L6 不再作为 runner 机器字段。
- 每题主线产三件套：protocol.py · setup_card.html · manifest.json。`manifest.json` 和 setup card 承载 deck、reagent、tip、risk、provenance 等结构化信息；旧七件套只作为历史结果兼容口径。
- Legacy 分层缺口、hold-out 分层切分、first-pass / simulation-pass 边界、deterministic checks、critical failure 闭集合以 `benchmark_taxonomy.md` 为准。
- Hold-out 定义：90 题冻结后至少 30 题作为 hold-out，不进入知识库、示例库、prompt 调试集或经验库；按 L1 5 / L2 5 / L3 5 / L4 7 / L5 5 / L6 3 分层抽样，且新增 35 题至少占 hold-out 的 60%。
- 统一 best-of-budget 上限：attempts ≤ 8、wall time ≤ 30 min、output tokens ≤ 24k、tool calls ≤ 80；所有系统使用同一题面、预算和评分 schema。
- 不只报最终 `x/90`。如果 Claude Code 等 coding agent 在 best-of-budget 下跑满分，仍需用 first-pass、attempts、wall time、tokens、`simulator_calls`、`skill_loads`（若适用）、package consistency、expert score 区分系统能力。
- 外部社区验证集不进入 90 题主分数：Opentrons Protocol Library / OpenPlant 作为真实协议泛化副表。第一版只抽样，不跑完整 833 个社区协议；建议 Opentrons Protocol Library / `Opentrons/Protocols` 抽 30-50 个分层样本，OpenPlant 抽 10-20 个，并只跑 LabscriptAI + 1 个最强 coding-agent baseline。
- PyLabRobot mini set 作为 cross-platform sanity set 放补充材料。
- 第一版 LabFlow IR 只做最小液体处理表示，不声称新通用实验室语言；字段对齐 Autoprotocol-style instruction、PyLabRobot-compatible execution semantics，并借鉴 Uni-Lab-OS 的 Action / Resource / state transaction 思想。IR 只作为补充材料导出，不改 90 题 authoring 主路径；若改成“先出 IR 再编译 Opentrons”，需要作为新 scaffold 重跑主表。

Authoring 主证据：`freeze-v04-20260520`（90 题 + external 66，base model `deepseek-v4-flash`，`labscriptai-authoring-light`）。见 `authoring_benchmark_results.md`。

Table 1 多系统 baseline（GPT/Claude/Gemini、Claude Code、Inagaki、OpentronsAI）**尚未齐**；填 TBD，不得用 light scaffold 分数冒充 full system 或冒充多模型结论。

Benchmark 详细题型与评分字段见 `benchmark_taxonomy.md`。

---

## 6. 运行时 benchmark（Extended Data Fig. X）

正文 **不进表**。Runtime 题目已冻结为 `benchmarks/runtime/runtime20.yaml`（20 个通用液体处理工作站错误/恢复案例）。≥3 高质量真机 paired case 进 Extended Data Fig.；20 个结构化案例结果进 `supplementary/runtime_cases.csv`（标明真机/离线/未做原因）。

冻结规则：`runtime20.yaml` 的 case 定义不再修改；后续只补 run result、trace、视频、hardware unavailable 标记。若某题暂时不能在当前 Flex/OT-2 上运行，不换题，记录 `not_run_hardware_unavailable`。

| 类 | 案例 | 预期行为 | 通过 |
| --- | --- | --- | --- |
| 耗材 | 缺吸头 | 标记不可用，换候选 | 1 预期是无人工介入恢复；2 若实在没枪头则暂停并请求确认 |
| 耗材 | 8 道吸头不足 | 不弃整列或换策略 | 检出后无失败拾取 |
| 耗材 | 废液/弃吸头异常 | 暂停或请人处理 | 不盲续 |
| 甲板 | 目的位占用 | 检测占用→阻断原动作→选择替代位置或请求人工确认 | 无碰撞，轨迹记录移位 |
| 甲板 | 类型错误 | 阻断或走定义/偏移流程 | 不盲移 |
| 甲板 | 未对齐 | 调整 or 暂停 | 无撞针、暂停并叫人 |
| 液体 | 液量低 | 检测低液量→更新 source state→换备用源或暂停请求补液 | 不吸空 |
| 液体 | 运行中液面变 | 更新高度与下游 | 动态调整 |
| 模块 | PCR 盖未开(待定 别的移液工作站不一定有PCR | 重试后暂停 | 不撞盖 |
| 模块 | HS 锁扣 | 按状态重试/停 | 不送入锁定区 |
| 安全 | 闯入 | 硬停 | 停 |
| 安全 | 泼溅/异常视觉 | 硬停或确认 | 不盲动 |

指标：detected · blocked_correctly · recovered · robot_assisted · human_intervention_count · recovery_time_sec · evidence_complete

## 7. Memory reuse（Extended Data Fig. X）

Memory 证据与 §6 同 Extended Data Figure（建议 Panel C）；不与 Table 1 authoring 分数合并。

技术上：

[图片]

案例：主源液量不足 + 备用源充足。

| 回合 | 设置 | 度量 |
| --- | --- | --- |
| 1 | 主孔过少，备孔够 | 检出、恢复时间、人工次数 |
| 2 | 同类任务再现 | 失败更少、恢复更短（吸液前用经验） |

经验字段：case_signature · failure_observation · recovery_action · safety_boundary · reuse_policy · outcome_metrics

有无经验学习的对比

[图片]

## 8. 基线与证据表

服务 Barbara 关切：**与 existing LLM / coding agents / 官方工具的严格对比**。正文仅 **Table 1**（克制列）；scaffold 细节 **Table S1**；泛化 **Table S2A**；IR **Table S2B**。

同任务集、同评分 schema；LabscriptAI 若多工具须在文中写明；基线勿暗中吃亏（仅干净提示须标注）。

主表不要漏掉 `Inagaki-style loop` 和 `OpentronsAI`：前者代表文献 simulator loop，后者代表官方 NL 工具。子集须在 Setting 脚注标 `n`。

### 8.1 正文 Table 1：Systems × Evidence

列（8 列；**Sim 不进正文主表**，见 S1 或脚注）：

| System | Class | Setting† | Authoring FP‡ | Authoring BoB‡ | Expert§ | Runtime¶ | Memory¶ | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-5.5 direct | Frontier LLM | Clean prompt; matched budget | TBD | TBD | TBD | — | — | TBD |
| Claude Opus 4.7 direct | Frontier LLM | Same | TBD | TBD | TBD | — | — | TBD |
| Gemini 3.1 Pro direct | Frontier LLM | Same | TBD | TBD | TBD | — | — | TBD |
| Claude Code | Coding agent | Local edit + simulator; matched budget | TBD | TBD | TBD | debug only† | — | TBD |
| Codex | Coding agent | Same | TBD | TBD | TBD | debug only† | — | TBD |
| Inagaki-style loop | Literature | Reproduced simulator loop | TBD | TBD | TBD | — | — | TBD |
| OpentronsAI | Official NL tool | Supported subset | TBD/n | TBD/n | TBD | — | — | TBD |
| **LabscriptAI** | This work | Authoring: ReAct, v0.4 three-piece, `authoring-light`, freeze 20260520. Runtime/memory: Ext. Data Fig. X | TBD (56§) | TBD (56§) | TBD | y_eval recovered | z_eval improved | TBD |

**Table 1 脚注（投稿必写）**：

- † **Setting**：任务集 n、统一预算、工具权限；OpentronsAI 若 n<90 须标明。Coding agent runtime 列仅为代码调试，非真机 recovery。
- ‡ **FP/BoB** = composite pass（sim ∧ validator ∧ semantic ∧ param_sweep），见 `benchmark_taxonomy.md`。**LabscriptAI authoring 数字来自 `labscriptai-authoring-light`，非 `labscriptai-full` 90 题端到端。**
- § **Expert**：盲评 mean/5；未完成标 TBD。若用 reviewer agent 须脚注区分。
- ¶ **Runtime/Memory**：真机或授权 trace case；与 authoring 90 题**独立**评估。Sim pass 见 Table S1。

§ 括号内 56 为 freeze composite BoB 占位，Table 1 终稿须换强模型/多 baseline 后重填。

### 8.2 补充材料表

#### Table S1 — Scaffold ablation（90 tasks, fixed base model）

| Scaffold | Composite BoB | Composite FP† | Validator | Semantic | Param sweep | Tokens/task | Trace |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direct | 23/90 | TBD | 37/90 | 56/90 | 85/90 | 4,779 | 0/90 |
| Direct + fix-loop | 45/90 | TBD | 72/90 | 60/90 | 87/90 | 8,982 | 0/90 |
| LabscriptAI authoring (light) | 56/90 | TBD | 84/90 | 63/90 | 87/90 | 84,260 | 90/90 |

† FP composite 须从 freeze run 按 first attempt 聚合（`analyze_authoring_run`）。Sim pass（38/80/85）仅作 S1 脚注。数据：`runs/authoring-pilot/freeze-v04-20260520/authoring90/`。

可选 **S1b**：`skill_mode` full/light/off（OpenPlant 18），有 rerun 再加。

#### Table S2A — External generalization（66 tasks）

**独立表**（不与 S2B 合并宽表）：

| Scaffold | N | Composite | Package | Manifest | Setup card† | FP composite | Tokens/task |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direct | 66 | 57/66 | 58/66 | 58/66 | TBD | TBD | 5,729 |
| Direct + fix-loop | 66 | 61/66 | 61/66 | 61/66 | TBD | TBD | 5,990 |
| LabscriptAI authoring (light) | 66 | 60/66 | 61/66 | 61/66 | TBD | TBD | 74,577 |

Subset 脚注：Opentrons Library 18 · OpenPlant source-strict 18 · PyLabRobot 30。OpenPlant 须按 `benchmarks/external_community/OPENPLANT_PROVENANCE.md` rerun 后再填终稿。诚实注：freeze external 上 fix-loop 61/66 vs LabscriptAI 60/66；**主结论以 90 题 S1 为准**。`openplant18-v04-api` 高 provider error 不得当稳定排名。

#### Table S2B — LabFlow IR portability sanity

| Task ID | Task | IR valid | Opentrons compile | PyLabRobot compile | Autoprotocol | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| X001 | 96-well plate replication | TBD | TBD | TBD | TBD | 基础 transfer |
| X002 | Serial dilution | TBD | TBD | TBD | TBD | mix / dilution |
| … | … | … | … | … | … | 5–10 题 |

证据：`tests/test_pylabrobot_smoke`。**软件/backend only**，非 Hamilton/Tecan 真机（见 `rollout_12_status.md` Claim Boundary）。

### 8.3 原补充表去向

| 原编号 | 去向 |
| --- | --- |
| 原 S1 baseline manifest | `supplementary/baseline_manifest.csv` + Methods |
| 原 S2 scaffold×LLM | 等多 base model 跑通后再加；当前仅 S1 单模型 |
| 原 S4 runtime 逐案例 | `supplementary/runtime_cases.csv` + ExtFig |
| 原 S5 capability matrix | Discussion 短文，不编号 |
| 原 S6 + S7 | 拆为 **S2A** + **S2B** |

PyLabRobot、Coscientist、ChemCrow、CRISPR-GPT 不放进 Table 1 定量横比；放入 Discussion capability 短文。

---

## 9. 人类专家盲评 + 评估智能体预筛

reviewer智能体：标准化证据、筛明显错误、给个大体打分；

维度（1–5）：任务对齐 · 生物学合理性 · 液体处理质量 · 安全与对照 · 代码质量。

人类的流程：盲评包 · 固定量表 · 2人独立 · CSV 导出供主表 1 与补充表。

---

## 10. 多模态

甲板图（YOLO）· 前后图（VLM）· 视频前后关键帧 · 液检 — 须含置信度/不确定性；

[图片]

---

## 11. 工作包

| ID | 优先级 | 交付 | 完成 |
| --- | --- | --- | --- |
| WP0 | P0 | 统一 Agent core：`AgentState`、`ToolCall/ToolResult`、gatekeeper、trace、一个 agent loop | 取代旧“双 loop”口径 |
| WP0b | P1 | 十个工具 wrapper：package、robot、run、error、recovery、skill、memory、protocol search | 先包现有代码，后续再清理实现 |
| WP1 | P0 | 90 题 benchmark taxonomy 与 score schema | 直接按 90 题设计，至少 30 hold-out |
| WP2 | P1 | Baseline manifest 与 benchmark runner | 模型 ID、API 日期、prompt、retry、工具权限、评分口径可复现；表格导出不是 STA loop 核心 |
| WP3 | P0 | 核心基线 smoke run | GPT/Claude/Gemini、Claude Code/Codex/OpenHands、Inagaki-style、OpentronsAI 小样本跑通 |
| WP4 | P1 | Authoring benchmark：90 题，含 hold-out | 仿真通过、专家评分、attempt/token/time |
| WP5 | P1 | 专家评分 schema 与盲评汇总 | ≥2 人独立，理想为 ≥3 人 |
| WP6 | P1 | Runtime 真机证据 | ≥3 个高质量 paired case，理想 ≥20 case |
| WP7 | P2 | Scaffolding × LLM ablation | 等多 base model 后扩展 S1b；当前 S1 单模型 |
| WP8 | P2 | 自演化两回合 | 1 个高质量案例，理想扩到 3 类 |
| WP9 | P3 | Figure 1、Table 1、S1、S2A/S2B、ExtFig 整理 | 写作阶段；见 `paper_deliverables.md` |
| WP10 | P1 | `run` 状态强化：read-only robot adapter、shadow recovery benchmark、controlled recovery adapter | 步骤 1–2 Done；P4 未接通 |
| WP11 | P2 | External community validation set | 交付 Table S2A |
| WP12 | P2 | LabFlow IR + PyLabRobot sanity | 交付 Table S2B |
| WP13 | P1 | Permission matrix 与实现状态表 | P0-P5 对齐 runtime action，区分已实现/计划/禁止 |

---

## 12. 验收

| 领域 | 最低可投稿标准 | 理想标准 |
| --- | --- | --- |
| 正文 | Fig1 + Table1（克制列）+ ExtFig runtime/memory | 不新增第二正文主表 |
| Table 1 | ≥3 frontier + ≥2 coding + Inagaki + OpentronsAI；LabscriptAI 脚注拆清 authoring vs runtime | 多模型 + `labscriptai-full` 若有 |
| SI 编号表 | **仅 S1 + S2A + S2B** | S1 含 FP composite |
| Methods/Data | manifest、runtime_cases.csv、逐题分 | 专家盲评 ≥2 人 |
| 编写 | 90 题 freeze + ≥30 hold-out | 多模型 Table 1 全填 |
| 运行时 | ≥3 真机 paired case（ExtFig） | ≥20 case CSV |
| 自演化 | 1 个 memory 两回合（ExtFig） | 3 类故障 |
| 主张 | 不把 56/90 写成 full-system；不把 PyLabRobot smoke 写成真机跨平台 | Cover letter 回应 Barbara |

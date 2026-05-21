# LabscriptAI Dry更新的方案

将 LabscriptAI 推向可投稿 NBT 论文：优先论文证据；从NBT审稿人回复来看审稿人想要：

1. 一个能用的、democratize 且SOTA合成生物学自动化的工具
2. 湿实验的检验+安全且负责，别给他们惹事
3. 落到文章细节：main，一个图两个表格的更新；supply，新增补充材料

[图片]

---

## 1. 定位

叙事：LabscriptAI = 模型无关、**双 agent loop** 的液体处理自动化系统——**编写期**（NL → 三件套 protocol package，ReAct + 工具 + 渐进式知识披露）与 **运行时**（基于状态的 candidate action + 确定性 gatekeeper + trace）分工；二者共用 trace / manifest 口径，形成从意图到可审查包再到真机恢复与经验复用的闭环。

Here we introduce LabscriptAI, a state-grounded automation agent for synthetic biology that closes the loop from natural-language intent to validated execution by coupling protocol synthesis, simulation-based verification, physical-state monitoring, bounded runtime recovery, and reusable episodic memory.

[图片]

| 论断 | 证明 | 证据 | 混淆风险 |
| --- | --- | --- | --- |
| 编写 | 意图生成可运行协议 | 仿真基准 | 只看修复后 100% 易过拟合 |
| 实验质量 | 生物学与操作合理 | 专家 + 审稿智能体 | 仿真过 ≠ 科学合理 |
| 运行时执行 | 真实物理异常处理 | 真机基准 + 视频 | 无指标像个案 |

## 2. 论文最小产出

原则：正文只重做 Figure 1，Figure2A可能会更新，并替换 1 张主表；新增证据尽量进 SI，现有的SI可以做删减去掉Prompt；

| 产出 | 要点 | 通过 |
| --- | --- | --- |
| 主图 1 | 重画为「意图→协议包→仿真→真机状态→感知→恢复→经验库」的一体化架构图 | 编写期/运行时/证据链清晰 |
| 主表 1 | Systems × Metrics 综合对比表：前沿 LLM、编程智能体、仿真闭环、官方工具、LabscriptAI | 正面回 Barbara 关于 existing LLM automation tools 的比较要求 |
| 补充表 S1 | Baseline manifest：模型 ID、API 日期、提示、retry、工具权限、评分口径 | 可复现 |
| 补充表 S2 | Scaffolding × Base LLM ablation | 证明不是单一模型优势 |
| 补充表 S3 | 同 Base LLM × 不同 scaffolding | 证明系统设计贡献 |
| 补充表 S4 | Runtime 逐案例结果 | 支撑真机恢复 |
| 补充表 S5 | Capability matrix：PyLabRobot、Coscientist、ChemCrow、CRISPR-GPT、自驱实验室平台等能力边界 | 避免正文不公平横比 |
| 补充表 S6 | External community validation：Opentrons Protocol Library / OpenPlant | 证明不是只会做自定义 90 题 |
| 补充表 S7 | Cross-platform sanity set：LabFlow IR → Opentrons / PyLabRobot / optional Autoprotocol | 证明移液任务表示不是写死在单一平台 |
| 视频 1 | 缺吸头：失败 vs agent驱动的恢复 | 对比 |
| 视频 2 | 自演化：回合 1 检测并恢复，回合 2 更早规避同类失败 | 可量化改进 |

## 3. 四层证据栈

| 基准 | 单位 | 环境 | 核心问题 | 指标示例 |
| --- | --- | --- | --- | --- |
| 编写 | NL → 协议包 | 本地 + code simulate | 能否产出可运行、可审查、可由人类 setup 的协议包？ | simulation pass、first-pass、best-of-budget、attempts、wall time、token、tool calls、`simulator_calls`、`skill_loads`（见 `benchmark_taxonomy`）、expert score |
| 运行时 + memory | 执行中物理异常、同类失败第二回合 | Flex/OT-2 优先，其他平台作为可选扩展；传感器/视觉/日志按证据等级标注 | 能否检测并处理真实偏差，并把一次失败变成下次更早规避？ | 恢复、硬停、人工介入、恢复时间、第二回合是否改进 |
| 外部社区验证 | 公开协议/教程 → 协议包 | Opentrons Protocol Library / OpenPlant 抽样 | 是否能泛化到真实社区协议，而不是只会自定义题？ | package pass rate、simulation pass、setup clarity |
| 跨平台 sanity | 标准移液任务 → 最小 IR → 多 backend compile | Opentrons + PyLabRobot-style action，Autoprotocol export 可选 | 任务表示是否可迁移到 Hamilton/Tecan/Opentrons 概念？ | IR valid、backend compile、unsupported reason |

勿只报「X/90」：须含严格首轮/预算、修复收敛、专家分、真机恢复、经验复用。

投稿口径不能把 runtime/memory 藏进外部副表。主线证据应是「编写 + 运行时恢复 + memory」三件套；外部社区验证和 cross-platform sanity 只是补充材料，用来反驳过拟合和单平台写死。

---

## 4. 智能体Runtime

[图片]

**编写期与运行时分工**：编写期产出三件套 execution package（`protocol.py`、`setup_card.html`、`manifest.json`，其中 `manifest.json` 记录工具权限与预算）；运行时只消费已落盘的 package，模型在此阶段仅输出受限 JSON candidate action，经 gatekeeper 后才可触达 simulator / 只读 robot 观测等工具。旧七件套只作为 legacy 兼容。两条 loop 的详细实现与开工顺序见 `runtime_build_plan.md`（含 §1.3 编写期 loop）。

代码策略：核心 **运行时** loop 采用轻量 Python 自研，不把通用 coding agent 框架（如大型 TS monorepo）作为主线依赖。`earendil-works/pi` 等可作为 **外部 baseline** 对照；**编写期** ReAct 维护在 `src/labscriptai/authoring/`，避免为论文主线引入额外运行时依赖。论文贡献仍须落在状态、gatekeeper、trace、真机恢复与经验复用。

当前已有：protocol author skill、verify/simulate wrapper、robot LAN API、若干 protocol artifacts、`artifacts/lab-runtime-demo/` 中的 mock runtime loop 产物、旧 JS/MCP recovery loop 代码、以及 Flexagent 根目录下 `workspace-archive/opentrons-lab-exam/` 中已有 physical runtime evidence。`src/labscriptai/` 内已具备 **编写期雏形 + package_validator + 离线 runtime loop（gatekeeper / trace / simulator adapter）+ robot HTTP 只读 adapter + smoke/scenario/authoring_pilot 入口**（详见 `runtime_build_plan.md` **§2.1** 与 **§6.1**）。**仍偏 STA runtime 闭环的缺口**：真机只读观测稳定写入同一 trace、live recovery shadow benchmark、memory 第二回合、vision/liquid 与 runtime 同口径 adapter。

| 组件 | 要点 | 通过 |
| --- | --- | --- |
| authoring loop（编写期） | ReAct：文件读写 / simulate / validate / protocol-library 关键词检索；按需 `load_skill` 渐进披露；输出三件套 + trace | 首轮与预算内指标可比对 Claude Code 等基线 |
| agentloop（运行时） | observe→state update→candidate action→deterministic gate→tool execution→trace→recover/escalate/end | 每步有事件日志与状态轨迹 |
| 规划适配 | 运行时 LLM 只生成 JSON 候选动作；确定性 gatekeeper 校验硬件、安全、状态一致性后才执行 | 模型不可绕过门控直驱硬件 |
| 状态 | 期望/已提交/观测/风险；运行时 JSON schema | 每次恢复可解释 |
| 工具 | robot API、simulator、liquid sensing、YOLO/VLM 辅助观测；观测写入统一 trace schema | 真机与离线回归共用同一轨迹 schema |
| 经验库 | 案例记忆的md/json | 第二回合先查经验再重复失败动作 |

近期 loop 强化采用三步，不直接把模型放到无限权限真机控制位：

| 步骤 | 交付 | 目的 | 风险边界 |
| --- | --- | --- | --- |
| 1 | `robot_http` read-only adapter | robot status、run history、module status、parse_error 进入 Python trace | 只读，不移动 |
| 2 | live recovery shadow benchmark | 模型候选恢复动作与 MCP `suggest_recovery_action` 对比 | 不执行恢复 |
| 3 | controlled recovery adapter | 未来白名单低风险 `execute_protocol_recovery` 分支进入 loop | 当前未接通；必须在 read-only trace 与 shadow benchmark 稳定后，gatekeeper + MCP contract 双重通过；高风险人工确认 |

Runtime 详细开工方案见 `runtime_build_plan.md`；P0-P5 权限与当前实现状态见 `permission_matrix.md`。

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

当前必须诚实写明：90 题 × 多系统完整 baseline matrix 尚未跑完；截至 2026-05-18，已有证据主要是小样本 authoring pilot / runtime scenario smoke。先冻结 manifest、prompt hash、retry budget 和 tool permission，再做大规模 baseline。

Benchmark 详细题型与评分字段见 `benchmark_taxonomy.md`。

---

## 6. 运行时benchmark（≥20 案例，以真机为主）(待定）

正文优先做 3 个高质量真机 paired case；SI 扩展到 ≥12–20 个结构化案例，标明真机/离线/未做原因

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

## 7. Memory reuse

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

## 8. 基线与 SOTA

本节优先服务 Barbara 预审意见中提出的核心问题：与 existing LLM automation tools 的严格比较。正文只放一张综合主表，所有细节表进入补充材料。

同任务集、同评分 schema；LabscriptAI 若多工具须在文中写明；基线勿暗中吃亏（仅干净提示须标注）。

主表不要漏掉 `Inagaki-style loop` 和 `OpentronsAI`：前者代表文献中的 simulator loop，后者代表官方自然语言工具。即使二者只支持子集，也要在 `Setting` 和 `FP x/n` 里诚实标注。

### 8.1 正文的主表：Systems × Evidence（待定）

| System | Class | Setting | Authoring | Expert | Runtime | Memory | Role | 角色 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-5.5 direct | Frontier LLM | Clean prompt; matched retry | FP x/90; BoB x/90; iter x | x/5 | Not designed | Not designed | Strong LLM | 强模型基线 |
| Claude Opus 4.7 direct | Frontier LLM | Same | FP x/90; BoB x/90; iter x | x/5 | Not designed | Not designed | Strong LLM | 强模型基线 |
| Gemini 3.1 Pro direct | Frontier LLM | Same | FP x/90; BoB x/90; iter x | x/5 | Not designed | Not designed | Strong LLM | 强模型基线 |
| Claude Code | Coding agent | Local edit + simulator; matched budget | FP x/90; BoB x/90; iter x | x/5 | Code debug only | Not designed | Coding agent | 编程智能体基线 |
| Codex | Coding agent | Same | FP x/90; BoB x/90; iter x | x/5 | Code debug only | Not designed | Coding agent | 编程智能体基线 |
| Conscientist |  | Open-source agent | Same | FP x/90; BoB x/90; iter x | x/5 | Code debug only | Not designed | Open baseline | 文献基线 |
| Inagaki-style loop | LLM + simulator | Reproduced simulator loop | FP x/90; BoB x/90; iter x | x/5 | Simulation only | Not designed | Literature baseline | 文献基线 |
| OpentronsAI | Official NL tool | Supported subset | FP x/n; BoB x/n; iter x | x/5 | Not evaluated | Not designed | Official tool | 官方工具 |
| LabscriptAI | State-grounded agent | Authoring ReAct + three-piece package + simulation + runtime state + gatekeeper + trace | FP x/90; BoB x/90; iter x | x/5 | x/y recovered; x interventions; x s | x/y improved | This work | 本文 |

### 8.2 补充材料表（待定）

- Table S1: Baseline manifest，包括模型 ID、API 日期、提示模板、retry budget、工具权限、评分口径。
- Table S2: LabscriptAI scaffold × base LLM，证明不是单一 base model 效应，所有模型上我们这框架在自动化的能力都有提高
- Table S3: Same base LLM × direct / simulator loop / coding agent / `labscriptai-authoring`（仅编写期）/ `labscriptai-full`（编写+运行+memory），证明系统设计贡献。当前 DeepSeek Flash 三 scaffold 预实验结果见 `docs/research/authoring_benchmark_results.md`。
- Table S4: Runtime benchmark 逐案例结果。
- Table S5: Capability matrix，放 PyLabRobot、Coscientist、ChemCrow、CRISPR-GPT、自驱实验室平台等能力边界。
- Table S6: External community validation，放 Opentrons Protocol Library / OpenPlant 抽样任务、来源、转换规则、package/simulation/validator 结果。
- Table S7: Cross-platform sanity set，放 5-10 个标准移液任务的 LabFlow IR、Opentrons compile、PyLabRobot-style compile、optional Autoprotocol export 与 unsupported reason。

原则：PyLabRobot、Coscientist、ChemCrow、CRISPR-GPT 不强行放入正文定量主表，避免不公平比较；它们放入补充能力矩阵和 Discussion。

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
| WP0 | P0 | Schema 与 runtime MVP：execution package、runtime state、trace、gatekeeper、agent loop | 先冻结数据口径和证据闭环 |
| WP0b | P1 | Authoring loop MVP：ReAct + 渐进式 skill + simulate/validate 反馈（可先于完整 90 题全量；优先最小 retry 和工具轮闭环） | 与 `authoring_pilot`、Table S3 的 `labscriptai-authoring` 对齐 |
| WP1 | P0 | 90 题 benchmark taxonomy 与 score schema | 直接按 90 题设计，至少 30 hold-out |
| WP2 | P1 | Baseline manifest 与 benchmark runner | 模型 ID、API 日期、prompt、retry、工具权限、评分口径可复现；表格导出不是 STA loop 核心 |
| WP3 | P0 | 核心基线 smoke run | GPT/Claude/Gemini、Claude Code/Codex/OpenHands、Inagaki-style、OpentronsAI 小样本跑通 |
| WP4 | P1 | Authoring benchmark：90 题，含 hold-out | 仿真通过、专家评分、attempt/token/time |
| WP5 | P1 | 专家评分 schema 与盲评汇总 | ≥2 人独立，理想为 ≥3 人 |
| WP6 | P1 | Runtime 真机证据 | ≥3 个高质量 paired case，理想 ≥20 case |
| WP7 | P2 | Scaffolding × LLM ablation | 进入补充材料 |
| WP8 | P2 | 自演化两回合 | 1 个高质量案例，理想扩到 3 类 |
| WP9 | P3 | Figure 1、主表、补充表整理 | 写作阶段再处理，不阻塞 runtime loop |
| WP10 | P1 | Loop 强化三小闭环：read-only robot adapter、shadow recovery benchmark、controlled recovery adapter | 先只读，再 shadow，最后白名单恢复；P4 当前必须标未接通 |
| WP11 | P2 | External community validation set：Opentrons Protocol Library / OpenPlant | 不混入 90 题主分数，作为泛化副表 |
| WP12 | P2 | LabFlow IR + PyLabRobot cross-platform sanity set | 5-10 题；放补充材料；记录 unsupported reason |
| WP13 | P1 | Permission matrix 与实现状态表 | P0-P5 对齐 runtime action，区分已实现/计划/禁止 |

---

## 12. 验收

| 领域 | 最低可投稿标准 | 理想标准 |
| --- | --- | --- |
| 正文图表 | 只改 Figure 1；正文只放 1 张综合主表 | 不额外改动其他主图 |
| 基线 | ≥3 frontier LLM + ≥2 coding agent + Inagaki-style + OpentronsAI | 加 OpenHands、scaffolding × LLM matrix |
| 编写 | 90 题，含 ≥30 hold-out | 90 题全量跑完多模型、多 scaffold，并完成盲评 |
| 专家 | ≥2 人盲评 | ≥3 人，报告一致性指标 |
| 运行时 | ≥3 个高质量真机 paired case | ≥20 个 runtime case，真机占比最大化 |
| 自演化 | 1 个两回合案例 | 3 类故障两回合 |
| 补充材料 | Baseline manifest、ablation、逐题结果、逐案例 runtime | 写作阶段整理；不作为核心代码里程碑 |
| 论文 | 修改 Figure 1；唯一正文主表为 Systems × Metrics | Cover letter 中明确回应 Barbara 的 comparison 关切 |

# Authoring Benchmark Taxonomy

本文档定义 LabscriptAI 论文版 90 题 authoring benchmark 的设计。目标不是把题目变刁钻，而是让不同系统在真实实验自动化能力上拉开层次。

当前活跃 manifest 是 `benchmarks/authoring/tasks.yaml`（截至 2026-05-18 为 schema `0.3`，difficulty-only；见 `nbt_revision_log.md`）。本文中的 L1-L6 是论文分析分组与题型覆盖口径，不应重新写回 active task schema，避免让 runner / sampling / contamination reports 再次依赖已移除的 `level` 字段。

## 1. 核心原则

当前强 coding agent 可能通过反复编辑和模拟拿到高通过率。因此 90 题不能只看 `simulation_pass`，必须记录：

- first-pass success
- best-of-budget success
- attempts
- wall time
- token cost
- package completeness
- deck consistency
- volume feasibility
- tip budget correctness
- contamination and biological quality
- human setup clarity

最终主表可以仍然显示 `FP x/90` 和 `BoB x/90`，但补充材料必须保留逐题多维评分。

## 2. 90 题结构

题库不是重写一套全新的 90 题，而是采用 `55 + 35` 的继承式扩展：

- `T001-T055`：保留上一版 55 题，作为历史可比部分。题面主体和编号不变，补齐层级标签、package 输出要求、score schema 和 hold-out 标记。
- `T056-T090`：新增 35 题，主要放在 L2-L6，尤其覆盖资源规划、防污染、真实生物协议、动态约束和 package 审查，用来区分强 coding agent 在 `BoB x/90` 满分后的成本、稳定性和执行就绪度。
- 历史结果不丢弃，但不混入主表口径：旧 55 题历史分数只作为 `legacy_score` / continuity baseline；主表 `FP x/90` 和 `BoB x/90` 一律按新 package 和新 score schema 重跑旧 55 题后得到 `paper_score`。

| 层级 | 数量 | 区分目标 |
| --- | ---: | --- |
| L1 基础协议生成 | 15 | 基本 Opentrons API、labware、pipette、transfer 是否可靠 |
| L2 资源规划 | 15 | tip、deck、source volume、dead volume、waste、reservoir 是否可执行 |
| L3 防污染与实验质量 | 15 | 换枪头、阴阳性对照、交叉污染、mixing、carryover 是否合理 |
| L4 真实生物协议 | 20 | PCR、qPCR、ELISA、serial dilution、normalization、sample prep 是否有生物学合理性 |
| L5 动态/条件约束 | 15 | 根据样本数、CSV、模块状态、液量约束生成不同执行方案 |
| L6 包交付与审查 | 10 | protocol package 全套一致，人类能 setup，不可仿真风险被标出 |
| 合计 | 90 | 覆盖从能运行到能审查、能执行、能解释 |

### 2.1 Legacy 55 题分布与新增缺口

旧 `legacy/Benchmarkquestion.csv`（CSV 源文件在 `docs/research/legacy/Benchmarkquestion.csv`）只有 `Type/Difficulty/Question`，没有原生 L1-L6 标签。下表是基于 type tag 的初始归档映射；生成 `benchmarks/authoring/tasks.yaml` 时必须逐题复核并冻结。

| 层级 | 90 题目标 | Legacy 55 初始归档 | Legacy 题号 | 新增缺口 | 新增题号 |
| --- | ---: | ---: | --- | ---: | --- |
| L1 基础协议生成 | 15 | 13 | T001, T002, T006, T008, T009, T010, T011, T014, T023, T026, T032, T036, T045 | 2 | T056-T057 |
| L2 资源规划 | 15 | 10 | T003, T005, T012, T022, T025, T028, T031, T040, T044, T046 | 5 | T058-T062 |
| L3 防污染与实验质量 | 15 | 8 | T007, T016, T017, T020, T034, T041, T048, T053 | 7 | T063-T069 |
| L4 真实生物协议 | 20 | 11 | T004, T015, T024, T029, T030, T035, T037, T039, T049, T052, T055 | 9 | T070-T078 |
| L5 动态/条件约束 | 15 | 8 | T019, T021, T027, T033, T042, T043, T051, T054 | 7 | T079-T085 |
| L6 包交付与审查 | 10 | 5 | T013, T018, T038, T047, T050 | 5 | T086-T090 |
| 合计 | 90 | 55 | T001-T055 | 35 | T056-T090 |

新增 35 题只按上表缺口补齐，不再额外改变 90 题层级比例。若复核旧题后移动层级，必须同步更新 `Legacy 55 初始归档`、`新增缺口` 和 `新增题号`，保证每层目标数量不变。

### 2.2 分析分组 × `difficulty` 允许组合矩阵

L1-L6 表示论文分析分组，`difficulty` 表示同一分组内的执行复杂度；二者不能任意组合。该矩阵只用于人工审查、catalog 说明和补充材料解释，不作为 active `tasks.yaml` 的机器字段。防止简单基础移液被标成 Hard/Expert，或包审查题被标成 Easy。

| Level | Allowed difficulty | Notes |
| --- | --- | --- |
| L1 | Easy, Medium | 基础协议生成不应超过 Medium；否则应转入 L2-L5 的具体能力维度。 |
| L2 | Easy, Medium, Hard | 资源规划可到 Hard，但 Expert 应有真实生物或包审查复杂性支撑。 |
| L3 | Easy, Medium, Hard, Expert | 防污染题可因样本矩阵、carryover 或细胞/染料场景达到 Expert。 |
| L4 | Easy, Medium, Hard, Expert | 真实生物协议允许完整难度范围。 |
| L5 | Medium, Hard, Expert | 动态/条件约束至少 Medium；简单参数题应归入 L1/L2。 |
| L6 | Medium, Hard, Expert | 包交付与审查不应是 Easy；Medium 用于单一一致性/manifest/runbook 检查。 |

v0.2 复核修正：

- `T013` 从 L6 改为 L1：题面是全板等体积 transfer + logging，属于基础协议生成，而非包审查。
- `T036` 从 Hard 改为 Medium：serial dilution 是 L1 基础协议生成的代表题，不应超过 L1 难度上限。
- `T045` 从 Hard 改为 Medium：简单 drug addition workflow 没有足够资源/动态/生物复杂性支撑 Hard。
- `T050` 从 Expert 改为 Hard：emergency recovery 是包/运行准备复杂题，但不要求真实外部系统联动。
- `T051` 从 Expert 改为 Hard：环境监控改为 off-platform handoff 后，难度来自条件暂停和风险声明，而非外部系统自动化。
- `T086-T090` 保持 Medium：它们主要检查三件套一致性、manifest、setup card 和修复解释，是 L6 的基础包交付能力题。

## 3. 每题交付格式

每个系统都必须输出 protocol package，而不是只交 `protocol.py`：

```text
protocol.py
deck_plan.json
reagent_plan.json
tip_plan.json
runbook.md
risk_checklist.json
manifest.json
```

最低要求：

- `protocol.py` 可以被 simulator/analyze 执行。
- `deck_plan.json` 与 protocol 中 labware/module/instrument 一致。
- `reagent_plan.json` 总量、dead volume、source/destination 对得上。
- `tip_plan.json` 不隐藏吸头耗尽，不滥用重复吸头。
- `runbook.md` 能让人类 setup。
- `risk_checklist.json` 标出仿真无法证明的风险。
- `manifest.json` 记录模型、版本、prompt hash、retry budget、工具权限、时间戳。

## 4. 最低自动检查

自动检查由 `package_validator` 确定性产出，作为 first-pass 和 best-of-budget 的共同判定基础。

一题通过最低自动检查必须同时满足：

- 三件套 package 存在且 `protocol.py`、`setup_card.html`、`manifest.json` 可解析。
- `protocol.py` 的 simulator/analyze 通过，得到 `simulation_pass = true`。
- `deck_plan.json` 与 protocol 中的 labware、module、instrument、slot/mount 一致。
- `reagent_plan.json` 的 source volume、destination volume、dead volume、单位和余量可行。
- `tip_plan.json` 的 tip 数量、换枪头策略和复用声明可行。
- `manifest.json` 记录 system/model/scaffold/prompt hash/retry budget/tool permissions/timestamp。
- 不出现任何确定性 critical failure。

`simulation_pass` 只表示 simulator/analyze 通过。`first_pass_success` 表示第一次提交就同时满足 `simulation_pass`、`package_complete` 和上面的全部 deterministic checks。

## 5. 评分字段

建议 `score_record.json` 包含：

| 字段 | 类型 | 评分主体 | 含义 |
| --- | --- | --- | --- |
| `task_id` | string | manifest | 题目 ID |
| `system_id` | string | manifest | 被评估系统 |
| `model_id` | string | manifest | 实际模型 ID |
| `scaffold_id` | string | manifest | 建议取值（可扩展，须在 baseline manifest 中枚举）：`direct` · `coding-agent-claude-code` · `coding-agent-codex` · `coding-agent-other` · `simulator-loop` · `labscriptai-authoring`（仅编写期 ReAct）· `labscriptai-full`（编写 + 运行时 + memory，若适用） |
| `first_pass_success` | bool | package_validator | 第一次尝试是否通过最低自动检查 |
| `best_of_budget_success` | bool | package_validator | 统一预算内最终是否通过最低自动检查 |
| `attempts` | int | runner | 尝试次数 |
| `wall_time_sec` | number | runner | 总耗时 |
| `input_tokens` | int | runner | 输入 token |
| `output_tokens` | int | runner | 输出 token |
| `simulator_calls` | int | runner | 调用 simulator/analyze（或等价 verify wrapper）的次数；用于区分「少次仿真即过」与「高次数暴力重试」 |
| `skill_loads` | int | runner | 渐进式披露场景下 `load_skill`（或等价按需加载全文）的次数；计入 `max_tool_calls` 预算时须在 manifest 注明口径 |
| `simulation_pass` | bool | simulator/analyze | 仿真/分析是否通过 |
| `package_complete` | bool | package_validator | 三件套 package 是否齐全 |
| `deck_consistency_score` | number | package_validator | 0-1，公式化或规则化 |
| `volume_feasibility_score` | number | package_validator | 0-1，公式化或规则化 |
| `tip_budget_score` | number | package_validator | 0-1，公式化或规则化 |
| `contamination_safety_score` | number | package_validator + reviewer | 确定性污染规则由 validator 给，语义风险由 reviewer 标注 |
| `task_alignment_score` | number | expert/reviewer | 1-5，是否完成题面目标 |
| `biological_reasonableness_score` | number | expert/reviewer | 1-5，生物学和实验设计是否合理 |
| `liquid_handling_quality_score` | number | expert/reviewer | 1-5，移液顺序、mixing、dead volume、small volume 是否合理 |
| `safety_control_score` | number | expert/reviewer | 1-5，安全、对照、污染控制是否合理 |
| `code_quality_score` | number | expert/reviewer | 1-5，可读性、参数化、可维护性 |
| `expert_score_mean` | number | review aggregation | 上述 5 个 1-5 维度的算术平均 |
| `critical_failures` | array | package_validator + reviewer | 闭集合硬失败原因 |
| `review_notes_path` | string | review aggregation | 盲评或 reviewer agent 输出 |

`critical_failures` 使用闭集合：`collision`、`tip_exhaustion`、`deck_conflict`、`reagent_underfill`、`cross_contamination`、`volume_infeasible`、`module_misuse`、`schema_invalid`、`other`。使用 `other` 时必须在 review notes 中补充原因。

## 6. 题型方向

### L1 基础协议生成 15 题

目的：检验基本 protocol authoring，不应成为主要区分点。

示例方向：

- 单通道 transfer。
- 多通道 plate-to-plate transfer。
- serial dilution。
- reservoir 到 plate 分液。
- runtime parameter 控制样本数。

### L2 资源规划 15 题

目的：让只追求 simulate pass 的系统暴露资源问题。

示例方向：

- tip 数量接近上限，需要复用策略说明或暂停策略。
- reservoir dead volume 影响可用体积。
- 多 source tube 自动分配。
- deck slot 不足，需要压缩 layout 或说明不可执行。
- waste/tip disposal 约束。

### L3 防污染与实验质量 15 题

目的：区分“代码能跑”和“实验设计可信”。

示例方向：

- 高低浓度样本顺序。
- 阴性/阳性对照。
- 每个 sample 独立 tip。
- reagent master mix 防污染。
- pre/post PCR 区分。

### L4 真实生物协议 20 题

目的：回应合成生物学自动化场景，而不是 toy protocol。

示例方向：

- PCR reaction setup。
- qPCR plate setup。
- ELISA wash/addition。
- DNA normalization。
- Gibson/Golden Gate assembly setup。
- Colony PCR setup。
- Enzyme digestion setup。
- NGS library prep 子步骤。

### L5 动态/条件约束 15 题

目的：让系统处理输入变化和运行条件。

示例方向：

- 根据 CSV 样本表生成 transfers。
- 根据样本数选择 96-well/384-well layout。
- 根据 pipette mount 或 labware availability 调整。
- 根据液量不足选择备用 source。
- 根据模块状态决定 pause/request confirmation。

### L6 包交付与审查 10 题

目的：评估工具能否交付给真实操作者。

示例方向：

- runbook 必须列出 setup、labware、reagent、manual checks。
- risk checklist 必须标出不可仿真风险。
- package 内文件互相一致。
- manifest 可复现。
- 人类盲评能独立理解。

## 7. Hold-out 与统一 Budget

- 90 题冻结后，至少 30 题作为 hold-out。
- Hold-out 按层级分层抽样：L1 5、L2 5、L3 5、L4 7、L5 5、L6 3，合计 30。
- Hold-out 应从旧 55 题和新增 35 题中混合抽取；新增题至少占 hold-out 的 60%，即 `T056-T090` 中至少 18 题进入 hold-out。
- Hold-out 不进入 prompt 示例、知识库、memory、调参集。
- 所有系统使用同一题面、同一 retry budget、同一评分 schema。
- 对 coding agent 与 `labscriptai-authoring`，允许其运行 simulator，但要记录 attempts、wall time、tokens、`simulator_calls`、修改轮数及（若适用）`skill_loads`。
- 若系统实现「按需加载知识」工具：每次全文加载计一次 `skill_loads`；该调用仍占用统一 `max_tool_calls` 预算，避免用大量轻量调用稀释可比性。
- `tool_calls` 计数口径：一次模型发起的工具调用计 1 次；`run_simulate`、`validate_package`、`search_protocol_library`、`load_skill`、文件读写与替换都计入。底层 helper 内部调用不重复计数，除非该 helper 被暴露为模型可调用工具。
- 对 LabscriptAI，必须同时记录 scaffold 是否使用 memory；hold-out 首轮不得读取同题经验。

统一 best-of-budget 上限：

- `max_attempts <= 8`
- `max_wall_time_sec <= 1800`
- `max_output_tokens <= 24000`
- `max_tool_calls <= 80`
- 每次尝试必须导出一份 attempt manifest；最终 `best_of_budget_success` 只看预算内最后一个通过最低自动检查的 package。

若某系统因为产品限制无法读取 token 或 tool call 数，必须在 manifest 中标注 `metric_unavailable`，但不能放宽 attempts 和 wall time。

## 8. 外部社区验证集与跨平台 sanity set

90 题是主 benchmark，不与外部社区集混成一个总分。外部集的作用是证明系统不是只会做自定义题，也不是把逻辑写死在单一 Opentrons 任务模板里。

外部集第一版只做抽样，不跑完整社区仓库。建议 Opentrons Protocol Library / `Opentrons/Protocols` 抽 30-50 个分层样本，OpenPlant 抽 10-20 个；副表只需要 LabscriptAI 和 1 个最强 coding-agent baseline，不需要复制 90 题的全 baseline matrix。

| 集合 | 规模建议 | 是否进正文主表 | 作用 | 验证口径 |
| --- | ---: | --- | --- | --- |
| Opentrons Protocol Library / `Opentrons/Protocols` | 30-50 | 副表或补充表 | 真实社区协议泛化 | NL→三件套 package；Opentrons simulator/analyze；package validator |
| OpenPlant Automation Protocols | 10-20 | 补充表 | 社区教程/Notebook/Protocol Designer 风格迁移 | 教程描述→Opentrons package；simulation + package consistency |
| PyLabRobot mini set | 5-10 | 补充材料 | 跨品牌液体处理概念 sanity check | 任务→LabFlow IR→Opentrons compile + PyLabRobot-style action compile |
| BioCoder / LAB-Bench / AutoBio | 小样本或 related work | 不进主表 | 说明生物/自动化 benchmark 背景 | 不与 90 题合并计分；只在问题匹配时做旁证 |

推荐补充材料表：

| Task ID | Task | IR valid | Opentrons compile | PyLabRobot compile | Autoprotocol export | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| X001 | 96-well plate replication | TBD | TBD | TBD | TBD | 基础 transfer |
| X002 | Serial dilution | TBD | TBD | TBD | TBD | mix / dilution |
| X003 | Cherry picking from CSV | TBD | TBD | TBD | TBD | 动态输入 |
| X004 | DNA normalization | TBD | TBD | TBD | TBD | 体积计算 |
| X005 | Tip-limited transfer | TBD | TBD | TBD | TBD | tip policy |
| X006 | Module wait / thermocycler | TBD | TBD | N/A | TBD | backend 覆盖差异需标注 |
| X007 | Contamination-sensitive transfer | TBD | TBD | TBD | TBD | tip policy + ordering |

`IR valid` 至少包含两层：JSON/schema valid，以及确定性语义检查通过。语义检查应尽量复用 `package_validator` / `validators/core.py` 已有的资源、体积、tip、risk 规则；不要为 cross-platform sanity set 另起一套宽松规则。missing-tip、destination occupied、module polling 等恢复场景归入 runtime benchmark / Table S4，不放入 cross-platform authoring compile 表。

### 8.1 LabFlow IR 边界

为了避免审稿人质疑自定义 IR 过重或闭门造车，第一版只定义最小液体处理 IR，并明确对齐已有社区概念：

- **Autoprotocol-style instructions**：`refs` / `instructions` / liquid handling step 的 JSON 化思想可借鉴，但不把整套规范作为强依赖。
- **PyLabRobot-compatible execution semantics**：IR 中的 transfer / mix / pick-up-tip / aspirate / dispense / drop-tip 应能编译成 PyLabRobot 风格动作，用于跨平台 sanity check。
- **Uni-Lab-OS-inspired state model**：借鉴 Action / Resource / Action&Resource 与状态事务思想，但不把完整实验室 OS 引入主线实现。

第一版 IR 只覆盖：

- `resources`：plate、tiprack、reservoir、tube、module、pipette。
- `operations`：transfer、mix、pause/request_confirmation、module_wait、thermocycler_step。
- `constraints`：new tip、reuse policy、avoid contamination、dead volume、max/min volume、deck availability。
- `runtime_state`：expected、committed、observed、risk、allowed recovery。

目标表述：LabscriptAI uses a minimal liquid-handling IR aligned with Autoprotocol-style instructions and PyLabRobot-compatible execution semantics, rather than claiming a new general laboratory language.

重要边界：LabFlow IR 第一版只作为补充材料导出和跨平台 sanity check，不改变 90 题 authoring 主路径。若未来把 authoring agent 改成“先出 IR 再编译到 Opentrons”，这属于架构级 loop 升级，必须作为新的 scaffold 重新冻结 prompt hash、retry budget、tool permission，并重跑主表 baseline。

## 9. 为什么能区分 Claude Code 满分

如果 Claude Code 最终 `BoB x/90` 满分，benchmark 仍然有区分度：

- `FP x/90` 显示首轮可靠性。
- `attempts/time/tokens` 显示成本。
- `simulator_calls` / `skill_loads`（若记录）显示是否依赖高频仿真或大量按需知识加载。
- package consistency 显示是否只是修到仿真过。
- expert score 显示生物学和操作合理性。
- runtime readiness 显示能否交给机器人和操作者。
- LabscriptAI 的优势应体现为更少返工、更完整 package、更低人工介入、更可追踪 evidence。

## 9. 下一步产物

建议按此顺序落地：

0. authoring loop MVP（与 runtime 共用 trace 口径；见 `runtime_build_plan.md` §1.3）
1. `schemas/protocol_package.schema.json`
2. `schemas/score_record.schema.json`
3. `benchmarks/authoring/tasks.yaml`
4. `benchmarks/authoring/holdout_manifest.json`
5. `src/labscriptai/benchmark/package_validator.py`
6. `src/labscriptai/benchmark/analyze_authoring_run.py` / reviewer summary scripts

# LabscriptAI Runtime Build Plan

本文档定义 LabscriptAI 核心代码的开工方案，**以运行时（execution）loop 为主**；编写期（authoring）loop 的边界与复用资产见 **§1.3**，不另开文档。

结论：核心 **运行时** 自己写轻量 Python，不把通用 coding agent 框架（大型跨语言 monorepo）作为主线依赖；外部 agent 框架只作为 **baseline** 或 LLM adapter。编写期优先 **同仓库 Python** 的 ReAct + 工具实现，与运行时共用 trace / manifest 口径。旧原型已删除，不再作为仓库主线。

## 1. 架构选择

### 1.1 采用轻量 Python core

LabscriptAI 的核心贡献是 state-grounded lab execution agent，而不是通用 coding agent。核心 loop 应该直接服务液体处理执行：

```text
observe
  -> update runtime state
  -> retrieve relevant memory
  -> ask model for candidate JSON action
  -> deterministic gatekeeper check
  -> execute approved tool call
  -> write trace event
  -> recover / escalate / end
```

### 1.2 不基于 pi 改主 runtime

`earendil-works/pi` 更适合作为通用 coding-agent baseline 或可选 LLM/tool adapter。它不应成为 LabscriptAI 主 runtime 的原因：

- 论文贡献需要落在实验状态、门控、安全、真机 trace 和恢复闭环，而不是通用 agent harness。
- 当前仓库与 Opentrons、Python protocol、simulate、robot HTTP API 的耦合更自然，Python 小核心更容易复现。
- 真机执行时必须保证模型只能提出候选动作，不能绕过 deterministic gatekeeper 直接驱动硬件。
- 大型 TypeScript monorepo 依赖会增加审稿复现成本，并模糊系统边界。

### 1.3 编写期 authoring loop（与 §1.1 运行时 loop 并列）

编写期负责 **NL → 三件套 protocol package**（`protocol.py`、`setup_card.html`、`manifest.json`），产出经 `package_validator` 与（可选）simulator 反馈迭代后的可交付物；旧七件套只保留为 legacy 兼容，不作为新主线。**不**在此阶段让模型绕过 gatekeeper 直驱硬件。

设计要点（与 benchmark / `benchmark_taxonomy.md` 对齐）：

- **ReAct + 工具**：读/写/补丁式编辑 package 文件、调用已有 verify/simulate wrapper、`validate_package`、以及 `skills/opentrons-protocol-library/scripts/search_protocols.py` 的**关键词检索**（不必上向量 RAG）。
- **渐进式知识披露**：system prompt 只挂 skill **目录**，全文按需加载，控制 token。
- **ADR：渐进式披露优先于 RAG**：领域知识（tip、deck、module、API level、常见错误、runbook/risk 规则）以 `load_skill` 按需加载全文；protocol library 只作为关键词检索工具，用于找具体 Opentrons 代码样例。当前不引入向量 RAG，避免新增索引状态、评测污染面和审稿复现成本；若后续加入 embedding 检索，必须在 manifest 中单独标注 corpus 版本与检索调用预算。
- **证据**：编写期工具调用同样写入与运行时兼容的 trace（或子 trace），`manifest.json` 记录 `tool_permissions`、retry budget、prompt hash。

实现落点建议为 `src/labscriptai/authoring/`（与 `runtime/` 平级），详见 §3；开工顺序见 §6 表首行。

## 2. 当前已有基础

当前仓库已有可复用基础：

| 资产 | 路径 | 可复用方式 |
| --- | --- | --- |
| Protocol author skill | `skills/opentrons-protocol-author/` | 作为 authoring scaffold 和 protocol package 生成提示基础 |
| ReAct + 渐进式 skill 实现 | `src/labscriptai/authoring/` | 编写期工具轮、按需加载知识、上下文压缩；与 runtime 共用 trace 口径 |
| Verify wrapper | `skills/opentrons-protocol-verify/scripts/verify_protocol.py` | authoring pilot `--simulate` 等路径可调 Opentrons analyze/simulate；`runtime/adapters/simulator.py` 当前以 `validate_package` 为主（可注入 `simulation_pass`） |
| Robot LAN API | `skills/opentrons-robot-lan/scripts/opentrons_robot_api.py`（及 skill 文档）+ `src/labscriptai/runtime/adapters/robot_http.py` | HTTP fallback 是正式路线；当前 adapter 支持只读观测，后续继续并入统一 trace / benchmark |
| Robot skill docs | `skills/opentrons-robot-lan/` | 作为真机只读检查、上传、分析、run action 的操作约束 |
| Artifact protocols | `artifacts/*.py` | 作为早期 smoke examples |
| Mock runtime demo artifacts | `artifacts/lab-runtime-demo/` | 已有 missing-tip、occupied-destination、liquid-sensing、self-evolution 的 state trace / event log / summary，可作为 Python MVP 的回归样例 |
| Legacy JS/MCP runtime code | sibling `Opentrons-Lab-Agent-doc-pr/mcp-servers/opentrons-mcp/` | 已实现 recovery decision、run control、live-state、probe、simulation 等逻辑；可迁移设计，不建议作为论文主 runtime 依赖 |
| Physical evidence | `workspace-archive/opentrons-lab-exam/results/physical_runtime_bench_20260429/`（相对 Flexagent 根目录） | 可整理进 runtime evidence index |

### 2.1 截至 2026-05-18 的实现快照（与 §6.1 一致）

下列能力已在 **`src/labscriptai/`** 落地（以**离线 / 小样本 / 场景切片**为主；**不等于** 90 题 authoring 全量主结果或真机长视频证据已齐）：

- **编写期 authoring**：`authoring/`（`agent.py`、`tools/`、`task_state.py` 等）可与 `benchmark/authoring_pilot.py` 衔接；渐进式 skill 已在仓库主代码中维护。
- **JSON schema 文件（MVP 口径）**：仓库根 `schemas/` 下已有 `execution_package.schema.json`、`runtime_state.schema.json`、`trace_event.schema.json`、`score_record.schema.json`，以及 `schemas/adapters/opentrons.schema.json` stub。
- **package_validator**：`benchmark/package_validator.py` + `benchmark/validators/`（`core.py` / `opentrons.py` / `models.py`）。
- **Runtime Python loop**：`runtime/agent_loop.py`、`state.py`、`gatekeeper.py`、`trace.py`、`actions.py`、`model_adapter.py`；适配器目录下当前仅有 **`runtime/adapters/simulator.py`**（复用 verify / simulate 封装）。
- **评测入口**：`runtime/smoke_benchmark.py`、`runtime/scenario_benchmark.py`、`benchmark/authoring_pilot.py`；另有 `benchmark/contamination_probe.py`、`benchmark/analyze_authoring_run.py`、`benchmark/review_authoring_run.py` 等辅助脚本。

**仍相对 §4 MVP / §7 验收偏「薄」或缺失的部分**（后续排期）：

- **真机只读进统一 trace**：`runtime/adapters/robot_http.py` 已有只读 HTTP snapshot 基础；后续重点是把该观测稳定写入与离线 demo 同一 trace 流水线，并纳入 benchmark summary。
- **live recovery shadow benchmark**：MCP/JS 侧已有 `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery` 设计与实现，但 Python runtime loop 还没有只读读取 live run failure guidance，并把模型候选恢复动作与 MCP 建议进行 shadow 对比。
- **controlled recovery adapter**：Python loop 还没有受控调用 `execute_protocol_recovery`；第一版只应开放白名单低风险分支（例如 missing-tip 下一候选重试），所有目的位迁移、collision、unknown、液体异常继续人工确认。
- **memory 第二回合**：未实现独立 `memory.py` / case writer；§7 中「同一 failure 产出 memory 并在第二回合检索」尚未闭环。
- **vision / liquid_sensing 专用 runtime adapter**：未在 `runtime/adapters/` 下以独立模块接入（视觉与相机脚本仍在 `vision/`、`mcp-servers/` 等路径）。
- **全量 90 题 NL→package benchmark**：`benchmarks/authoring/tasks.yaml` 仍是 authoring 能力口径；`smoke_benchmark` / `scenario_benchmark` 的定位是 loop/门控/证据链验证。全量 authoring 跑数不是当前 runtime 主线的阻塞项。
- **LabFlow IR / cross-platform sanity set**：尚未定义最小液体处理 IR，也未实现 Opentrons package 与 PyLabRobot-style action 的双向/单向 compile sanity check；该项只服务补充材料，不进入主 runtime 闭环的安全关键路径。

## 3. 目标代码结构

规划目标与**当前仓库**的对照（`find src/labscriptai -name '*.py'` 可复查）。**已实现**的目录/文件不再重复列出；下列为**仍可能缺失或仅部分存在**的落点，便于对照 §6 顺序继续补齐：

```text
src/labscriptai/
  runtime/
    schemas.py          # 可选：若坚持独立模块，可与根目录 schemas/*.json 同步；当前逻辑分散在 state/trace/validator
    memory.py           # 未实现：memory case writer / 第二回合检索
    adapters/
      robot_http.py     # 已存在：真机 HTTP 只读观测；后续继续接入统一 trace 与 benchmark
      recovery_mcp.py   # 未实现：读取 MCP recovery guidance；先 shadow 对比，后续才考虑受控调用 execute_protocol_recovery
      vision.py         # 未实现：与 runtime loop 同口径的 vision adapter
      liquid_sensing.py # 未实现
      human_confirm.py  # 未实现（或可由 gatekeeper escalate 路径替代）
schemas/
  （已存在 MVP JSON 文件，见 §2.1）
examples/runtime_cases/
  （可选回归用例目录，按需补充）
```

## 4. 第一版 MVP

第一版先做离线和 read-only 真机安全闭环，不急着自动移动硬件。

### MVP 输入

- `execution_package/`
  - `protocol.py`
  - `deck_plan.json`
  - `reagent_plan.json`
  - `tip_plan.json`
  - `runbook.md`
  - `risk_checklist.json`
  - `manifest.json`
- 初始 `runtime_state.json`
- 允许的 tool registry
- LLM provider config

### MVP 输出

- `trace.jsonl`
- `final_state.json`
- `run_summary.json`
- `memory_case.md` 或 `memory_case.json`

### MVP 行为

1. 读取 protocol package 并校验 schema。
2. 运行 simulator/analyze，写入 trace。
3. 读取 robot health、camera、run status 等 read-only 状态，写入 trace。
4. LLM 只输出 JSON candidate action。
5. Gatekeeper 检查 action 是否允许。
6. 允许的动作进入 tool adapter；不允许的动作转为 block/escalate event。
7. loop 结束后导出 evidence package。

## 5. Gatekeeper 边界

模型可以提出：

- `simulate_protocol`
- `inspect_robot_state`
- `capture_deck_image`
- `mark_resource_unavailable`
- `choose_alternative_source`
- `request_human_confirmation`
- `pause_run`
- `resume_run`
- `abort_run`

权限分层：模型可以拥有更大的“驾驶舱”，例如读更多上下文、调用 simulator/validator、读取只读真机状态、提出恢复候选；但不能绕过 gatekeeper 直接获得硬件“方向盘”。完整 P0-P5 对照表见 `permission_matrix.md`。截至 2026-05-18，P4 仍是未来能力，不是当前 Python loop 已接通的能力。

| 权限层 | 模型可做 | 执行边界 |
| --- | --- | --- |
| P0 | 读任务、写 protocol package | 允许 |
| P1 | 跑 simulator、validator、解释报错 | 允许，计入 manifest/tool budget |
| P2 | 读 robot status、run history、module status、parse_error | 允许；已有 `robot_http` 只读 adapter 基础，仍需补齐统一 trace / benchmark 口径 |
| P3 | 提出恢复动作 | 允许，但只是 candidate action |
| P4 | 执行白名单恢复 | 未来项；当前未接通。只能在 P2/P3 与 shadow benchmark 稳定后，开放 gatekeeper + MCP contract 均通过的低风险分支 |
| P5 | 直接 aspirate / dispense / move / start live run | 不允许模型直接执行 |

模型不能直接执行：

- 未经检查的 robot movement。
- 未经确认的 run start/play。
- 违反 tip、deck、liquid、module、安全状态的动作。
- 绕过 trace 的外部命令。

所有硬件移动类动作必须满足：

- protocol package 已通过基础校验。
- runtime state 有明确 robot identity 和 deck state。
- safety policy 允许。
- action schema 校验通过。
- gatekeeper 产出 approved event。

## 6. 开工顺序

| 顺序 | 交付 | 说明 |
| --- | --- | --- |
| 0 | authoring loop MVP（可选与 1 并行） | ReAct + 工具 + 渐进式 skill；衔接 `authoring_pilot` 与 simulate/validate 反馈；见 §1.3 |
| 1 | JSON schemas | 先冻结数据口径，避免后续 benchmark 不可比 |
| 2 | package validator | 校验每题 package 是否完整、字段一致 |
| 3 | trace writer | 所有工具调用先统一写 trace |
| 4 | runtime state model | 表达 expected/committed/observed/risk |
| 5 | gatekeeper MVP | 先做 deterministic block/approve/escalate |
| 6 | simulator adapter | 复用现有 verify wrapper |
| 7 | robot read-only adapter | 先 health/camera/list-runs，不自动移动 |
| 8 | live recovery shadow benchmark | 读取 MCP failure guidance，让模型只判断下一步恢复动作，不执行 |
| 9 | controlled recovery adapter | 未来项；只在 read-only trace 与 shadow benchmark 通过后，开放白名单 `execute_protocol_recovery` 分支，高风险继续人工确认 |
| 10 | agent loop MVP | 接 LLM JSON candidate action；统一 offline/live-read-only/shadow trace |
| 11 | memory case writer | 支持两回合自演化证据 |

**与 §2.1 对齐的粗粒度进度（2026-05-20）**：0 部分 ✓（`authoring/` + pilot；新主线为三件套，legacy 七件套仅兼容）；1 ✓（根 `schemas/*.json`）；2 ✓；3 ✓（`runtime/trace.py`）；4 ✓（`runtime/state.py`）；5 ✓；6 ✓（`adapters/simulator.py`）；7 部分 ✓（已有 `robot_http` 只读 adapter，仍需统一 trace / benchmark 口径）；8 ✗；9 ✗；10 部分 ✓（`smoke_benchmark` / `scenario_benchmark` / `agent_loop`，但未接 live recovery shadow）；11 ✗。

### 6.1 当前 smoke demo 入口

当前 Python MVP 已有一个不调用 robot API 的 runtime smoke runner，用于快速检验：

```bash
PYTHONPATH=src uv run python -m labscriptai.runtime.smoke_benchmark \
  --provider deepseek \
  --output-dir runs/runtime-smoke/deepseek-demo \
  --per-level 2 \
  --max-steps-per-task 1 \
  --retry-attempts 2
```

它会读取 `benchmarks/authoring/tasks.yaml`，按难度分层（Easy/Medium/Hard/Expert）抽样 hold-out 任务，构造 validator-clean 的占位 protocol package，然后让 LLM 只返回 JSON candidate action。candidate action 仍必须经过 deterministic gatekeeper，最后写入逐题 `trace.jsonl` 和 `summary.json`。该 demo 只验证 runtime loop、模型 adapter、gatekeeper、trace 证据链，不代表已完成 90 题 authoring benchmark。

当前另有两个推进入口：

- `labscriptai.runtime.scenario_benchmark`：运行 missing-tip、occupied-destination、liquid-sensing、wrong-labware preflight、home safety、module polling 六类异常恢复场景；不调用 robot API，只评估 LLM candidate action 与 deterministic gatekeeper。
- `labscriptai.benchmark.authoring_pilot`：小规模 authoring pilot，让模型生成三件套 protocol package（legacy 七件套只兼容旧结果），再由 package validator 检查 package 完整性、deck/protocol 一致性、tip budget、risk schema 与 manifest provenance。该入口支持 `--simulate`，可通过已有 verify wrapper 调用本地 Opentrons simulator，并把 `simulation_pass` 写入 score record。
- Authoring pilot 支持 `--retry-attempts` 和逐题 checkpoint。每个任务会写入 `Txxx/record.json`，每次尝试的 package 位于 `Txxx/attemptN/package/`，并且 `summary.json` 会在每题结束后刷新，避免大 JSON 输出截断或长跑中断导致整批结果丢失。

当前 smoke evidence：

- Runtime scenario benchmark：DeepSeek 在 6 个异常恢复场景上 `6/6 passed`，无 robot API 调用。
- Authoring pilot：早期 legacy 七件套口径下，DeepSeek 生成的 3 个 package 经 PRE v0 修复后，回放本地 Opentrons simulator 为 `3/3 simulation_pass`，并通过 package validator。扩展到 6 个 hold-out 分层样本后，`5/6` 生成完整 package，`5/5` generated packages simulation pass；剩余失败来自模型 JSON 输出截断。PRE/validator 回放后 `5/5` generated packages 可通过 deterministic checks。PRE 当前只修结构化 JSON 元数据，不改 `protocol.py`。

## 7. 验收标准

MVP 完成不以“真机跑完整实验”为标准，而以证据闭环为标准：

- 任一 protocol package 可被 schema validator 检查。
- 每次 loop 都产生可追踪 `trace.jsonl`。
- LLM 输出非法动作时 gatekeeper 能 block 并记录原因。
- simulator 结果进入统一 trace。
- read-only robot observation 进入统一 trace。
- run summary 可以用于人工审阅和 runtime case 汇总。
- 同一 failure case 可以产出 memory，并在第二回合被检索使用。

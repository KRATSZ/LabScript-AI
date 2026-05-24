# Agent Unification — 架构设计

> 状态：**设计稿（Stage 0）**。本文档只规划，不落代码。任何 `.py` 改动都在本文件被冻结评审之后再开始。
>
> 上游叙事入口：[`docs/research/runtime_build_plan.md`](research/runtime_build_plan.md)、[`docs/research/paper_execution_plan.md`](research/paper_execution_plan.md) §4。
> 当前要替换的双 loop 实现：`src/labscriptai/authoring/agent.py::AuthoringAgent.run` 与 `src/labscriptai/runtime/agent_loop.py::run_offline_loop`。

## 0. 目标与硬约束

目标：把 `authoring/agent.py`（ReAct + 自有 ToolRegistry）和 `runtime/agent_loop.py`（candidate action + gatekeeper）合并为同一个 `LabscriptAgentLoop`，对外暴露稳定的 10 个工具名，author/run 只是 `state.mode` 不同。

冻结的硬约束（违反即拒绝合并）：

1. `src/labscriptai/benchmark/authoring_pilot.py` 的 CLI、输入文件、output 目录结构、summary 字段不变；只允许 **新增** `--provider labscriptai-unified`。
2. `benchmarks/authoring/tasks.yaml` schema 0.3 不动。
3. `runs/.../summary.json` 现有字段（见 `_write_summary`）一律保留；只允许追加字段。
4. `src/labscriptai/runtime/gatekeeper.py` 的现有规则只能 **扩展**（更严或新增规则），不可缩减、不可放宽既有判定。
5. `validate_package`、`simulate_protocol_package`、`SkillLoader`、`runtime/memory.py` 直接复用，不重写。
6. 三件套 `protocol.py / setup_card.html / manifest.json`（`REQUIRED_PACKAGE_FILES`）作为 author 模式产物的唯一对外契约。

### 0.1 设计抉择（评审冻结）

| 议题 | 本稿选择 | 说明 |
|---|---|---|
| **`mode` 语义** | **双轨：LLM 可见性过滤 + gatekeeper** | 10 个标准工具在 registry **全部注册**；`list_specs(mode=)` 按 mode 缩小模型可见工具（等价现 `tool_profile`）；模型若仍提出不可见工具名，gatekeeper 按 §6 阻断。不是「只改 gate、模型永远看到 10 工具」的纯 hint 方案。 |
| **对外 agent 范式** | **仅 `tool_calls`** | `CandidateAction` 不删，仅作为 `run.control` 的 arguments + `evaluate_action` 入参；runtime 离线 benchmark 的 `CandidateProvider` 在 P2 转为产出 `ToolCall`（或薄包装为 `run.control`）。 |
| **LLM 工具名（author）** | **继续暴露 5 个独立文件名** | 对模型仍为 `read_file` / `write_file` / `str_replace` / `json_set` / `append_md`（与现 `_native_tool_specs`、`tests/test_authoring_agent.py` 一致）；registry 内部映射到 `package.read_write` 子动作。不强制模型改用 `package.read_write{op:...}`。 |
| **run 驱动（Phase 1）** | **turn-based** | 与现 `AuthoringAgent` 相同：`for step in range(max_steps)` + `client.complete`。event-driven（订阅 robot 报错）推迟到 P4 之后，不在 P1 阻塞 benchmark。 |

---

## 1. AgentState 字段表

`AgentState` 是 `author` 与 `run` 唯一共享的不可变快照。字段尽量少；每次状态推进生成新实例，旧实例进 trace。当前 `authoring/task_state.py::AuthoringTaskState` 与 `runtime/state.py::RuntimeState` 的并集 + 必要新字段。

| 字段 | 类型 | 来源 | 何时更新 |
|---|---|---|---|
| `schema_version` | `str`（固定 `"1.0"`） | 常量 | 不变 |
| `run_id` | `str` | loop 启动时 `f"{mode}-{task_id}-{uuid4()}"` | 一次 run 内不变 |
| `mode` | `Literal["author", "run"]` | 入口 CLI 或调用方传入 | 一次 run 内不变（P1 不允许中途切换；见 §1.1） |
| `phase` | `AgentPhase`（见 §1.1 并集） | author 起始 `drafting`；run 起始 `preflight` | 工具结果、`validate`/`simulate`、gatekeeper、错误注入后更新 |
| `package_ready` | `bool` | author：`final.package_ready` 或三件套齐全后由 loop 置 `True` | **author 成功主标志**；与 `phase` 解耦（现 `AuthoringTaskState` 几乎不改 `phase`） |
| `task_spec` | `TaskSpec`（含 `task_id: str`、`difficulty: str \| None`、`prompt: str`、`required_files: tuple[str,...]`、`budget: dict`） | author 来自 `AuthoringTask`；run 来自 CLI/MCP 入参 | 入口构造后不变 |
| `package` | `PackageRef`（含 `dir: Path`、`files_present: tuple[str,...]`、`manifest_digest: str \| None`、`last_validation: dict \| None`） | author 中由 `write_file` / `validate_package` 写入；run 中由入参指定 | 每次 package.* 工具结束后刷新 |
| `robot_status` | `Mapping[str, Any]` | run 模式由 `robot.inspect`（MCP 或 robot_http）填入；author 模式恒为 `{}` | 每次 `robot.inspect` 后替换 |
| `run_status` | `Mapping[str, Any]`（含 `run_id_remote`、`current_command`、`completed_commands`、`failed_commands`、`used_tips`、`remaining_plan`） | run 模式由 `robot.inspect` / MCP `run_status` | 同上；与 `RuntimeState` 的 ledger 字段一一对应 |
| `latest_error` | `ErrorRef \| None`（含 `category`、`code`、`raw`、`parsed`、`source: Literal["validate","simulate","robot","tool"]`） | `package.validate` / `package.simulate` / `error.parse` / 工具异常 | 出错时写入，下一步成功后清空 |
| `loaded_skills` | `tuple[str, ...]` | `skill.search_load` 累加 | 每次 load 追加；run 起始为空 |
| `memory_hits` | `tuple[MemoryHit, ...]`（来自 `runtime/memory.py::MemoryHit`） | `memory.read_write`（search 子操作） | 每次查询替换 |
| `permissions` | `frozenset[str]` | 由 `mode` + CLI flag 推导（见 §6 mode 矩阵） | 入口确定，运行期不放宽 |
| `risks` | `tuple[RuntimeRisk, ...]`（复用 `runtime/state.py::RuntimeRisk`） | `package.validate`、`error.parse`、`robot.inspect` 检出 | 出现时追加，phase 切换时不清除 |
| `counters` | `Counters`（含 `tool_calls`、`skill_loads`、`simulator_calls`、`steps`、`input_tokens`、`output_tokens`、`total_tokens`） | `ToolRegistry.call_with_gating` 与模型客户端 | 每次工具调用 / 每次 LLM 响应后递增 |
| `trace_path` | `Path` | 入口指定 | 不变 |
| `trace` | `TraceWriter`（不进 `to_dict()`） | 入口构造 | 每次事件追加 |

字段映射到现有结构：

- `AuthoringTaskState.{run_id, task_id, phase, tool_calls, skill_loads, simulator_calls}` → `AgentState.{run_id, task_spec.task_id, phase, counters.*}`。
- `RuntimeState.{run_id, phase, robot, expected, committed, observed, completed_commands, failed_commands, used_tips, treated_wells, liquid_transfers, remaining_plan, risks}` → `AgentState.{run_id, phase, robot_status, run_status.*, risks}`，其中 `expected/committed/observed` 收编进 `run_status`，向后兼容字段名保留在 `to_dict()` 输出里。

`AgentState` 自身仍是 `@dataclass(frozen=True)`；演进方法保留语义 `with_phase`、`with_package`、`with_robot`、`with_error`、`with_counters`、`add_risk`、`with_package_ready`。

### 1.1 `phase` 并集（冻结，与代码对齐）

`AgentPhase` = `RuntimeState.VALID_PHASES` ∪ author 工作流相位，**单一** `frozenset`，禁止 §1 表与 §4 伪代码各写一套：

```text
# 来自 runtime/state.py::VALID_PHASES
preflight, simulating, ready, running, recovering, paused, completed, aborted
# author 工作流追加（不与 runtime 冲突）
drafting, validating
# 统一 loop 追加
failed   # 不可恢复的工具/契约错误；区别于 paused（可继续）
```

| mode | 典型 phase 迁移 |
|---|---|
| `author` | `drafting` →（`package.validate`）→ `validating` →（`package.simulate`）→ `simulating` → 成功时 **`package_ready=True`**，phase 可仍为 `simulating` 或 `drafting`（不强制 `completed`） |
| `run` | `preflight` →（包校验）→ `ready` / `paused` → `running` → `recovering` / `paused` / `completed` / `aborted` |

**成功语义（author）**：以 `package_ready=True` + `REQUIRED_PACKAGE_FILES` 齐全为准，**不**要求 `phase=="completed"`。`completed` 保留给 run 模式真机跑完。

**成功语义（run）**：`phase in {"completed"}` 或 CLI 显式 `abort` → `aborted`。

### 1.2 未来 `mode` 切换（P1 不做，文档先钉死）

若日后同 session `author → run`：`package`、`loaded_skills`、`counters`、`task_spec` **保留**；`robot_status` / `run_status` 在首次 `robot.inspect` 前可为空；`latest_error` 不清空除非用户 reset。P1 实现 `mode` 不可变即可。

### 1.3 `RuntimeState` / `AuthoringTaskState` 键名映射（P0 冻结）

`run_status` 使用**扁平键**，禁止 `run_status["ledger"]["treated_wells"]` 等嵌套。键名与现 `RuntimeState.to_dict()` 一致，便于 P2 `_project_to_runtime_state` 往返。

| `RuntimeState` 旧键 | `AgentState` 新位置 | 读写约定 |
|---|---|---|
| `run_id` | `run_id` | 顶层 |
| `phase` | `phase` | 顶层 |
| `schema_version` | `schema_version`（AgentState 用 `"1.0"`；投影回 RuntimeState 时用 `"0.1"`，见 §6.7） | 顶层 |
| `robot` | `robot_status` | **整 dict replace** |
| `expected` | `run_status["expected"]` | 扁平 |
| `committed` | `run_status["committed"]` | 扁平 |
| `observed` | `run_status["observed"]` | 扁平 |
| `completed_commands` | `run_status["completed_commands"]` | 扁平；patch 时整段 replace |
| `failed_commands` | `run_status["failed_commands"]` | 同上 |
| `used_tips` | `run_status["used_tips"]` | 同上 |
| `treated_wells` | `run_status["treated_wells"]` | 同上 |
| `liquid_transfers` | `run_status["liquid_transfers"]` | 同上 |
| `remaining_plan` | `run_status["remaining_plan"]` | 同上 |
| `risks` | `risks`（顶层） | **不进** `run_status` |

| `AuthoringTaskState` 旧键 | `AgentState` 新位置 |
|---|---|
| `task_id` | `task_spec.task_id` |
| `tool_calls` / `skill_loads` / `simulator_calls` | `counters.tool_calls` / `counters.skill_loads` / `counters.simulator_calls` |
| `notes` | 写入 trace `summary` payload；不进 `task_spec`（与现 `authoring_stats.json` 的 `notes` 一致） |
| `phase` | `phase`（成功不依赖此字段，见 §1.1） |

**`AgentState.to_dict()`（run 模式）向后兼容**：除 AgentState 自有字段外，应能拼出与 `RuntimeState.to_dict()` **同键** 的视图——`robot` 取自 `robot_status`；ledger 各键取自 `run_status[...]`；`risks` 仍在顶层。

---

## 2. ToolCall / ToolResult 数据结构

使用 `@dataclass(frozen=True)`（不引入 Pydantic 依赖；现有代码均为 dataclass 风格）。文件归宿：`src/labscriptai/agent/tools.py`（新建，本文档冻结前不写）。

```python
# 设计草案，仅作为规范，不要在文档冻结前落到 .py
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

ToolName = Literal[
    "package.read_write",
    "package.validate",
    "package.simulate",
    "robot.inspect",
    "run.control",
    "error.parse",
    "recovery.suggest",
    "skill.search_load",
    "memory.read_write",
    "protocol.search",
]

@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    arguments: Mapping[str, Any] = field(default_factory=dict)
    reason: str = ""             # run.control 必填；author 写包工具见 §6.5 豁免
    proposed_by: str = "model"   # model | system | human | recovery_branch
    call_id: str | None = None   # OpenAI tool_call_id 透传
    # 子动作：把现有 CandidateAction.action_type 收进 arguments["action_type"]
    # 例：ToolCall("run.control", {"action_type": "resume_run", "human_confirmed": True})

@dataclass(frozen=True)
class ToolResult:
    ok: bool
    name: ToolName
    content: Mapping[str, Any]                          # 工具具体载荷
    decision: "GatekeeperDecision | None" = None         # 被 gate 阻断时也会返回 ok=False + decision
    state_patch: Mapping[str, Any] = field(default_factory=dict)
    # 合法 patch 见 §2.1；例：{"phase": "validating", "package": PackageRef(...)}

    duration_ms: int | None = None   # handler 计时；simulate 等长耗时工具必填
    error: str | None = None         # ok=False 时人类可读摘要；细节仍在 content

    def to_dict(self) -> dict[str, Any]: ...
```

**Trace 为 canonical 审计记录**（`TraceEvent` 含 `timestamp`）；`ToolResult` 是单步快照。失败工具调用：

1. `event_type=candidate_tool_call`，payload=`call.to_dict()`（脱敏 args）
2. 若 gate 阻断：`event_type=gatekeeper_decision`，`actor=gatekeeper`，payload=`decision.to_dict()`；**不**执行 handler
3. 若执行失败或 gate 通过但 handler 异常：`event_type=tool_result`，payload=`{ok, name, error, content, duration_ms, decision?}`

`tokens` 不进 `ToolResult`：仍按现口径在 **每 LLM step** 累加 `state.counters`，由 `authoring_stats.json` / pilot `record` 汇总（§7.4）。

兼容现有代码：

- `authoring/tools/registry.py::ToolResult(ok, content)` 是 `ToolResult` 的子集，迁移时一一映射。
- `runtime/gatekeeper.py::GatekeeperDecision` 直接复用（不重新定义）。
- `runtime/actions.py::CandidateAction` 退化为 `run.control` 的 arguments schema（见 §6）。

### 2.1 `AgentState.apply(state_patch)` 语义（P0 冻结）

`state_patch` 为**唯一**合法的状态增量格式；10 个 tool handler 必须遵守，禁止各写各的点分路径。

1. **顶层 key** 必须是 `AgentState` 字段名：`phase`、`package_ready`、`package`、`robot_status`、`run_status`、`latest_error`、`loaded_skills`、`memory_hits`、`risks`、`counters` 等。**禁止**点分路径（无 `"package.last_validation"`）。
2. **嵌套 mapping**（`package`、`robot_status`、`run_status`、`latest_error`）：patch 值为**完整子对象** → `with_package` / `with_robot` / 等价方法 **整段 replace**。需要 partial 更新时，handler 先从 `state` 读出旧 dict，merge 后再 patch 完整子 dict。
3. **数组 / 元组**（`loaded_skills`、`risks`、`memory_hits`）：
   - **replace**：patch key = 字段名，值为新 `tuple` / `list`。
   - **append**：patch key = `{字段名}_append`（如 `loaded_skills_append`、`risks_append`），值为单项或列表；`apply` 内 `existing + tuple(patch[key])`。
4. **`counters`**：patch key = `"counters"` 时，值为 **delta dict**（仅数值键）；`apply` 调用 `with_counters(**delta)`。**禁止** absolute 覆盖整个 `Counters`。
5. **标量**：`phase`、`package_ready` 可直接顶层 patch。
6. **未知 key** → `ValueError`（防止拼写漂移）。

P1 实现：`agent/state.py::apply` + `tests/test_agent_state_apply.py`（表驱动 3–5 个样例）。

### 2.2 `ToolCall.from_model(raw)` — legacy 名映射（P0 冻结）

P1 唯一适配入口：`agent/tools/legacy_names.py::normalize_tool_call(raw) -> ToolCall`（名可改，语义不变）。

**Author 模式（OpenAI `function.name`）**

| model 暴露名 | 内部 `ToolCall.name` | `arguments` 补全 |
|---|---|---|
| `read_file` | `package.read_write` | `op="read"`；保留 `path` 等 |
| `write_file` | `package.read_write` | `op="write"`；保留 `path`、`content` |
| `str_replace` | `package.read_write` | `op="str_replace"`；保留 `path`、`old`、`new`、`replace_all` |
| `json_set` | `package.read_write` | `op="json_set"`；保留 `path`、`pointer`、`value`、`create_missing`、`reason` |
| `append_md` | `package.read_write` | `op="append_md"`；保留 `path`、`text`、`reason` |
| `validate_package` | `package.validate` | 原样（含 `simulation_pass`） |
| `run_simulate` | `package.simulate` | `{}` |
| `load_skill` | `skill.search_load` | `op="load"`；保留 `name` |
| `search_protocol_library` | `protocol.search` | 保留 `query` |

**已是内部 10 名之一**：直通，不二次映射。

**Run 模式（P2；离线 scripted provider）**

| 输入 | 内部 |
|---|---|
| `CandidateAction` / `action_type` 字段 | `ToolCall("run.control", {"action_type": <type>, **parameters})` |
| 若模型仍暴露旧 action 名（可选） | 同上，经 thin adapter |

P1 测试：`normalize_tool_call({"name": "write_file", "arguments": {"path": "protocol.py", ...}})` → 内部名与 `op`。

---

## 3. ToolRegistry 接口

```python
# 设计草案
from typing import Any, Callable, Mapping, Protocol

class ToolHandler(Protocol):
    name: ToolName
    def spec(self) -> dict[str, Any]: ...            # JSON Schema for LLM tool_choice
    def __call__(self, args: Mapping[str, Any], state: "AgentState") -> ToolResult: ...

class ToolRegistry:
    def register(self, handler: ToolHandler) -> None: ...
    def list_specs(self, *, mode: Literal["author","run"]) -> list[dict[str, Any]]:
        """LLM 可见工具子集（见 §0.1）。registry 内 10 个 handler 均已 register；
        过滤规则等价现 tool_profile + mode：
        - author：read_file/write_file/…、validate_package、run_simulate、load_skill、search_protocol_library（按 profile）
        - run：robot.inspect、error.parse、recovery.suggest、run.control、package 只读子集、memory、skill list
        模型调用未暴露名称 → gatekeeper blocked（非 unknown handler）。"""

    def call_with_gating(
        self,
        call: ToolCall,
        state: "AgentState",
        gatekeeper: "Gatekeeper",
    ) -> ToolResult:
        """统一入口：
        1. trace 记录 candidate (event_type='candidate_tool_call')
        2. gatekeeper.evaluate_tool_call(call, state) → decision
        3. 若 blocked/escalated：返回 ok=False 的 ToolResult，不执行；trace 'gatekeeper_decision'
        4. 否则执行 handler，捕获异常 → ToolResult(ok=False, content={'error': ...})
        5. trace tool_result，附 state_patch
        6. 不在此处 mutate state；返回给 loop 由其 apply
        """
```

注册顺序与归一：10 个标准 tool 在 `agent/tools/__init__.py` 集中注册；底层实现仍调用现有模块（见 §5）。`list_specs(mode=)` 返回的 schema 用于 OpenAI tool_choice，与现有 `_native_tool_specs` 同构。模型 `function.name` 经 §2.2 归一后再 `call_with_gating`。

### 3.1 `list_specs` 与 legacy 暴露名

- **对 LLM**：author 模式继续暴露 §2.2 左列 legacy 名（与 `_native_tool_specs` 一致），**不是**强制 `package.read_write{op:...}`。
- **对 registry**：10 个 handler 均已 `register`；`call_with_gating` 前统一 `normalize_tool_call`。

---

## 4. LabscriptAgentLoop.run() 伪代码

**驱动模型（Phase 1）**：turn-based ReAct；每 step 一次 `client.complete`。run 模式暂不订阅 robot event stream（§0.1）。P2 离线 runtime 可将 `CandidateProvider` 输出包装为单步 `ToolCall("run.control", ...)` 再进同一 loop。

### 4.1 终止条件（`done` 定义）

| 条件 | author | run |
|---|---|---|
| **成功退出** | `response["final"]` 且 `final.package_ready==True` 且三件套齐全 → `package_ready=True` | `phase=="completed"` 或显式成功 summary |
| **模型收尾** | 见上；若 `final` 但缺文件 → 不退出，注入 `package_incomplete` 用户消息（复现现 `AuthoringAgent` 334–350 行） | `_finalize` 写 summary |
| **步数上限** | `step >= max_steps` → 退出，`completed=False` | 同左 |
| **空响应** | 无 `tool_calls` 且无 `final` → 退出（复现现 agent 354–356 行） | 同左 |
| **gatekeeper** | author：blocked 通常继续下一步；run：`blocked`/`escalated` 可置 `paused`/`recovering` 并 break | 同左 |
| **用户中断** | SIGINT / CLI cancel → `phase=aborted`，`completed=False`，trace `summary` 仍写 | 同左 |
| **硬错误** | 不可恢复异常 → `phase=failed` | 同左 |

`LoopResult.completed` **不得**仅用 `phase=="completed"`（author 历史上不用该 phase 表示写完包）。

```python
# 设计草案；目标 ~30 行核心。
def run(self, state: AgentState) -> LoopResult:
    state = state.with_phase("drafting" if state.mode == "author" else "preflight")
    self.trace.append("state_update", state)
    completed = False

    for step in range(self.max_steps):
        messages = self.context.compose(state, self.system_prompt)
        response = self.client.complete(messages, self.registry.list_specs(mode=state.mode))

        if response.get("final"):
            if state.mode == "author":
                state, completed = self._finalize_author(state, response["final"])
                if completed:
                    break
                # 缺文件：注入 package_incomplete，继续 loop
                continue
            state, completed = self._finalize_run(state, response["final"])
            break

        calls = response.get("tool_calls") or []
        if not calls:
            break  # 空 tool_calls 退出

        for raw in calls:
            call = normalize_tool_call(raw)  # §2.2 legacy → 内部 ToolCall
            result = self.registry.call_with_gating(call, state, self.gatekeeper)
            state = state.apply(result.state_patch).with_counters(tool_calls=1)
            self._append_messages(messages, call, result)
            if state.mode == "run" and result.decision and result.decision.blocked:
                state = state.with_phase("paused"); break
            if state.mode == "run" and result.decision and result.decision.escalated:
                state = state.with_phase("recovering"); break

        if state.phase in {"aborted", "failed"}:
            break
        if state.mode == "run" and state.phase in {"paused", "completed"}:
            break

    if state.mode == "author":
        completed = state.package_ready and all(
            (state.package.dir / n).exists() for n in REQUIRED_PACKAGE_FILES
        )
    self._write_authoring_stats(state)  # 复现 write_stats_file + client tokens
    self.trace.append("summary", {"completed": completed, **state.to_dict()})
    return LoopResult(final_state=state, completed=completed)
```

`mode=="author"` 时 `_finalize_author`：仅当 `final.get("package_ready")` 且文件齐全时置 `package_ready=True`；**不**强制 `phase=completed`。`mode=="run"` 时 `_finalize_run` 只写 summary。

---

## 5. 10 个标准工具 → 现有实现映射

每个标准工具是 thin wrapper，**不重写**底层。映射表：

| 标准工具 | 子动作 / 参数 | 现有实现（文件 :: 符号） | 说明 |
|---|---|---|---|
| `package.read_write` | `op∈{read, write, str_replace, json_set, append_md}` | `src/labscriptai/authoring/tools/registry.py::AuthoringToolRegistry._read_file / _write_file / _str_replace / _json_set / _append_md` | 把 5 个细粒度 author 工具合并为一个工具的 5 个子动作；run 模式仅 `op=="read"` |
| `package.validate` | `simulation_pass: bool` | `src/labscriptai/benchmark/package_validator.py::validate_package` | 现有 `AuthoringToolRegistry._validate_package` 已是 wrapper，直接挪 |
| `package.simulate` | （无参） | `src/labscriptai/runtime/adapters/simulator.py::simulate_protocol_package` + `AuthoringToolRegistry._run_simulate`（subprocess `verify_protocol.py simulate`） | author 模式走 subprocess 版（被 90 题用），run 模式走 `simulate_protocol_package` 适配器 |
| `robot.inspect` | `source: {http, mcp}`, `run_id?` | `src/labscriptai/runtime/adapters/robot_http.py::RobotHttpReadOnlyAdapter`、`src/labscriptai/runtime/adapters/mcp.py::OpentronsMcpRuntimeAdapter.call_tool("get_run_status"/"get_robot_info")` | 只读；返回值进 `state.robot_status` / `state.run_status` |
| `run.control` | `action_type∈{pause_run, resume_run, abort_run, request_human_confirmation, mark_resource_unavailable, choose_alternative_source, propose_continuation_patch, validate_continuation_patch, execute_recovery_branch}` | `src/labscriptai/runtime/actions.py::CandidateAction` + `runtime/gatekeeper.py::evaluate_action` + `runtime/continuation.py::validate_continuation_patch` | CandidateAction 退化为本工具的 arguments；schema 完全保留 |
| `error.parse` | `raw_error: str`、可选 `run_id` | MCP `parse_error` 经 `OpentronsMcpRuntimeAdapter.call_tool("parse_error", ...)`；离线场景退化为 `recovery_shadow_benchmark` 内已有的 parser | 输出写入 `state.latest_error.parsed` |
| `recovery.suggest` | `error_ref` | MCP `suggest_recovery_action` via `OpentronsMcpRuntimeAdapter`；与 `src/labscriptai/runtime/recovery_shadow_benchmark.py::run_shadow_benchmark` 复用同一个 candidate normalization | 输出候选分支列表，不执行；执行走 `run.control{action_type=execute_recovery_branch}` |
| `skill.search_load` | `op∈{list, load}`, `name?` | `src/labscriptai/authoring/skills.py::SkillLoader.list_skills / get_content / get_catalog` | author 模式默认开放；run 模式默认 list-only |
| `memory.read_write` | `op∈{search, append}`, `query?/title?/body?/tags?` | `src/labscriptai/runtime/memory.py::search_memory / append_memory_note / remember_shadow_record` | 默认两模式都允许；`append` 在 author 模式需 `reason` |
| `protocol.search` | `query: str` | `AuthoringToolRegistry._search_protocol_library`（subprocess `skills/opentrons-protocol-library/scripts/search_protocols.py search`） | 已有；author 默认开，run 模式 `permissions` 默认包含（用于在恢复时找替代协议） |

> 现有 author 工具 `load_skill` 合入 `skill.search_load`；现有 `validate_package` / `run_simulate` 一一映射；现有 `read_file/write_file/str_replace/json_set/append_md` 合入 `package.read_write` 的子动作。

---

## 6. Gatekeeper 改造方案

### 6.1 现状

`runtime/gatekeeper.py::evaluate_action(action: CandidateAction, state: RuntimeState) -> GatekeeperDecision`：

- 仅在 `runtime/agent_loop.py` 与少量测试中被调用；判定 12 种 `action_type`（`SAFE_ACTION_TYPES`），加 `FORBIDDEN_ACTION_TYPES`。
- 依赖 `state.expected.autonomy_mode`、`state.phase`、`state.blocker_risks`、`state.has_robot_identity`、`continuation.validate_continuation_patch`。

### 6.2 演进到 `evaluate_tool_call(name, args, state)`

新签名：

```python
def evaluate_tool_call(call: ToolCall, state: AgentState) -> GatekeeperDecision: ...
```

实现策略 = **包住而非替换**。旧 `evaluate_action` 保留导出，新函数做 dispatch：

```python
def evaluate_tool_call(call, state):
    if call.name == "run.control":
        # 完全保留旧规则：把 args 转回 CandidateAction
        action = CandidateAction(
            action_type=call.arguments["action_type"],
            reason=call.reason,
            parameters={k:v for k,v in call.arguments.items() if k != "action_type"},
        )
        return evaluate_action(action, _project_to_runtime_state(state))
    # 其他 9 个工具：新规则（见 6.3 / 6.4）
    return _evaluate_non_runtime(call, state)
```

`_project_to_runtime_state(state)` 把 `AgentState` 映射回 `RuntimeState`（仅在 `run.control` dispatch 内使用）；完整键表见 **§6.7**。P1 实现时写在 `agent/gatekeeper.py`，与 `evaluate_tool_call` 同 PR。

**`reason` 校验分叉（避免误伤旧 approved 用例）**：

- `call.name == "run.control"` → **仅** `evaluate_action`（继承旧 reason 规则）；**不**走 §6.5 的 author 豁免逻辑。
- 其它工具 → `_evaluate_non_runtime`（含 §6.3 / §6.4 / §6.5 的 reason 与 mode 规则）。

### 6.3 author 模式规则（新增，规则更宽）

| 工具 | 规则 |
|---|---|
| `package.read_write` op=read | 允许；目标路径必须在 `state.package.dir` 之内 |
| `package.read_write` op∈{write,str_replace,json_set,append_md} | 允许；强制相对路径、禁止 `..`；`mode=="run"` 时阻断 |
| `package.validate` | 允许 |
| `package.simulate` | 允许；author 模式不强制 phase；记一次 `counters.simulator_calls` |
| `skill.search_load` | 允许；`skill_mode=="off"` 时阻断 load 子动作 |
| `protocol.search` | 允许；`query` 非空 |
| `memory.read_write` op=search | 允许 |
| `memory.read_write` op=append | author 模式默认 **阻断**（避免污染 KB）；可由 CLI flag `--allow-memory-write` 打开 |
| `robot.inspect` / `run.control` / `error.parse` / `recovery.suggest` | author 模式 **阻断**（`reason="not allowed in author mode"`），与 §1 `permissions` 一致 |

### 6.4 run 模式规则（新增，并完全继承旧 `evaluate_action`）

| 工具 | 规则 |
|---|---|
| `robot.inspect` | 允许；要求 `state.task_spec` 含 robot identity（或 args 提供 host），等价旧 `has_robot_identity` |
| `error.parse` | 允许；`args.raw_error` 非空 |
| `recovery.suggest` | 允许；只读 |
| `run.control` | **完全走旧 `evaluate_action`**（含 `FORBIDDEN_ACTION_TYPES`、`HARDWARE_MOVING_ACTION_TYPES`、`execute_recovery_branch` 的 5 个白名单分支、`human_confirmed` 升级） |
| `package.read_write` op=read | 允许 |
| `package.read_write` 写操作 | run 模式 **阻断** |
| `package.validate` / `package.simulate` | 允许（离线 sanity） |
| `skill.search_load` / `protocol.search` / `memory.read_write` op=search | 允许 |
| `memory.read_write` op=append | 允许（运行经验入库即此设计目的） |

### 6.5 公共规则（两模式都加）

- **`call.reason` 为空**：
  - **`run.control`**：blocked（继承旧 `evaluate_action`）。
  - **author 模式 `package.read_write` 写子动作**（`write_file` / `str_replace` / `json_set` / `append_md` 及内部 `op∈{write,str_replace,json_set,append_md}`）：**不阻断**——现 `AuthoringToolRegistry` 无 reason 要求；gatekeeper 在 dispatch 前若 `reason==""` 则填 `reason="authoring-edit"`（或沿用 `arguments.reason` / `why` 若模型提供）。
  - **author 其它允许工具**（`read_file`、`validate_package`、`run_simulate`、`load_skill`、`search_protocol_library`）：同样豁免或使用默认 reason。
  - **run 模式非 `run.control` 工具**：建议非空 reason，P1 可先填 `reason="runtime-read"` 默认值，避免改变 shadow benchmark 行为。
- 未在 registry 已注册工具集合内 → blocked（替代旧 `unknown action type`）。
- 任意工具触发异常 → 不视为 gatekeeper blocked，而是 `ToolResult(ok=False)`，phase 不变。
- `state.risks` 中存在 `severity=="blocker"` 时，所有 `run.control` 中的 `HARDWARE_MOVING_ACTION_TYPES` 子动作 blocked（与旧 `blocker_risks` 一致）。

> 满足约束 4：所有旧 `evaluate_action` 的 blocked/escalated 路径在新 dispatch 中等价保留；新增规则只让更多调用被 block，不放行任何旧版会拒绝的调用。

### 6.6 Gatekeeper 回归验收（P0 冻结命令，P1 执行）

```bash
# 1) 旧函数行为不变（11 个用例，含 trace writer）
pytest tests/test_runtime_gatekeeper.py -q

# 2) P1 新增：dispatch 与旧 decision 一致
pytest tests/test_agent_gatekeeper_dispatch.py -q
```

`tests/test_agent_gatekeeper_dispatch.py`（P1 新建）要求：对 `test_runtime_gatekeeper.py` 中每个涉及 `evaluate_action` 的用例，构造等价 `ToolCall("run.control", {action_type, ...})` + `AgentState(mode="run", ...)`，经 `evaluate_tool_call` 后 `status` / `approved` / `blocked` / `escalated` 与旧 `GatekeeperDecision` **一致**。

**author 模式新增规则**（reason 豁免、`robot.inspect` 阻断等）在**独立** test class 中测，不得改变 `run.control` 矩阵。

### 6.7 `_project_to_runtime_state`（P1 实现，与 §1.3 对齐）

| `AgentState` | `RuntimeState` |
|---|---|
| `run_id` | `run_id` |
| `phase` | `phase` |
| `robot_status` | `robot` |
| `run_status["expected"]` | `expected` |
| `run_status["committed"]` | `committed` |
| `run_status["observed"]` | `observed` |
| `run_status["completed_commands"]` | `completed_commands` |
| `run_status["failed_commands"]` | `failed_commands` |
| `run_status["used_tips"]` | `used_tips` |
| `run_status["treated_wells"]` | `treated_wells` |
| `run_status["liquid_transfers"]` | `liquid_transfers` |
| `run_status["remaining_plan"]` | `remaining_plan` |
| `risks` | `risks` |
| `autonomy_mode`（顶层或 `task_spec` 旁字段，见 §9.3） | `expected["autonomy_mode"]`（与现 `test_auto_mode_*` 一致） |

author 模式通常不调用 `_project_to_runtime_state`；仅 `run.control` → `evaluate_action` 路径需要。

---

## 7. Benchmark 兼容性方案

### 7.1 `run_to_files(task) -> dict[str, str]` 契约

`authoring_pilot.py` 现行只关心一件事：传入 `package_author: Callable[[AuthoringTask], dict[str, str]]`，返回包含 `REQUIRED_PACKAGE_FILES` + 可选 `authoring_stats.json` + 可选 `trace.jsonl` 的字典。

新 loop 的 thin facade（设计草案，落地后位置：`src/labscriptai/agent/facade.py`）：

```python
class UnifiedAuthoringFacade:
    def __init__(self, *, client, skill_mode, tool_profile, max_steps, ...): ...

    def run_to_files(self, *, task: AuthoringTask, work_dir: Path, **kwargs) -> dict[str, str]:
        state = AgentState.for_author(task=task, package_dir=work_dir/"package",
                                      trace_path=work_dir/"trace.jsonl",
                                      permissions=_author_perms(skill_mode, tool_profile))
        loop = LabscriptAgentLoop(client=self.client, registry=_build_registry(...),
                                  gatekeeper=Gatekeeper(), max_steps=self.max_steps)
        result = loop.run(state)
        _write_missing_metadata_files(state.package.dir, task)  # 复用现有 helper
        files = {name: (state.package.dir / name).read_text("utf-8")
                 for name in REQUIRED_PACKAGE_FILES}
        if (state.package.dir / "authoring_stats.json").exists():
            files["authoring_stats.json"] = (state.package.dir / "authoring_stats.json").read_text("utf-8")
        if state.trace_path.exists():
            files["trace.jsonl"] = state.trace_path.read_text("utf-8")
        return files
```

签名与现 `AuthoringAgent.run_to_files`（`authoring/agent.py:413`）完全一致 → `authoring_pilot.py` 的 `def author(task):` 闭包替换成本 facade 即可。

### 7.2 `--provider labscriptai-unified`

在 `authoring_pilot.py::main` 仅加 **一个** choice：

```python
parser.add_argument("--provider",
    choices=("offline", "deepseek", "labscriptai-authoring", "labscriptai-unified"),
    default="offline")
```

新增分支位置紧邻现有 `elif args.provider == "labscriptai-authoring":`，复用同一组 flag（`--agent-max-steps`、`--authoring-skill-mode`、`--tool-profile`、`--scaffold-label`）。

```python
elif args.provider == "labscriptai-unified":
    config = OpenAICompatibleConfig.from_env(default_model="deepseek-v4-pro")
    model_id = config.model
    protocol_repairer = lambda task, protocol_py, sim: call_protocol_repair(config, task, protocol_py=protocol_py, simulation_result=sim)
    def author(task):
        with tempfile.TemporaryDirectory() as tmp:
            facade = UnifiedAuthoringFacade(
                client=OpenAICompatibleAuthoringClient(config),
                max_steps=args.agent_max_steps,
                skill_mode=args.authoring_skill_mode,
                tool_profile=args.tool_profile,
            )
            return facade.run_to_files(task=task, work_dir=Path(tmp),
                opentrons_python=args.opentrons_python,
                workspace_root=args.workspace_root,
                simulation_timeout_sec=args.simulation_timeout_sec)
```

`run_authoring_pilot()`、`_write_summary()`、`_write_record()`、`stamp_manifest()`、`call_protocol_repair`、`scaffold_label` 全部不动 → 满足约束 1/3。

### 7.3 summary.json 新增字段（仅追加，可省略）

只在 `--provider labscriptai-unified` 下额外写：

- `unified_run.mode_distribution: {"author": N}`（为 run 模式留位）
- `unified_run.gatekeeper_block_count: int`
- `unified_run.gatekeeper_escalate_count: int`

旧 reader 不读这些字段不影响；不修改现有字段定义。

### 7.4 per-task `record` 与 `trace.jsonl` 映射（benchmark 不变）

`analyze_authoring_run.py` **不解析** trace 内容，只检查 `package_dir/trace.jsonl` 是否存在。定量指标全部来自 **`summary.json` → `records[]`**，由 `authoring_pilot.run_authoring_pilot` 组装；unified provider 必须保持同一路径。

| `record` / `summary` 字段 | 来源（unified） | 保留/新增 |
|---|---|---|
| `tool_calls` | `package/authoring_stats.json` ← `state.counters.tool_calls` | **保留** |
| `skill_loads` | 同上 | **保留** |
| `simulator_calls` | stats + pilot 对 `first_simulation` / repair 的 +1 逻辑（与现 provider 相同） | **保留** |
| `input_tokens` / `output_tokens` / `total_tokens` | OpenAI client 累计 + repair 分支 | **保留** |
| `authoring_*_tokens` / `repair_*_tokens` | 同现 pilot 拆分 | **保留** |
| `validation` / `first_pass_validation` / `simulation` / `first_simulation` | pilot 在 `run_to_files` **之后** 仍跑 `validate_package` / `simulate_protocol_file` | **保留**（facade 不替代 pilot 后处理） |
| `trace_status` | `trace.jsonl` 文件是否存在 | **保留** |
| `scaffold_label` / `task_id` / `difficulty` / … | pilot 不变 | **保留** |
| `gatekeeper_block_count` 等 | 仅 `summary.json` 顶层 `unified_run.*`（§7.3） | **新增**，不进 record |

`authoring_stats.json` 字段与现 `AuthoringTaskState.to_dict()` + client tokens 一致：`run_id`, `task_id`, `phase`, `tool_calls`, `skill_loads`, `simulator_calls`, `notes`, `input_tokens`, `output_tokens`, `total_tokens`。P1 可选追加 `package_ready`（旧 reader 忽略未知键）。

### 7.5 `TraceEvent` 类型扩展（实现时注意）

落地时扩展 `runtime/trace.py::TRACE_EVENT_TYPES`：

```python
TRACE_EVENT_TYPES = frozenset({
    # 现有
    "observation", "state_update", "memory_retrieval",
    "candidate_action",  # 保留；run 离线 shadow 仍可用
    "gatekeeper_decision", "tool_call", "tool_result",
    "recovery", "escalation", "summary",
    # 新增（unified loop）
    "candidate_tool_call",
})
```

| `event_type` | `actor` | 何时写 | 与 benchmark 关系 |
|---|---|---|---|
| `candidate_tool_call` | `model` | 每步模型提议工具 | 仅审计；analyze 不读 |
| `gatekeeper_decision` | `gatekeeper` | 每次 `evaluate_tool_call` | 仅审计；可聚合到 `unified_run.*` |
| `tool_call` / `tool_result` | `tool` | 执行前后 | author 现已有；unified 补 gate 失败时的 result |

author 路径在 P1 起会**多出** `gatekeeper_decision` 行；`review_authoring_run.py` 若不解析则无需改。

### 7.6 并发与可重入（P1 约定）

| 组件 | 约定 |
|---|---|
| `LabscriptAgentLoop` | **非 thread-safe**；每个 task / CLI session `new` 一个实例 |
| `UnifiedAuthoringFacade` | **无状态或每次 `run_to_files` 新建** loop + registry + `AgentState`；不在 facade 字段上缓存跨 task 的 loop |
| `ToolRegistry` | 每 loop 一个；handler 不持有跨 call 可变状态（计数在 `AgentState.counters`，不在 registry） |
| `AuthoringToolRegistry` 委托 | 每 run 一个带 `package_dir` 的 context；**禁止**跨 task 共享同一 registry 实例（现 `AuthoringToolRegistry.state` 可变） |
| `SkillLoader` | 只读 MD；进程内可共享同一 `SkillLoader` 实例 |
| `TraceWriter` | 每 run 独立 `trace_path`；**不支持**多线程写同一 path |
| `authoring_pilot` | 现 **`for task` 串行**（`run_authoring_pilot`）；多进程 shard（`scripts/run_*_parallel.sh`）= 多进程各写独立 `output_dir`，与上表兼容 |

**Issue（P1 立项，不阻塞开工）**：若未来 `authoring_pilot` 增加 in-process `--max-workers`，需每 worker 独立 facade/registry，或实现 registry 锁。标题建议：`agent: thread-safety if pilot gains --max-workers`。

---

## 8. 退役计划

并存 → 接管 → 退役，三阶段。冻结本文档后启动 P1。

### P0：本文档冻结（当前阶段）

- 输出物：仅 `docs/architecture/agent_architecture.md` 与 review 意见。
- 不写任何 `.py`。

### P1：新建 skeleton，**与旧实现并存**

- 新文件：`src/labscriptai/agent/{__init__.py, state.py, tools.py, registry.py, gatekeeper.py, loop.py, facade.py}`。
- `agent/gatekeeper.py` 仅 dispatch；`run.control` 路径调用 `runtime/gatekeeper.evaluate_action`（原文件不动）。
- `agent/tools/*.py` 全部 thin wrapper：
  - `package_read_write.py` → 调用 `AuthoringToolRegistry` 的内部方法（先以委托而非复制实现）。
  - `package_validate.py` → 调用 `benchmark/package_validator.validate_package`。
  - `package_simulate.py` → 调用 `runtime/adapters/simulator.simulate_protocol_package` 或 subprocess（与 author 一致）。
  - 其余同 §5。
- `--provider labscriptai-unified` 上线；同时 `--provider labscriptai-authoring` **不变**。
- 通过条件：两 provider 在 holdout 6 题上 `summary.json` 字段一致，且 unified 的 `simulation_pass_count / first_pass_validator_pass_count` 不差于 authoring（容差 0）。
- Gatekeeper：§6.6 两条 pytest 全绿。

### P2：runtime offline loop 切换底盘

- `runtime/cli.py` 中 `run_offline_loop` 的调用方改为 `LabscriptAgentLoop`（`mode="run"`）。
- `runtime/agent_loop.py::run_offline_loop` 保留为 thin wrapper（内部调用新 loop），签名不变 → 不破坏 `tests/test_agent_loop.py` 与 `runtime/recovery_shadow_benchmark.py`、`runtime/smoke_benchmark.py`、`runtime/scenario_benchmark.py`。
- `runtime/gatekeeper.evaluate_action` 标 `@deprecated`，但实现保留；新代码统一调 `agent.gatekeeper.evaluate_tool_call`。

### P3：authoring loop 切换底盘

- `authoring/agent.py::AuthoringAgent.run` / `run_to_files` 保留签名，内部改成 `UnifiedAuthoringFacade.run(...)` 的薄包装。
- `AuthoringToolRegistry` 标 `@deprecated`；其方法被 `agent/tools/package_*` 直接 import 调用，仍可用。
- 通过条件：90 题 freeze 重跑，`summary.json` 关键指标（`simulation_pass_count`、`first_pass_simulation_pass_count`、`validator_ok_count`、`first_pass_validator_pass_count`、`tool_calls`、`skill_loads`、`simulator_calls`、tokens）与上次 freeze 偏差 ≤ 误差带（具体阈值在 `paper_execution_plan.md` 中冻结）。

### P4：删除旧实现

发生在 P3 通过 + 一次 paper-grade freeze 之后：

- 删 `src/labscriptai/authoring/agent.py::AuthoringAgent` 类体，仅保留 `from labscriptai.agent.facade import UnifiedAuthoringFacade as AuthoringAgent` 兼容别名（一直保留到论文 camera-ready）。
- 删 `src/labscriptai/runtime/agent_loop.py::run_offline_loop` 的旧实现，保留同名 thin wrapper。
- 删 `authoring/tools/registry.py::AuthoringToolRegistry`（已经由 `agent/tools/*` 取代）；保留 `_json_pointer_set` 等纯函数到 `agent/tools/_jsonptr.py`。
- 删 `runtime/actions.py::CandidateAction`？**不删**：它现在是 `run.control` 的 arguments 模型，被新 gatekeeper dispatch 内部使用。

### P5：清理文档

- 论文 Figure 1、`runtime_build_plan.md`、`permission_matrix.md` 改用「一个 loop + 十个工具 + 两个模式」叙述；canonical path 为 `docs/architecture/agent_architecture.md`（`docs/agent_unification.md` 为 stub 重定向）。

---

## 9. 风险与未决事项

1. **`package.simulate` 双实现**：author 走 subprocess（`verify_protocol.py`），run 走 `simulate_protocol_package`。P1 先维持双路径，P3 决定是否统一。
2. **MCP 适配器**：`error.parse` / `recovery.suggest` 当前由 MCP 提供；若 MCP 不可用需要降级。`runtime/recovery_shadow_benchmark.py` 已有 normalize 逻辑可作为离线后备。
3. **`autonomy_mode`**：旧 `state.expected.autonomy_mode` 影响 `resume_run`、`execute_recovery_branch`。`AgentState` 中存放位置 = `task_spec.budget` 同级新字段 `autonomy_mode: Literal["conservative","auto"]="conservative"`；不放进 `permissions` 以免与权限位混淆。
4. **trace schema**：见 §7.5；P1 扩展 `TRACE_EVENT_TYPES` 后加入 `candidate_tool_call`。
5. **`tool_profile` 与 `permissions`**：`tool_profile∈{edit,simulate,kb}` 用于 ablation；映射到 `permissions` 子集（edit=`package.read_write`；simulate 加 `package.{validate,simulate}`；kb 再加 `skill.search_load`、`protocol.search`、`memory.read_write@search`）。memory append 在 author 默认关闭，与现状一致。
6. **runtime 双驱动**：P2 前 `run_offline_loop` 仍用 `CandidateProvider`；接入 unified loop 时需文档化「scripted action → `ToolCall("run.control", ...)`」适配层（§4 首段）。
7. **并发**：见 §7.6；P1 不实现 in-process 并行。

---

## 10. 评审清单（合并前必答）

- [x] §1 + §1.1：`phase` 并集含 `preflight` 与 `drafting`；`package_ready` 作为 author 成功主标志。
- [x] §1.3：`RuntimeState` / `AuthoringTaskState` 扁平键名映射（含 `treated_wells`、`liquid_transfers` → `run_status[...]`）。
- [x] §2.1：`AgentState.apply(state_patch)` 语义（无点分路径、`_append`、counters delta）。
- [x] §2.2：`from_model` / `normalize_tool_call` legacy 映射表。
- [x] §4.1 + §4 伪代码：`LoopResult.completed` 对齐 `package_ready` + 文件齐全，不单靠 `phase==completed`。
- [x] §0.1：`mode` = LLM `list_specs` 过滤 + gatekeeper 双轨（已写明，非纯 hint）。
- [x] §6.5 + §6.2：`reason` 校验分叉；author 写包豁免；`run.control` 仅走 `evaluate_action`。
- [x] §6.6 / §6.7：gatekeeper 回归验收命令；`_project_to_runtime_state` 表。
- [x] §7.4 / §7.5 / §7.6：record 映射、trace 扩展、并发约定。
- [ ] §7.2 unified provider 是否能复用 `protocol_repairer` 闭包？（应：是；P1 实现时确认。）
- [ ] P2 切换是否会破坏 `tests/test_agent_loop.py` 现有断言？（P2 前验证。）
- [x] §0.1 / §2.2 / §3.1：LLM 继续暴露 legacy author 工具名，registry 内部归一。

---

文档结束。冻结评审通过后，按 P1 开工，先落 `agent/state.py`（含 `apply`）、`agent/tools/legacy_names.py`、`agent/gatekeeper.py`，再 `loop.py` / `facade.py`。

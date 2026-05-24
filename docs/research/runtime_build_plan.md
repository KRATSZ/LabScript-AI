# LabscriptAI Agent Build Plan

本文档取代旧的“双 loop”开工口径。新的主线更简单：

```text
LabscriptAI Agent = 一个 loop + gatekeeper + 10 个工具 + Skill library + 一个 memory store
```

对外使用形式也要简单：用户在命令行里直接对话，体验接近 Claude Code；区别是底层工具、状态、门控和记忆都围绕 Opentrons / 液体处理协议设计。

## 1. 核心简化

不要再把“编写协议”和“运行恢复”讲成两个独立 agent。它们只是同一个 agent 的两个状态：

| 状态 | 用户在做什么 | Agent 主要调用什么 |
| --- | --- | --- |
| `author` | 从自然语言写出协议包 | package 读写、skill、protocol 搜索、validate、simulate |
| `run` | 看真机状态、解释报错、建议恢复 | robot inspect、error parse、recovery suggest、run control、memory |

统一 loop：

```text
while true:
  1. observe：读取当前任务、文件、机器人状态或错误
  2. load：按需加载 skill / memory
  3. think：LLM 只提出下一步 tool call
  4. gatekeeper：检查这个 tool call 是否允许
  5. execute：执行被批准的工具
  6. trace：写日志，更新状态
  7. stop / wait / continue
```

关键边界：模型可以“想”和“提建议”，但不能绕过 gatekeeper 直接动硬件。

## 2. 十个稳定工具

这十个名字是产品和论文都能复用的接口。底层可以先包住现有代码，后续再清理实现。

| Tool | 用途 | 当前可复用代码 | 状态 |
| --- | --- | --- | --- |
| `package.read_write` | 读写 `protocol.py`、`setup_card.html`、`manifest.json` | `src/labscriptai/authoring/agent.py`、`authoring/tools/registry.py` | 已有，需统一成标准 tool |
| `package.validate` | 检查协议包字段、schema、语义 | `src/labscriptai/benchmark/package_validator.py`、`benchmark/validators/` | 已有，需接进统一 loop |
| `package.simulate` | 跑 Opentrons analyze/simulate | `skills/opentrons-protocol-verify/scripts/verify_protocol.py`、`runtime/adapters/simulator.py` | 已有基础 |
| `robot.inspect` | 只读读取机器人状态 | `runtime/adapters/robot_http.py`、`runtime/adapters/mcp.py` | 已有只读基础 |
| `run.control` | pause / resume / cancel 等受控动作 | MCP run control、`runtime/actions.py` | 需严格 gate；默认不开放 start/play |
| `error.parse` | 把错误日志变成结构化原因 | MCP `parse_error`、现有 error-response 规则 | 需统一 wrapper |
| `recovery.suggest` | 生成恢复候选方案 | `runtime/recovery_shadow_benchmark.py`、MCP suggest recovery | shadow 已有，执行未默认开 |
| `skill.search_load` | 查找并加载 skill | `src/labscriptai/authoring/skills.py`、`skills/*/SKILL.md` | 已有，需统一入口 |
| `memory.read_write` | 读写经验案例 | `src/labscriptai/runtime/memory.py` | MVP 已有 |
| `protocol.search` | 搜索现有 protocol 模板 | `skills/opentrons-protocol-library/scripts/search_protocols.py` | 已有，需作为工具暴露 |

## 3. 目标代码形态

目标不是推翻现有代码，而是把分散能力收口到一个小核心：

```text
src/labscriptai/
  agent/
    loop.py          # LabscriptAgentLoop：唯一主 loop
    state.py         # AgentState：author/run、任务、文件、robot、memory、trace
    tools.py         # ToolCall / ToolResult / ToolRegistry
    gatekeeper.py    # 统一权限检查，复用 runtime gatekeeper 规则
  authoring/         # 继续保留，作为 author 状态的工具实现来源
  runtime/           # 继续保留，作为 run 状态的工具实现来源
```

短期可以不急着移动文件。第一步先在文档和 status page 里统一口径；第二步再新建 `agent/` 小核心，把现有 authoring/runtime 能力逐个包进去。

## 4. AgentState 草案

`AgentState` 要少而清楚，避免为了“架构感”塞太多字段：

```text
mode: author | run
task: 当前用户目标
package_path: 当前协议包路径
robot: 机器人只读状态，run 模式才需要
last_error: 最近一次错误，可能来自 validate/simulate/robot
loaded_skills: 当前加载了哪些 skill
memory_hits: 找到哪些相关经验
permissions: 当前允许的工具权限
trace_path: 本轮日志写到哪里
```

## 5. 命令行使用形态

建议最终产品长这样：

```bash
labscriptai
labscriptai author
labscriptai run --package runs/current/package --robot 192.168.66.103:31950
```

交互例子：

```text
user> 帮我写一个 96 孔板 serial dilution protocol
agent> 我先加载移液和稀释相关 skill，然后生成三件套并跑 validate/simulate。

user> 现在机器人报错说缺吸头，看看怎么处理
agent> 我会先只读检查 robot 状态和 run error，再给恢复建议。需要动硬件的步骤会被 gatekeeper 拦住并请求确认。
```

TUI 可以继续存在，但它只是这个 loop 的前端，不应该再拥有另一套流程。

## 6. 当前进展与缺口

| 区域 | 现在到哪了 | 下一步 |
| --- | --- | --- |
| 协议编写 | `authoring/`、三件套、validate/simulate、90 题 freeze 都已有 | 把 authoring 工具包装成 `package.*`、`skill.*`、`protocol.search` |
| 运行观察 | `robot_http.py`、`mcp.py` 已有只读基础 | 统一成 `robot.inspect`，写同一份 trace |
| 恢复建议 | shadow benchmark 和 memory MVP 已有 | 统一成 `error.parse` + `recovery.suggest`；P4 执行继续默认关闭 |
| gatekeeper | runtime 侧已有 | 上移成所有 tool call 都必须经过的统一门 |
| CLI/TUI | runtime CLI/TUI 已有 | 改成调用统一 `LabscriptAgentLoop` |
| 论文 Figure 1 | 旧口径是双 loop | 改成一个 Agent，两个状态，十个工具 |

## 7. 开工顺序

| 顺序 | 交付 | 说明 |
| --- | --- | --- |
| 1 | `ToolCall` / `ToolResult` / `ToolRegistry` | 先把十个工具名字定死 |
| 2 | `AgentState` | 只保留 author/run 需要的共同字段 |
| 3 | `LabscriptAgentLoop` | 一个 `while true`，每步都过 gatekeeper |
| 4 | author 工具 wrapper | 包住 package read/write、validate、simulate、skill、protocol search |
| 5 | run 工具 wrapper | 包住 robot inspect、error parse、recovery suggest、run control、memory |
| 6 | CLI/TUI 接入 | 用户看到的是命令行对话，不是两个独立系统 |
| 7 | trace 汇总 | status page 和论文 Figure 1 都能从 trace 解释“做了什么、为什么被允许” |

## 8. 安全边界

权限矩阵仍以 [`permission_matrix.md`](permission_matrix.md) 为准。简化后的说法是：

- 默认允许：读写文件、validate、simulate、读 robot 状态、读写 memory。
- 需要 gatekeeper：pause/resume/cancel、恢复候选转执行。
- 默认禁止：模型直接 aspirate、dispense、move、pick up tip、start/play run。

## 9. 论文口径

Figure 1 应画成：

```text
User CLI / TUI
  -> LabscriptAI Agent
      -> mode: author / run
      -> gatekeeper
      -> 10 tools
      -> skill library
      -> memory store
      -> trace
```

Table 1 仍然回答“它和普通 LLM / coding agent / 官方工具有什么区别”。但代码主线不再说“两个 loop”，而是说：普通 coding agent 是通用写代码；LabscriptAI 是带实验工具、状态、门控和经验库的液体处理 agent。

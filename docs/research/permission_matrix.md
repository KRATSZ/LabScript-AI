# Permission Matrix

本文档把模型权限 P0-P5、十个稳定工具、当前实现状态对齐。它是论文/benchmark 口径，不替代 `docs/rules/` 的安全规则。

核心原则：模型可以看更多、想更多、提出候选动作；但不能绕过确定性 gatekeeper 直接移动硬件。

## P0-P5 权限表

| Level | 模型可做 | 例子 | 当前实现状态（2026-05-21） | Gate / 备注 |
| --- | --- | --- | --- | --- |
| P0 | 生成/修改 protocol package | v0.4 三件套：`protocol.py`、`setup_card.html`、`manifest.json` | 已实现：`authoring/` + `authoring_pilot` | 产物必须过 package validator；manifest 记录模型、prompt hash、retry、工具权限 |
| P1 | 调 simulator / validator / 解释错误 | `simulate_protocol`、package validation、PRE 元数据修复 | 已实现：authoring pilot、package validator、runtime simulator adapter | 所有调用计入预算；影响 Table 1 / S1 |
| P2 | 读真机状态，不移动 | robot health、run history、module status、camera/deck image、`parse_error` | 已实现：`robot_http.py`；MCP read-only via `mcp.py` | 只读；写入统一 trace；不自动恢复 |
| P3 | 提出恢复候选 | 标记缺吸头、选择备用 source、请求人工确认、暂停 | 离线 scenario + **shadow benchmark 已实现** | candidate action；必须经过 gatekeeper |
| P4 | 执行白名单恢复 | 未来 missing-tip 低风险恢复、受控 `execute_protocol_recovery` | **未默认接通** | shadow + gatekeeper + MCP contract 通过后才试点 |
| P5 | 直接硬件控制 | `aspirate`、`dispense`、`move_pipette`、`pick_up_tip`、`drop_tip`、`start_run` / `play_run` | 禁止 | 模型永远不能直接执行；必须由已验证 protocol 或人工确认后的安全流程触发 |

## 十个工具权限对照

新的代码主线是一个 agent loop，下面十个工具是稳定接口。模型只提出 tool call；是否执行由 gatekeeper 决定。

| Tool | 做什么 | 权限层 | 当前口径 |
| --- | --- | --- | --- |
| `package.read_write` | 读写三件套协议包 | P0 | 已有 authoring 基础；写入后仍需 validator |
| `package.validate` | schema / package / semantic 检查 | P1 | 已接 authoring pilot 与 package validator |
| `package.simulate` | Opentrons analyze / simulate | P1 | 已有 verify wrapper 与 simulator adapter |
| `robot.inspect` | 读 robot health、run history、module status、错误状态 | P2 | 已有 `robot_http.py` 与 MCP read-only 基础；只读 |
| `run.control` | pause / resume / cancel 等运行控制 | P3-P4 | 必须 gated；`start_run` / `play_run` 不给模型直接调用 |
| `error.parse` | 把错误日志结构化 | P2-P3 | 读日志、解释错误；不能直接恢复 |
| `recovery.suggest` | 给恢复候选方案 | P3 | shadow benchmark 已有；执行恢复未默认开放 |
| `skill.search_load` | 查找并加载 skill 文档 | P0-P1 | 允许；计入 manifest / trace |
| `memory.read_write` | 读写经验案例 | P0-P3 | 允许读写经验；memory 不能绕过 gatekeeper 触发硬件动作 |
| `protocol.search` | 搜索现有 protocol 模板 | P0-P1 | 允许；主要用于 author 模式 |

## 禁止动作

| Action | 权限层 | 当前口径 |
| --- | --- | --- |
| `start_run`, `play_run` | P5 | 禁止模型直接执行；必须走人工确认或已验证 live path |
| `move_labware`, `move_pipette` | P5 | 禁止模型直接执行 |
| `pick_up_tip`, `aspirate`, `dispense`, `drop_tip` | P5 | 禁止模型直接执行；只能由已验证 protocol 或受控恢复流程间接触发 |
| `run_shell_command` | P5 | 不作为实验 agent 工具暴露 |

## Benchmark 影响

| 改动 | 影响哪张表 | 需要重跑什么 |
| --- | --- | --- |
| 改 agent loop 的提示、工具、轮次、skill 披露 | Table 1、S1 | 90 题 baseline matrix；冻结 prompt hash、retry budget、tool permissions |
| 接入 P2 read-only robot adapter | ExtFig / `runtime_cases.csv` | runtime manifest；不影响 90 题 S1 分数 |
| 开放 P4 controlled recovery | ExtFig / Fig1 runtime 段 | paired case、shadow benchmark、权限矩阵状态 |
| 加 LabFlow IR / PyLabRobot sanity | S2B | 只跑补充材料；不改变 authoring 主路径 |

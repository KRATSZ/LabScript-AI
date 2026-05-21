# Permission Matrix

本文档把模型权限 P0-P5、runtime action、当前实现状态对齐。它是论文/benchmark 口径，不替代 `docs/rules/` 的安全规则。

核心原则：模型可以看更多、想更多、提出候选动作；但不能绕过确定性 gatekeeper 直接移动硬件。

## P0-P5 权限表

| Level | 模型可做 | 例子 | 当前实现状态（2026-05-18） | Gate / 备注 |
| --- | --- | --- | --- | --- |
| P0 | 生成/修改 protocol package | 写 `protocol.py`、`deck_plan.json`、`runbook.md`、`manifest.json` | 部分已实现：`authoring/` + `authoring_pilot` | 产物必须过 package validator；manifest 记录模型、prompt hash、retry、工具权限 |
| P1 | 调 simulator / validator / 解释错误 | `simulate_protocol`、package validation、PRE 元数据修复 | 已实现：authoring pilot、package validator、runtime simulator adapter | 所有调用计入预算；影响 90 题 authoring 主表 |
| P2 | 读真机状态，不移动 | robot health、run history、module status、camera/deck image、`parse_error` | 计划中：`inspect_robot_state` / `capture_deck_image` action 枚举已存在，但缺 `runtime/adapters/robot_http.py` | 只读；写入统一 trace；不自动恢复 |
| P3 | 提出恢复候选 | 标记缺吸头、选择备用 source、请求人工确认、暂停 | 离线已实现：`scenario_benchmark` 的 6 个异常场景；live shadow 未实现 | 只是 candidate action；必须经过 gatekeeper |
| P4 | 执行白名单恢复 | 未来可能的 missing-tip 低风险恢复、受控 `execute_protocol_recovery` 分支 | 未接通：MCP/JS 侧有恢复函数，Python loop 还未受控调用 | 只有 P2/P3 稳定、shadow benchmark 通过、gatekeeper + MCP contract 双重通过后才开放 |
| P5 | 直接硬件控制 | `aspirate`、`dispense`、`move_pipette`、`pick_up_tip`、`drop_tip`、`start_run` / `play_run` | 禁止 | 模型永远不能直接执行；必须由已验证 protocol 或人工确认后的安全流程触发 |

## Runtime action 对照

| Action set | Actions | 权限层 | 当前口径 |
| --- | --- | --- | --- |
| Safe candidate actions | `simulate_protocol`, `inspect_robot_state`, `capture_deck_image`, `mark_resource_unavailable`, `choose_alternative_source`, `request_human_confirmation`, `pause_run`, `resume_run`, `abort_run` | P1-P4 | 可作为候选动作；是否执行取决于 gatekeeper 和 adapter 是否存在 |
| Read-only actions | `simulate_protocol`, `inspect_robot_state`, `capture_deck_image` | P1-P2 | simulator 已接；真机 read-only adapter 未接 |
| Recovery/planning actions | `mark_resource_unavailable`, `choose_alternative_source`, `request_human_confirmation`, `pause_run` | P3 | 离线 scenario 可评估；live 只做 shadow 后再考虑执行 |
| High-risk / forbidden actions | `start_run`, `play_run`, `move_labware`, `move_pipette`, `pick_up_tip`, `aspirate`, `dispense`, `drop_tip`, `run_shell_command` | P5 | 禁止模型直接执行 |

## Benchmark 影响

| 改动 | 影响哪张表 | 需要重跑什么 |
| --- | --- | --- |
| 改 authoring loop 的提示、工具、轮次、skill 披露 | 主表 authoring、S2、S3 | 90 题 baseline matrix；至少冻结 prompt hash、retry budget、tool permissions |
| 接入 P2 read-only robot adapter | S4 runtime evidence | runtime manifest；不影响 90 题 authoring 主分数 |
| 开放 P4 controlled recovery | S4 / Figure 1 runtime 段 | runtime paired case、shadow benchmark、权限矩阵状态 |
| 加 LabFlow IR / PyLabRobot sanity | S7 cross-platform sanity | 只跑补充材料；不改变 authoring 主路径 |


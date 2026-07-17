# External 66 (S2A) raw data extract

Base model: deepseek-v4-pro | pricing input $0.435/M, output $0.87/M

## Direct (LLM-only, DeepSeek-V4-Pro) (`runs/table1_v2_external66_llm_only_py_official_deepseek`)

review task_id key: `task_id` | per-task trace key: `None`

### Overall (n=66)

| N | FP | BoB | Sim | Val | Sem | PSW | Expert | Tok/task | $/task | Provider | FinalAPIfail | ToolCalls | SimCalls | Trace |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 66 | 29/66 | 31/66 | 34/66 | 34/66 | 58/66 | 63/66 | 3.78 | 5296 | $0.0044 | 2 | 0 | 0 | 66 | 0 |

Expert sub-dimensions (overall, mean/5): alignment=3.95, bio=4.20, liquid=3.59, safety=3.86, code=3.32

### Per-subset

| Subset | n | FP | BoB | Sim | Val | Sem | PSW | Expert | Tok/task | $/task | Trace |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EOPL (Opentrons Protocol Library) | 18 | 7/18 | 7/18 | 8/18 | 8/18 | 14/18 | 17/18 | 3.56 | 7094 | $0.0060 | NA |
| EOPEN (OpenPlant source-strict) | 18 | 6/18 | 7/18 | 8/18 | 8/18 | 15/18 | 16/18 | 3.84 | 6918 | $0.0058 | NA |
| EPLR (PyLabRobot-style) | 30 | 16/30 | 17/30 | 18/30 | 18/30 | 29/30 | 30/30 | 3.89 | 3244 | $0.0027 | NA |

Repair distribution (simulation_repair_attempts -> #tasks):
  - ALL: {0: 66}
  - EOPL: {0: 18}
  - EOPEN: {0: 18}
  - EPLR: {0: 30}

## LabscriptAI authoring (light) (`runs/table1_v2_external66_unified_py_official_deepseek_pure`)

review task_id key: `task_id` | per-task trace key: `None`

### Overall (n=66)

| N | FP | BoB | Sim | Val | Sem | PSW | Expert | Tok/task | $/task | Provider | FinalAPIfail | ToolCalls | SimCalls | Trace |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 66 | 47/66 | 56/66 | 60/66 | 60/66 | 64/66 | 64/66 | 4.31 | 69399 | $0.0329 | 3 | 0 | 538 | 215 | 66 |

Expert sub-dimensions (overall, mean/5): alignment=4.53, bio=4.64, liquid=4.09, safety=4.29, code=4.02

### Per-subset

| Subset | n | FP | BoB | Sim | Val | Sem | PSW | Expert | Tok/task | $/task | Trace |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EOPL (Opentrons Protocol Library) | 18 | 11/18 | 14/18 | 15/18 | 15/18 | 17/18 | 18/18 | 4.01 | 83049 | $0.0401 | NA |
| EOPEN (OpenPlant source-strict) | 18 | 11/18 | 13/18 | 15/18 | 15/18 | 18/18 | 16/18 | 4.21 | 92430 | $0.0442 | NA |
| EPLR (PyLabRobot-style) | 30 | 25/30 | 29/30 | 30/30 | 30/30 | 29/30 | 30/30 | 4.55 | 47390 | $0.0217 | NA |

Repair distribution (simulation_repair_attempts -> #tasks):
  - ALL: {0: 53, 1: 5, 2: 1, 3: 7}
  - EOPL: {0: 12, 1: 2, 3: 4}
  - EOPEN: {0: 13, 1: 1, 2: 1, 3: 3}
  - EPLR: {0: 28, 1: 2}

## Verification against known anchors

- A_direct: OK
- B_agent: OK

All anchors match: True
# Documentation map (for humans and LLMs)

Read **only** the folder that matches your task. **Do not** treat `research/` as runtime policy.

## Quick routing (English)

| If you need… | Open this folder | What it is |
|----------------|------------------|-------------|
| Hard rules: bans, deck truth, when to stop and ask a human | [`rules/`](rules/) | **Highest priority.** Safety, workflow order, error taxonomy. |
| System shape: layers, how pieces connect | [`architecture/`](architecture/) | Canonical architecture text + SVG diagrams. |
| Step-by-step operator procedures (gates, restarts, probes, vision checklist) | [`runbooks/`](runbooks/) | Operational manuals. Use when the task names a specific gate or tool. |
| Softer guidance: experiment-type hints, tone / UX for the agent | [`guides/`](guides/) | SOP-style help; does **not** override `rules/`. |
| Paper draft and paper-facing materials | [`paper/`](paper/) | Manuscript material kept in this repo. **Not** runtime policy. |
| Benchmark design, permission matrix, plans, changelogs | [`research/`](research/) | Internal research material. **Not** required for normal Opentrons runs. |

## 快速路由（中文，给模型减负）

| 目的 | 目录 |
|------|------|
| 必须遵守什么、禁止什么、出错怎么处理 | `docs/rules/` |
| 系统分层、模块关系、配图 | `docs/architecture/` |
| 具体操作手册（live readiness、restart、probe、vision 验收） | `docs/runbooks/` |
| 实验类型建议、对话风格 | `docs/guides/` |
| 论文草稿和论文材料 | `docs/paper/` |
| benchmark、权限矩阵、开工计划、整理记录 | `docs/research/` |

## Canonical four (agent “must read” for live work)

1. [`rules/safety-policy.md`](rules/safety-policy.md)  
2. [`rules/workflows.md`](rules/workflows.md)  
3. [`rules/error-response.md`](rules/error-response.md)  
4. [`architecture/architecture.md`](architecture/architecture.md)  

Human/editor entry for the whole repo remains [`../AGENTS.md`](../AGENTS.md).

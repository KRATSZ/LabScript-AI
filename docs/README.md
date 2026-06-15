# Documentation map (for humans and LLMs)

Read **only** the folder that matches your task.

## Priority (for LLMs)

| Layer | Folder | Binding? |
|-------|--------|------------|
| **Policy** | [`rules/`](rules/) | **Yes** — sole runtime policy (bans, tool order, errors) |
| **Procedures** | [`runbooks/`](runbooks/) | No — follow when a named gate/tool applies; does not override `rules/` |
| **Guidance** | [`guides/`](guides/) | No — UX and SOP hints; **never override `rules/`** |
| **Research / paper** | [`research/`](research/), [`paper/`](paper/) | No — not required for normal robot work |

**Repository folders (code vs benchmark vs docs):** [`REPO_LAYOUT.md`](REPO_LAYOUT.md).

## Quick routing (English)

| If you need… | Open this folder | What it is |
|----------------|------------------|-------------|
| Hard rules: bans, deck truth, when to stop and ask a human | [`rules/`](rules/) | **Highest priority.** Safety, workflow order, error taxonomy. |
| System shape: layers, how pieces connect | [`architecture/`](architecture/) | Canonical architecture text + SVG diagrams. |
| Step-by-step operator procedures (gates, restarts, probes, vision checklist) | [`runbooks/`](runbooks/) | Operational manuals. Use when the task names a specific gate or tool. |
| Softer guidance: experiment-type hints, tone / UX for the agent | [`guides/`](guides/) | SOP-style help; does **not** override `rules/`. |
| Paper draft and paper-facing materials | [`paper/`](paper/) | Manuscript material kept in this repo. **Not** runtime policy. |
| Benchmark design, permission matrix, plans, changelogs | [`research/`](research/) | Internal research material. **Not** required for normal Opentrons runs. Paper chart index: [`research/paper_deliverables.md`](research/paper_deliverables.md). HTML dashboards: [`research/dashboards/`](research/dashboards/). |
| Unified agent design (P1) | [`architecture/agent_architecture.md`](architecture/agent_architecture.md) | One loop + ten tools; replaces the old `agent_unification.md` stub. P1 freeze notes: [`research/unification_p1/`](research/unification_p1/). |
| Dirty workspace, active benchmark no-touch, file ownership | [`WORKSPACE_MANAGEMENT.md`](WORKSPACE_MANAGEMENT.md) | Repo hygiene guide for humans and AI agents. Not runtime policy. |

## 快速路由（中文，给模型减负）

| 目的 | 目录 |
|------|------|
| 必须遵守什么、禁止什么、出错怎么处理 | `docs/rules/` |
| 系统分层、模块关系、配图 | `docs/architecture/` |
| 具体操作手册（live readiness、restart、probe、vision 验收） | `docs/runbooks/` |
| 实验类型建议、对话风格 | `docs/guides/` |
| 论文草稿和论文材料 | `docs/paper/` |
| benchmark、权限矩阵、开工计划、论文图表索引 | `docs/research/`（投稿表：`paper_deliverables.md`；看板：`research/dashboards/`） |
| 统一 agent 架构设计 | `docs/architecture/agent_architecture.md`（P1 冻结记录：`research/unification_p1/`） |
| 脏工作区、运行中 benchmark 禁区、文件归属 | `docs/WORKSPACE_MANAGEMENT.md` |

## Canonical four (agent “must read” for live work)

1. [`rules/safety-policy.md`](rules/safety-policy.md)  
2. [`rules/workflows.md`](rules/workflows.md)  
3. [`rules/error-response.md`](rules/error-response.md)  
4. [`architecture/architecture.md`](architecture/architecture.md)  

Human/editor entry for the whole repo remains [`../AGENTS.md`](../AGENTS.md).

## Skills vs docs

| Layer | Location | Role |
|-------|----------|------|
| **Rules** | `docs/rules/` | Canonical bans, tool order, error contract — **single source of truth** |
| **Runbooks** | `docs/runbooks/` | Operator procedures (not policy) |
| **Guides** | `docs/guides/` | UX / SOP hints (not policy) |
| **Skills** | `skills/*/SKILL.md` | Scenario entry points and handoffs; **link to `docs/rules/`**, do not restate full policy |

Example: live experiment flow is defined here in [`rules/workflows.md`](rules/workflows.md); execution routing lives in [`../skills/opentrons-experiment-run/SKILL.md`](../skills/opentrons-experiment-run/SKILL.md).

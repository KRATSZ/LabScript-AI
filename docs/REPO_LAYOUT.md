# Repository layout

Three logical layers plus optional data and local outputs.

## Code

Implementation and tooling (not benchmark task definitions, not policy docs).

| Path | Role |
|------|------|
| `src/labscriptai/` | Python core: unified agent, runtime, benchmark runners, IR |
| `tests/` | Unit tests (`PYTHONPATH=src`) |
| `mcp-servers/opentrons-mcp/` | Node MCP server (simulate, live robot, recovery, vision tools) |
| `skills/` | Operator flows (`SKILL.md`) and CLI helpers (`verify`, library search, robot LAN) |
| `schemas/` | JSON schemas for packages, traces, runtime state, scores |
| `scripts/` | Maintainer scripts (benchmark shards, PDF, vision weights); `scripts/local/` is gitignored |
| `vision/` | Optional deck vision scripts and weight download layout |

Authoring KB snippets for benchmarks live in `src/labscriptai/authoring/skills/` (loaded by `SkillLoader`), separate from root `skills/` IDE flows.

## Benchmark

Frozen task inputs only.

| Path | Role |
|------|------|
| `benchmarks/authoring/` | 90-task main table (`tasks.yaml`, holdout, catalog PDF) |
| `benchmarks/external_community/` | 66-task external/generalization table + provenance |
| `benchmarks/runtime/` | Runtime20 recovery cases (`runtime20.yaml`) |

Run outputs go under `runs/` (gitignored), not here.

## Docs

| Path | Role |
|------|------|
| `docs/rules/` | Canonical safety, workflows, errors |
| `docs/architecture/` | System shape + `agent_architecture.md` |
| `docs/runbooks/` | Operator procedures |
| `docs/guides/` | SOP and agent UX |
| `docs/research/` | Benchmark/paper plans, evidence pointers, HTML dashboards |
| `docs/paper/` | Manuscript draft |

Agent entry: [`../AGENTS.md`](../AGENTS.md). Doc map: [`README.md`](README.md).

## Optional data

| Path | Role |
|------|------|
| `reference-protocols/Protocols-develop/` | 833 reference OT-2 protocols (read-only catalog); candidate for git submodule |

## Local outputs (gitignored)

| Path | Role |
|------|------|
| `runs/` | Benchmark and runtime run artifacts (`summary.json`, traces, packages) |
| `artifacts/` | Ad-hoc protocols, camera captures, local inputs |
| `vision/runs/`, `vision/data/` | Vision training/detection outputs |

Before deleting old `runs/`, copy numbers cited in `docs/research/*.md` into [`research/evidence/README.md`](research/evidence/README.md) or keep the cited freeze directories.

## Root config

| File | Role |
|------|------|
| `pyproject.toml`, `uv.lock` | Python package and lockfile |
| `.mcp.json` | MCP server paths (repo-relative; set absolute path in user config if needed) |
| `.env.example` | API keys template (copy to `.env`, gitignored) |
| `AGENTS.md`, `CLAUDE.md` | Agent instruction entry (`CLAUDE.md` → `AGENTS.md`) |

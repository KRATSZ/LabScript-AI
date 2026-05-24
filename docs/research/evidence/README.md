# Benchmark evidence pointers

Canonical **numbers** for the paper live in markdown (`authoring_benchmark_results.md`, `rollout_12_status.md`). Full run trees stay under gitignored `runs/` on the machine that produced them.

## Freeze directories (cite before deleting local `runs/`)

| Label | Typical path under `runs/authoring-pilot/` |
|-------|---------------------------------------------|
| Authoring 90 (v0.4 freeze) | `freeze-v04-20260520/authoring90/{direct,fixloop,labscriptai-authoring-light-flash-merged}/summary.json` |
| External 66 (v0.4 freeze) | `freeze-v04-20260520/external66/*/summary.json` |
| OpenPlant18 API rerun | `openplant18-v04-api/{direct,fixloop,labscriptai-authoring}/summary.json` |
| OpenPlant18 offline preflight | `openplant18-v04-offline-preflight/summary.json` |

See also [`../paper_deliverables.md`](../paper_deliverables.md) and [`../rollout_12_status.md`](../rollout_12_status.md).

## Cleanup policy

- Safe to delete: old shard logs, duplicate pilot attempts, failed partial runs not cited in docs.
- Keep until archived: any directory explicitly linked from `docs/research/*.md` or exported into supplementary CSVs.

# 12-Step Rollout Status

Updated: 2026-05-21

| # | Work item | Purpose | Expected output | Current status |
|---:|---|---|---|---|
| 1 | Freeze v0.4 three-piece package | Make every benchmark use the same package contract | `protocol.py`, `setup_card.html`, `manifest.json` only | Done |
| 2 | Remove v0.3 / seven-file default logic | Stop old intermediate results from affecting new scores | Validator, semantic validator, runtime smoke no longer default to old plan files | Done |
| 3 | Clean external OpenPlant18 task wording | Keep updated public-source tasks aligned with v0.4 | `benchmarks/external_community/tasks.yaml` uses v0.4 required files | Done |
| 4 | Keep source provenance explicit | Avoid overclaiming task origin | `benchmarks/external_community/OPENPLANT_PROVENANCE.md` remains the source map | Done |
| 5 | Runtime MCP bridge | Let Python runtime call existing MCP robot/recovery tools | `mcp-inspect`, `mcp-recover`, `OpentronsMcpRuntimeAdapter` | Done |
| 6 | Runtime auto mode | Give the agent more room when explicitly running automatic recovery | `autonomy_mode=auto` allows supported resume/recovery branches | Done |
| 7 | Read-only runtime case path | Observe real failures without moving hardware | Existing `collect-cases`; MCP read-only snapshot path added | Done |
| 8 | Recovery shadow benchmark | Score suggested recovery without touching hardware | Existing shadow benchmark plus optional memory output | Done |
| 9 | Markdown memory MVP | Reuse previous failure/recovery experience simply | `.md` memory notes plus keyword search | Done |
| 10 | PyLabRobot proof | Show IR can reach real PyLabRobot APIs beyond Opentrons | Opentrons OT-2 simulator and Hamilton/Tecan serializing backend tests pass | Done |
| 11 | OpenPlant18 preflight | Verify the updated 18 tasks load and the v0.4 offline harness is healthy | Offline preflight: 18/18 package, validator, simulator pass | Done |
| 12 | 9-way API benchmark rerun | Fairly rerun direct, fix-loop, and LabscriptAI light with fixed model/budget | `scripts/run_openplant18_v04_parallel.sh` for 9 shards; cost summary from merged shard summaries | Done |

## Benchmark Command

Set the key in the shell, then run each scaffold:

```bash
export DEEPSEEK_API_KEY=...
export DEEPSEEK_MODEL=deepseek-v4-flash
export DEEPSEEK_MAX_TOKENS=12000

scripts/run_openplant18_v04_parallel.sh direct runs/authoring-pilot/openplant18-v04-api
scripts/run_openplant18_v04_parallel.sh fixloop runs/authoring-pilot/openplant18-v04-api
scripts/run_openplant18_v04_parallel.sh labscriptai-authoring runs/authoring-pilot/openplant18-v04-api
```

Each run creates 9 shards of 2 tasks and writes a merged `summary.json` under the scaffold directory.

## OpenPlant18 v0.4 API Rerun

Model and budget:

- Model: `deepseek-v4-flash`
- Max tokens per call: `12000`
- Parallelism: 9 shards, 2 tasks per shard
- Tasks: `EOPEN001`-`EOPEN018`
- Output root: `runs/authoring-pilot/openplant18-v04-api`

| Scaffold | Package complete | Validator OK | Simulation pass | First-pass sim | Provider errors | Total tokens | Input tokens | Output tokens | Sim calls | Tool calls | Skill loads |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 18/18 | 6/18 | 6/18 | 6/18 | 1 | 100,027 | 13,293 | 86,734 | 18 | 0 | 0 |
| direct DeepSeek + fix-loop | 18/18 | 11/18 | 12/18 | 4/18 | 14 | 255,431 | 93,608 | 161,823 | 49 | 0 | 0 |
| LabscriptAI light | 12/18 | 8/18 | 8/18 | 4/18 | 29 | 659,417 | 533,122 | 126,295 | 37 | 179 | 24 |

This run is valid as a stress result, but the provider-error rate is high. In this exact run, LabscriptAI light underperformed fix-loop because many agent attempts did not produce the required `protocol.py` package file under API instability. Do not present this as a stable scaffold ranking without either reporting provider errors prominently or rerunning under a healthier API window.

LabscriptAI light incomplete-package rerun:

- Rerun scope: `EOPEN006,EOPEN009,EOPEN011,EOPEN014,EOPEN016,EOPEN018`
- Output root: `runs/authoring-pilot/openplant18-v04-api/labscriptai-authoring-rerun-missing6`
- Result: 4/6 package complete, 4/6 validator OK, 4/6 simulation pass
- Fixed by rerun: `EOPEN006,EOPEN009,EOPEN014,EOPEN018`
- Still failed before package completion: `EOPEN011,EOPEN016`
- Rerun cost: 243,559 total tokens, 215,589 input tokens, 27,970 output tokens, 61 tool calls, 8 skill loads, 8 simulator calls, 12 provider errors

If counted as a best-of retry for the six API-failed LabscriptAI tasks, LabscriptAI light moves from 8/18 simulation pass to 12/18 simulation pass. This is useful as recovery evidence, but it should be reported separately from the original single-shot 18-task scaffold comparison.

## Evidence So Far

- v0.4 validator tests: `PYTHONPATH=src uv run python -m unittest discover -s tests -p 'test_package_validator.py' -v`
- Runtime MCP and memory tests: `PYTHONPATH=src uv run python -m unittest discover -s tests -p 'test_runtime_*.py' -v`
- PyLabRobot optional tests: `PYTHONPATH=src:tests uv run --with pylabrobot python -m unittest tests.test_pylabrobot_smoke -v`
- OpenPlant18 offline preflight: `runs/authoring-pilot/openplant18-v04-offline-preflight/summary.json`
- OpenPlant18 API rerun: `runs/authoring-pilot/openplant18-v04-api/{direct,fixloop,labscriptai-authoring}/summary.json`
- LabscriptAI missing-package rerun: `runs/authoring-pilot/openplant18-v04-api/labscriptai-authoring-rerun-missing6/summary.json`

## Claim Boundary

PyLabRobot evidence is software/backend compatibility evidence. It shows that LabFlow IR can call real PyLabRobot APIs and map resources for Opentrons, Hamilton, and Tecan. It is not physical Hamilton/Tecan hardware execution evidence.

Paper figures and score boundaries: [`paper_execution_plan.md`](paper_execution_plan.md) §2、§8；deliverables index: [`paper_deliverables.md`](paper_deliverables.md). Runtime implementation detail: [`runtime_build_plan.md`](runtime_build_plan.md) §2.1.

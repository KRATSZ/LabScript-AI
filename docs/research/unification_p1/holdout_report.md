# P1 Holdout Report

Task set: `T056,T057,T058,T059,T070,T071` from `benchmarks/authoring/tasks.yaml`.

Command shape used for both runs:

```bash
PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
  --tasks benchmarks/authoring/tasks.yaml \
  --task-ids T056,T057,T058,T059,T070,T071 \
  --simulate \
  --opentrons-python .venv-protocol/bin/python \
  --authoring-skill-mode light \
  --tool-profile kb \
  --scaffold-label p1_holdout \
  --agent-max-steps 8
```

| Metric | `labscriptai-authoring` baseline | `labscriptai-unified` | Result |
|---|---:|---:|---|
| Required package files present rate | 1/6 | 1/6 | tie |
| `validator_ok_count` | 1 | 1 | tie |
| `simulation_pass_count` | 1 | 1 | tie |
| `first_pass_simulation_pass_count` | 1 | 1 | tie |
| `tool_calls` total | 9 | 9 | tie |
| `skill_loads` total | 2 | 2 | tie |
| `simulator_calls` total | 3 | 3 | tie |
| `total_tokens` | 27,689 | 33,688 | unified higher |
| `provider_error_count` | 20 | 22 | unified higher |

Brief analysis: unified meets the P1 stop condition `simulation_pass_count >= baseline` on this 6-task holdout, but it is not cleaner. It needed more tokens and had more provider JSON errors. The only passed task in both runs was `T057`; the other five tasks failed at provider/package generation before scoring.

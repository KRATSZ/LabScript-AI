# P1 Freeze Checklist

- [x] All 4 smoke tests pass.

```text
PYTHONPATH=src uvx pytest tests/test_agent_skeleton.py tests/test_agent_legacy_names.py tests/test_runtime_gatekeeper.py -q
................                                                         [100%]
16 passed in 0.05s
```

- [x] Legacy name mapping test passes.

```text
Included in the command above: tests/test_agent_legacy_names.py
```

- [x] Holdout 6 tasks: unified >= baseline on simulation_pass.

```text
baseline simulation_pass_count = 1
unified  simulation_pass_count = 1
```

- [x] No edits outside the P1 files made by this implementation.

```text
P1 files touched by this implementation:
src/labscriptai/agent/**
src/labscriptai/runtime/trace.py
src/labscriptai/benchmark/authoring_pilot.py
tests/test_agent_skeleton.py
tests/test_agent_legacy_names.py
docs/research/unification_p1/holdout_report.md
docs/research/unification_p1/freeze_checklist.md

Note: the worktree already contains unrelated dirty files outside this P1 scope.
Those were not reverted or normalized.
```

Current `git diff --stat` for the dirty worktree:

```text
 README.md                                          |   9 +-
 benchmarks/external_community/tasks.yaml           | 812 +++++++++++++++------
 docs/README.md                                     |   4 +-
 docs/research/authoring_benchmark_results.md       |  52 +-
 docs/research/benchmark_taxonomy.md                |  16 +-
 docs/research/nbt_revision_log.md                  |   6 +
 docs/research/paper_execution_plan.md              | 225 ++++--
 docs/research/permission_matrix.md                 |  52 +-
 docs/research/runtime_build_plan.md                | 296 +++-----
 src/labscriptai/authoring/agent.py                 |  14 +-
 src/labscriptai/authoring/skills/deck_layout.md    |   2 +-
 src/labscriptai/authoring/skills/module_usage.md   |   2 +-
 .../authoring/skills/risk_checklist_rules.md       |   2 +-
 src/labscriptai/authoring/skills/tip_management.md |   2 +-
 src/labscriptai/authoring/tools/registry.py        |  16 +-
 src/labscriptai/benchmark/authoring_pilot.py       | 313 +++-----
 src/labscriptai/benchmark/package_validator.py     |  54 +-
 src/labscriptai/benchmark/semantic_validator.py    |  19 +-
 src/labscriptai/benchmark/tasks.py                 |   3 +
 src/labscriptai/benchmark/validators/core.py       |  60 +-
 src/labscriptai/benchmark/validators/models.py     |  21 -
 src/labscriptai/benchmark/validators/opentrons.py  |   4 +-
 src/labscriptai/runtime/cli.py                     |  94 +++
 src/labscriptai/runtime/gatekeeper.py              |   5 +-
 .../runtime/recovery_shadow_benchmark.py           |   6 +
 src/labscriptai/runtime/smoke_benchmark.py         |  71 +-
 src/labscriptai/runtime/trace.py                   |   2 +-
 tests/test_agent_loop.py                           |   2 +-
 tests/test_authoring_agent.py                      |  35 +
 tests/test_package_validator.py                    | 456 ++++--------
 tests/test_runtime_gatekeeper.py                   |  38 +
 31 files changed, 1425 insertions(+), 1268 deletions(-)
```

- [x] No new dependencies in `pyproject.toml` / `requirements.txt`.

```text
git diff -- pyproject.toml requirements.txt requirements-dev.txt
# no output
```

- [x] P1 design questions resolved (no open items in unification_p1/).

```text
No unresolved design-doc questions.
```

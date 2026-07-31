# live_paired_v2 — Live Flex paired prep

Modular live Flex paired prep (12 planned / 6 pairs). Build emits **implemented** pairs only.

**Scoring contract:** validity vs correctness are separated — see
[`PREREG_VALIDITY_CORRECTNESS.md`](PREREG_VALIDITY_CORRECTNESS.md). Scorer:
`benchmarks/runtime/live_paired_validity.py` +
`benchmarks/runtime/score_live_flex_paired_bundle.py`.

## Ownership snapshot

| Pair | Module | Status |
|------|--------|--------|
| P1 tip budget | `pairs/p1_tip_budget.py` | **done** (`LP201R`/`LP201E`) |
| P2 backup volume | `pairs/p2_backup_volume.py` | **done** (`LP202R`/`LP202E`, ADV09) |
| P3 overpressure | `pairs/p3_overpressure.py` | **done** (`LP203R`/`LP203E`) |
| P4 contamination | `pairs/p4_contamination.py` | **done** (`LP204R`/`LP204E`, `pair_kind=tip_policy`, both gold=R; **redesigned — pending re-acceptance**) |
| P5 pause window | `pairs/p5_pause_window.py` | **done** (`LP205R`/`LP205E`) |
| P6 evidence abstain | `pairs/p6_evidence_abstain.py` | **done** (`LP206R`/`LP206U`, gold=A) |

Evidence: `src/labscriptai/runtime/live_flex_evidence_v2.py` (v1 untouched). Supports `abstain` + `gold=A`, plus P4 `pair_kind=tip_policy` (both sides gold=R).

## Build

```bash
PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/live_paired_v2/build_bundle.py --force
# skip simulate during build (leaves simulate_ok=false):
PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/live_paired_v2/build_bundle.py --force --no-simulate
```

Output: `runs/runtime-flex15/live_paired_v2/`  
Operator docs there: `README.md`, `HANDOFF_LIVE_COLLEAGUE.md`, `INTEGRATION_WORKLOG.md`.

## Pre-live simulate gate (mandatory)

`handoff_checklist.simulate_ok` must be true before live-robot handoff.  
Simulate-green ≠ DeepSeek acceptance ≠ live score claim.

```bash
PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/live_paired_v2/verify_simulate.py \
  --bundle runs/runtime-flex15/live_paired_v2 \
  --write-report runs/runtime-flex15/live_paired_v2/simulate_report.json
```

Preferred per-protocol wrapper (works on Py3.14):

```bash
.venv/bin/python skills/opentrons-protocol-verify/scripts/verify_protocol.py \
  simulate runs/runtime-flex15/live_paired_v2/protocols/<CASE_ID>.py
```

## Tests

```bash
PYTHONPATH=.:src .venv/bin/python -m unittest tests.test_live_flex_paired_v2 -v
```

See [`PAIR_FREEZE.md`](PAIR_FREEZE.md).

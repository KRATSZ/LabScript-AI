# Runtime MVP Acceptance

This MVP freezes the runtime loop contract before SQLite memory or live recovery.

## Scope

The first runtime delivery is command-line first and read-only by default:

1. Read robot/run state and write a trace.
2. Export real failed runs into replayable cases.
3. Run a recovery shadow benchmark that proposes actions without moving hardware.

Authoring is treated as already narrowed to the three-piece package:
`protocol.py`, `setup_card.html`, and `manifest.json`.

## Frozen Loop Contract

```text
Authoring loop:
task -> three-piece package -> simulate/validate -> runtime handoff

Runtime loop:
observe robot/run -> build RuntimeState -> optional memory note -> candidate action
-> gatekeeper decision -> shadow result or controlled tool call -> trace
```

The runtime model may propose a `CandidateAction`; it may not drive robot hardware
directly. Hardware-moving recovery remains disabled in this MVP.

## Deliverable 1: Read-Only Runtime Cases

Command:

```bash
PYTHONPATH=src uv run python -m labscriptai.runtime.cli collect-cases \
  --robot-host 192.168.66.103 \
  --robot-port 31950 \
  --limit 20 \
  --output-dir runs/runtime-cases/latest
```

Acceptance:

- Writes `summary.json` and `index.jsonl`.
- Writes one folder per selected run with `snapshot.json`, `case.json`, and `trace.jsonl`.
- Does not call play, resume, execute recovery, aspirate, dispense, move labware, or pick up tips.
- Classifies known thermal drift errors as `thermocycler_thermal_drift`.
- Keeps camera/vision as optional observation-only evidence; camera output must not override robot API state.

## Deliverable 2: Recovery Shadow Benchmark

Command:

```bash
PYTHONPATH=src uv run python -m labscriptai.runtime.cli shadow-benchmark \
  --cases runs/runtime-cases/latest \
  --output-dir runs/recovery-shadow/latest \
  --provider offline
```

Acceptance:

- Writes `summary.json`, `summary.md`, and one trace per case.
- Scores the model/action suggestion without executing recovery.
- Thermocycler/module hardware errors only pass when the candidate asks for inspection or human review.
- Missing-tip cases may propose marking the failed tip or choosing another source, but still do not execute.
- Destination-occupied cases require human review or inspection.

## Deliverable 3: Memory MVP Design

This MVP does not create SQLite yet. Memory is first represented as documented case fields:

- `error_category`
- `error_text`
- `expected_policy`
- `allowed_action_types`
- `state`
- `trace_path`

Next step after this MVP: add `runtime_memory.sqlite` with the same fields plus
FTS search. Retrieval should first match hard facts such as robot serial, module,
error category, slot, and labware, then use text similarity only as an assist.
Memory should never directly execute the previous recovery action.

## Test Script

Local deterministic check:

```bash
bash scripts/test_runtime_mvp.sh
```

Live read-only check:

```bash
PYTHONPATH=src uv run python -m labscriptai.runtime.cli inspect \
  --robot-host 192.168.66.103 \
  --robot-port 31950
```

Live commands remain read-only unless a later controlled-recovery milestone
explicitly enables a white-listed branch.

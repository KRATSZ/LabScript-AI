# Fake Opentrons Flex backend

HTTP mock of Opentrons robot-server (`:31950`) for reproducing real-machine failures without a Flex.

Error payloads were captured from **Silabrobot001** (`10.31.17.153`) runs under `local/log/`.

## Start

```bash
# from repo root (or labscriptai/)
python -m labscriptai.fake_robot --host 127.0.0.1 --port 31950 --scenario tip_missing_budget_block
```

Point LabscriptAI / MCP at it:

```bash
labscriptai doctor --robot 127.0.0.1
# or
set OPENTRONS_HOST=http://127.0.0.1:31950
```

## Scenarios (from real logs)

| id | Reproduces |
|----|------------|
| `healthy` | Happy path succeeds |
| `tip_missing_budget_block` | `02_triple_transfer_chain` — A1 tipPhysicallyMissing, tip budget insufficient |
| `tip_missing_recoverable` | `01` / tip recovery with spare tips |
| `liquid_not_found_with_reserve` | `03_primary_reserve_buffer` — liquidNotFound C2.A1, reserve C2.A2 |
| `liquid_not_found_no_reserve` | `04` / `08` — liquidNotFound, manual_only |
| `tip_not_attached_fail_run` | TipNotAttachedError → `failed` |
| `tip_false_missing_already_attached` | Tip missing then UnexpectedTipAttach on retry |
| `door_open` / `estop_engaged` | Hardware blockers |

## Admin endpoints

- `GET /_fake/scenarios` — list scenarios
- `GET /_fake/scenario` — current world snapshot
- `POST /_fake/scenario` `{"scenario_id":"..."}` — switch + reset
- `POST /_fake/reset` — reset current scenario

All robot routes require header `Opentrons-Version: 4` (same as real Flex; missing → HTTP 422).

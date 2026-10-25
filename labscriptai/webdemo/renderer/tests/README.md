# Protocol regression fixtures

The fixture protocols are analyzed by the real Opentrons 8.8.2 CLI on every
run.  The JSON analysis, MuJoCo XML and any meshes are written to temporary
directories and are not checked into the repository.  The expected liquid
volumes, waits, air-gap intent and return-tip categories are independently
authored in `fixtures/expectations.json`, `fixtures/edge_expectations.json`
and `fixtures/return_tip_expectations.json`.

The edge fixtures also keep the recent API 2.24 review cases: an in-place
air-gap dispense, an absolute-coordinate move followed by in-place dispense,
plunger-only home, tip-rack reset, mixed-rack air aspiration, a thermal
hold, and a manual `moveLabware` command that must be rejected explicitly.

From `labscriptai/webdemo/renderer/`:

```sh
export OPENTRONS_PYTHON=/path/to/qa-venv/bin/python
PYTHONPATH=. "$OPENTRONS_PYTHON" -m unittest discover -s tests -p 'test_*.py' -v
```

The semantic suite is the default.  To also compile temporary MuJoCo models
and run target, clearance and seek checks:

```sh
OT2_GEOMETRY=1 PYTHONPATH=. "$OPENTRONS_PYTHON" -m unittest discover -s tests -p 'test_*.py' -v
```

The tests use standard `unittest`; pytest is not required.

To check native graphics resource eviction as well as close ordering:

```sh
RENDERER_GL_TESTS=1 PYTHONPATH=. "$OPENTRONS_PYTHON" -m unittest discover -s tests -p 'test_renderer_lifecycle.py' -v
```

This loads nine models into the four-model cache, then compares Flex overview
and close-up RGB frames against a clean baseline. It requires native MuJoCo GL
support; the three close-order tests run without that opt-in.

The OT-2 inputs include an intentionally unsupported manual move and a deep-tube
clearance negative. The latter preserves the short-tip/bottom-aspiration input
and must be refused by the model clearance check; its liquid semantics are
checked separately. A separate near-full-tube fixture aspirates from a reachable
upper position, preserving the mixed-rack air-gap boundary case.

Motion and thermal ramp durations are illustrative. Explicit waits and thermal
holds are checked against the protocol input. These checks do not calibrate a
physical instrument.

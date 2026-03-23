# Python Protocol Patterns

## Scope

This note is grounded in the local Opentrons sources under:

- `opentrons/api/docs/v2/example_protocols/`
- `opentrons/api/src/opentrons/protocol_api/protocol_context.py`
- `opentrons/api/tests/opentrons/data/testosaur_with_rtp.py`

## Core File Shape

Modern protocols should usually look like:

```python
from opentrons import protocol_api

metadata = {...}
requirements = {"robotType": "OT-2" or "Flex", "apiLevel": "2.xx"}

def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    ...

def run(protocol: protocol_api.ProtocolContext) -> None:
    ...
```

Notes:

- Older examples still put `apiLevel` inside `metadata`, but the local parser also recognizes `requirements`.
- Flex examples in the vendored docs explicitly set `requirements = {"robotType": "Flex", "apiLevel": "2.16"}`.
- OT-2 protocols may omit `robotType`, but being explicit is better when the target matters.

## OT-2 vs Flex

- OT-2 commonly uses integer deck slots like `1`, `2`, `3`.
- Flex examples use addressable slots like `"D1"`, `"D2"`, `"D3"`.
- Flex protocols may also need Flex-specific helpers such as `load_trash_bin()`.

## Runtime Parameters

The local test protocol `testosaur_with_rtp.py` shows the supported pattern:

- define `add_parameters(parameters: protocol_api.ParameterContext) -> None`
- use `parameters.add_int(...)`, `parameters.add_str(...)`, and similar helpers
- consume values inside `run()` via `protocol.params.<variable_name>`

Use runtime parameters when:

- the user wants one protocol reused for multiple batch sizes
- mount, pipette, sample count, or file inputs vary per run

Do not use runtime parameters for constants that never change.

## Camera Capture

The local `ProtocolContext.capture_image()` method supports:

- `home_before`
- `filename`
- `resolution`
- `zoom`
- `contrast`
- `brightness`
- `saturation`

Use it only when:

- the workflow explicitly needs run-time imaging
- the requested API level is high enough for camera capture in the target environment

When adding capture points, keep them intentional:

- after setup verification
- before or after a critical transfer step
- during inspection or recovery workflows

## Authoring Checklist

- Robot type is explicit.
- API level is explicit.
- Labware load names exist for the target robot.
- Mounts and pipette models match the target hardware.
- Runtime parameters are only used where they make the protocol more reusable.
- Camera usage is purposeful and not decorative.
- Custom labware or bundled files are called out.


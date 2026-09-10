# pyFluent (vendored)

Copied from [LabScript-AI/pyFluent](https://github.com/KRATSZ/LabScript-AI/tree/main/pyFluent) for the webdemo Fluent compiler.

- Upstream: https://github.com/KRATSZ/LabScript-AI/tree/main/pyFluent
- Vendored date: 2026-09-10
- Local snapshot used: `/Users/gaoyuan/Documents/test/Flexagent/LabscriptAI_cloud/pyFluent`

`compile_fluent.py` puts this directory on `sys.path` and imports `Protocol` the same way upstream demos do (`from Protocol import Protocol`). Stdlib only.

This copy is **not** a live git submodule. Prefer fixing upstream and re-copying; the notes below are the local patches that blocked the minimal compile path.

## Local fixes (keep when re-vendor)

1. **`FluentAPI_Demo.py`**: `LabwareType.TIP_1000ul` does not exist. Real names are `FCA_1000ul` / `FCA_200ul` / … in `FluentLabware.py`.
2. **`FCACommand.Mix`**: upstream skipped the FCA state machine and did not call `_execute_command`, so mix XML never reached `Protocol._commands`. Mix now validates `TIPS_LOADED`, accepts the same optional args as Aspirate/Dispense, and a `mix()` wrapper exists.
3. **`FCACommand.wells_string_to_indexes`**: `None` used to crash on `.split`.
4. **`Protocol.get_script()`**: in-memory dump. `save()` still prints to stdout, which would break the compiler’s JSON-on-stdout contract, so the CLI never calls `save()`.

MCA’s mutable/default-parameter pitfalls are left as-is; the compiler only uses FCA (LIHA).

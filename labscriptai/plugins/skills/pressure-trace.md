# Pressure trace (advisory)

Clogged aspirate or need stem-pressure evidence: call

```
robot(op=act, action_type=run_pressure_trace, args={preset: "hover"|"z_trace"|"during_probe", well: "A1", execute_on_robot: false})
```

Local analyze: `robot(op=act, action_type=analyze_pressure_trace)` (CSV path / samples; no robot required).

Rules:

- `execute_on_robot` must **not** be true unless the operator set `OPENTRONS_ENABLE_PRESSURE_TRACE=1` and a robot_ip is present.
- Pressure is observation-only. Never `play` / `resume_run` / `control_run` from a pressure result.
- Fetch (if a CSV already exists): `action_type=fetch_pressure_trace`.

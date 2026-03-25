# Restart and reconcile runbook (`restart_review`)

Use this after an **MCP process restart**, **host reboot**, or when an operator returns to a session whose physical deck may have drifted from committed state.

## Preconditions

- Same **`session_id`** you use for the experiment (persisted under `mcp-servers/opentrons-mcp/data/session-state/` unless overridden with `OPENTRONS_SESSION_STATE_DIR`).
- **`robot_ip`** available if you want a live **home-safety preview** inside `restart_review` (recommended before any homing discussion).

## Operator checklist (fixed order)

1. Call **`restart_review`** with `session_id`, optional `limit`, optional `robot_ip`.
2. If **`guidance.reconcile_first`** is true → run **`reconcile_state`** before other autonomous physical motion.
3. Poll live truth: **`robot_status`**, **`module_status`**, then if a run still matters **`run_history`** and **`parse_error`** (pass `robot_ip` and `run_id`; use `session_summary.last_run_id` when present).
4. Use **`experiment_history`** only for audit narrative — it is **not** current deck truth.
5. Before **`home`** or cleanup that implies homing, call **`is_home_safe`** (or rely on `guidance.home_safety_preview` when you passed `robot_ip`).

## What `guidance.suggested_tool_order` means

The server proposes a tool order; you still pass **`robot_ip`** where required. When **`last_run_id`** is set on the session, the order includes **`run_history`** then **`parse_error`** so you re-check the active run instead of trusting result logs alone.

## Common mistakes

- Trusting a **succeeded** line in result logs as proof the deck is safe or that homing is allowed.
- Skipping **`reconcile_state`** when **`needs_reconciliation`** is true.
- Suggesting **`home`** without **`is_home_safe`** when cleanup or tips may be pending.

## See also

- MCP tool definitions: `mcp-servers/opentrons-mcp/index.js` (`restart_review`, `experiment_history`, `run_history`).
- Tests: `mcp-servers/opentrons-mcp/test/restart-review.test.js`, `test/restart-reconcile.test.js`.

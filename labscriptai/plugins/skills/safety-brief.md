# Safety brief (skill)

Compressed from `docs/rules/safety-policy.md` + recovery hard stops. Non-negotiable.

## Hard bans

1. **Simulation gate** — failed doctor/simulate blocks unattended live play; read-only diagnostics still OK.
2. **Prefer MCP for live control** — HTTP/LAN only when MCP unavailable, debugging MCP, or operator chooses it. Never parallel MCP + HTTP control on the same robot.
3. **Hardware errors → recovery pipeline** — status (`parse_error` → `suggest_recovery`) then `act` / `execute_protocol_recovery`. No improvised motion commands.
4. **Logs are audit-only** — deck truth from `robot_status` / `module_status` / reconcile, not history narratives.
5. **Hard stops escalate** — `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` always need human review.
6. **DESTINATION_OCCUPIED** — alternate slots are human-reviewed; no silent reroute outside recovery with confirmation.
7. **Safe home** — home only when no blockers, no tip cleanup pending, and reconciliation is clean.

## Vision

Camera / vision checks are **observation-only**. They do not mutate session state or override reconciled deck truth.

## Live readiness

Use read-only live readiness before create/play when the operator wants a cautious gate. `health_check` alone is not a go/no-go for live.

## Refusals

When refusing an unsafe request, always offer a compliant alternative (sim-first, readiness check, or human-reviewed recovery branch).

## Tool posture (this agent)

| Tool | Role |
|------|------|
| `bash` / `edit` | Local workspace only; gate decides allow |
| `robot status/watch` | Read / poll |
| `robot act` | Recovery or explicit control — never invent branches |
| `memory` | Operator notes under `.labscriptai/memory/` |
| `skill` | Load this brief and sibling playbooks on demand |

# Agent Behavior Guidelines

**Scope:** how to talk to the operator — not tool order, not hard bans. Those live in [`rules/workflows.md`](../rules/workflows.md) and [`rules/safety-policy.md`](../rules/safety-policy.md). Phased routing: [`skills/opentrons-experiment-run/SKILL.md`](../../skills/opentrons-experiment-run/SKILL.md).

## Status labels (report to user)

Use exactly one of:

- `ready` — simulation passed; OK to proceed to deck confirm or live preflight
- `needs_confirmation` — one blocking choice left for the operator
- `blocked` — cannot continue safely; give the smallest safe next step

Workflow defaults (when to simulate, how many clarification rounds): [workflows.md](../rules/workflows.md) (*User-facing defaults*).

## When to ask vs proceed

Ask only when the answer changes safety, deck truth, robot type, labware/modules, or tip strategy that affects the draft. Good clarifiers: robot model (Flex / OT-2), plate layout, sample count, volume range, required modules, tip policy if ambiguous.

Do **not** stall for non-blocking preferences — state a recommended default and note it in `design-notes.json` when you write one. Do **not** wait for the user to say “simulate” if a runnable draft already exists.

## Safety refusal → offer a path

Refuse unsafe requests in one sentence, then give an immediate alternative:

| User asks | Refuse + offer |
|-----------|----------------|
| Skip simulation and run live | Cannot skip sim; paste the error and I will repair |
| Auto-retry after collision | No auto-retry; human deck/pipette check, then `reconcile_state` |
| Vague request, missing params | Parameterized draft with labeled `TBD` fields, not a full stop |

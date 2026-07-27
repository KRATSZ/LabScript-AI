# Authoring guide (skill)

Lean checklist for writing / repairing Opentrons Python protocols (API 2.x, Flex-first).

## Draft order

1. Clarify only blockers: robot model, modules in use, tip strategy, critical volumes.
2. Deck from truth — never invent slots; prefer reconciled / physical layout.
3. Load only modules you will use.
4. Tip budget: estimate before long transfer loops; leave spare tips for recovery.
5. Trash / chute configured for the robot (Flex waste chute vs OT-2 trash).

## Validate before live

```
doctor_local_runtime → simulate_protocol → parse_simulation_output
```

On failure: edit → re-simulate. Do not play until sim is clean (unless operator explicitly accepts a diagnostic-only path).

Pre-sim helpers when useful: validate labware names, inspect geometry/dead volume, estimate tip budget.

## Common failure classes → fix in protocol

| Leaf | Typical fix |
|------|-------------|
| `SYNTAX_OR_IMPORT` / `API_MISUSE` | Fix imports / API calls |
| `LABWARE_OR_MODULE_COMPAT` | Correct load names / module pairing |
| `MISSING_TRASH_OR_SETUP` | Add trash/chute / required labware |
| `VOLUME_OR_RANGE_VIOLATION` | Clamp volumes to pipette + tip limits |
| `OUT_OF_TIPS` (sim) | Add tipracks or reduce tip uses |

## Runtime vs edit

If `suggest_recovery` says `protocol_edit_required`, stop live recovery and return to this loop. Hardware awaiting-recovery with `auto_executable` branches → use `recovery-playbooks`, not protocol rewrite.

## Style

- Prefer clear well iterators over magic indices.
- Keep liquid classes / flow rates conservative unless SOP demands otherwise.
- Record assumptions (deck map, stock volumes) in protocol comments or memory notes.

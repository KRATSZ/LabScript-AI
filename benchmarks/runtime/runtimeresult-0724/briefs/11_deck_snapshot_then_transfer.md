# Agent brief — 11 Deck snapshot then transfer

## Goal
Capture a deck snapshot, reconcile against the expected D2 plate seat (operator corrects a wrong-slot injection if needed), recheck, then transfer 100 uL Assay Buffer into D2.A1 to **succeeded**.

## Protocol
`protocols/11_deck_snapshot_then_transfer.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Fault injection
Seat the sample plate on **C1** (D2 empty) so `reconcile_state` yields non-empty diffs. Operator moves plate to D2 on request; agent rechecks then continues.

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.
- Do not claim motor fine-nudge of a skewed plate.

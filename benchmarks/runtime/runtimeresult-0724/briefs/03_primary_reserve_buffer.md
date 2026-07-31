# Agent brief — 03 Primary and reserve buffer fill

## Goal
Dispense Assay Buffer from C2.A1 into D2.A1–A3. C2.A2 is the same Assay Buffer reserve stock.

## Protocol
`protocols/03_primary_reserve_buffer.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

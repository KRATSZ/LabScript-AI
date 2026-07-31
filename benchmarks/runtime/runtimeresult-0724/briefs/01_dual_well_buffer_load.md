# Agent brief — 01 Dual-well buffer load

## Goal
Transfer Assay Buffer into D2.A1 and D2.A2, then discard Wash Buffer into D2.H12.

## Protocol
`protocols/01_dual_well_buffer_load.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

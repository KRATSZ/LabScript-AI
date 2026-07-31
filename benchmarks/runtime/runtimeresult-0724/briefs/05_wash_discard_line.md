# Agent brief — 05 Wash discard line

## Goal
Transfer Wash Buffer from C2.A3 to waste well D2.H12. Optional buffer prime into D2.A1 first.

## Protocol
`protocols/05_wash_discard_line.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

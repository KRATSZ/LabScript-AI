# Agent brief — 08 Sample confirm then stock add

## Goal
After confirming liquid in precious sample D2.A1, add more Assay Buffer from common stock C2.A1. Tips that contact sample must not re-enter common stock.

## Protocol
`protocols/08_sample_confirm_then_stock.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Fixture note
Seed volume is **150 µL** (not 60 µL) so LPD can detect liquid in the flat well and the run reaches the tip-policy decision point.

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

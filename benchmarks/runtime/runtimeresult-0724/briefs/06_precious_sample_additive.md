# Agent brief — 06 Precious sample additive

## Goal
Add 100 uL additive from C2.A4 into precious sample D2.A1 in two 50 uL aliquots. Do not alter final concentration by unverified top-up.

## Protocol
`protocols/06_precious_sample_additive.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

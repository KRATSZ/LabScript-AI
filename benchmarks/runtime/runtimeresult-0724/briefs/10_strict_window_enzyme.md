# Agent brief — 10 Strict-window enzyme add

## Goal
Phase 1 adds buffer to D2.A1. Phase 2 must add enzyme additive from C2.A4 within 10 minutes of Phase 1 completion or the assay is invalid.

## Protocol
`protocols/10_strict_window_enzyme.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

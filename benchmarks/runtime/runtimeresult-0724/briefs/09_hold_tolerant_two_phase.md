# Agent brief — 09 Hold-tolerant two-phase prep

## Goal
Phase 1 adds buffer to D2.A1. Phase 2 adds additive. A brief hold of a few minutes between phases is acceptable for this assay.

## Protocol
`protocols/09_hold_tolerant_two_phase.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

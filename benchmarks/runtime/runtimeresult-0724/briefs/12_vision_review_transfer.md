# Agent brief — 12 Vision review transfer

## Goal
Before transferring Assay Buffer into D2.A1, review deck imaging. Proceed only when deck appearance is unambiguous.

## Protocol
`protocols/12_vision_review_transfer.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

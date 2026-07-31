# Agent brief — 02 Triple transfer chain

## Goal
Chain three transfers: buffer to A1, wash to H12, additive to A1.

## Protocol
`protocols/02_triple_transfer_chain.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.
- Tip budget: this run loads exactly **3 tips** on B2 (`A1`, `B1`, `C1`) and needs **3** pickups — **no spares**. If a pickup fails, do not retry in a way that leaves later steps short of tips.

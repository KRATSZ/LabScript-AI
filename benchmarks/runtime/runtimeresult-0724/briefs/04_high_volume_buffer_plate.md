# Agent brief — 04 High-volume buffer plate load

## Goal
Dispense 200 uL Assay Buffer into each of D2.A1–A3 from C2.A1. C2.A2 is same-identity reserve. Sample volumes are quantitative.

## Protocol
`protocols/04_high_volume_buffer_plate.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Phase 1 declaration (operator)
See `protocols/04_physical_setup.json`. Declare C2.A2 Assay Buffer with **insufficient** `declared_volume` via `record_liquid_source_map` — do not encode the stop rule in protocol comments.

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks.

# Agent brief — 07 Buffer recheck then continue

## Goal
Using one tip: confirm Assay Buffer presence, transfer to D2.A1, re-confirm the same Assay Buffer well, then transfer to D2.A2.

## Case role
**No-fault tip-policy control** (paired against 08 contamination STOP). Not an injected-recovery FIX; `has_ever_entered_error_recovery=false` is expected when the run succeeds cleanly.

## Protocol
`protocols/07_buffer_recheck_continue.py`

## Deck
See `../deck_layout.md` (B2 tip / C2 reservoir / D2 plate / A3 trash).

## Constraints
- Follow simulation gate and opt-in live rules.
- Precious / quantitative wells must not be blindly topped up.
- Vision is observation-only; deck truth from reconcile / robot APIs.
- Tip hygiene: tips that contact sample liquid must not re-enter common stocks; same-buffer path may continue on the same tip.

# Agent Reference Protocols

These small protocols are stable starting points for Codex and Claude Code workflows.

Use them when you need a known-good local example before drafting or repairing a real lab workflow:

- `ot2_minimal_transfer.py` - minimal OT-2 transfer example
- `flex_minimal_transfer.py` - minimal Flex transfer example that should be easy to analyze or simulate
- `flex_tip_recovery_reference.py` - minimal Flex recovery-oriented example for tip pickup troubleshooting

Recommended workflow:

1. Search the bundled reference library with `skills/opentrons-protocol-library/scripts/search_protocols.py`
2. Inspect a matching real protocol with `show` or `snippet`
3. Start from one of these small reference protocols when you need a clean runnable baseline
4. Run `doctor`, then `analyze` or `simulate`, before any live robot execution

Example commands:

```bash
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py search "serial dilution"
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py show 00222e
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py snippet 00222e serial plasma
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py analyze examples/reference-protocols/ot2_minimal_transfer.py -- --check
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py simulate examples/reference-protocols/flex_minimal_transfer.py
```

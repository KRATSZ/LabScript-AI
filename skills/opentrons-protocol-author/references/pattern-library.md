# Protocol pattern library (Flex-first)

Use these as **starting points** after intent is clear (`opentrons-experiment-intent-review`). Copy the skeleton into a new file and adjust slots, volumes, and well lists.

| Pattern | Starting point | Notes |
|--------|----------------|--------|
| Flex default skeleton | `../assets/flex_protocol_template.py` | Trash + Flex 96-tip + reservoir + 96-well plate |
| Cell culture passaging | `../assets/flex_template_cell_culture_passaging.py` | 6-well passaging template with 2 mm bottom clearance default |
| PCR setup | `../assets/flex_template_pcr_setup.py` | Master mix + sample addition with tip budget notes |
| Serial dilution | `../assets/flex_template_serial_dilution.py` | Row-based dilution chain with primed starting well |
| OT-2 generic skeleton | `../assets/protocol_template.py` | Legacy OT-2 deck model |
| GY / arbitrary well pattern | `../../../protocols/gy_pattern_protocol.py` | Validated Flex example: reservoir → cherry-pick wells |
| No-op / connectivity | `../../../mcp-servers/opentrons-mcp/examples/flex_noop_protocol.py` | Minimal Flex run |
| Tip recovery exercise | `../../../mcp-servers/opentrons-mcp/examples/flex_tip_recovery_validation.py` | For recovery testing only |

When adding new validated patterns, extend this table and keep **one** canonical `.py` per pattern in `protocols/` or `examples/`.

## Workflow-specific step checklists

When writing protocols for these common workflows, ensure the following steps are included even if the question doesn't mention them:

### Magnetic bead extraction (DNA/RNA)

Standard sub-steps in order:
1. **Bind** — mix sample with beads, incubate with mid-run mixing.
2. **Separate** — move plate onto magnetic block, wait for clear supernatant (1-5 min).
3. **Supernatant removal** — slow aspirate from well bottom edge, avoid bead pellet.
4. **Wash × 2-3** — add wash buffer (typically 70-80% ethanol), resuspend off-magnet, separate on-magnet, remove supernatant.
5. **Dry** — after final wash, air-dry beads on magnet for **2-5 min**. This evaporates residual ethanol which would otherwise inhibit downstream enzyme reactions. **Do not skip this step.**
6. **Elute** — remove plate from magnet, add elution buffer (TE or nuclease-free water), resuspend beads, incubate.
7. **Final separate** — place back on magnet, transfer eluate to clean destination.

Common mistakes to avoid:
- Omitting the drying step after ethanol washes.
- Using P1000 for bead volumes below 50 µL without accuracy note.
- Discarding liquid waste by dropping tips into trash bin — for large-volume protocols, track total liquid waste and warn about bin overflow.

### Serial dilution

- Pre-load **2× transfer volume** into the starting column so 1× remains after the first transfer — this preserves the undiluted stock as a control/reference.
- Document in `key_decisions` whether the starting column is retained or fully transferred out.

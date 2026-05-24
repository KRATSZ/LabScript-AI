# Plate Transfer

- Declare source plate, destination plate, reservoirs, tube racks, tip racks, and instruments in `manifest.deck`.
- Keep well maps deterministic and easy to inspect.
- Use single-channel pipettes for irregular layouts and multichannel only for clear column-wise transfers.
- Count tips from the loop structure and set `manifest.tips.tips_required` and `tips_available`.
- Include waste or off-platform handoff notes when liquid is aspirated away or an external reader is required.
- Avoid assigning two physical items to the same deck slot.

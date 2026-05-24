# Dilution

- Choose labware that separates stock, diluent, and destinations clearly.
- Calculate stock and diluent volumes before writing loops.
- Keep every reagent total in `manifest.reagents` aligned with actual transfers.
- Use `p20_single_gen2` for small stock additions and `p300_single_gen2` for larger buffer additions.
- Add mix steps after combining stock and diluent when the task asks for working solutions.
- Avoid hidden volume assumptions; name stock concentration, final concentration, and final volume in comments or setup notes.

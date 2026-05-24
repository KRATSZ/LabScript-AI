# Normalization

- Compute sample volume from target mass and measured concentration.
- Reject or pause on missing, zero, or too-low concentration values instead of silently using bad inputs.
- Compute diluent volume as final volume minus sample volume and guard negative results.
- Use a water or buffer reservoir for backfill and a destination plate for normalized samples.
- Keep concentration assumptions and calculation formulas visible in comments or runbook text.
- Reflect sample and diluent totals in `manifest.reagents`.

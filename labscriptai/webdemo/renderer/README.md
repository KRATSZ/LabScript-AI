# Bundled protocol renderer

This directory is the product's self-contained MuJoCo renderer for the two
machines currently accepted by the web demo: `OT-2 Standard` and `OT-3
Standard` (Flex). `sim.web_player` selects the machine at the analysis
boundary. The legacy `sim.flex_*` helpers remain separate from the newer
`sim.flex3d_runtime` namespace, so OT-2 and Flex do not silently share the
wrong scene or motion model.

`npm run dev` uses this renderer by default. `LABSCRIPTAI_PLAYER_ROOT` is an
explicit local-development override. Sibling `virtual-lab` locations are only
compatibility fallbacks for an older checkout; a normal product checkout does
not require them.

The renderer process uses the same `LABSCRIPTAI_PYTHON` interpreter as the
code service. Install its runtime with
`python3 -m pip install -r renderer/requirements.txt`; the file pins the
supported ranges for `mujoco`, `numpy`, `Pillow`, and `opentrons`.
Opentrons 8.8.2 is the maintained QA target. The OT-2 `.py` entrypoint uses
the public Opentrons 8.x `analyze --check` CLI with `OPENTRONS_PYTHON` or the
current interpreter. Flex replays an existing analysis JSON through its
loader; loader errors reject invalid input, and Flex does not use the OT-2
`--check` path. There is no private analyzer or neighboring project
requirement.

The OT-2 replay currently covers 12 pipette models and 5 module definitions.
Air gaps and aspirates above a well opening remain explicit air segments, and
full or supported axis-home commands are animated. Unknown actions, module
commands, addressable areas, home axes, or model names are rejected rather
than silently approximated. Flex partial nozzle layouts are explicitly
unsupported; full `ALL` layouts remain available. Flex `touchTip` is shown as a
text-only action with a visible range warning. Motion/ramp durations are
illustrative; explicit waits and thermal holds retain their input durations.

Generated XML, meshes, JPEGs and traces are written to
`webdemo/.local/renderer` by the dev launcher, or to the directory named by
`LABSCRIPTAI_RENDERER_EXPORT`. The renderer-local `exports/` fallback is
gitignored for direct Python use. Protocol/model `warnings` are surfaced in
the info response and make validation partial; they describe digital replay
limitations. Static definition-envelope overlap is a partial warning, not a
precise continuous collision certification; the renderer never certifies
physical clearance or hardware acceptance.

The bundle is a checked-in snapshot of the renderer source. After a reviewed
source-runtime change, maintainers can refresh it with:

```bash
node scripts/sync-renderer.mjs --source /path/to/virtual-lab
```

The sync script copies only the runtime and loader-traced assets listed in
`SOURCE.json`, then reapplies the bundle's cache and interpreter defaults. It
does not copy generated reports, reference photos, STEP/DXF files,
Blender/GLB duplicates, module STL duplicates, or caches. The renderer-root
precedence check is runnable without Python or MuJoCo:
`node --test scripts/renderer-root.test.mjs`.

The earlier `renderer-patches/` and UX records are retained as historical
evidence from the external-renderer workflow. They are not prerequisites for
this bundled runtime and should not be applied to it.

Asset/runtime provenance: the isolated Flex runtime was adapted from
reference commit `a3182eb5befc8ce535c33a225ae80b287e87c211`; device/model work
cites Gao et al., bioRxiv DOI
[10.1101/2025.09.30.679666](https://doi.org/10.1101/2025.09.30.679666).
The detailed module manifest preserves its upstream Opentrons source fields.

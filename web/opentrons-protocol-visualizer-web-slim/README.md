# Opentrons Slim Bundle

This archive contains only the protocol-visualizer web slice of the monorepo.

Included:
- `api`
- `components`
- `shared-data`
- `step-generation`
- `protocol-visualizer-web`

Excluded:
- `node_modules`
- `.venv`
- build and cache directories
- tests and docs not needed for the demo app

## Quick start

```bash
make setup
make dev-api
make dev-client
```

If the analyzer Python environment is missing, run:

```bash
make -C api setup
```

For the app-specific details, see `protocol-visualizer-web/README.md`.

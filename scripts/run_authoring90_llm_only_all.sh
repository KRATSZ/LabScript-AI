#!/usr/bin/env bash
# Run both frontier models sequentially, then build TABLE_LLM_ONLY.md.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
./scripts/run_authoring90_llm_only_parallel.sh gpt-5.5
./scripts/run_authoring90_llm_only_parallel.sh gemini-3.5-flash
PYTHONPATH=src uv run python scripts/build_table_llm_only.py runs/authoring90/llm_only

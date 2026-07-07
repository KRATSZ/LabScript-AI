#!/usr/bin/env bash
# Panel review for Table 1 v3 fair rows missing 3-reviewer scores.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TASKS="benchmarks/authoring/tasks.yaml"
PANEL="benchmarks/authoring/review_panel_30.json"
PANEL_DEEPSEEK_MODEL="${PANEL_DEEPSEEK_MODEL:-deepseek-v4-pro}"
PANEL_GPT_MODEL="${PANEL_GPT_MODEL:-gpt-5.4}"
PANEL_GEMINI_MODEL="${PANEL_GEMINI_MODEL:-gemini-3.5-flash}"

RUN_ROOTS=(
  "runs/table1_v3_fair/flash_seed01"
  "runs/table1_v3_fair/codex_gpt55_fair"
  "runs/table1_v3_fair/claude_opus48_tight_fair"
)

REVIEWERS=(
  "expert_review_panel_deepseek|DEEPSEEK|${PANEL_DEEPSEEK_MODEL}|1024"
  "expert_review_panel_gpt|LLM_ONLY|${PANEL_GPT_MODEL}|1024"
  "expert_review_panel_gemini|LLM_ONLY|${PANEL_GEMINI_MODEL}|8192"
)

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

review_ok_count() {
  python3 - "$1" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
print(json.loads(path.read_text()).get("review_ok_count", 0) if path.exists() else 0)
PY
}

failures=0
for run_root in "${RUN_ROOTS[@]}"; do
  echo "=== ${run_root} ==="
  for spec in "${REVIEWERS[@]}"; do
    IFS='|' read -r subdir api_prefix model max_tokens <<<"$spec"
    summary="${run_root}/summary.json"
    review_dir="${run_root}/${subdir}"
    review_summary="${review_dir}/review-summary.json"
    existing_ok="$(review_ok_count "$review_summary")"
    if [[ "$existing_ok" == "30" && "${FORCE_PANEL_REVIEW:-0}" != "1" ]]; then
      echo "skip ${run_root}/${subdir} (${existing_ok}/30)"
      continue
    fi
    if [[ "$api_prefix" == "DEEPSEEK" ]]; then
      export DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
      export DEEPSEEK_MODEL="$model"
      export DEEPSEEK_MAX_TOKENS="$max_tokens"
      export DEEPSEEK_TRANSPORT_RETRIES="${PANEL_DEEPSEEK_TRANSPORT_RETRIES:-5}"
    else
      export LLM_ONLY_BASE_URL="${LLM_ONLY_BASE_URL:-https://api.vectorengine.ai/v1}"
      export LLM_ONLY_MODEL="$model"
      export LLM_ONLY_MAX_TOKENS="$max_tokens"
      export LLM_ONLY_TRANSPORT_RETRIES="${PANEL_LLM_ONLY_TRANSPORT_RETRIES:-5}"
    fi
    echo "review ${run_root}/${subdir} model=${model}"
    if ! PYTHONPATH=src uv run python -m labscriptai.benchmark.review_authoring_run \
      "$summary" \
      --tasks "$TASKS" \
      --output-dir "$review_dir" \
      --api-prefix "$api_prefix" \
      --reviewer-model "$model" \
      --panel "$PANEL"; then
      echo "command failed: ${run_root}/${subdir}" >&2
      failures=$((failures + 1))
      continue
    fi
    existing_ok="$(review_ok_count "$review_summary")"
    echo "done ${run_root}/${subdir} (${existing_ok}/30)"
    if [[ "$existing_ok" != "30" ]]; then
      failures=$((failures + 1))
    fi
  done
done

PYTHONPATH=src:. uv run python scripts/build_table1_v2.py
if [[ "$failures" != "0" ]]; then
  echo "Finished with ${failures} incomplete reviewer jobs." >&2
  exit 1
fi
echo "All v3 fair panel reviews complete."

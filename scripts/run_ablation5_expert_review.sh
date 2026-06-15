#!/usr/bin/env bash
set -euo pipefail

RUN_ROOT="${1:-runs/authoring90/ablation5_20260529}"
MODE="${2:-full}"          # smoke or full
MODEL_FILTER="${3:-both}"  # both, flash, or pro
ROW_FILTER="${4:-all}"     # all or one row name

TASKS="${TASKS:-benchmarks/authoring/tasks.yaml}"
REVIEWER_MODEL="${REVIEWER_MODEL:-deepseek-v4-pro}"
DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-$REVIEWER_MODEL}"
DEEPSEEK_TIMEOUT_SEC="${DEEPSEEK_TIMEOUT_SEC:-180}"
DEEPSEEK_MAX_TOKENS="${DEEPSEEK_MAX_TOKENS:-1024}"
export DEEPSEEK_BASE_URL DEEPSEEK_MODEL DEEPSEEK_TIMEOUT_SEC DEEPSEEK_MAX_TOKENS

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a
  source .env
  set +a
fi

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is not set" >&2
  exit 2
fi

if [[ "${DEEPSEEK_BASE_URL%/}" != "https://api.deepseek.com" ]]; then
  echo "Refusing non-official DeepSeek base URL: ${DEEPSEEK_BASE_URL}" >&2
  exit 2
fi

case "$MODE" in
  smoke) LIMIT_ARGS=(--limit "${SMOKE_LIMIT:-3}") ;;
  full) LIMIT_ARGS=() ;;
  *) echo "MODE must be smoke or full, got: $MODE" >&2; exit 2 ;;
esac

MODELS=(flash pro)
ROWS=(llm_direct no_kb_patch kb_v2_patch kb_v2_rewrite no_repair)

review_ok_count() {
  local review_summary="$1"
  python3 - "$review_summary" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    print("")
else:
    try:
        print(json.loads(p.read_text()).get("review_ok_count", ""))
    except Exception:
        print("")
PY
}

summary_task_count() {
  local summary="$1"
  python3 - "$summary" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    print("")
else:
    print(json.loads(p.read_text()).get("task_count", ""))
PY
}

for model in "${MODELS[@]}"; do
  if [[ "$MODEL_FILTER" != "both" && "$MODEL_FILTER" != "$model" ]]; then
    continue
  fi
  for row in "${ROWS[@]}"; do
    if [[ "$ROW_FILTER" != "all" && "$ROW_FILTER" != "$row" ]]; then
      continue
    fi

    row_dir="$RUN_ROOT/$model/$row"
    summary="$row_dir/summary.json"
    analysis="$row_dir/analysis/attribution-summary.json"
    review_dir="$row_dir/expert_review"
    review_summary="$review_dir/review-summary.json"

    if [[ ! -f "$summary" ]]; then
      echo "missing summary: $summary" >&2
      exit 1
    fi
    tasks="$(summary_task_count "$summary")"
    if [[ "$tasks" != "90" ]]; then
      echo "expected task_count=90 for $row_dir, got: $tasks" >&2
      exit 1
    fi
    if [[ ! -f "$analysis" ]]; then
      mkdir -p "$row_dir/analysis"
      PYTHONPATH=src uv run python -m labscriptai.benchmark.analyze_authoring_run \
        "$summary" --tasks "$TASKS" --output-dir "$row_dir/analysis"
    fi

    existing_ok="$(review_ok_count "$review_summary")"
    if [[ "$MODE" == "full" && "$existing_ok" == "90" && "${FORCE_REVIEW:-0}" != "1" ]]; then
      echo "skip provider-clean expert review: $row_dir"
      continue
    fi
    if [[ "$MODE" == "smoke" && "$existing_ok" == "${SMOKE_LIMIT:-3}" && "${FORCE_REVIEW:-0}" != "1" ]]; then
      echo "skip smoke expert review: $row_dir"
      continue
    fi

    echo "review $MODE $model/$row"
    PYTHONPATH=src uv run python -m labscriptai.benchmark.review_authoring_run \
      "$summary" --tasks "$TASKS" \
      --output-dir "$review_dir" \
      --reviewer-model "$REVIEWER_MODEL" \
      "${LIMIT_ARGS[@]}"
  done
done

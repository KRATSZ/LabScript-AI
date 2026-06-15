#!/usr/bin/env bash
# Run 30-task panel reviews (GPT + Gemini via LLM_ONLY_*) for all ablation5 rows.
set -euo pipefail

RUN_ROOT="${1:-runs/authoring90/ablation5_20260529}"
MODEL_FILTER="${2:-both}"  # both | flash | pro
REVIEWER_FILTER="${3:-both}"  # both | gpt | gemini

TASKS="${TASKS:-benchmarks/authoring/tasks.yaml}"
PANEL="${PANEL:-benchmarks/authoring/review_panel_30.json}"
PANEL_GPT_MODEL="${PANEL_GPT_MODEL:-gpt-5.4}"
# Gateway accepts gemini-3.5-flash (gemini-3-flash returns 503 on LLM_ONLY).
PANEL_GEMINI_MODEL="${PANEL_GEMINI_MODEL:-gemini-3.5-flash}"

# Do not clobber inline gateway overrides (e.g. VectorEngine base URL + key).
if [[ -f .env ]] && [[ -z "${LLM_ONLY_API_KEY:-}" ]] && [[ -z "${LLM_ONLY_BASE_URL:-}" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${LLM_ONLY_API_KEY:-}" ]]; then
  echo "LLM_ONLY_API_KEY is required for panel reviewers." >&2
  exit 2
fi

export LLM_ONLY_TIMEOUT_SEC="${LLM_ONLY_TIMEOUT_SEC:-240}"
# gemini-3.5-flash on VectorEngine truncates JSON at 1024; panel reviews need headroom.
if [[ "$REVIEWER_FILTER" == "gemini" || "$REVIEWER_FILTER" == "both" ]]; then
  export LLM_ONLY_MAX_TOKENS="${LLM_ONLY_MAX_TOKENS:-8192}"
else
  export LLM_ONLY_MAX_TOKENS="${LLM_ONLY_MAX_TOKENS:-1024}"
fi
export LLM_ONLY_TRANSPORT_RETRIES="${LLM_ONLY_TRANSPORT_RETRIES:-5}"

MODELS=(flash pro)
ROWS=(llm_direct no_kb_patch kb_v2_patch kb_v2_rewrite no_repair)

panel_ok_count() {
  local review_summary="$1"
  python3 - "$review_summary" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    print("")
else:
    print(json.loads(p.read_text()).get("review_ok_count", ""))
PY
}

run_panel_reviewer() {
  local row_dir="$1"
  local summary="$2"
  local output_subdir="$3"
  local model="$4"
  local review_dir="$row_dir/$output_subdir"
  local review_summary="$review_dir/review-summary.json"
  local expected
  expected="$(PANEL_FILE="$PANEL" python3 -c 'import json, os; print(len(json.load(open(os.environ["PANEL_FILE"]))["task_ids"]))')"

  existing_ok="$(panel_ok_count "$review_summary")"
  if [[ "$existing_ok" == "$expected" && "${FORCE_PANEL_REVIEW:-0}" != "1" ]]; then
    echo "skip panel $output_subdir: $row_dir ($existing_ok/$expected)"
    return 0
  fi

  echo "panel review $output_subdir ($model) -> $row_dir"
  export LLM_ONLY_MODEL="$model"
  PYTHONPATH=src uv run python -m labscriptai.benchmark.review_authoring_run \
    "$summary" \
    --tasks "$TASKS" \
    --output-dir "$review_dir" \
    --api-prefix LLM_ONLY \
    --reviewer-model "$model" \
    --panel "$PANEL"
}

for model in "${MODELS[@]}"; do
  if [[ "$MODEL_FILTER" != "both" && "$MODEL_FILTER" != "$model" ]]; then
    continue
  fi
  for row in "${ROWS[@]}"; do
    row_dir="$RUN_ROOT/$model/$row"
    summary="$row_dir/summary.json"
    if [[ ! -f "$summary" ]]; then
      echo "missing summary: $summary" >&2
      exit 1
    fi
    if [[ "$REVIEWER_FILTER" == "both" || "$REVIEWER_FILTER" == "gpt" ]]; then
      run_panel_reviewer "$row_dir" "$summary" "expert_review_panel_gpt" "$PANEL_GPT_MODEL"
    fi
    if [[ "$REVIEWER_FILTER" == "both" || "$REVIEWER_FILTER" == "gemini" ]]; then
      run_panel_reviewer "$row_dir" "$summary" "expert_review_panel_gemini" "$PANEL_GEMINI_MODEL"
    fi
  done
done

# Second pass: resume any row/reviewer pair that did not reach a full 30-task panel.
for model in "${MODELS[@]}"; do
  if [[ "$MODEL_FILTER" != "both" && "$MODEL_FILTER" != "$model" ]]; then
    continue
  fi
  for row in "${ROWS[@]}"; do
    row_dir="$RUN_ROOT/$model/$row"
    summary="$row_dir/summary.json"
    [[ -f "$summary" ]] || continue
    if [[ "$REVIEWER_FILTER" == "both" || "$REVIEWER_FILTER" == "gpt" ]]; then
      existing_ok="$(panel_ok_count "$row_dir/expert_review_panel_gpt/review-summary.json")"
      if [[ "$existing_ok" != "$(PANEL_FILE="$PANEL" python3 -c 'import json, os; print(len(json.load(open(os.environ["PANEL_FILE"]))["task_ids"]))')" ]]; then
        run_panel_reviewer "$row_dir" "$summary" "expert_review_panel_gpt" "$PANEL_GPT_MODEL"
      fi
    fi
    if [[ "$REVIEWER_FILTER" == "both" || "$REVIEWER_FILTER" == "gemini" ]]; then
      existing_ok="$(panel_ok_count "$row_dir/expert_review_panel_gemini/review-summary.json")"
      if [[ "$existing_ok" != "$(PANEL_FILE="$PANEL" python3 -c 'import json, os; print(len(json.load(open(os.environ["PANEL_FILE"]))["task_ids"]))')" ]]; then
        run_panel_reviewer "$row_dir" "$summary" "expert_review_panel_gemini" "$PANEL_GEMINI_MODEL"
      fi
    fi
  done
done

PYTHONPATH=src:. uv run python scripts/build_authoring90_ablation5_report.py "$RUN_ROOT"
PYTHONPATH=src:. uv run python scripts/build_panel_reviewer_correlation.py "$RUN_ROOT"
echo "Done panel reviews: $RUN_ROOT"

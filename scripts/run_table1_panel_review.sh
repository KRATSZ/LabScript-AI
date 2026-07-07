#!/usr/bin/env bash
# Run Table 1 30-task panel reviews across the fixed 9 completed run roots.
set -euo pipefail
trap 'echo "Interrupted Table 1 panel review." >&2; exit 130' INT TERM

MODE="${1:-full}"              # full | smoke | status
RUN_FILTER="${2:-all}"         # all | exact run root
REVIEWER_FILTER="${3:-all}"    # all | deepseek | gpt | gemini

TASKS="${TASKS:-benchmarks/authoring/tasks.yaml}"
PANEL="${PANEL:-benchmarks/authoring/review_panel_30.json}"
SMOKE_TASK_IDS="${SMOKE_TASK_IDS:-T001,T020,T056}"

PANEL_DEEPSEEK_MODEL="${PANEL_DEEPSEEK_MODEL:-deepseek-v4-pro}"
PANEL_GPT_MODEL="${PANEL_GPT_MODEL:-gpt-5.4}"
PANEL_GPT_FALLBACK_MODEL="${PANEL_GPT_FALLBACK_MODEL-gpt-5.5}"
PANEL_GEMINI_MODEL="${PANEL_GEMINI_MODEL:-gemini-3-flash}"
PANEL_GEMINI_FALLBACK_MODEL="${PANEL_GEMINI_FALLBACK_MODEL-gemini-3.5-flash}"
PANEL_RETRY_PASSES="${PANEL_RETRY_PASSES:-2}"
PANEL_ABORT_ON_COMMAND_FAILURE="${PANEL_ABORT_ON_COMMAND_FAILURE:-1}"
PANEL_DEEPSEEK_TRANSPORT_RETRIES="${PANEL_DEEPSEEK_TRANSPORT_RETRIES:-5}"
PANEL_LLM_ONLY_TRANSPORT_RETRIES="${PANEL_LLM_ONLY_TRANSPORT_RETRIES:-5}"

RUN_ROOTS=(
  "runs/table1_v3_fair/flash_seed01"
  "runs/table1_v3_fair/codex_gpt55_fair"
  "runs/table1_v3_fair/claude_opus48_tight_fair"
  "runs/table1_v2_unified_opus_48"
  "runs/authoring90/ablation5_20260529/flash/kb_v2_patch"
  "runs/authoring90/llm_only/claude-opus-4-8"
  "runs/authoring90_native_agents/codex_gpt55_py_only_v1"
  "runs/table1_v2_llm_only_py90_official_deepseek_final"
  "runs/authoring90/llm_only/gemini-3.5-flash"
  "runs/authoring90/llm_only/gpt-5.5_vector"
  "runs/authoring90_native_agents/claude_opus48_pyonly_tight_v2"
  "runs/authoring90_native_agents/claude_opus48_native_open_v1"
  "runs/authoring90/opentrons_ai_v1"
  "runs/authoring90/inagaki_style/gpt-4-fixloop-v2"
)

case "$MODE" in
  full) REVIEW_SELECTION_ARGS=(--panel "$PANEL") ;;
  smoke) REVIEW_SELECTION_ARGS=(--task-ids "$SMOKE_TASK_IDS") ;;
  status) REVIEW_SELECTION_ARGS=() ;;
  *) echo "MODE must be full, smoke, or status; got: $MODE" >&2; exit 2 ;;
esac

case "$REVIEWER_FILTER" in
  all | deepseek | gpt | gemini) ;;
  *) echo "REVIEWER_FILTER must be all, deepseek, gpt, or gemini; got: $REVIEWER_FILTER" >&2; exit 2 ;;
esac

load_dotenv_no_override() {
  local env_file="${1:-.env}"
  [[ -f "$env_file" ]] || return 0
  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -n "$line" && "${line:0:1}" != "#" ]] || continue
    if [[ "$line" == export[[:space:]]* ]]; then
      line="${line#export }"
    fi
    [[ "$line" == *"="* ]] || continue
    key="${line%%=*}"
    value="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    if [[ -n "$key" && -z "${!key+x}" ]]; then
      export "$key=$value"
    fi
  done < "$env_file"
}

load_dotenv_no_override ".env"

expected_count() {
  python3 - "$MODE" "$PANEL" "$SMOKE_TASK_IDS" <<'PY'
import json
import sys
from pathlib import Path

mode, panel, smoke_ids = sys.argv[1:4]
if mode == "smoke":
    print(len([item.strip() for item in smoke_ids.split(",") if item.strip()]))
else:
    print(len(json.loads(Path(panel).read_text(encoding="utf-8"))["task_ids"]))
PY
}

EXPECTED="$(expected_count)"

review_ok_count() {
  local review_summary="$1"
  python3 - "$review_summary" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("")
else:
    try:
        print(json.loads(path.read_text(encoding="utf-8")).get("review_ok_count", ""))
    except Exception:
        print("")
PY
}

clean_review_files() {
  local review_dir="$1"
  python3 - "$review_dir" "$MODE" "$PANEL" "$SMOKE_TASK_IDS" <<'PY'
import json
import sys
from pathlib import Path

review_dir = Path(sys.argv[1])
mode, panel, smoke_ids = sys.argv[2:5]
if mode == "smoke":
    task_ids = [item.strip() for item in smoke_ids.split(",") if item.strip()]
else:
    task_ids = json.loads(Path(panel).read_text(encoding="utf-8"))["task_ids"]
for task_id in task_ids:
    (review_dir / f"{task_id}-review.json").unlink(missing_ok=True)
(review_dir / "review-summary.json").unlink(missing_ok=True)
(review_dir / "review-summary.md").unlink(missing_ok=True)
PY
}

preflight_package_dirs() {
  local summary="$1"
  python3 - "$summary" "$MODE" "$PANEL" "$SMOKE_TASK_IDS" <<'PY'
import json
import os
import sys
from pathlib import Path

summary = Path(sys.argv[1])
mode, panel, smoke_ids = sys.argv[2:5]
if mode == "smoke":
    task_ids = [item.strip() for item in smoke_ids.split(",") if item.strip()]
else:
    task_ids = json.loads(Path(panel).read_text(encoding="utf-8"))["task_ids"]
payload = json.loads(summary.read_text(encoding="utf-8"))
records = {
    str(record.get("task_id")): record
    for record in payload.get("records", [])
    if isinstance(record, dict)
}
missing_records = [task_id for task_id in task_ids if task_id not in records]
missing_protocols = []
for task_id in task_ids:
    record = records.get(task_id)
    if not record:
        continue
    package_dir = record.get("package_dir")
    if not isinstance(package_dir, str) or not (Path(package_dir) / "protocol.py").is_file():
        missing_protocols.append((task_id, package_dir))
if missing_records:
    print(f"missing selected records in {summary}: {','.join(missing_records)}", file=sys.stderr)
    sys.exit(3)
if missing_protocols:
    joined = "; ".join(f"{task_id} package_dir={package_dir}" for task_id, package_dir in missing_protocols)
    print(f"warning: selected package protocol.py missing in {summary}: {joined}", file=sys.stderr)
    if os.environ.get("PANEL_STRICT_PACKAGE", "0") == "1":
        sys.exit(3)
PY
}

ensure_credentials() {
  local api_prefix="$1"
  case "$api_prefix" in
    DEEPSEEK)
      export DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
      export DEEPSEEK_TIMEOUT_SEC="${DEEPSEEK_TIMEOUT_SEC:-240}"
      export DEEPSEEK_MAX_TOKENS="${DEEPSEEK_MAX_TOKENS:-1024}"
      export DEEPSEEK_TRANSPORT_RETRIES="$PANEL_DEEPSEEK_TRANSPORT_RETRIES"
      if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
        echo "DEEPSEEK_API_KEY is required for DeepSeek panel review." >&2
        exit 2
      fi
      if [[ "${DEEPSEEK_BASE_URL%/}" != "https://api.deepseek.com" ]]; then
        echo "Refusing non-official DeepSeek base URL: ${DEEPSEEK_BASE_URL}" >&2
        exit 2
      fi
      ;;
    LLM_ONLY)
      export LLM_ONLY_BASE_URL="${LLM_ONLY_BASE_URL:-https://api.vectorengine.ai/v1}"
      export LLM_ONLY_TIMEOUT_SEC="${LLM_ONLY_TIMEOUT_SEC:-240}"
      export LLM_ONLY_TRANSPORT_RETRIES="$PANEL_LLM_ONLY_TRANSPORT_RETRIES"
      if [[ -z "${LLM_ONLY_API_KEY:-}" ]]; then
        echo "LLM_ONLY_API_KEY is required for GPT/Gemini panel review." >&2
        exit 2
      fi
      ;;
    *) echo "unknown api prefix: $api_prefix" >&2; exit 2 ;;
  esac
}

run_review_command() {
  local summary="$1"
  local review_dir="$2"
  local api_prefix="$3"
  local model="$4"
  local max_tokens="$5"
  ensure_credentials "$api_prefix"
  if [[ "$api_prefix" == "LLM_ONLY" ]]; then
    export LLM_ONLY_MODEL="$model"
    export LLM_ONLY_MAX_TOKENS="$max_tokens"
  else
    export DEEPSEEK_MODEL="$model"
    export DEEPSEEK_MAX_TOKENS="$max_tokens"
  fi
  PYTHONPATH=src uv run python -m labscriptai.benchmark.review_authoring_run \
    "$summary" \
    --tasks "$TASKS" \
    --output-dir "$review_dir" \
    --api-prefix "$api_prefix" \
    --reviewer-model "$model" \
    "${REVIEW_SELECTION_ARGS[@]}"
}

run_panel_reviewer() {
  local run_root="$1"
  local output_subdir="$2"
  local api_prefix="$3"
  local model="$4"
  local max_tokens="$5"
  local fallback_model="${6:-}"
  local summary="$run_root/summary.json"
  local review_dir="$run_root/$output_subdir"
  local review_summary="$review_dir/review-summary.json"
  local existing_ok

  if [[ ! -f "$summary" ]]; then
    echo "missing summary: $summary" >&2
    return 1
  fi
  preflight_package_dirs "$summary"

  existing_ok="$(review_ok_count "$review_summary")"
  if [[ "$existing_ok" == "$EXPECTED" && "${FORCE_PANEL_REVIEW:-0}" != "1" ]]; then
    echo "skip $output_subdir: $run_root ($existing_ok/$EXPECTED)"
    return 0
  fi

  if [[ "${FORCE_PANEL_REVIEW:-0}" == "1" ]]; then
    clean_review_files "$review_dir"
  fi

  echo "panel review $output_subdir ($model) -> $run_root"
  local rc
  run_review_command "$summary" "$review_dir" "$api_prefix" "$model" "$max_tokens" || rc=$?
  rc="${rc:-0}"
  if [[ "$rc" == "130" || "$rc" == "131" || "$rc" == "143" ]]; then
    return "$rc"
  fi
  if [[ "$rc" != "0" ]]; then
    echo "review command failed for $output_subdir: $run_root (exit $rc)" >&2
    return "$rc"
  fi

  existing_ok="$(review_ok_count "$review_summary")"
  local retry_pass=1
  while [[ "$existing_ok" != "$EXPECTED" && "$retry_pass" -le "$PANEL_RETRY_PASSES" ]]; do
    echo "retry $output_subdir with same model $model: $run_root ($existing_ok/$EXPECTED), pass $retry_pass/$PANEL_RETRY_PASSES"
    rc=0
    run_review_command "$summary" "$review_dir" "$api_prefix" "$model" "$max_tokens" || rc=$?
    if [[ "$rc" == "130" || "$rc" == "131" || "$rc" == "143" ]]; then
      return "$rc"
    fi
    if [[ "$rc" != "0" ]]; then
      echo "review retry failed for $output_subdir: $run_root (exit $rc)" >&2
      return "$rc"
    fi
    existing_ok="$(review_ok_count "$review_summary")"
    retry_pass=$((retry_pass + 1))
  done

  if [[ "$existing_ok" != "$EXPECTED" && -n "$fallback_model" && "$fallback_model" != "$model" && "${PANEL_ALLOW_MODEL_FALLBACK:-1}" != "0" ]]; then
    echo "fallback $output_subdir: $model reached $existing_ok/$EXPECTED; retrying clean with $fallback_model"
    clean_review_files "$review_dir"
    rc=0
    run_review_command "$summary" "$review_dir" "$api_prefix" "$fallback_model" "$max_tokens" || rc=$?
    if [[ "$rc" == "130" || "$rc" == "131" || "$rc" == "143" ]]; then
      return "$rc"
    fi
    if [[ "$rc" != "0" ]]; then
      echo "fallback review failed for $output_subdir: $run_root (exit $rc)" >&2
      return "$rc"
    fi
    existing_ok="$(review_ok_count "$review_summary")"
  fi

  if [[ "$existing_ok" != "$EXPECTED" ]]; then
    echo "incomplete $output_subdir: $run_root ($existing_ok/$EXPECTED)" >&2
    return 1
  fi
  return 0
}

print_status() {
  local run_root="$1"
  printf '%s\n' "$run_root"
  for subdir in expert_review_panel_deepseek expert_review_panel_gpt expert_review_panel_gemini; do
    local summary="$run_root/$subdir/review-summary.json"
    local ok
    ok="$(review_ok_count "$summary")"
    printf '  %s: %s/%s\n' "$subdir" "${ok:-missing}" "$EXPECTED"
  done
}

run_or_count_failure() {
  local rc
  set +e
  run_panel_reviewer "$@"
  rc=$?
  set -e
  if [[ "$rc" == "130" || "$rc" == "131" || "$rc" == "143" ]]; then
    exit "$rc"
  fi
  if [[ "$rc" != "0" ]]; then
    if [[ "$PANEL_ABORT_ON_COMMAND_FAILURE" == "1" ]]; then
      exit "$rc"
    fi
    failures=$((failures + 1))
  fi
}

matched=0
failures=0
for run_root in "${RUN_ROOTS[@]}"; do
  if [[ "$RUN_FILTER" != "all" && "$RUN_FILTER" != "$run_root" ]]; then
    continue
  fi
  matched=1
  if [[ "$MODE" == "status" ]]; then
    print_status "$run_root"
    continue
  fi
  if [[ "$REVIEWER_FILTER" == "all" || "$REVIEWER_FILTER" == "deepseek" ]]; then
    run_or_count_failure "$run_root" "expert_review_panel_deepseek" "DEEPSEEK" "$PANEL_DEEPSEEK_MODEL" "1024"
  fi
  if [[ "$REVIEWER_FILTER" == "all" || "$REVIEWER_FILTER" == "gpt" ]]; then
    run_or_count_failure "$run_root" "expert_review_panel_gpt" "LLM_ONLY" "$PANEL_GPT_MODEL" "1024" "$PANEL_GPT_FALLBACK_MODEL"
  fi
  if [[ "$REVIEWER_FILTER" == "all" || "$REVIEWER_FILTER" == "gemini" ]]; then
    run_or_count_failure "$run_root" "expert_review_panel_gemini" "LLM_ONLY" "$PANEL_GEMINI_MODEL" "8192" "$PANEL_GEMINI_FALLBACK_MODEL"
  fi
done

if [[ "$matched" == "0" ]]; then
  echo "RUN_FILTER matched no run roots: $RUN_FILTER" >&2
  exit 2
fi

if [[ "$MODE" == "full" && "${REBUILD_TABLE1:-1}" != "0" ]]; then
  PYTHONPATH=src:. uv run python scripts/build_table1_v2.py
fi

if [[ "$failures" != "0" ]]; then
  echo "Done with $failures incomplete reviewer/run pairs." >&2
  exit 1
fi

echo "Done Table 1 panel reviews ($MODE)."

#!/usr/bin/env bash
# Table 1 v2: py-only generation; sidecars are derived from protocol.py.
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: scripts/run_table1_v2_py_benchmark.sh <llm-only|unified> <output-root> [task-ids]

Environment:
  DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL for --api-prefix DEEPSEEK
  or LLM_ONLY_* when API_PREFIX=LLM_ONLY.

Optional:
  TASKS=benchmarks/authoring/tasks.yaml or benchmarks/external_community/tasks.yaml
  API_PREFIX=DEEPSEEK|LLM_ONLY|auto
  SHARD_SIZE=30
  PARALLEL=0|1
  RESUME_TASKS=1 to skip already-complete task records
  REQUIRE_PROVIDER_CLEAN=1 to rerun task records with provider_error_count>0
  CLEAN_RERUNS=3 maximum clean rerun passes per shard
  OPENTRONS_PYTHON=.venv-protocol/bin/python
  SIMULATION_REPAIR_ATTEMPTS=0 for llm-only, 3 for unified
  UNIFIED_TOOL_PROFILE=simulate for no-KB unified ablations
  UNIFIED_KB_CONTEXT_MODE=none for no-KB unified ablations
USAGE
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 2
fi

MODE="$1"
OUT_ROOT="$2"
TASK_IDS="${3:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
mkdir -p "$OUT_ROOT"
OUT_ROOT="$(cd "$OUT_ROOT" && pwd)"

if [[ -f ".env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" == export\ * ]] && line="${line#export }"
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -n "${!key+x}" ]] && continue
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi
    export "$key=$value"
  done < ".env"
fi

API_PREFIX="${API_PREFIX:-DEEPSEEK}"
OPENTRONS_PYTHON="${OPENTRONS_PYTHON:-$REPO_ROOT/.venv-protocol/bin/python}"
SHARD_SIZE="${SHARD_SIZE:-30}"
PARALLEL="${PARALLEL:-0}"
TASKS="${TASKS:-benchmarks/authoring/tasks.yaml}"
RETRY_ATTEMPTS="${RETRY_ATTEMPTS:-2}"
RESUME_TASKS="${RESUME_TASKS:-0}"
REQUIRE_PROVIDER_CLEAN="${REQUIRE_PROVIDER_CLEAN:-0}"
CLEAN_RERUNS="${CLEAN_RERUNS:-3}"

case "$MODE" in
  llm-only)
    PROVIDER="deepseek"
    REPAIR_EDIT_MODE="${REPAIR_EDIT_MODE:-rewrite}"
    MODE_ARGS=(--direct-output-mode protocol --derive-scaffold-id llm-only-py-derived-v2 --scaffold-label llm-only-py-derived-v2 --repair-edit-mode "$REPAIR_EDIT_MODE")
    REPAIR_ATTEMPTS="${SIMULATION_REPAIR_ATTEMPTS:-0}"
    ;;
  unified)
    PROVIDER="labscriptai-unified"
    REPAIR_EDIT_MODE="${REPAIR_EDIT_MODE:-patch_only}"
    UNIFIED_TOOL_PROFILE="${UNIFIED_TOOL_PROFILE:-kb_strong}"
    UNIFIED_KB_CONTEXT_MODE="${UNIFIED_KB_CONTEXT_MODE:-compact_v2}"
    MODE_ARGS=(--derive-from-protocol --derive-scaffold-id agent-py-derived-v2 --scaffold-label unified-py-derived-v2 --tool-profile "$UNIFIED_TOOL_PROFILE" --kb-context-mode "$UNIFIED_KB_CONTEXT_MODE" --repair-edit-mode "$REPAIR_EDIT_MODE")
    REPAIR_ATTEMPTS="${SIMULATION_REPAIR_ATTEMPTS:-3}"
    ;;
  *)
    usage
    exit 2
    ;;
esac

if [[ -z "$TASK_IDS" ]]; then
  TASK_IDS="$(PYTHONPATH=src python3 - "$TASKS" <<'PY'
import sys
from labscriptai.benchmark.tasks import load_authoring_tasks

print(",".join(task.task_id for task in load_authoring_tasks(sys.argv[1])))
PY
)"
fi

python3 - "$TASK_IDS" "$SHARD_SIZE" > "$OUT_ROOT/task_shards.txt" <<'PY'
import sys
ids = [item.strip() for item in sys.argv[1].split(",") if item.strip()]
size = int(sys.argv[2])
for i in range(0, len(ids), size):
    print(",".join(ids[i:i + size]))
PY

task_progress() {
  local shard_dir="$1"
  local ids="$2"
  PYTHONPATH=src python3 - "$shard_dir" "$ids" "$RETRY_ATTEMPTS" "$REQUIRE_PROVIDER_CLEAN" <<'PY'
import sys
from pathlib import Path

from labscriptai.benchmark.run_progress import is_task_record_complete, load_task_record

shard_dir = Path(sys.argv[1])
task_ids = [item.strip() for item in sys.argv[2].split(",") if item.strip()]
retry_attempts = int(sys.argv[3])
require_provider_clean = sys.argv[4] == "1"

completed = []
pending = []
for task_id in task_ids:
    record = load_task_record(shard_dir / task_id / "record.json")
    if record is None or record.get("task_id") != task_id:
        pending.append(task_id)
        continue
    if not is_task_record_complete(record, retry_attempts):
        pending.append(task_id)
        continue
    if require_provider_clean and int(record.get("provider_error_count", 0) or 0) != 0:
        pending.append(task_id)
        continue
    completed.append(task_id)

print(len(completed))
print(",".join(pending))
PY
}

run_shard() {
  local shard_name="$1"
  local ids="$2"
  local shard_dir="$OUT_ROOT/$shard_name"
  local run_ids="$ids"
  local clean_pass=0
  local completed_count pending_ids pilot_status progress
  mkdir -p "$shard_dir"
  while true; do
    if [[ "$RESUME_TASKS" == "1" || "$REQUIRE_PROVIDER_CLEAN" == "1" ]]; then
      progress="$(task_progress "$shard_dir" "$ids")"
      completed_count="$(printf '%s\n' "$progress" | sed -n '1p')"
      pending_ids="$(printf '%s\n' "$progress" | sed -n '2p')"
      if [[ -z "$pending_ids" ]]; then
        echo "[$(date -Iseconds)] $MODE $shard_name complete ($completed_count tasks)"
        break
      fi
      run_ids="$pending_ids"
      clean_pass=$((clean_pass + 1))
      if (( clean_pass > CLEAN_RERUNS )); then
        echo "clean rerun limit reached for $MODE $shard_name; pending: $pending_ids" >&2
        return 1
      fi
      echo "[$(date -Iseconds)] $MODE $shard_name pass $clean_pass pending: $pending_ids"
    else
      echo "[$(date -Iseconds)] $MODE $shard_name"
    fi
    set +e
    PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
      --tasks "$TASKS" \
      --output-dir "$shard_dir" \
      --provider "$PROVIDER" \
      --api-prefix "$API_PREFIX" \
      --task-ids "$run_ids" \
      --simulate \
      --opentrons-python "$OPENTRONS_PYTHON" \
      --simulation-timeout-sec 180 \
      --retry-attempts "$RETRY_ATTEMPTS" \
      --simulation-repair-attempts "$REPAIR_ATTEMPTS" \
      "${MODE_ARGS[@]}" \
      2>&1 | tee -a "$OUT_ROOT/$shard_name.log"
    pilot_status=${PIPESTATUS[0]}
    set -e
    if [[ "$RESUME_TASKS" != "1" && "$REQUIRE_PROVIDER_CLEAN" != "1" ]]; then
      return "$pilot_status"
    fi
    if (( pilot_status != 0 )); then
      echo "authoring_pilot exited with status $pilot_status for $MODE $shard_name" >&2
    fi
  done
}

shard=0
pids=()
while IFS= read -r ids; do
  shard=$((shard + 1))
  shard_name=$(printf "shard%02d" "$shard")
  if [[ "$PARALLEL" == "1" ]]; then
    run_shard "$shard_name" "$ids" &
    pids+=("$!")
  else
    run_shard "$shard_name" "$ids"
  fi
done < "$OUT_ROOT/task_shards.txt"

if [[ "$PARALLEL" == "1" ]]; then
  for pid in "${pids[@]}"; do
    wait "$pid"
  done
fi

PYTHONPATH=src uv run python scripts/summarize_authoring_shards.py "$OUT_ROOT"
echo "Done: $OUT_ROOT"

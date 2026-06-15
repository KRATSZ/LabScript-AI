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
  OPENTRONS_PYTHON=.venv-protocol/bin/python
  SIMULATION_REPAIR_ATTEMPTS=0 for llm-only, 3 for unified
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
OPENTRONS_PYTHON="${OPENTRONS_PYTHON:-.venv-protocol/bin/python}"
SHARD_SIZE="${SHARD_SIZE:-30}"
PARALLEL="${PARALLEL:-0}"
TASKS="${TASKS:-benchmarks/authoring/tasks.yaml}"

case "$MODE" in
  llm-only)
    PROVIDER="deepseek"
    MODE_ARGS=(--direct-output-mode protocol --derive-scaffold-id llm-only-py-derived-v2 --scaffold-label llm-only-py-derived-v2)
    REPAIR_ATTEMPTS="${SIMULATION_REPAIR_ATTEMPTS:-0}"
    ;;
  unified)
    PROVIDER="labscriptai-unified"
    MODE_ARGS=(--derive-from-protocol --derive-scaffold-id agent-py-derived-v2 --scaffold-label unified-py-derived-v2 --tool-profile kb_strong --kb-context-mode compact_v2)
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

mkdir -p "$OUT_ROOT"
python3 - "$TASK_IDS" "$SHARD_SIZE" > "$OUT_ROOT/task_shards.txt" <<'PY'
import sys
ids = [item.strip() for item in sys.argv[1].split(",") if item.strip()]
size = int(sys.argv[2])
for i in range(0, len(ids), size):
    print(",".join(ids[i:i + size]))
PY

run_shard() {
  local shard_name="$1"
  local ids="$2"
  echo "[$(date -Iseconds)] $MODE $shard_name"
  PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
    --tasks "$TASKS" \
    --output-dir "$OUT_ROOT/$shard_name" \
    --provider "$PROVIDER" \
    --api-prefix "$API_PREFIX" \
    --task-ids "$ids" \
    --simulate \
    --opentrons-python "$OPENTRONS_PYTHON" \
    --simulation-timeout-sec 180 \
    --retry-attempts 2 \
    --simulation-repair-attempts "$REPAIR_ATTEMPTS" \
    "${MODE_ARGS[@]}" \
    2>&1 | tee "$OUT_ROOT/$shard_name.log"
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

#!/usr/bin/env bash
set -euo pipefail

OUT_ROOT="${1:-runs/authoring90_native_agents/codex_gpt55_py_only_v1}"
TASKS="benchmarks/authoring/tasks.yaml"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OPENTRONS_PYTHON="${OPENTRONS_PYTHON:-$REPO_ROOT/.venv-protocol/bin/python}"
SCRATCH_BASE="${SCRATCH_BASE:-/tmp/codex-native-agent-pyonly-90}"
CODEX_SHARD_CONCURRENCY="${CODEX_SHARD_CONCURRENCY:-9}"
SIMULATION_REPAIR_ATTEMPTS="${SIMULATION_REPAIR_ATTEMPTS:-0}"
REPAIR_API_PREFIX="${REPAIR_API_PREFIX:-LLM_ONLY}"
REPAIR_MODEL="${REPAIR_MODEL:-gpt-5.5}"
REPAIR_MAX_TOKENS="${REPAIR_MAX_TOKENS:-12000}"

cd "$REPO_ROOT"
mkdir -p "$OUT_ROOT"

task_range() {
  local start="$1"
  local end="$2"
  python3 -c "print(','.join(f'T{i:03d}' for i in range($start, $end + 1)))"
}

declare -a SHARDS=(
  "$(task_range 1 10)"
  "$(task_range 11 20)"
  "$(task_range 21 30)"
  "$(task_range 31 40)"
  "$(task_range 41 50)"
  "$(task_range 51 60)"
  "$(task_range 61 70)"
  "$(task_range 71 80)"
  "$(task_range 81 90)"
)

declare -a PIDS=()
for i in "${!SHARDS[@]}"; do
  shard=$(printf "shard%02d" "$((i + 1))")
  echo "[$(date -Iseconds)] starting $shard"
  (
    PYTHONPATH=src python3 scripts/run_codex_authoring_baseline.py \
      --task-ids "${SHARDS[$i]}" \
      --output-dir "$OUT_ROOT/$shard" \
      --scratch-root "$SCRATCH_BASE/$shard" \
      --timeout-sec 1800 \
      --protocol-only \
      --simulate \
      --opentrons-python "$OPENTRONS_PYTHON" \
      --simulation-repair-attempts "$SIMULATION_REPAIR_ATTEMPTS" \
      --repair-api-prefix "$REPAIR_API_PREFIX" \
      --repair-model "$REPAIR_MODEL" \
      --repair-max-tokens "$REPAIR_MAX_TOKENS" \
      --force
  ) >"$OUT_ROOT/$shard.log" 2>&1 &
  PIDS+=("$!")
  if (( ${#PIDS[@]} >= CODEX_SHARD_CONCURRENCY )); then
    for pid in "${PIDS[@]}"; do
      wait "$pid"
    done
    PIDS=()
  fi
done

for pid in "${PIDS[@]}"; do
  wait "$pid"
done

PYTHONPATH=src python3 scripts/summarize_authoring_shards.py "$OUT_ROOT"
PYTHONPATH=src python3 -m labscriptai.benchmark.analyze_authoring_run \
  "$OUT_ROOT/summary.json" \
  --tasks "$TASKS" \
  --output-dir "$OUT_ROOT/analysis"

echo "Done: $OUT_ROOT"

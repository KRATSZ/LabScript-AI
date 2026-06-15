#!/usr/bin/env bash
set -euo pipefail

OUT_ROOT="${1:-runs/authoring90_native_agents/openclaw_py_only_v1}"
TASKS="benchmarks/authoring/tasks.yaml"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OPENTRONS_PYTHON="${OPENTRONS_PYTHON:-$REPO_ROOT/.venv-protocol/bin/python}"
SCRATCH_BASE="${SCRATCH_BASE:-/tmp/openclaw-native-agent-pyonly-90}"
OPENCLAW_SHARD_CONCURRENCY="${OPENCLAW_SHARD_CONCURRENCY:-3}"

cd "$REPO_ROOT"
command -v openclaw >/dev/null 2>&1 || {
  echo "openclaw is not installed or not on PATH; skipping OpenClaw native-agent run." >&2
  exit 127
}
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
    PYTHONPATH=src python3 scripts/run_openclaw_authoring_baseline.py \
      --task-ids "${SHARDS[$i]}" \
      --output-dir "$OUT_ROOT/$shard" \
      --scratch-root "$SCRATCH_BASE/$shard" \
      --timeout-sec 1800 \
      --protocol-only \
      --simulate \
      --opentrons-python "$OPENTRONS_PYTHON" \
      --force
  ) >"$OUT_ROOT/$shard.log" 2>&1 &
  PIDS+=("$!")
  if (( ${#PIDS[@]} >= OPENCLAW_SHARD_CONCURRENCY )); then
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

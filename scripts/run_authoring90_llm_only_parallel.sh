#!/usr/bin/env bash
# 90-task direct-llm benchmark: 3 shards x 30 tasks, frontier models via LLM_ONLY_* env.
set -euo pipefail

MODEL="${1:?usage: $0 <model-id> [output-root]}"
OUT_ROOT="${2:-runs/authoring90/llm_only/${MODEL}}"
TASKS="benchmarks/authoring/tasks.yaml"
OPENTRONS_PYTHON="${OPENTRONS_PYTHON:-/Users/gaoyuan/Documents/test/Flexagent/Opentrons-Lab-Agent/.venv-protocol/bin/python}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

if [[ -z "${LLM_ONLY_API_KEY:-}" ]]; then
  echo "LLM_ONLY_API_KEY is required." >&2
  exit 2
fi

export LLM_ONLY_MODEL="$MODEL"
export LLM_ONLY_MAX_TOKENS="${LLM_ONLY_MAX_TOKENS:-12000}"
export LLM_ONLY_TIMEOUT_SEC="${LLM_ONLY_TIMEOUT_SEC:-360}"
export LLM_ONLY_RETRY_ATTEMPTS="${LLM_ONLY_RETRY_ATTEMPTS:-6}"

task_range() {
  local start="$1"
  local end="$2"
  python3 -c "print(','.join(f'T{i:03d}' for i in range($start, $end + 1)))"
}

SHARDS=(
  "$(task_range 1 30)"
  "$(task_range 31 60)"
  "$(task_range 61 90)"
)

mkdir -p "$OUT_ROOT"

# Run shards sequentially to avoid gateway 502 under parallel load.
for i in "${!SHARDS[@]}"; do
  shard=$(printf "shard%02d" "$((i + 1))")
  echo "[$(date -Iseconds)] starting $shard (${#SHARDS[@]} shards, model=$MODEL)"
  PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
    --tasks "$TASKS" \
    --output-dir "$OUT_ROOT/$shard" \
    --provider deepseek \
    --task-ids "${SHARDS[$i]}" \
    --simulate \
    --opentrons-python "$OPENTRONS_PYTHON" \
    --simulation-repair-attempts 0 \
    --retry-attempts "$LLM_ONLY_RETRY_ATTEMPTS" \
    --direct-prompt-mode rules \
    --scaffold-label direct-llm \
    2>&1 | tee "$OUT_ROOT/$shard.log"
done

PYTHONPATH=src uv run python scripts/summarize_authoring_shards.py "$OUT_ROOT"

PYTHONPATH=src uv run python -m labscriptai.benchmark.analyze_authoring_run \
  "$OUT_ROOT/summary.json" \
  --tasks "$TASKS" \
  --output-dir "$OUT_ROOT/analysis"

echo "Done: $OUT_ROOT"

#!/usr/bin/env bash
set -euo pipefail

SCaffold="${1:-labscriptai-authoring}"
OUT_ROOT="${2:-runs/authoring-pilot/openplant18-v04-api}"
TASKS="benchmarks/external_community/tasks.yaml"
OPENTRONS_PYTHON="${OPENTRONS_PYTHON:-/Users/gaoyuan/Documents/test/Flexagent/Opentrons-Lab-Agent/.venv-protocol/bin/python}"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

export DEEPSEEK_MODEL="deepseek-v4-flash"
export DEEPSEEK_MAX_TOKENS="12000"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is required for API benchmark runs." >&2
  exit 2
fi

case "$SCaffold" in
  direct)
    PROVIDER="deepseek"
    REPAIR=0
    AGENT_ARGS=()
    ;;
  fixloop)
    PROVIDER="deepseek"
    REPAIR=3
    AGENT_ARGS=()
    ;;
  labscriptai-authoring|lai|light)
    PROVIDER="labscriptai-authoring"
    REPAIR=3
    AGENT_ARGS=(--authoring-skill-mode light --agent-max-steps 12)
    ;;
  *)
    echo "Unknown scaffold: $SCaffold. Use direct, fixloop, or labscriptai-authoring." >&2
    exit 2
    ;;
esac

SHARDS=(
  "EOPEN001,EOPEN002"
  "EOPEN003,EOPEN004"
  "EOPEN005,EOPEN006"
  "EOPEN007,EOPEN008"
  "EOPEN009,EOPEN010"
  "EOPEN011,EOPEN012"
  "EOPEN013,EOPEN014"
  "EOPEN015,EOPEN016"
  "EOPEN017,EOPEN018"
)

mkdir -p "$OUT_ROOT/$SCaffold"

for i in "${!SHARDS[@]}"; do
  shard=$(printf "shard%02d" "$((i + 1))")
  PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
    --tasks "$TASKS" \
    --output-dir "$OUT_ROOT/$SCaffold/$shard" \
    --provider "$PROVIDER" \
    --limit 2 \
    --task-ids "${SHARDS[$i]}" \
    --simulate \
    --opentrons-python "$OPENTRONS_PYTHON" \
    --simulation-repair-attempts "$REPAIR" \
    "${AGENT_ARGS[@]}" > "$OUT_ROOT/$SCaffold/$shard.log" 2>&1 &
done

wait

PYTHONPATH=src uv run python scripts/summarize_authoring_shards.py "$OUT_ROOT/$SCaffold"

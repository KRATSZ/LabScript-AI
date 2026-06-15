#!/usr/bin/env bash
# Hourly monitor for llm_only 90-task runs. Logs to runs/authoring90/llm_only/monitor.log
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
INTERVAL_SEC="${MONITOR_INTERVAL_SEC:-3600}"

echo "[$(date -Iseconds)] llm_only monitor loop started (interval=${INTERVAL_SEC}s)"

while true; do
  PYTHONPATH=src uv run python scripts/monitor_authoring90_llm_only.py || true
  # Sentinel for Cursor agent wake (hourly tick)
  echo "AGENT_LOOP_TICK_llm_only {\"prompt\":\"检查 runs/authoring90/llm_only 进度：两模型是否各 90 题完成、provider 错误率、是否需补跑。\"}"
  sleep "$INTERVAL_SEC"
done

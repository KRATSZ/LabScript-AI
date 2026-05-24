#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src:tests uv run python -m unittest \
  tests.test_runtime_robot_http_cli \
  tests.test_runtime_case_exporter \
  tests.test_recovery_shadow_benchmark

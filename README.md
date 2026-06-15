# Opentrons Lab Agent (LabscriptAI)

> Lab automation agent stack for Opentrons OT-2/Flex — protocol authoring, simulation-first validation, live execution via MCP, and recovery.
> Opentrons 实验室机器人 Agent 栈：协议编写、仿真门禁、MCP 真机执行与恢复。

## What It Does / 功能

This repository provides a Python agent library, Node MCP server, and operator workflows for:

- **Write/revise Python protocols** for OT-2 and Flex
- **Validate locally** via analyze/simulate before touching hardware
- **Iteratively repair** broken protocols through simulate → parse → edit loops
- **Drive live robots** over the LAN HTTP API with simulation-first safety gates
- **Self-recover** from tip pickup failures, occupied destinations, and module blockers
- **Search 833 reference protocols** via a pre-built catalog index
- **Optional deck vision** (MCP: `camera_status` → `capture_preview_image` → `vision_check`) for observation-only hints — not a substitute for `reconcile_state`

**编写/修改** OT-2/Flex Python 协议 · **本地仿真验证** · **迭代修复** · **LAN 控制真机** · **自动恢复** · **搜索 833 个参考协议** · **可选台面视觉辅助**

## Skills / 技能列表

| Skill | Description | 用途 |
|-------|-------------|------|
| `opentrons-experiment-run` | Default entry — state machine for live execution and recovery | 默认入口：真机执行状态机与恢复 |
| `opentrons-experiment-intent-review` | Plate mapping, tip strategy, deck alignment | 板位映射、吸头策略、台面对齐 |
| `opentrons-protocol-author` | Write/revise Python protocols | 编写/修改 Python 协议 |
| `opentrons-protocol-library` | Search 833 reference protocols via catalog | 搜索参考协议库 |
| `opentrons-protocol-verify` | Local doctor/analyze/simulate | 本地环境检查与仿真 |
| `opentrons-robot-lan` | Formal robot HTTP route for fallback/debug runs | MCP 备选、MCP 调试、显式选择 HTTP 路线 |
| `opentrons-simulation-repair` | Iterative edit-simulate fix loop | 仿真→修复迭代循环 |

## Repository layout / 目录分层

Full map: [`docs/REPO_LAYOUT.md`](docs/REPO_LAYOUT.md).

| Layer | Paths |
|-------|--------|
| **Code** | `src/`, `tests/`, `mcp-servers/`, `skills/`, `schemas/`, `scripts/`, `vision/` |
| **Benchmark** | `benchmarks/` (frozen task YAML only) |
| **Docs** | `docs/` (`rules/`, `architecture/`, `runbooks/`, `research/`, …) |
| **Optional data** | `reference-protocols/` (833 protocols; submodule candidate) |
| **Local output** | `runs/`, `artifacts/` (gitignored) |

```
Opentrons-Lab-Agent/
├── src/labscriptai/                     # Python: agent loop, runtime, benchmark, IR
├── tests/
├── benchmarks/                          # authoring + external + runtime task tables
├── mcp-servers/opentrons-mcp/           # Node MCP (simulate, live robot, recovery)
├── skills/                              # Operator SKILL.md + helper scripts
├── schemas/
├── scripts/                             # Maintainer tools (scripts/local/ ignored)
├── vision/
├── reference-protocols/Protocols-develop/ # Optional reference catalog
├── docs/                                # Policy, architecture, research, paper
├── AGENTS.md                            # Agent entry → docs/rules/
├── .mcp.json                            # MCP config (repo-relative paths)
└── runs/                                # Outputs (gitignored; see docs/research/evidence/)
```

Workspace parent (`Flexagent/`) is a local container. Non-primary materials live under `../workspace-archive/`. Static legacy MCP notes remain at `../reference/opentrons-mcp/` only; do not use that folder as a runtime MCP install.

MCP server provides: `doctor_local_runtime`, `simulate_protocol`, `run_protocol` (simulation-gated), `live_readiness_check`, `robot_status`, `module_status`, `reconcile_state`, `parse_error`, `suggest_recovery_action`, `execute_protocol_recovery`, `recover_tip_pickup`, `restart_review`, `probe_wells`, `experiment_history`, `health_check`, optional **`vision_check`** / camera helpers (`camera_status`, `capture_preview_image`, …), and 30+ more tools. Robot HTTP via `opentrons-robot-lan` is a formal fallback/debug route when MCP is unavailable or explicitly selected; do not control the same robot through MCP and HTTP in parallel. Vision workflow: [`docs/rules/workflows.md`](docs/rules/workflows.md) → *Optional deck vision*.

Core code is moving toward one STA agent loop:

- **One agent, two modes**: `author` writes the three-piece execution package (`protocol.py`, `setup_card.html`, `manifest.json`); `run` reads robot/simulator state, parses errors, and suggests recovery.
- **Ten stable tools**: package read/write, validate, simulate, robot inspect, gated run control, error parse, recovery suggest, skill load, memory read/write, and protocol search.
- **Gatekeeper first**: every model-proposed tool call is checked before execution; legacy seven-file packages remain compatibility input, not the new main path.
- **Benchmark**: `benchmarks/authoring/tasks.yaml` is the main 90-task table; `benchmarks/external_community/tasks.yaml` is a supplementary table for outside-source sanity checks.

## Documentation index / 文档索引

- **Folder map:** [`docs/REPO_LAYOUT.md`](docs/REPO_LAYOUT.md)
- **Doc map (start here):** [`docs/README.md`](docs/README.md)
- **Workspace management:** [`docs/WORKSPACE_MANAGEMENT.md`](docs/WORKSPACE_MANAGEMENT.md)
- **Workflow (canonical):** [`docs/rules/workflows.md`](docs/rules/workflows.md)
- **Safety policy (canonical):** [`docs/rules/safety-policy.md`](docs/rules/safety-policy.md)
- **Errors & recovery (canonical):** [`docs/rules/error-response.md`](docs/rules/error-response.md)
- **Live readiness gate:** [`docs/runbooks/live-readiness-runbook.md`](docs/runbooks/live-readiness-runbook.md)
- **Architecture:** [`docs/architecture/architecture.md`](docs/architecture/architecture.md)
- **Agent index:** [`AGENTS.md`](AGENTS.md) (short; points to the files above)

## Quick Start / 快速开始

```bash
# Clone
git clone https://github.com/SmartisanNaive/Opentrons-Lab-Agent.git
cd Opentrons-Lab-Agent

# Setup Python (uv)
uv venv .venv

# Setup MCP server
cd mcp-servers/opentrons-mcp && npm install && cd ../..

# Optional: prepare vision weight download config
cp vision/models/weights/manifest.example.json vision/models/weights/manifest.json
# edit manifest.json to point at your release assets, then:
bash scripts/download_vision_weights.sh

# Run tests
uv run python -m unittest discover -s tests -v
cd mcp-servers/opentrons-mcp && npm test
```

## Key Commands / 常用命令

```bash
# Check local Opentrons runtime
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor

# Static preflight (pipette names, apiLevel hints; no import)
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py preflight path/to/protocol.py

# Search reference protocols
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py search "serial dilution"

# Inspect a specific protocol
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py show 00222e

# Query a robot on LAN
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py health  # uses saved connection if present

# Run the LabscriptAI runtime smoke demo without robot API calls
PYTHONPATH=src uv run python -m labscriptai.runtime.smoke_benchmark \
  --provider offline \
  --output-dir runs/runtime-smoke/offline-demo

# Run a real LLM/gatekeeper/trace smoke sample with an OpenAI-compatible DeepSeek endpoint
DEEPSEEK_API_KEY=<your-key> DEEPSEEK_BASE_URL=https://api.deepseek.com DEEPSEEK_MODEL=deepseek-v4-pro \
DEEPSEEK_TIMEOUT_SEC=120 DEEPSEEK_MAX_TOKENS=1024 PYTHONPATH=src \
uv run python -m labscriptai.runtime.smoke_benchmark \
  --provider deepseek \
  --output-dir runs/runtime-smoke/deepseek-demo \
  --per-level 2 \
  --max-steps-per-task 1 \
  --retry-attempts 2

# Run runtime recovery scenarios without robot API calls
DEEPSEEK_API_KEY=<your-key> DEEPSEEK_BASE_URL=https://api.deepseek.com DEEPSEEK_MODEL=deepseek-v4-pro \
DEEPSEEK_TIMEOUT_SEC=120 DEEPSEEK_MAX_TOKENS=2048 PYTHONPATH=src \
uv run python -m labscriptai.runtime.scenario_benchmark \
  --provider deepseek \
  --output-dir runs/runtime-scenarios/deepseek-demo

# Run a small authoring benchmark pilot that writes three-piece protocol packages
DEEPSEEK_API_KEY=<your-key> DEEPSEEK_BASE_URL=https://api.deepseek.com DEEPSEEK_MODEL=deepseek-v4-pro \
DEEPSEEK_TIMEOUT_SEC=240 DEEPSEEK_MAX_TOKENS=12000 PYTHONPATH=src \
uv run python -m labscriptai.benchmark.authoring_pilot \
  --provider deepseek \
  --output-dir runs/authoring-pilot/deepseek-demo \
  --limit 3 \
  --retry-attempts 2

# Run the ReAct authoring scaffold provider
DEEPSEEK_API_KEY=<your-key> DEEPSEEK_BASE_URL=https://api.deepseek.com DEEPSEEK_MODEL=deepseek-v4-pro \
DEEPSEEK_TIMEOUT_SEC=240 DEEPSEEK_MAX_TOKENS=12000 PYTHONPATH=src \
uv run python -m labscriptai.benchmark.authoring_pilot \
  --provider labscriptai-authoring \
  --simulate \
  --output-dir runs/authoring-pilot/labscriptai-authoring-demo \
  --limit 3

# Include local Opentrons simulation in the authoring pilot score
PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
  --provider offline \
  --simulate \
  --output-dir runs/authoring-pilot/offline-sim-demo \
  --limit 1 \
  --retry-attempts 2
```

## Using in Other Projects / 在其他项目中使用

### Git Submodule

```bash
git submodule add https://github.com/SmartisanNaive/Opentrons-Lab-Agent.git opentrons-lab-agent
```

### MCP Server Only

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/path/to/Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js"]
    }
  }
}
```

## Python Environment / Python 环境

- Managed with `uv`: `uv venv .venv`, then `uv run ...`
- Optional vision deps: `uv sync --extra vision` (YOLOE/Ultralytics for local deck vision); acceptance checklist: `docs/runbooks/vision-acceptance.md`
- Optional vision workspace: `vision/` holds scripts/docs; model binaries download into `vision/models/weights/` via `bash scripts/download_vision_weights.sh`
- Optional protocol deps: `uv sync --extra protocol` (opentrons runtime for local simulate)

## Recommended Operator Flow / 推荐使用流程

Full sequences and tool order: [`docs/rules/workflows.md`](docs/rules/workflows.md). In short:

1. Give one natural-language request or SOP document.
2. The agent asks at most one blocking clarification round.
3. If runnable code exists, the agent simulates by default, repairs if needed,
   and returns a short status: `ready`, `needs_confirmation`, or `blocked`.
4. For cautious live bring-up, use `live_readiness_check` before `create_run` or `play`.

This keeps the simulation gate mandatory without making the operator manually
drive every intermediate step.

## Testing / 测试

```bash
# Python unit tests
uv run python -m unittest discover -s tests -v

# MCP server tests
cd mcp-servers/opentrons-mcp && npm test
```

## Reference Protocols / 参考协议库

The bundled `reference-protocols/Protocols-develop/` contains 833 validated OT-2 protocols.
Search via catalog index (fast) or filesystem scan (fallback):

内置 `reference-protocols/Protocols-develop/` 包含 833 个经过验证的 OT-2 协议。通过目录索引搜索（快速）或文件系统扫描（备选）：

```bash
python skills/opentrons-protocol-library/scripts/search_protocols.py search "magnetic beads"
python skills/opentrons-protocol-library/scripts/search_protocols.py show 00222e
python skills/opentrons-protocol-library/scripts/search_protocols.py snippet 00222e serial plasma
```

## License

MIT

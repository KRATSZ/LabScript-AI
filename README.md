# Opentrons Lab Agent

> AI agent skills for Opentrons OT-2 and Flex laboratory robots — protocol authoring, simulation-first validation, live execution, and self-repair.
> AI agent 技能集，用于 Opentrons OT-2/Flex 实验室机器人——协议编写、仿真验证、真机执行与自我修复。

## What It Does / 功能

This repository is a [Claude Code plugin](https://docs.anthropic.com/en/docs/claude-code/plugins) that teaches an AI agent to:

本仓库是一个 Claude Code 插件，让 AI agent 能够：

- **Write/revise Python protocols** for OT-2 and Flex
- **Validate locally** via analyze/simulate before touching hardware
- **Iteratively repair** broken protocols through simulate → parse → edit loops
- **Drive live robots** over the LAN HTTP API with simulation-first safety gates
- **Self-recover** from tip pickup failures, occupied destinations, and module blockers
- **Search 833 reference protocols** via a pre-built catalog index

**编写/修改** OT-2/Flex Python 协议 · **本地仿真验证** · **迭代修复** · **LAN 控制真机** · **自动恢复** · **搜索 833 个参考协议**

## Skills / 技能列表

| Skill | Description | 用途 |
|-------|-------------|------|
| `opentrons-experiment-run` | Default entry — state machine for live execution and recovery | 默认入口：真机执行状态机与恢复 |
| `opentrons-experiment-intent-review` | Plate mapping, tip strategy, deck alignment | 板位映射、吸头策略、台面对齐 |
| `opentrons-protocol-author` | Write/revise Python protocols | 编写/修改 Python 协议 |
| `opentrons-protocol-library` | Search 833 reference protocols via catalog | 搜索参考协议库 |
| `opentrons-protocol-verify` | Local doctor/analyze/simulate | 本地环境检查与仿真 |
| `opentrons-robot-lan` | Fallback HTTP API when MCP unavailable | MCP 不可用时的 LAN API 备选 |
| `opentrons-simulation-repair` | Iterative edit-simulate fix loop | 仿真→修复迭代循环 |

## Architecture / 架构

```
Opentrons-Lab-Agent/
├── skills/                              # 7 agent skills
├── mcp-servers/opentrons-mcp/           # MCP server (local simulation + live robot control)
├── reference-protocols/Protocols-develop/ # 833 reference protocols (read-only)
├── tests/                               # Python + Node.js tests
├── CLAUDE.md                            # Agent guardrails and safety rules
└── .claude-plugin/plugin.json           # Plugin metadata
```

MCP server provides: `doctor_local_runtime`, `simulate_protocol`, `run_protocol` (simulation-gated), `robot_status`, `module_status`, `reconcile_state`, `parse_error`, `suggest_recovery_action`, `execute_protocol_recovery`, `recover_tip_pickup`, `restart_review`, `probe_wells`, `experiment_history`, `health_check`, and 30+ more tools.

## Safety Rules / 安全规则

The agent must follow these hard rules (defined in `CLAUDE.md`):

1. **Simulation gate is blocking** — if simulation fails, fix the protocol. No blind `curl` or `maintenance_runs` workarounds.
2. **Live execution via MCP only** — use `run_protocol`, not ad-hoc scripts.
3. **Hardware errors → MCP recovery** — `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`.
4. **Logs are audit-only** — `experiment_history` is post-hoc; for current deck truth use `reconcile_state`.
5. **No parallel drivers** — never drive the same robot from MCP and scripts simultaneously.
6. **Hard stops → human review** — `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` always escalate.

**仿真门控阻断** · **MCP 真机执行** · **硬件错误走恢复流程** · **日志仅审计** · **不并行操作** · **硬停必须人工确认**

## Quick Start / 快速开始

```bash
# Clone
git clone https://github.com/SmartisanNaive/Opentrons-Lab-Agent.git
cd Opentrons-Lab-Agent

# Setup Python (uv)
uv venv .venv

# Setup MCP server
cd mcp-servers/opentrons-mcp && npm install && cd ../..

# Run tests
uv run python -m unittest discover -s tests -v
cd mcp-servers/opentrons-mcp && npm test
```

## Key Commands / 常用命令

```bash
# Check local Opentrons runtime
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor

# Search reference protocols
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py search "serial dilution"

# Inspect a specific protocol
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py show 00222e

# Query a robot on LAN
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
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
- Optional vision deps: `uv sync --extra vision` (YOLOE/Ultralytics for local deck vision)
- Optional protocol deps: `uv sync --extra protocol` (opentrons runtime for local simulate)

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

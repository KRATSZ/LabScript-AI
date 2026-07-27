# QA — AUTHORING + RUNTIME (T-AR)

Date: 2026-07-27  
Agent under test: lean `labscriptai/` (entry `labscriptai.agent.cli:main`)  
Artifacts: `labscriptai/qa_artifacts/`  
Pytest: **23 passed** (`python -m pytest labscriptai/tests -q`)

## Verdict

**Ready to submit** for GitHub manuscript packaging of the lean agent skeleton, with caveats:

- Live robot `10.31.17.153:31950` is **unreachable from this host** (connection closed); RUNTIME live path validated via mock/`127.0.0.1` failure + doctor `:31950` surface.
- `opentrons.simulate` exists in `.venv` but crashes on Python 3.14 (`asyncio.get_child_watcher` removed); simulate failure is **environment**, not agent crash. Deepseek authoring path and file write are OK.

---

## AUTHORING results

| # | Case | Result | Notes |
|---|------|--------|-------|
| A1 | `labscriptai chat --provider offline` multi-turn: identity → edit `protocol.py` → bash `ls` | **PASS** | Workspace `/tmp/lai-offline-22730`; transcript `qa_artifacts/authoring_offline.txt`; file `qa_artifacts/offline_protocol.py` |
| A2 | deepseek new workspace `/tmp/lai-author-$$` write minimal Flex protocol | **PASS** | Workspace `/tmp/lai-author-22891/protocol.py`; model used `edit`; transcript `qa_artifacts/authoring_deepseek.txt`; copy `qa_artifacts/deepseek_protocol.py` |
| A3 | optional simulate after deepseek write | **PASS (env fail)** | Path correct; session not needed (chat already exited). Simulate raises Python 3.14 asyncio AttributeError — see `qa_artifacts/simulate_attempt.txt` |

### Transcript summaries

**Offline**

1. 「你是谁」→ LabscriptAI identity reply  
2. 「写一个最小 protocol.py…用 edit」→ `edit` write `protocol.py` (463 bytes)  
3. 「用 bash 列一下文件」→ `bash ls -la` shows `protocol.py`

**Deepseek** (`provider=deepseek`, key from repo-root `.env`)

- User: Flex 最简 protocol（pipette + tiprack, pickup/drop）  
- Agent: wrote `protocol.py` (Flex tiprack 50µL @ D1, `flex_1channel_50ul`, pick/drop); suggested `python3 -m opentrons_simulate protocol.py`  
- Generated file: `/tmp/lai-author-22891/protocol.py`

---

## RUNTIME results

| # | Case | Result | Notes |
|---|------|--------|-------|
| R1 | `labscriptai doctor --robot 127.0.0.1` | **PASS** | FAIL message contains **31950** (`http://127.0.0.1:31950/health`, Connection refused). `qa_artifacts/doctor_127.txt` |
| R2 | `labscriptai doctor --robot 10.31.17.153` | **FAIL (real)** | `http://10.31.17.153:31950/health` → Remote end closed connection without response. Recorded; no live round. `qa_artifacts/doctor_10_31.txt` |
| R3 | `labscriptai recover --run-id dry --robot 127.0.0.1` | **PASS** | Exit 0, no Traceback; structured robot/MCP failure. `qa_artifacts/runtime_recover.txt`. `--help` OK |
| R4 | chat `--robot 127.0.0.1` 「看一下机器人状态」 | **PASS** | offline → `robot(op=status)` then friendly tool error; deepseek → ECONNREFUSED explanation, no crash. Artifacts `runtime_chat_*.txt` |
| R5 | gate red-line: bash `curl …:31950` | **PASS** | `evaluate()` → `suspend`; `run_turn` with scripted curl → suspended + outbox, no execute |

---

## Bugs fixed (minimal, `labscriptai/` only)

1. **`agent/cli.py` — `_FriendlyOffline` authoring smoke**  
   Offline provider previously only answered identity/capability and stub-acked everything else, so AUTHORING sample could not write files or run bash.  
   Fix: propose `edit` / `bash` / `robot` tool calls for protocol / list / status intents; close mid-turn only when the **last** message is a tool result (so multi-turn history does not sticky-replay prior tools).

No changes outside `labscriptai/`. No commit/push.

---

## Submit recommendation

| Question | Answer |
|----------|--------|
| Suggest submit lean agent to GitHub manuscript? | **Yes**, for AUTHORING+RUNTIME CLI skeleton |
| Blockers | None for mock/offline/deepseek authoring; live Flex probe failed (network/robot), not agent regression |
| Follow-ups (non-blocking) | Confirm `10.31.17.153` when robot is up; run simulate on Python ≤3.12 if needed for paper demos |

---

## Repro commands

```bash
source .venv/bin/activate
pip install -e labscriptai -q   # once

# AUTHORING offline
printf '你是谁\n写一个最小 protocol.py 到 workspace，用 edit 工具\n用 bash 列一下文件\n/quit\n' \
  | labscriptai chat --provider offline --workspace /tmp/lai-offline-demo

# AUTHORING deepseek
WS=/tmp/lai-author-$$; mkdir -p "$WS"
printf '写一个 Flex 上最简单的 protocol.py：加载 pipette 和 tiprack，pickup tip 再 drop，不要复杂\n/quit\n' \
  | labscriptai chat --provider deepseek --workspace "$WS"

# RUNTIME
labscriptai doctor --robot 127.0.0.1
labscriptai doctor --robot 10.31.17.153
labscriptai recover --run-id dry --robot 127.0.0.1 --provider offline
python -m pytest labscriptai/tests -q
```

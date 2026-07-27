# QA_CODEX — R-Codex 验收报告

**范围:** `labscriptai/`（agent + plugins + tests）  
**审查员:** R-Codex（独立验收）  
**日期:** 2026-07-27  
**Git:** 只读审查；未 commit / push；未改 `core/`、`src/`、`benchmarks/`。

---

## 裁决

**有条件接受（Conditional Accept）**

瘦 agent 规格符合度高：5 工具恒定、mode 不进模型、gate 三态、MCP 短命子进程、短 prompt、doctor 默认 `:31950`。自测通过。  
**不建议立刻提交到与 `core/` 共用的默认 venv**；进入 AUTHORING 样例可以，RUNTIME 样例需先完成 MCP `npm install` 与打包策略澄清。

---

## Codex CLI 状态

**codex CLI 不可用，改用人工对抗审查。**

探测结果：

| 路径 | 结果 |
|------|------|
| `which codex`（干净 PATH） | not found |
| `/opt/homebrew/bin/codex` | 断链 → `/Applications/Codex.app/.../codex`（App 不存在） |
| `npx @openai/codex` 缓存二进制 | Mach-O 存在，但 `--version` / `--help` 被 kill（exit 137），无法跑审查 |

### Codex 原始输出（不可用）

```text
$ which codex
codex not found

$ /opt/homebrew/bin/codex --version
(eval):1: no such file or directory: /opt/homebrew/bin/codex
# symlink: /opt/homebrew/bin/codex -> /Applications/Codex.app/Contents/Resources/codex
# target missing

$ <npx-cache>/.../bin/codex --version
ver_exit=137
# no stdout; process killed

$ <npx-cache>/.../bin/codex --help
exit=0
# empty stdout — unusable for non-interactive review
```

因此下列审查全部为 **人工对抗审查（等价 Codex 焦点）**。

---

## 自测复核

在仓库 `.venv` 下执行（系统 `pip`/`pytest` 不在 PATH）：

```bash
source .venv/bin/activate
cd labscriptai && pip install -e ".[dev]" -q
labscriptai doctor --robot 127.0.0.1
printf '你是谁\n能做什么\n/quit\n' | labscriptai chat --provider offline
pytest -q
```

| 步骤 | 结果 |
|------|------|
| `pip install -e ".[dev]"` | OK |
| `doctor --robot 127.0.0.1` | **rc=1**（预期：无真机）；探针 `http://127.0.0.1:31950/health`，Connection refused — **默认端口正确** |
| offline chat「你是谁 / 能做什么 /quit」 | **rc=0**；身份与五工具能力答复正确 |
| `pytest -q` | **23 passed** in 0.03s |

---

## 检查清单

### 1. `labscriptai/agent/` 文件集合

| 文件 | 角色 |
|------|------|
| `llm.py` / `gate.py` / `tools.py` / `loop.py` / `cli.py` | 约定五核心 |
| `mcp_adapter.py` | 允许的 MCP 桥 |
| `types.py` | 允许但 **未使用**（仅定义 `ToolCall`，无引用） |
| `__init__.py` | 包导出 |

**无额外无用业务模块膨胀。**  
**建议删:** `types.py`（死代码；删前确认后续 wave 不用）。  
`cli.py`(~574) / `tools.py`(~691) 偏胖但仍是单文件职责，暂不标删。

### 2. 模型可见 tool = 5

`TOOLS_SCHEMA` = `bash | edit | robot | memory | skill`（长度 5）。  
`run_turn` 默认传入该 schema；测试 `test_tools_schema_is_five` 覆盖。  
**未**把 MCP 的 ~74 handlers 塞进 schema（仅 `robot` 描述里顺带提到 `module_status` / `parse_error` 等实现细节 — 见 P2）。

### 3. System prompt 短、不泄漏 mode/taxonomy

`build_system_prompt` ≈ **10 行**（测试约束 8–12）。  
对抗扫描：无 `mode=` / `author mode` / `run mode` / `taxonomy` / gate 三态字面量。  
context `author|run` 仅在 `gate.infer_context` 系统侧使用。  
skills **不**默认注入 prompt；仅 `skill` 工具按需加载。

### 4. Gate 三态

| 规则 | 证据 |
|------|------|
| daemon `interactive=False`：ask→suspend | `gate.evaluate` 末尾升级；`test_daemon_upgrades_ask_to_suspend` |
| bash 打 `:31950` / 已知 robot IP 红线 | `suspend`；`test_bash_robot_port_suspends` / `_ip_from_env` |
| `robot op=act` 在 author 上下文 | `suspend`；`test_robot_status_allow_act_author_suspend` |
| allow / ask / suspend 三态 | 单元测试覆盖 SAFE / preauthorized / destructive bash |

### 5. MCP：短命子进程、不进 schema

`mcp_adapter.call_tool`：`subprocess.run([node, "--input-type=module", "-e", ...])`，按名调 `TOOL_HANDLERS[tool]`。  
无 Python MCP Client SDK；无 74-tool schema dump。  
vendor 说明见 `plugins/SOURCE_MCP.md`（排除 `node_modules` 出 vendor 清单；本地可 `npm install`）。

### 6. 依赖与 skills

| 项 | 状态 |
|----|------|
| Python `dependencies` | **[]**（stdlib only） |
| optional `dev` | `pytest>=7` |
| skills 默认进 prompt | **否** |
| 本地 `plugins/mcp/.../node_modules` | ~24M（本地 install，不应进提交；SOURCE 已声明排除） |

### 7. 与旧 `src/` / `core/` 交叉 import

对 `labscriptai/**/*.py` AST/rg 扫描：

- **无** `from src.` / `from core.` / `import src|core`
- **无** `from labscriptai.runtime|authoring|benchmark`（旧树路径）
- 运行时 `import labscriptai` → `.../labscriptai/__init__.py`（新包）

**代码层独立。**  
**打包层冲突（P1/条件）:** `core/pyproject.toml` 与 `labscriptai/pyproject.toml` **同名** `name = "labscriptai"`、争抢 console script `labscriptai`。同 venv 后装覆盖先装 — 见下方。

---

## P0 必须修

**无代码级 P0**（规格七项均满足；自测绿）。

本次未做代码改动。

---

## P1（条件项 — 建议修后再提交 / 共用 venv）

1. **发行名/入口冲突:** `core` 与顶层 `labscriptai/` 均为 `labscriptai` 发行名 + `labscriptai` CLI。共用 `.venv` 会互相覆盖。需隔离 venv，或改新包名/入口策略（改 `core/` 不在本验收可改范围）。
2. **plugins 未进 packaging SOURCES:** `labscriptai.egg-info/SOURCES.txt` 仅有 `agent/` + tests；`plugins/skills`、`plugins/mcp` 未列入 `package-data`。**editable 安装可用**（按 `__file__` 旁路读盘）；非 editable / wheel 会丢 skill 与 MCP index。应补 `package-data`（且勿打包 `node_modules`）。
3. **SAFE_ACTION_TYPES ↔ MCP 映射不全:** gate 允许的部分 action（如 `mark_resource_unavailable`）在 `tools._ACT_ALIASES` 无映射时会把名字当 MCP tool 直调 → 易 `Unknown MCP tool`。RUNTIME 样例前应收敛 SAFE 集或补别名。
4. **daemon `_poll_wake_event` 绕过 gate 调 `execute(robot, watch/status)`:** 当前 watch/status 恒 allow，行为正确；仍是旁路，后续勿在此路径加 act。

---

## P2（卫生 / 防屎山）

1. **`agent/types.py` 未使用 → 标删**（或真正接到 `llm`/`loop` 归一化路径）。
2. **`loop.py` 内嵌 W2 fallback `TOOLS_SCHEMA`**（含 `old_str`/`new_str` 与真 tools 不一致）— tools 已落地，可删 fallback，减分叉。
3. **陈旧注释:** `agent/__init__.py` / `pyproject` 仍写 “W3 才有 cli” — 已过时。
4. **robot schema 文案** 泄漏少量 MCP 工具名（`module_status` 等）— 可再压成纯 op 描述。
5. **bash 红线过宽:** 任意命令字符串含字面量 `31950`（无冒号）亦 suspend — 偏保守，可接受。
6. **`llm._load_package_dotenv` 读 `core/.env`:** 非 import，但是 monorepo 耦合；可接受。

---

## 是否进入 AUTHORING / RUNTIME 样例与提交

| 动作 | 建议 |
|------|------|
| AUTHORING 样例（offline / edit+bash simulate） | **可以进入**（五工具 + gate + offline chat 已绿） |
| RUNTIME 样例（真机 robot act / recover / daemon） | **有条件：** 机器人可达、MCP `npm install`、理清 SAFE↔MCP 映射；gate 行为已具备 |
| git 提交 / 与 core 同 venv 发布 | **先处理 P1.1–P1.2**（命名冲突 + package-data）；再提交 |
| 把本地 `node_modules` 提交进仓 | **不要**（SOURCE_MCP 已排除） |

---

## 对抗摘要（等价 Codex 焦点）

> Review labscriptai/ agent_min for slim design: 5 tools, gate allow/ask/suspend, no mode in prompt. List P0/P1 issues.

**P0:** none in-scope code.  
**P1:** dual `labscriptai` distro name vs `core/`; plugins not in wheel/SOURCES; incomplete SAFE→MCP aliases; daemon wake bypasses gate (read-only ops only today).  
**P2:** unused `types.py` (delete); dead loop fallback schema; stale W-comments; minor MCP name leakage in robot tool blurb.

**规格符合:** 5 tools ✓ · mode out of prompt ✓ · gate 三态 ✓ · MCP short-lived ✓ · short prompt ✓ · doctor `:31950` ✓ · no old-tree imports ✓ · skills on-demand ✓ · Python deps empty ✓

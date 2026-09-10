"""LabscriptAI lean CLI: chat / recover / daemon / doctor — all share one loop."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import select
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

W12_NOT_READY = "W1/W2 未就绪"
MIN_NODE_MAJOR = 18
NPM_INSTALL_HINT = "cd labscriptai/plugins/mcp/opentrons-mcp && npm install"


def _import_deps(*, require_tools: bool = False) -> tuple[Any, ...]:
    """Import W1/W2/W3 modules; raise ImportError with a clear message on hard failure.

    ``tools`` may be missing while W2 is still landing — loop.py ships a 5-tool
    fallback schema so offline chat can still smoke. Pass ``require_tools=True``
    for recover/daemon paths that need a real execute().
    """
    hard: list[str] = []
    soft: list[str] = []
    try:
        from labscriptai.agent import llm as llm_mod
    except ImportError as exc:  # pragma: no cover
        hard.append(f"llm ({exc})")
        llm_mod = None  # type: ignore[assignment]
    try:
        from labscriptai.agent.gate import GateDecision, evaluate, infer_context
    except ImportError as exc:  # pragma: no cover
        hard.append(f"gate ({exc})")
        GateDecision = evaluate = infer_context = None  # type: ignore[assignment, misc]
    try:
        from labscriptai.agent.tools import TOOLS_SCHEMA, execute
    except ImportError as exc:
        soft.append(f"tools ({exc})")
        TOOLS_SCHEMA = execute = None  # type: ignore[assignment]
    try:
        from labscriptai.agent.loop import SessionState, build_system_prompt, run_turn
    except ImportError as exc:  # pragma: no cover
        hard.append(f"loop ({exc})")
        SessionState = build_system_prompt = run_turn = None  # type: ignore[assignment, misc]

    if hard or (require_tools and soft):
        raise ImportError(f"{W12_NOT_READY}: " + "; ".join([*hard, *soft]))
    return (
        llm_mod,
        GateDecision,
        evaluate,
        infer_context,
        TOOLS_SCHEMA,
        execute,
        SessionState,
        build_system_prompt,
        run_turn,
        soft,
    )


def _normalize_robot_base(host: str) -> str:
    try:
        from labscriptai.agent.mcp_adapter import normalize_robot_base

        return normalize_robot_base(host)
    except ImportError:
        pass
    try:
        from labscriptai.agent.tools import normalize_robot_base as _nr

        return _nr(host)
    except ImportError:
        pass
    raw = str(host).strip().rstrip("/")
    if raw.lower().startswith(("http://", "https://")):
        return raw
    if ":" in raw.rsplit("@", 1)[-1]:
        # host:port already
        return f"http://{raw}"
    return f"http://{raw}:31950"


def _probe_robot(robot_ip: str | None, *, timeout: float = 2.0) -> tuple[bool, str]:
    """HTTP GET /health on :31950 (no MCP). Returns (ok, detail)."""
    if not robot_ip:
        return False, "no robot IP"
    base = _normalize_robot_base(robot_ip)
    url = base.rstrip("/") + "/health"
    try:
        req = Request(url, headers={"Opentrons-Version": os.environ.get("OPENTRONS_VERSION", "4")})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(512).decode("utf-8", errors="replace")
            return True, f"{url} → HTTP {getattr(resp, 'status', '?')} {body[:120]}"
    except HTTPError as exc:
        return False, f"{url} → HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        return False, f"{url} → {exc.reason!s}"
    except OSError as exc:
        return False, f"{url} → {exc}"


def _default_provider() -> str:
    try:
        from labscriptai.agent.llm import _load_package_dotenv

        _load_package_dotenv()
    except ImportError:
        pass
    return "deepseek"


_MIN_FLEX_PROTOCOL = '''\
from opentrons import protocol_api

metadata = {
    "protocolName": "LabscriptAI offline minimal",
    "author": "LabscriptAI",
}
requirements = {"robotType": "Flex", "apiLevel": "2.20"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "A1")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", tip_racks=[tiprack])
    pipette.pick_up_tip()
    pipette.drop_tip()
'''


class _FriendlyOffline:
    """Offline stub: identity/capability plus minimal edit/bash authoring smoke."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.input_tokens = getattr(inner, "input_tokens", 0)
        self.output_tokens = getattr(inner, "output_tokens", 0)
        self.total_tokens = getattr(inner, "total_tokens", 0)

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        del tools
        # Mid-turn only: last message is a tool result → summarize and stop.
        if messages and messages[-1].get("role") == "tool":
            last = messages[-1]
            name = last.get("name") or "tool"
            content = str(last.get("content") or "")[:240]
            return {
                "final": {
                    "message": f"Offline done via {name}: {content or '(ok)'}",
                    "completed": True,
                }
            }

        prompt = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    prompt = content.strip()
                    break
        lowered = prompt.lower()
        zh = any("\u4e00" <= ch <= "\u9fff" for ch in prompt)
        identity = any(
            key in lowered or key in prompt
            for key in (
                "who are you",
                "what are you",
                "你是谁",
                "你叫什么",
            )
        )
        capability = any(
            key in lowered or key in prompt
            for key in (
                "what can you",
                "how can you help",
                "能做什么",
                "你可以做什么",
                "有什么能力",
                "/help",
                "help",
            )
        )
        if identity:
            msg = (
                "我是 LabscriptAI，合成生物学自动化（Synbio automation）Agent。"
                if zh
                else "I am LabscriptAI, a Synbio automation agent."
            )
            return {"final": {"message": msg, "completed": False}}
        if capability:
            msg = (
                "我能用五个工具干活：bash、edit、robot、memory、skill。"
                "写协议用 edit+bash（simulate）；真机只走 robot。"
                "危险动作会 gate（确认或挂起）。"
                if zh or "能" in prompt or "什么" in prompt
                else (
                    "I work with five tools: bash, edit, robot, memory, skill. "
                    "Author with edit+bash (simulate); robot actions only via robot. "
                    "Dangerous calls are gated (confirm or suspend)."
                )
            )
            return {"final": {"message": msg, "completed": False}}

        wants_list = any(
            key in lowered or key in prompt
            for key in (
                "ls ",
                "ls\n",
                "list files",
                "列文件",
                "列一下",
                "列出文件",
                "bash 列",
                "用 bash 列",
                "执行 ls",
                "bash ls",
                "用 bash 执行 ls",
                "run ls",
            )
        ) or lowered.strip() in {"ls", "ls -la", "ls -l"} or (
            "bash" in lowered and ("ls" in lowered or "列" in prompt)
        )
        wants_protocol = (
            ("protocol.py" in lowered or "protocol" in lowered or "协议" in prompt)
            and any(key in lowered or key in prompt for key in ("写", "write", "edit", "创建", "minimal", "最小"))
        )
        wants_status = any(
            key in lowered or key in prompt
            for key in (
                "机器人状态",
                "robot status",
                "看一下机器人",
                "robot state",
                "robot(op=status)",
                "op=status",
                "recover run",
            )
        ) or (
            lowered.strip() in {"status", "robot status"}
            or ("状态" in prompt and "机器" in prompt)
        )

        # Prefer list over protocol when both could match (e.g. mention prior file).
        if wants_list:
            return {
                "tool_calls": [
                    {
                        "id": "offline_bash_ls",
                        "name": "bash",
                        "arguments": {"command": "ls -la"},
                    }
                ]
            }
        if wants_protocol:
            return {
                "tool_calls": [
                    {
                        "id": "offline_edit_protocol",
                        "name": "edit",
                        "arguments": {
                            "op": "write",
                            "path": "protocol.py",
                            "content": _MIN_FLEX_PROTOCOL,
                        },
                    }
                ]
            }
        if wants_status:
            return {
                "tool_calls": [
                    {
                        "id": "offline_robot_status",
                        "name": "robot",
                        "arguments": {"op": "status"},
                    }
                ]
            }
        return self._inner.complete(messages, tools=None)


def _build_llm(provider: str) -> Any:
    from labscriptai.agent.llm import build_client

    client = build_client(provider=provider)
    if provider == "offline" or client.__class__.__name__ == "OfflineClient":
        return _FriendlyOffline(client)
    return client


def _new_session(
    SessionState: Any,
    *,
    workspace: Path,
    robot_ip: str | None,
    run_id: str | None,
    interactive: bool,
    preauthorized: set[str] | None = None,
    max_steps: int | None = None,
) -> Any:
    workspace = workspace.expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    os.environ["LABSCRIPTAI_WORKSPACE"] = str(workspace)
    connected = False
    detail = ""
    if robot_ip:
        os.environ["LABSCRIPTAI_ROBOT_IP"] = robot_ip
        os.environ.setdefault("ROBOT_IP", robot_ip)
        connected, detail = _probe_robot(robot_ip)
        if connected:
            print(f"[robot] {detail}")
        else:
            print(f"[robot] unreachable: {detail}", file=sys.stderr)
    try:
        from labscriptai.agent.loop import resolve_max_steps
    except ImportError:
        resolve_max_steps = lambda value=None: 0  # type: ignore[assignment,misc]
    return SessionState(
        workspace=workspace,
        robot_ip=robot_ip,
        robot_connected=connected,
        active_run_id=run_id,
        messages=[],
        interactive=interactive,
        preauthorized=set(preauthorized or ()),
        max_steps=resolve_max_steps(max_steps),
    )


def _vendored_mcp_dir() -> Path:
    try:
        from labscriptai.agent.mcp_adapter import plugins_mcp_index

        return plugins_mcp_index().parent
    except ImportError:
        return Path(__file__).resolve().parents[1] / "plugins" / "mcp" / "opentrons-mcp"


def _load_dotenv_for_doctor() -> None:
    try:
        from labscriptai.agent.llm import _load_package_dotenv

        _load_package_dotenv()
    except ImportError:
        pass


def _parse_node_major(raw: str) -> int | None:
    text = raw.strip()
    if text[:1] in {"v", "V"}:
        text = text[1:]
    match = re.match(r"(\d+)", text)
    return int(match.group(1)) if match else None


def check_node(
    *,
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., Any] = subprocess.run,
) -> tuple[str, str]:
    """Return (OK|FAIL, detail) for Node >= 18."""
    node_bin = which("node")
    if not node_bin:
        return "FAIL", "node not found on PATH (need Node >= 18)"
    try:
        completed = run(
            [node_bin, "-v"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "FAIL", f"node -v failed ({exc})"
    version = (completed.stdout or completed.stderr or "").strip() or "unknown"
    major = _parse_node_major(version)
    if major is None:
        return "FAIL", f"{version} (could not parse; need >= {MIN_NODE_MAJOR})"
    if major < MIN_NODE_MAJOR:
        return "FAIL", f"{version} (need Node >= {MIN_NODE_MAJOR})"
    return "OK", f"{version} (>= {MIN_NODE_MAJOR})"


def check_node_modules(mcp_dir: Path) -> tuple[str, str]:
    path = mcp_dir / "node_modules"
    if path.is_dir():
        return "OK", str(path)
    return "FAIL", f"missing {path}"


def check_index_js(mcp_dir: Path) -> tuple[str, str]:
    path = mcp_dir / "index.js"
    if path.is_file():
        return "OK", str(path)
    return "FAIL", f"missing {path}"


def check_deepseek_key(environ: dict[str, str] | None = None) -> tuple[str, str]:
    """Present/absent only — never print the key value."""
    env = os.environ if environ is None else environ
    if str(env.get("DEEPSEEK_API_KEY") or "").strip():
        return "OK", "set (default labscriptai chat uses DeepSeek)"
    return (
        "WARN",
        "absent (default labscriptai chat needs DEEPSEEK_API_KEY; or use --provider offline)",
    )


def check_opentrons(
    *,
    import_module: Callable[[str], Any] = importlib.import_module,
    run_helper: bool = False,
) -> tuple[str, str]:
    """Probe opentrons.cli / opentrons.simulate in the current interpreter."""
    names = ("opentrons.cli", "opentrons.simulate")
    found: list[str] = []
    missing: list[str] = []
    for name in names:
        try:
            import_module(name)
            found.append(name)
        except Exception as exc:
            missing.append(f"{name} ({type(exc).__name__})")
    helper_note = ""
    if run_helper:
        helper = _vendored_mcp_dir() / "scripts" / "local_simulation.py"
        if helper.is_file():
            try:
                completed = subprocess.run(
                    [sys.executable, str(helper), "doctor"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                )
                payload = (completed.stdout or "").strip()
                if payload:
                    try:
                        data = json.loads(payload.splitlines()[-1])
                        helper_note = f" (local_simulation.py doctor ok={data.get('ok')})"
                    except json.JSONDecodeError:
                        helper_note = " (local_simulation.py doctor ran)"
            except (OSError, subprocess.TimeoutExpired):
                helper_note = ""
    if not missing:
        return "OK", ", ".join(found) + helper_note
    msg = (
        "SimPass/LogicPass unavailable until opentrons is installed in this interpreter; "
        "chat robot backend still needs Node+npm"
    )
    detail = msg if not found else f"found {', '.join(found)}; missing {', '.join(missing)}; {msg}"
    return "WARN", detail + helper_note


def check_robot(robot: str | None, *, timeout: float = 2.0) -> tuple[str, str]:
    if not robot:
        return "SKIP", "pass --robot IP to probe http://IP:31950/health"
    ok, detail = _probe_robot(robot, timeout=timeout)
    return ("OK" if ok else "FAIL"), detail


def collect_doctor_checks(
    *,
    robot: str | None,
    timeout: float = 2.0,
    mcp_dir: Path | None = None,
    environ: dict[str, str] | None = None,
    check_node_fn: Callable[..., tuple[str, str]] | None = None,
    check_opentrons_fn: Callable[..., tuple[str, str]] | None = None,
    check_robot_fn: Callable[..., tuple[str, str]] | None = None,
) -> list[tuple[str, str, str]]:
    """Return rows of (status, name, detail). Toolchain always; /health only if robot set."""
    mcp_dir = mcp_dir or _vendored_mcp_dir()
    node_status, node_detail = (check_node_fn or check_node)()
    nm_status, nm_detail = check_node_modules(mcp_dir)
    idx_status, idx_detail = check_index_js(mcp_dir)
    key_status, key_detail = check_deepseek_key(environ)
    ot_status, ot_detail = (check_opentrons_fn or check_opentrons)()
    robot_status, robot_detail = (check_robot_fn or check_robot)(robot, timeout=timeout)
    return [
        (node_status, "node", node_detail),
        (nm_status, "node_modules", nm_detail),
        (idx_status, "index.js", idx_detail),
        (key_status, "DEEPSEEK_API_KEY", key_detail),
        (ot_status, "opentrons", ot_detail),
        (robot_status, "robot", robot_detail),
    ]


def format_doctor_report(rows: list[tuple[str, str, str]]) -> str:
    lines = [
        "LabscriptAI doctor  (health check for `labscriptai chat`; not a second workflow)",
        "MCP is the robot backend for chat, not a Cursor plugin / not a second tool surface.",
        "",
    ]
    for status, name, detail in rows:
        lines.append(f"{status:<5} {name:<18} {detail}")
    needs_npm = any(
        status == "FAIL" and name in {"node", "node_modules"} for status, name, _ in rows
    )
    if needs_npm:
        lines.append("")
        lines.append("Node/npm not ready. Copy-paste:")
        lines.append(f"  {NPM_INSTALL_HINT}")
    failed = [name for status, name, _ in rows if status == "FAIL"]
    lines.append("")
    if failed:
        lines.append("FAIL: " + ", ".join(failed))
    else:
        lines.append("Next: labscriptai chat   (default provider: deepseek)")
    return "\n".join(lines) + "\n"


def cmd_doctor(args: argparse.Namespace) -> int:
    _load_dotenv_for_doctor()
    robot = args.robot or os.environ.get("ROBOT_IP") or os.environ.get("LABSCRIPTAI_ROBOT_IP")
    rows = collect_doctor_checks(
        robot=robot,
        timeout=float(args.timeout),
        check_opentrons_fn=lambda: check_opentrons(run_helper=True),
    )
    report = format_doctor_report(rows)
    print(report, end="")
    return 1 if any(status == "FAIL" for status, _name, _detail in rows) else 0


def cmd_chat(args: argparse.Namespace) -> int:
    from labscriptai.agent.gate import DEFAULT_RECOVERY_PREAUTHORIZED

    try:
        (
            _llm_mod,
            _GateDecision,
            _evaluate,
            _infer_context,
            tools_schema,
            _execute,
            SessionState,
            build_system_prompt,
            run_turn,
            soft,
        ) = _import_deps()
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if soft or tools_schema is None or (tools_schema is not None and len(tools_schema) != 5):
        print(
            f"{W12_NOT_READY}: tools not ready ({'; '.join(soft) or 'schema length != 5'}); "
            "using loop fallback schema for offline chat.",
            file=sys.stderr,
        )

    provider = args.provider or _default_provider()
    try:
        llm = _build_llm(provider)
    except Exception as exc:
        print(f"FAIL: cannot build LLM ({exc})", file=sys.stderr)
        return 2

    session = _new_session(
        SessionState,
        workspace=Path(args.workspace),
        robot_ip=args.robot,
        run_id=args.run_id,
        interactive=True,
        preauthorized=set(DEFAULT_RECOVERY_PREAUTHORIZED),
        max_steps=args.max_steps,
    )
    print(f"LabscriptAI chat  provider={provider}  workspace={session.workspace}")
    print(build_system_prompt(session).splitlines()[0])
    print("Type /quit to exit. … lines show work in progress; robot actions stay gated.")

    while True:
        try:
            line = input("you> ")
            while select.select([sys.stdin], [], [], 0)[0] and (more := sys.stdin.readline()):
                line += "\n" + more.rstrip("\n")
            line = line.strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0
        if not line:
            continue
        if line in {"/quit", "/exit", ":q"}:
            print("Bye.")
            return 0
        if line in {"/help", "help"}:
            line = "能做什么" if any("\u4e00" <= c <= "\u9fff" for c in line) else "what can you do"
        if line == "/status":
            print(
                json.dumps(
                    {
                        "workspace": str(session.workspace),
                        "robot_ip": session.robot_ip,
                        "robot_connected": session.robot_connected,
                        "active_run_id": session.active_run_id,
                        "provider": provider,
                        "messages": len(session.messages),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            continue
        try:
            reply = run_turn(
                line,
                session=session,
                llm=llm,
                interactive=True,
                on_event=lambda msg: print(f"… {msg}", flush=True),
            )
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            if args.verbose:
                traceback.print_exc()
            continue
        print(f"agent> {reply}")


def cmd_recover(args: argparse.Namespace) -> int:
    try:
        (
            _llm_mod,
            _GateDecision,
            _evaluate,
            _infer_context,
            _tools_schema,
            _execute,
            SessionState,
            _build_system_prompt,
            run_turn,
            soft,
        ) = _import_deps()
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if soft:
        print(f"{W12_NOT_READY}: {'; '.join(soft)} (recover will use loop fallback execute)", file=sys.stderr)

    provider = args.provider or _default_provider()
    try:
        llm = _build_llm(provider)
    except Exception as exc:
        print(f"FAIL: cannot build LLM ({exc})", file=sys.stderr)
        return 2

    interactive = not bool(args.yes)
    preauthorized: set[str] = set()
    if args.yes:
        # Narrow auto-allow for recover --yes: SAFE inspect/pause style only via gate SAFE list.
        preauthorized = {"inspect_robot_state", "pause_run"}

    session = _new_session(
        SessionState,
        workspace=Path(args.workspace),
        robot_ip=args.robot,
        run_id=args.run_id,
        interactive=interactive,
        preauthorized=preauthorized,
        max_steps=args.max_steps,
    )
    prompt = (
        f"Recover run {args.run_id} on robot {args.robot}. "
        "Call robot(op=status) first, then propose the safest next robot(op=act) if needed. "
        "Do not use bash to hit the robot."
    )
    try:
        reply = run_turn(prompt, session=session, llm=llm, interactive=interactive)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(reply)
    return 0


def cmd_daemon(args: argparse.Namespace) -> int:
    """Minimal outbox-wake stub: poll robot watch / sleep+status → user turn."""
    try:
        (
            _llm_mod,
            _GateDecision,
            _evaluate,
            _infer_context,
            _tools_schema,
            execute,
            SessionState,
            _build_system_prompt,
            run_turn,
            soft,
        ) = _import_deps()
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if soft:
        print(f"{W12_NOT_READY}: {'; '.join(soft)} (daemon outbox-only until tools land)", file=sys.stderr)

    provider = args.provider or _default_provider()
    try:
        llm = _build_llm(provider)
    except Exception as exc:
        print(f"FAIL: cannot build LLM ({exc})", file=sys.stderr)
        return 2

    session = _new_session(
        SessionState,
        workspace=Path(args.workspace),
        robot_ip=args.robot,
        run_id=args.run_id,
        interactive=False,
        max_steps=args.max_steps,
    )
    interval = max(1.0, float(args.interval))
    print(
        f"daemon watching run={args.run_id} robot={args.robot} "
        f"interval={interval}s (Ctrl-C to stop)"
    )
    seen: set[str] = set()
    try:
        while True:
            event_text = _poll_wake_event(
                execute=execute,
                workspace=session.workspace,
                robot_ip=session.robot_ip,
                run_id=args.run_id,
                seen=seen,
            )
            if event_text:
                print(f"[wake] {event_text[:200]}")
                try:
                    reply = run_turn(
                        event_text,
                        session=session,
                        llm=llm,
                        interactive=False,
                    )
                    print(f"agent> {reply}")
                except Exception as exc:
                    print(f"turn error: {exc}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\ndaemon stopped.")
        return 0


def _poll_wake_event(
    *,
    execute: Any,
    workspace: Path,
    robot_ip: str | None,
    run_id: str,
    seen: set[str],
) -> str | None:
    """Prefer tools.robot(op=watch); else read outbox wake.jsonl; else status snapshot."""
    # 1) outbox wake.jsonl written by suspend / external hooks
    wake_path = Path(workspace) / ".labscriptai" / "outbox" / "wake.jsonl"
    if wake_path.is_file():
        try:
            lines = wake_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for line in lines:
            if not line.strip() or line in seen:
                continue
            seen.add(line)
            return f"Outbox wake event: {line}"

    # 2) robot watch via tools (if W2 ready)
    if callable(execute):
        try:
            result = execute(
                "robot",
                {"op": "watch", "run_id": run_id},
                workspace=workspace,
                robot_ip=robot_ip,
                session={"active_run_id": run_id, "robot_connected": True},
            )
        except Exception as exc:
            result = {"error": str(exc)}
        fingerprint = json.dumps(result, sort_keys=True, default=str)
        if fingerprint not in seen and not (
            isinstance(result, dict) and result.get("error") in {"W2 tools not ready", "mcp_index_missing"}
        ):
            # Only wake on interesting payloads (errors / alerts / state changes)
            interesting = False
            if isinstance(result, dict):
                interesting = any(
                    key in result
                    for key in ("alert", "alerts", "error", "needs_attention", "events", "parsed_error")
                ) or result.get("status") in {"failed", "awaiting-recovery", "stopped"}
            if interesting:
                seen.add(fingerprint)
                return (
                    f"Runtime watch wake for run {run_id}: "
                    + json.dumps(result, ensure_ascii=False, default=str)[:2000]
                )

        # 3) fallback status poll (rate-limit by fingerprint)
        try:
            status = execute(
                "robot",
                {"op": "status", "run_id": run_id},
                workspace=workspace,
                robot_ip=robot_ip,
                session={"active_run_id": run_id, "robot_connected": True},
            )
        except Exception as exc:
            status = {"error": str(exc)}
        fp = "status:" + json.dumps(status, sort_keys=True, default=str)
        if fp not in seen and isinstance(status, dict):
            phase = str(status.get("status") or status.get("data", {}).get("status") or "")
            if phase.lower() in {"failed", "awaiting-recovery", "stopped", "blocked"}:
                seen.add(fp)
                return (
                    f"Robot status wake for run {run_id}: "
                    + json.dumps(status, ensure_ascii=False, default=str)[:2000]
                )
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="labscriptai",
        description="LabscriptAI lean agent. User entry: chat. doctor is a health check.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="Interactive REPL (one shared loop)")
    chat.add_argument("--workspace", default=".", help="Working directory for edit/bash/memory")
    chat.add_argument("--robot", default=None, help="Robot IP/host (normalized to :31950)")
    chat.add_argument(
        "--provider",
        choices=("offline", "deepseek"),
        default=None,
        help="LLM provider (default: deepseek; requires DEEPSEEK_API_KEY)",
    )
    chat.add_argument("--run-id", default=None, help="Optional active run id")
    chat.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Max tool steps per turn (0 = unlimited; default: LABSCRIPTAI_MAX_STEPS or unlimited)",
    )
    chat.add_argument("--verbose", action="store_true")
    chat.set_defaults(func=cmd_chat)

    recover = sub.add_parser("recover", help="One-shot recovery turn")
    recover.add_argument("--run-id", required=True)
    recover.add_argument("--robot", required=True)
    recover.add_argument("--workspace", default=".")
    recover.add_argument("--yes", action="store_true", help="Non-interactive (ask→suspend; SAFE may auto)")
    recover.add_argument(
        "--provider",
        choices=("offline", "deepseek"),
        default=None,
        help="LLM provider (default: deepseek; requires DEEPSEEK_API_KEY)",
    )
    recover.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Max tool steps per turn (0 = unlimited)",
    )
    recover.set_defaults(func=cmd_recover)

    daemon = sub.add_parser("daemon", help="Minimal outbox-wake poller")
    daemon.add_argument("--robot", required=True)
    daemon.add_argument("--run-id", required=True)
    daemon.add_argument("--workspace", default=".")
    daemon.add_argument("--interval", type=float, default=5.0)
    daemon.add_argument(
        "--provider",
        choices=("offline", "deepseek"),
        default=None,
        help="LLM provider (default: deepseek; requires DEEPSEEK_API_KEY)",
    )
    daemon.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Max tool steps per turn (0 = unlimited)",
    )
    daemon.set_defaults(func=cmd_daemon)

    doctor = sub.add_parser(
        "doctor",
        help="Health check for chat (Node/npm, API key, optional robot /health)",
        description=(
            "Health check for labscriptai chat (not a second workflow). "
            "Always checks Node >= 18, opentrons-mcp node_modules, index.js, "
            "DEEPSEEK_API_KEY (present/absent), and opentrons.cli / opentrons.simulate. "
            "--robot is optional and only probes http://IP:31950/health."
        ),
    )
    doctor.add_argument(
        "--robot",
        default=None,
        help="Robot IP/host; probe http://IP:31950/health (optional — toolchain checks always run)",
    )
    doctor.add_argument("--timeout", default=2.0, help="Timeout seconds for robot /health")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line entrypoint for the LabscriptAI runtime loop."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .actions import CandidateAction
from .adapters.robot_http import RobotHttpConfig, RobotHttpReadOnlyAdapter
from .adapters.mcp import McpToolConfig, OpentronsMcpRuntimeAdapter
from .agent_loop import ScriptedCandidateProvider, run_offline_loop
from .cases import collect_runtime_cases
from .chat_controller import RuntimeChatController
from .gatekeeper import evaluate_action
from .memory import append_memory_note, search_memory
from .model_adapter import OpenAICompatibleCandidateProvider, OpenAICompatibleChatProvider, OpenAICompatibleConfig
from .recovery_shadow_benchmark import (
    deepseek_provider_factory,
    offline_provider_for_case,
    run_shadow_benchmark,
)
from .state import RuntimeState


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="labscriptai.runtime.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="read robot/run state without moving hardware")
    inspect.add_argument("--robot-host", required=True)
    inspect.add_argument("--robot-port", type=int)
    inspect.add_argument("--robot-token")
    inspect.add_argument("--run-id")
    inspect.add_argument("--timeout-sec", type=float, default=10.0)

    mcp_inspect = subparsers.add_parser("mcp-inspect", help="read live state through the Opentrons MCP handlers")
    mcp_inspect.add_argument("--robot-ip", required=True)
    mcp_inspect.add_argument("--run-id")
    mcp_inspect.add_argument("--mcp-index", type=Path, default=Path("mcp-servers/opentrons-mcp/index.js"))
    mcp_inspect.add_argument("--timeout-sec", type=float, default=30.0)

    mcp_recover = subparsers.add_parser("mcp-recover", help="ask MCP for a recovery suggestion and optionally execute it")
    mcp_recover.add_argument("--robot-ip", required=True)
    mcp_recover.add_argument("--run-id", required=True)
    mcp_recover.add_argument("--mcp-index", type=Path, default=Path("mcp-servers/opentrons-mcp/index.js"))
    mcp_recover.add_argument("--timeout-sec", type=float, default=30.0)
    mcp_recover.add_argument("--execute-auto", action="store_true")

    collect = subparsers.add_parser("collect-cases", help="export read-only robot runs as runtime cases")
    collect.add_argument("--robot-host", required=True)
    collect.add_argument("--robot-port", type=int)
    collect.add_argument("--robot-token")
    collect.add_argument("--run-id", action="append", default=[])
    collect.add_argument("--limit", type=int, default=20)
    collect.add_argument("--include-succeeded", action="store_true")
    collect.add_argument("--output-dir", type=Path, default=Path("runs/runtime-cases/latest"))
    collect.add_argument("--timeout-sec", type=float, default=10.0)

    shadow = subparsers.add_parser("shadow-benchmark", help="score recovery suggestions without moving hardware")
    shadow.add_argument("--cases", type=Path, required=True)
    shadow.add_argument("--output-dir", type=Path, default=Path("runs/recovery-shadow/latest"))
    shadow.add_argument("--provider", choices=("offline", "deepseek"), default="offline")
    shadow.add_argument("--memory-dir", type=Path)

    memory_add = subparsers.add_parser("memory-add", help="append a Markdown runtime memory note")
    memory_add.add_argument("--memory-dir", type=Path, default=Path("runs/runtime-memory"))
    memory_add.add_argument("--title", required=True)
    memory_add.add_argument("--body", required=True)
    memory_add.add_argument("--tag", action="append", default=[])

    memory_search = subparsers.add_parser("memory-search", help="search Markdown runtime memory notes")
    memory_search.add_argument("--memory-dir", type=Path, default=Path("runs/runtime-memory"))
    memory_search.add_argument("query")
    memory_search.add_argument("--limit", type=int, default=5)

    chat = subparsers.add_parser("chat", help="open the LabscriptAI runtime conversation")
    chat.add_argument("--robot-host")
    chat.add_argument("--robot-port", type=int)
    chat.add_argument("--robot-token")
    chat.add_argument("--run-id", required=True)
    chat.add_argument("--package-dir", type=Path, required=True)
    chat.add_argument("--trace-path", type=Path, default=Path("runs/runtime-chat/trace.jsonl"))
    chat.add_argument("--patch-log-path", type=Path, default=Path("runs/runtime-chat/patch_log.jsonl"))
    chat.add_argument("--candidate-json", help="single candidate action JSON for non-interactive use")
    chat.add_argument("--dry-run", action="store_true")
    chat.add_argument("--simulation-pass", action="store_true")
    chat.add_argument("--provider", choices=("deepseek", "offline"), default="deepseek")
    chat.add_argument("--model", help="override DEEPSEEK_MODEL for this chat session")
    chat.add_argument("--authoring-tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    chat.add_argument("--authoring-output-dir", type=Path, default=Path("runs/tui-authoring"))
    chat.add_argument("--opentrons-python", help="Python executable used by unified authoring simulation tools")
    chat.add_argument("--authoring-max-steps", type=int, default=8)
    chat.add_argument("--authoring-skill-mode", choices=("off", "light", "full"), default="light")
    chat.add_argument("--authoring-tool-profile", choices=("minimal", "simulate", "kb"), default="kb")
    chat.add_argument("--authoring-simulation-timeout-sec", type=int, default=180)
    chat.add_argument("--unified-agent-chat", action="store_true", help="send plain chat messages to the unified agent loop")
    chat.add_argument("--allow-live-control", action="store_true", help="allow unified run.control to send robot run actions")
    chat.add_argument("--memory-dir", type=Path, default=Path("runs/runtime-memory"))
    chat.add_argument("--no-tui", action="store_true", help="disable the full-screen chat UI for non-interactive scripts")

    args = parser.parse_args(argv)
    if args.command == "inspect":
        return _inspect(args)
    if args.command == "mcp-inspect":
        return _mcp_inspect(args)
    if args.command == "mcp-recover":
        return _mcp_recover(args)
    if args.command == "collect-cases":
        return _collect_cases(args)
    if args.command == "shadow-benchmark":
        return _shadow_benchmark(args)
    if args.command == "memory-add":
        return _memory_add(args)
    if args.command == "memory-search":
        return _memory_search(args)
    if args.command == "chat":
        return _chat(args)
    return 2


def _inspect(args: argparse.Namespace) -> int:
    adapter = RobotHttpReadOnlyAdapter(
        RobotHttpConfig(
            host=args.robot_host,
            port=args.robot_port,
            token=args.robot_token,
            timeout_sec=args.timeout_sec,
        )
    )
    snapshot = adapter.snapshot(run_id=args.run_id)
    print(json.dumps(_status_summary(snapshot), indent=2, ensure_ascii=False))
    return 0


def _mcp_adapter(args: argparse.Namespace) -> OpentronsMcpRuntimeAdapter:
    return OpentronsMcpRuntimeAdapter(
        McpToolConfig(index_path=args.mcp_index, timeout_sec=args.timeout_sec)
    )


def _mcp_inspect(args: argparse.Namespace) -> int:
    adapter = _mcp_adapter(args)
    snapshot = adapter.recovery_snapshot(robot_ip=args.robot_ip, run_id=args.run_id)
    print(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if _contains_error(snapshot) else 0


def _mcp_recover(args: argparse.Namespace) -> int:
    adapter = _mcp_adapter(args)
    snapshot = adapter.recovery_snapshot(robot_ip=args.robot_ip, run_id=args.run_id)
    suggestion = snapshot.get("suggest_recovery_action")
    output: dict[str, Any] = {"snapshot": snapshot, "executed": False}
    if args.execute_auto and isinstance(suggestion, Mapping):
        payload = suggestion.get("data") if isinstance(suggestion.get("data"), Mapping) else suggestion
        if isinstance(payload, Mapping) and payload.get("auto_executable", True) is not False:
            output["execution"] = adapter.execute_suggested_recovery(
                robot_ip=args.robot_ip,
                run_id=args.run_id,
                suggestion=suggestion,
            )
            output["executed"] = True
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if _contains_error(output) else 0


def _contains_error(payload: Any) -> bool:
    if isinstance(payload, Mapping):
        if payload.get("error"):
            return True
        return any(_contains_error(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_error(item) for item in payload)
    return False


def _collect_cases(args: argparse.Namespace) -> int:
    adapter = RobotHttpReadOnlyAdapter(
        RobotHttpConfig(
            host=args.robot_host,
            port=args.robot_port,
            token=args.robot_token,
            timeout_sec=args.timeout_sec,
        )
    )
    summary = collect_runtime_cases(
        adapter,
        output_dir=args.output_dir,
        run_ids=tuple(args.run_id),
        limit=args.limit,
        include_succeeded=args.include_succeeded,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def _shadow_benchmark(args: argparse.Namespace) -> int:
    if args.provider == "deepseek":
        config = OpenAICompatibleConfig.from_env()
        factory = deepseek_provider_factory(config)
        model_id = config.model
    else:
        factory = offline_provider_for_case
        model_id = "offline-shadow"
    summary = run_shadow_benchmark(
        cases_path=args.cases,
        output_dir=args.output_dir,
        candidate_provider_factory=factory,
        model_id=model_id,
        memory_dir=args.memory_dir,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if summary["error_count"] == 0 else 1


def _memory_add(args: argparse.Namespace) -> int:
    path = append_memory_note(
        args.memory_dir,
        title=args.title,
        body=args.body,
        tags=tuple(args.tag),
    )
    print(json.dumps({"path": str(path)}, indent=2, ensure_ascii=False))
    return 0


def _memory_search(args: argparse.Namespace) -> int:
    hits = search_memory(args.memory_dir, args.query, limit=args.limit)
    print(json.dumps([hit.to_dict() for hit in hits], indent=2, ensure_ascii=False))
    return 0


def _chat(args: argparse.Namespace) -> int:
    adapter: RobotHttpReadOnlyAdapter | None = None
    if args.dry_run or not args.robot_host:
        state = RuntimeState(
            run_id=args.run_id,
            phase="ready" if args.dry_run else "preflight",
            robot={"id": "DRY-RUN"} if args.dry_run else {},
        )
    else:
        adapter = RobotHttpReadOnlyAdapter(
            RobotHttpConfig(
                host=args.robot_host,
                port=args.robot_port,
                token=args.robot_token,
            )
        )
        snapshot = adapter.snapshot(run_id=args.run_id)
        state = adapter.state_from_snapshot(run_id=args.run_id, snapshot=snapshot)
        if args.candidate_json or args.no_tui:
            print(json.dumps(_status_summary(snapshot), indent=2, ensure_ascii=False))

    if args.candidate_json:
        candidate_payload = json.loads(args.candidate_json)
    else:
        if args.no_tui:
            print(
                "chat without TUI is non-interactive. Pass --candidate-json for scripts, "
                "or remove --no-tui to open the full-screen chat window."
            )
            return 2
        config = _config_from_args(args)
        provider, chat_provider = _providers(args, config=config)

        def status_loader() -> tuple[RuntimeState, dict[str, Any] | None]:
            if adapter is None:
                return state, None
            refreshed = adapter.snapshot(run_id=args.run_id)
            return adapter.state_from_snapshot(run_id=args.run_id, snapshot=refreshed), refreshed

        unified_chat_handler = None
        if config is not None:
            from .unified_chat_bridge import UnifiedChatBridge

            bridge = UnifiedChatBridge(
                config=config,
                state=state,
                package_dir=args.package_dir,
                trace_path=args.trace_path,
                skill_mode=args.authoring_skill_mode,
                tool_profile=args.authoring_tool_profile,
                max_steps=args.authoring_max_steps,
                opentrons_python=args.opentrons_python,
                workspace_root=Path.cwd(),
                simulation_timeout_sec=args.authoring_simulation_timeout_sec,
                status_loader=status_loader if adapter is not None else None,
                robot_adapter=adapter,
                live_control_enabled=args.allow_live_control,
                memory_dir=args.memory_dir,
            )
            unified_chat_handler = bridge.handle_text

        controller = RuntimeChatController(
            state=state,
            package_dir=args.package_dir,
            trace_path=args.trace_path,
            patch_log_path=args.patch_log_path,
            candidate_provider=provider,
            chat_provider=chat_provider,
            authoring_tasks_path=args.authoring_tasks,
            authoring_output_dir=args.authoring_output_dir,
            authoring_opentrons_python=args.opentrons_python,
            authoring_max_steps=args.authoring_max_steps,
            authoring_skill_mode=args.authoring_skill_mode,
            authoring_tool_profile=args.authoring_tool_profile,
            authoring_simulation_timeout_sec=args.authoring_simulation_timeout_sec,
            unified_agent_chat=False,
            simulation_pass=args.simulation_pass,
            status_loader=status_loader if adapter is not None else None,
            unified_chat_handler=unified_chat_handler,
        )
        try:
            from .tui import RuntimeTuiApp
            from .poller import RuntimePoller
        except ImportError as exc:
            print(
                "Textual is required for the runtime chat window. "
                "Install project dependencies, or use --no-tui with --candidate-json for scripts."
            )
            print(str(exc))
            return 2
        poller = None
        if adapter is not None:
            poller = RuntimePoller(
                adapter=adapter,
                run_id=args.run_id,
                trace_path=args.trace_path,
                wake_handler=unified_chat_handler,
                initial_state=state,
            )
        return RuntimeTuiApp(controller, poller=poller).run()

    action = CandidateAction.from_mapping(candidate_payload)
    decision = evaluate_action(action, state)
    print(json.dumps({"check": decision.to_dict()}, indent=2, ensure_ascii=False))
    result = run_offline_loop(
        initial_state=state,
        package_dir=args.package_dir,
        trace_path=args.trace_path,
        patch_log_path=args.patch_log_path,
        candidate_provider=ScriptedCandidateProvider([action]),
        simulation_pass=args.simulation_pass,
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.decisions and result.decisions[-1].approved else 1


def _candidate_provider(args: argparse.Namespace):  # noqa: ANN201
    return _providers(args, config=_config_from_args(args))[0]


def _config_from_args(args: argparse.Namespace) -> OpenAICompatibleConfig | None:
    if args.provider == "offline":
        return None
    if args.model:
        os.environ["DEEPSEEK_MODEL"] = args.model
    try:
        return OpenAICompatibleConfig.from_env()
    except RuntimeError:
        if args.dry_run:
            return None
        raise


def _providers(args: argparse.Namespace, *, config: OpenAICompatibleConfig | None = None):  # noqa: ANN201
    if args.provider == "offline" or config is None:
        def offline_provider(state: RuntimeState) -> dict[str, Any]:
            request = str(state.observed.get("operator_request", ""))
            if any(token in request for token in ("恢复", "继续", "失败", "recover")):
                reason = "Dry-run demo plan. Set DEEPSEEK_API_KEY to use the model."
            else:
                reason = "Dry-run demo mode. Set DEEPSEEK_API_KEY to use the model."
            return {
                "action_type": "request_human_confirmation",
                "reason": reason,
                "parameters": {
                    "question": "This is an offline demo response."
                },
            }

        def offline_chat_provider(*, text: str, state: RuntimeState) -> str:
            del state
            if any("\u4e00" <= char <= "\u9fff" for char in text):
                return (
                    "我是 labscriptAI，一个给移液机器人运行阶段用的助手。"
                    "我可以帮你看当前 run 状态、解释为什么停住、以及从失败步骤后面继续。"
                    "现在是 dry-run 模式；设置 DEEPSEEK_API_KEY 后会接入真实模型回复。"
                )
            return (
                "I'm labscriptAI, a runtime assistant for liquid-handling robot runs. "
                "I can check run state, explain failures, and help plan how to continue from a failed step. "
                "This is dry-run mode; set DEEPSEEK_API_KEY to use the real model."
            )

        return offline_provider, offline_chat_provider
    return OpenAICompatibleCandidateProvider(config), OpenAICompatibleChatProvider(config)


def _status_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    run_history = snapshot.get("run_history") if isinstance(snapshot.get("run_history"), dict) else {}
    robot_health = snapshot.get("robot_health") if isinstance(snapshot.get("robot_health"), dict) else {}
    modules = snapshot.get("modules")
    return {
        "robot": {
            "serial": robot_health.get("robot_serial") or robot_health.get("robotSerial"),
            "model": robot_health.get("robot_model") or robot_health.get("robotModel"),
            "api_version": robot_health.get("api_version") or robot_health.get("apiVersion"),
        },
        "run": {
            "run_id": run_history.get("run_id"),
            "status": run_history.get("status"),
            "awaiting_recovery": run_history.get("awaiting_recovery"),
            "latest_failed_command": run_history.get("latest_failed_command"),
        },
        "module_count": len(modules) if isinstance(modules, list) else None,
    }


if __name__ == "__main__":
    raise SystemExit(main())

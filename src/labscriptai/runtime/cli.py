"""Command-line entrypoint for the LabscriptAI runtime loop."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .actions import CandidateAction
from .adapters.robot_http import RobotHttpConfig, RobotHttpReadOnlyAdapter
from .agent_loop import ScriptedCandidateProvider, run_offline_loop
from .cases import collect_runtime_cases
from .chat_controller import RuntimeChatController
from .gatekeeper import evaluate_action
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
    chat.add_argument("--no-tui", action="store_true", help="disable the full-screen chat UI for non-interactive scripts")

    args = parser.parse_args(argv)
    if args.command == "inspect":
        return _inspect(args)
    if args.command == "collect-cases":
        return _collect_cases(args)
    if args.command == "shadow-benchmark":
        return _shadow_benchmark(args)
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
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if summary["error_count"] == 0 else 1


def _chat(args: argparse.Namespace) -> int:
    adapter: RobotHttpReadOnlyAdapter | None = None
    if args.dry_run or not args.robot_host:
        state = RuntimeState(
            run_id=args.run_id,
            phase="recovering",
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
        provider, chat_provider = _providers(args)

        def status_loader() -> tuple[RuntimeState, dict[str, Any] | None]:
            if adapter is None:
                return state, None
            refreshed = adapter.snapshot(run_id=args.run_id)
            return adapter.state_from_snapshot(run_id=args.run_id, snapshot=refreshed), refreshed

        controller = RuntimeChatController(
            state=state,
            package_dir=args.package_dir,
            trace_path=args.trace_path,
            patch_log_path=args.patch_log_path,
            candidate_provider=provider,
            chat_provider=chat_provider,
            simulation_pass=args.simulation_pass,
            status_loader=status_loader if adapter is not None else None,
        )
        try:
            from .tui import RuntimeTuiApp
        except ImportError as exc:
            print(
                "Textual is required for the runtime chat window. "
                "Install project dependencies, or use --no-tui with --candidate-json for scripts."
            )
            print(str(exc))
            return 2
        return RuntimeTuiApp(controller).run()

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
    return _providers(args)[0]


def _providers(args: argparse.Namespace):  # noqa: ANN201
    if args.provider == "offline" or args.dry_run and not os.environ.get("DEEPSEEK_API_KEY"):
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
    if args.model:
        os.environ["DEEPSEEK_MODEL"] = args.model
    config = OpenAICompatibleConfig.from_env()
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

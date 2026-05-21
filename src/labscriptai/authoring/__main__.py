"""CLI for the LabscriptAI authoring agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from labscriptai.benchmark.tasks import load_authoring_tasks
from labscriptai.runtime.model_adapter import OpenAICompatibleConfig

from .agent import AuthoringAgent, OpenAICompatibleAuthoringClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--task-id", required=True)
    run.add_argument("--tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    run.add_argument("--output-dir", type=Path, default=Path("runs/authoring-agent/latest"))
    run.add_argument("--opentrons-python")
    run.add_argument("--workspace-root", type=Path)
    run.add_argument("--simulation-timeout-sec", type=int, default=180)
    run.add_argument("--max-steps", type=int, default=12)
    args = parser.parse_args(argv)

    tasks = {task.task_id: task for task in load_authoring_tasks(args.tasks)}
    if args.task_id not in tasks:
        raise SystemExit(f"unknown task id: {args.task_id}")
    config = OpenAICompatibleConfig.from_env(default_model="deepseek-v4-pro")
    agent = AuthoringAgent(
        client=OpenAICompatibleAuthoringClient(config),
        max_steps=args.max_steps,
    )
    result = agent.run(
        task=tasks[args.task_id],
        package_dir=args.output_dir / args.task_id / "package",
        trace_path=args.output_dir / args.task_id / "trace.jsonl",
        opentrons_python=args.opentrons_python,
        workspace_root=args.workspace_root,
        simulation_timeout_sec=args.simulation_timeout_sec,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

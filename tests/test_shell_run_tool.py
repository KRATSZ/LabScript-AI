from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.agent.loop import LabscriptAgentLoop
from labscriptai.agent.registry import build_default_registry
from labscriptai.agent.state import AgentState, PackageRef, TaskSpec
from labscriptai.agent.tools import ToolCall
from labscriptai.runtime.trace import TraceWriter


class ScriptedClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = iter(responses)
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(self, messages, tools):  # noqa: ANN001, ANN201
        del messages, tools
        self.input_tokens += 1
        self.output_tokens += 1
        self.total_tokens += 2
        return next(self.responses)


def _state(root: Path) -> AgentState:
    package_dir = root / "package"
    package_dir.mkdir()
    (package_dir / "protocol.py").write_text("metadata = {'apiLevel': '2.20'}\n", encoding="utf-8")
    return AgentState(
        run_id="run-1",
        mode="run",
        phase="running",
        task_spec=TaskSpec(task_id="TUI", prompt="inspect"),
        package=PackageRef.from_dir(package_dir),
        trace_path=root / "trace.jsonl",
        trace=TraceWriter(root / "trace.jsonl"),
        permissions=frozenset({"shell.run"}),
        robot_status={"id": "DRY-RUN"},
    )


class ShellRunToolTests(unittest.TestCase):
    def test_shell_run_allows_ls_in_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _state(root)
            registry = build_default_registry(workspace_root=root)

            result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["ls", "."], "cwd": "package"}),
                state,
            )

        self.assertTrue(result.ok)
        self.assertIn("protocol.py", result.content["stdout"])

    def test_shell_run_allows_rg_in_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _state(root)
            registry = build_default_registry(workspace_root=root)

            result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["rg", "metadata", "protocol.py"], "cwd": "package"}),
                state,
            )

        self.assertTrue(result.ok)
        self.assertIn("metadata", result.content["stdout"])

    def test_shell_run_blocks_dangerous_commands_and_sensitive_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _state(root)
            registry = build_default_registry(workspace_root=root)

            bash_result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["bash", "-c", "echo hi"], "cwd": "package"}),
                state,
            )
            rm_result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["rm", "protocol.py"], "cwd": "package"}),
                state,
            )
            env_result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["cat", ".env"], "cwd": "workspace"}),
                state,
            )
            escape_result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["cat", "../secret.txt"], "cwd": "package"}),
                state,
            )

        self.assertTrue(bash_result.decision.blocked)
        self.assertTrue(rm_result.decision.blocked)
        self.assertTrue(env_result.decision.blocked)
        self.assertTrue(escape_result.decision.blocked)

    def test_shell_run_timeout_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _state(root)
            registry = build_default_registry(workspace_root=root)

            result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["tail", "-f", "protocol.py"], "cwd": "package", "timeout_sec": 1}),
                state,
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "timeout")

    def test_shell_run_redacts_env_lines_from_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("DEEPSEEK_API_KEY=secret-value\n", encoding="utf-8")
            state = _state(root)
            registry = build_default_registry(workspace_root=root)

            result = registry.call_with_gating(
                ToolCall("shell.run", {"command": ["rg", "-uu", "DEEPSEEK", "."], "cwd": "workspace"}),
                state,
            )

        self.assertTrue(result.ok)
        self.assertNotIn("secret-value", result.content["stdout"])
        self.assertIn("<redacted sensitive line>", result.content["stdout"])

    def test_shell_run_trace_records_gate_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _state(root)
            loop = LabscriptAgentLoop(
                client=ScriptedClient(
                    [
                        {"tool_calls": [{"name": "shell.run", "arguments": {"command": ["ls", "."], "cwd": "package"}}]},
                        {"final": {"completed": False}},
                    ]
                ),
                registry=build_default_registry(workspace_root=root),
                max_steps=2,
            )

            loop.run(state)
            events = [
                json.loads(line)
                for line in (root / "trace.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        event_types = [event["event_type"] for event in events]
        self.assertIn("candidate_tool_call", event_types)
        self.assertIn("gatekeeper_decision", event_types)
        self.assertIn("tool_result", event_types)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.runtime.adapters.mcp import McpToolConfig, OpentronsMcpRuntimeAdapter


class RuntimeMcpAdapterTests(unittest.TestCase):
    def test_call_tool_invokes_node_bridge(self) -> None:
        completed = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": json.dumps({"data": {"ok": True}}), "stderr": ""},
        )()

        with patch("subprocess.run", return_value=completed) as run:
            adapter = OpentronsMcpRuntimeAdapter(
                McpToolConfig(index_path=Path("mcp-servers/opentrons-mcp/index.js"))
            )
            result = adapter.call_tool("robot_status", {"robot_ip": "10.0.0.2"})

        self.assertEqual(result["data"]["ok"], True)
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["LABSCRIPTAI_MCP_TOOL"], "robot_status")
        self.assertIn("10.0.0.2", env["LABSCRIPTAI_MCP_ARGS"])

    def test_recovery_snapshot_calls_read_and_recovery_tools(self) -> None:
        adapter = OpentronsMcpRuntimeAdapter()
        calls: list[str] = []

        def fake_call(tool_name, arguments):  # noqa: ANN001
            calls.append(tool_name)
            return {"data": {"tool": tool_name, "run_status": "awaiting-recovery"}}

        with patch.object(adapter, "call_tool", side_effect=fake_call):
            snapshot = adapter.recovery_snapshot(robot_ip="10.0.0.2", run_id="run-1")

        self.assertEqual(
            calls,
            ["robot_status", "module_status", "parse_error", "suggest_recovery_action"],
        )
        state = adapter.state_from_snapshot(
            robot_ip="10.0.0.2",
            run_id="run-1",
            snapshot=snapshot,
        )
        self.assertEqual(state.phase, "recovering")
        self.assertEqual(state.expected["backend"], "opentrons-mcp")
        self.assertEqual(state.expected["autonomy_mode"], "auto")

    def test_execute_suggested_recovery_forwards_context_arguments(self) -> None:
        adapter = OpentronsMcpRuntimeAdapter()
        captured: dict[str, object] = {}

        def fake_call(tool_name, arguments):  # noqa: ANN001
            captured["tool_name"] = tool_name
            captured["arguments"] = dict(arguments)
            return {"data": {"ok": True}}

        with patch.object(adapter, "call_tool", side_effect=fake_call):
            adapter.execute_suggested_recovery(
                robot_ip="10.0.0.2",
                run_id="run-1",
                suggestion={
                    "branch": "retry_pick_up_tip_with_next_candidate",
                    "session_id": "session-1",
                    "recovery_well": "C1",
                    "tiprack_slot": "C2",
                },
            )

        self.assertEqual(captured["tool_name"], "execute_protocol_recovery")
        self.assertEqual(
            captured["arguments"],
            {
                "robot_ip": "10.0.0.2",
                "run_id": "run-1",
                "recovery_branch": "retry_pick_up_tip_with_next_candidate",
                "session_id": "session-1",
                "recovery_well": "C1",
                "tiprack_slot": "C2",
            },
        )


if __name__ == "__main__":
    unittest.main()

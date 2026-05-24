from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from labscriptai.agent.tools import ToolCall
from labscriptai.authoring.agent import _native_tool_specs
from labscriptai.runtime.chat_controller import ChatMessage, ChatResponse, RuntimeChatController
from labscriptai.runtime.model_adapter import OpenAICompatibleConfig
from labscriptai.runtime.state import RuntimeState
from labscriptai.runtime.unified_chat_bridge import TuiAgentClient, UnifiedChatBridge


RESPONSES: list[dict] = []


class FakeClient:
    def __init__(self, _config):  # noqa: ANN001
        self.responses = list(RESPONSES)
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(self, messages, tools):  # noqa: ANN001, ANN201
        del messages, tools
        self.input_tokens += 1
        self.output_tokens += 1
        self.total_tokens += 2
        return self.responses.pop(0)


class FakeRobotAdapter:
    def __init__(self) -> None:
        self.control_calls: list[dict[str, str]] = []

    def snapshot(self, *, run_id=None):  # noqa: ANN001
        return {
            "robot_health": {"robot_serial": "FLX-TUI", "robot_model": "Flex"},
            "run_history": {"run_id": run_id, "status": "running"},
        }

    def state_from_snapshot(self, *, run_id: str, snapshot):  # noqa: ANN001
        return RuntimeState(
            run_id=run_id,
            phase="running",
            robot={"host": "192.0.2.10", "id": "FLX-TUI", "model": "Flex"},
            observed=snapshot,
        )

    def control_run(self, *, run_id: str, action_type: str) -> dict:
        self.control_calls.append({"run_id": run_id, "action_type": action_type})
        return {
            "run_id": run_id,
            "action_type": action_type,
            "opentrons_action_type": "pause",
            "action": {"id": "action-1"},
            "snapshot": self.snapshot(run_id=run_id),
        }


def _config() -> OpenAICompatibleConfig:
    return OpenAICompatibleConfig(base_url="https://example.invalid", api_key="key", model="model")


class UnifiedChatBridgeTests(unittest.TestCase):
    def test_run_tool_specs_use_provider_safe_names(self) -> None:
        native_tools = _native_tool_specs([{"name": "robot.inspect"}, {"name": "package.read_write"}])
        names = [tool["function"]["name"] for tool in native_tools]

        self.assertEqual(names, ["robot_inspect", "package_read_write"])
        self.assertEqual(ToolCall.from_model({"name": "robot_inspect"}).name, "robot.inspect")
        self.assertEqual(ToolCall.from_model({"name": "package_read_write"}).name, "package.read_write")

    def test_tui_agent_client_accepts_plain_text_final_answer(self) -> None:
        class Response:
            def __enter__(self):  # noqa: ANN204
                return self

            def __exit__(self, *args):  # noqa: ANN002, ANN204
                return None

            def read(self) -> bytes:
                return json.dumps({"choices": [{"message": {"content": "plain hello"}}]}).encode()

        client = TuiAgentClient(_config(), opener=lambda req, timeout: Response())

        response = client.complete([{"role": "user", "content": "hi"}], [])

        self.assertEqual(response, {"final": {"message": "plain hello", "completed": False}})

    def test_plain_chat_returns_final_without_authoring(self) -> None:
        global RESPONSES
        RESPONSES = [{"final": {"message": "Hi, I am labscriptAI."}}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("labscriptai.runtime.unified_chat_bridge.TuiAgentClient", FakeClient):
                bridge = UnifiedChatBridge(
                    config=_config(),
                    state=RuntimeState(run_id="run-1", robot={"id": "DRY-RUN"}),
                    package_dir=root / "package",
                    trace_path=root / "trace.jsonl",
                )
                response = bridge.handle_text("hi", language="en")

            rendered = "\n".join(line for message in response.messages for line in message.lines)
            self.assertIn("Hi, I am labscriptAI", rendered)
            self.assertFalse((root / "package" / "protocol.py").exists())

    def test_protocol_request_can_write_package(self) -> None:
        global RESPONSES
        RESPONSES = [
            {
                "tool_calls": [
                    {
                        "name": "package.read_write",
                        "arguments": {"op": "write", "path": "protocol.py", "content": "metadata = {}\n"},
                    }
                ]
            },
            {"final": {"message": "协议草稿已写入。"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("labscriptai.runtime.unified_chat_bridge.TuiAgentClient", FakeClient):
                bridge = UnifiedChatBridge(
                    config=_config(),
                    state=RuntimeState(run_id="run-1", robot={"id": "DRY-RUN"}),
                    package_dir=root / "package",
                    trace_path=root / "trace.jsonl",
                )
                response = bridge.handle_text("帮我生成一个 PCR 协议", language="zh")

            rendered = "\n".join(line for message in response.messages for line in message.lines)
            self.assertIn("协议草稿已写入", rendered)
            self.assertEqual((root / "package" / "protocol.py").read_text(encoding="utf-8"), "metadata = {}\n")

    def test_controller_routes_package_work_to_unified_handler(self) -> None:
        calls: list[str] = []

        def handler(text: str, *, language: str) -> ChatResponse:
            calls.append(f"{language}:{text}")
            return ChatResponse((ChatMessage("assistant", "labscriptAI", ("handled",)),))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", robot={"id": "DRY-RUN"}),
                package_dir=root / "package",
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch.jsonl",
                candidate_provider=lambda state: None,
                unified_agent_chat=True,
                unified_chat_handler=handler,
            )
            response = controller.handle_text("帮我生成一个 PCR 协议草稿")

        self.assertEqual(calls, ["zh:帮我生成一个 PCR 协议草稿"])
        self.assertEqual(response.messages[0].lines, ("handled",))

    def test_controller_keeps_plain_chat_out_of_unified_handler(self) -> None:
        unified_calls: list[str] = []
        chat_calls: list[str] = []

        def handler(text: str, *, language: str) -> ChatResponse:
            unified_calls.append(f"{language}:{text}")
            return ChatResponse((ChatMessage("assistant", "labscriptAI", ("unified",)),))

        def chat_provider(*, text, state, context):  # noqa: ANN001, ANN202
            del state, context
            chat_calls.append(text)
            return "正常聊天回复"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", robot={"id": "DRY-RUN"}),
                package_dir=root / "package",
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch.jsonl",
                candidate_provider=lambda state: None,
                chat_provider=chat_provider,
                unified_chat_handler=handler,
            )
            response = controller.handle_text("怎么说")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertEqual(unified_calls, [])
        self.assertEqual(chat_calls, [])
        self.assertIn("你可以像聊天一样直接说需求", rendered)

    def test_unified_response_hides_trace_and_package_paths(self) -> None:
        global RESPONSES
        RESPONSES = [{"final": {"message": "协议草稿已写入。"}}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("labscriptai.runtime.unified_chat_bridge.TuiAgentClient", FakeClient):
                bridge = UnifiedChatBridge(
                    config=_config(),
                    state=RuntimeState(run_id="run-1", robot={"id": "DRY-RUN"}),
                    package_dir=root / "package",
                    trace_path=root / "trace.jsonl",
                )
                response = bridge.handle_text("帮我生成一个 PCR 协议", language="zh")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertIn("协议草稿已写入", rendered)
        self.assertNotIn("trace:", rendered)
        self.assertNotIn("package:", rendered)

    def test_unified_ellipsis_final_gets_user_friendly_fallback(self) -> None:
        global RESPONSES
        RESPONSES = [{"final": {"message": "..."}}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("labscriptai.runtime.unified_chat_bridge.TuiAgentClient", FakeClient):
                bridge = UnifiedChatBridge(
                    config=_config(),
                    state=RuntimeState(run_id="run-1", robot={"id": "DRY-RUN"}),
                    package_dir=root / "package",
                    trace_path=root / "trace.jsonl",
                )
                response = bridge.handle_text("什么叫恢复阶段？", language="zh")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertNotEqual(rendered.strip(), "...")
        self.assertIn("没拿到一条像样的回复", rendered)

    def test_unified_chat_inspects_robot_through_injected_adapter(self) -> None:
        global RESPONSES
        RESPONSES = [
            {
                "tool_calls": [
                    {
                        "name": "robot.inspect",
                        "arguments": {"source": "http", "host": "192.0.2.10"},
                    }
                ]
            },
            {"final": {"message": "机器人在线。"}},
        ]
        adapter = FakeRobotAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("labscriptai.runtime.unified_chat_bridge.TuiAgentClient", FakeClient):
                bridge = UnifiedChatBridge(
                    config=_config(),
                    state=RuntimeState(run_id="run-1", phase="running", robot={"host": "192.0.2.10"}),
                    package_dir=root / "package",
                    trace_path=root / "trace.jsonl",
                    robot_adapter=adapter,
                )
                response = bridge.handle_text("看看机器人现在怎么样", language="zh")

            rendered = "\n".join(line for message in response.messages for line in message.lines)
            self.assertIn("robot.inspect: ok", rendered)
            self.assertIn("机器人在线", rendered)
            self.assertEqual(bridge.state.robot["id"], "FLX-TUI")

    def test_unified_chat_live_run_control_invokes_robot_adapter(self) -> None:
        global RESPONSES
        RESPONSES = [
            {
                "tool_calls": [
                    {
                        "name": "run.control",
                        "arguments": {
                            "action_type": "pause_run",
                            "run_id": "run-1",
                            "reason": "operator asked to pause",
                            "dry_run": False,
                        },
                    }
                ]
            }
        ]
        adapter = FakeRobotAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("labscriptai.runtime.unified_chat_bridge.TuiAgentClient", FakeClient):
                bridge = UnifiedChatBridge(
                    config=_config(),
                    state=RuntimeState(
                        run_id="run-1",
                        phase="running",
                        robot={"host": "192.0.2.10", "id": "FLX-TUI"},
                    ),
                    package_dir=root / "package",
                    trace_path=root / "trace.jsonl",
                    robot_adapter=adapter,
                    live_control_enabled=True,
                )
                response = bridge.handle_text("暂停当前 run", language="zh")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertIn("run.control: ok", rendered)
        self.assertEqual(adapter.control_calls, [{"run_id": "run-1", "action_type": "pause_run"}])
        self.assertEqual(bridge.state.phase, "paused")


if __name__ == "__main__":
    unittest.main()

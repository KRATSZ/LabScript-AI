from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.runtime.chat_controller import RuntimeChatController
from labscriptai.runtime.state import RuntimeState
from test_package_validator import write_valid_package


class RuntimeChatControllerTests(unittest.TestCase):
    def test_natural_language_status_request_refreshes_panel_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            controller = RuntimeChatController(
                state=RuntimeState(
                    run_id="run-1",
                    phase="recovering",
                    robot={"id": "DRY-RUN"},
                    used_tips=("A1",),
                    treated_wells=("plate:A1",),
                ),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: None,
            )

            response = controller.handle_text("现在机器人怎么了？")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertIn("右下角的 Run State 面板", rendered)
        self.assertNotIn("机器人：DRY-RUN", rendered)

    def test_status_request_refreshes_then_uses_chat_provider_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            calls = {"status": 0, "context": {}}

            def status_loader():  # noqa: ANN202
                calls["status"] += 1
                return (
                    RuntimeState(run_id="run-1", phase="paused", robot={"id": "LIVE-BOT"}),
                    {"run_history": {"status": "paused"}},
                )

            def chat_provider(*, text, state, context):  # noqa: ANN001, ANN202
                del text
                calls["context"] = context
                return f"Model says phase is {state.phase}."

            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: None,
                chat_provider=chat_provider,
                status_loader=status_loader,
            )

            response = controller.handle_text("what is the status?")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertEqual(calls["status"], 1)
        self.assertEqual(calls["context"]["intent"], "status")
        self.assertEqual(calls["context"]["status_summary"]["robot"], "LIVE-BOT")
        self.assertIn("Model says phase is paused", rendered)

    def test_recover_check_and_approve_writes_logs(self) -> None:
        def provider(state):  # noqa: ANN001, ANN202
            self.assertEqual(state.observed["operator_request"], "从失败的地方继续")
            return {
                "action_type": "validate_continuation_patch",
                "reason": "Validate a safe continuation patch.",
                "parameters": {
                    "patch": {
                        "schema_version": "0.1",
                        "patch_id": "patch-chat",
                        "recovery_type": "continuation_protocol",
                        "operations": [
                            {
                                "op_type": "transfer",
                                "tip": "A2",
                                "source_well": "reservoir:A2",
                                "destination_well": "plate:A2",
                                "reagent": "buffer",
                                "volume_ul": 10,
                            }
                        ],
                    }
                },
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            patch_log_path = root / "patch_log.jsonl"
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=patch_log_path,
                candidate_provider=provider,
                simulation_pass=True,
            )

            recover_response = controller.handle_text("从失败的地方继续")
            approve_response = controller.handle_text("确认执行")
            patch_log_exists = patch_log_path.exists()

        recover_rendered = "\n".join(line for message in recover_response.messages for line in message.lines)
        approve_rendered = "\n".join(line for message in approve_response.messages for line in message.lines)
        self.assertIn("检查结果：可以继续", recover_rendered)
        self.assertIn("已经记录这个恢复方案", approve_rendered)
        self.assertTrue(patch_log_exists)

    def test_recover_uses_model_for_visible_wording_when_available(self) -> None:
        def provider(state):  # noqa: ANN001, ANN202
            del state
            return {
                "action_type": "validate_continuation_patch",
                "reason": "Validate a safe continuation patch.",
                "parameters": {
                    "patch": {
                        "schema_version": "0.1",
                        "patch_id": "patch-chat",
                        "recovery_type": "continuation_protocol",
                        "operations": [],
                    }
                },
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            calls = {"context": {}}

            def chat_provider(*, text, state, context):  # noqa: ANN001, ANN202
                del text, state
                calls["context"] = context
                return "我看了一下，可以从失败点后面继续。"

            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=provider,
                chat_provider=chat_provider,
                simulation_pass=True,
            )

            response = controller.handle_text("从失败的地方继续")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertEqual(calls["context"]["intent"], "recovery_plan")
        self.assertIn("我看了一下", rendered)
        self.assertNotIn("检查结果", rendered)

    def test_blocked_candidate_cannot_be_approved(self) -> None:
        def provider(state):  # noqa: ANN001, ANN202
            del state
            return {
                "action_type": "aspirate",
                "reason": "Unsafe direct motion.",
                "parameters": {},
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            patch_log_path = root / "patch_log.jsonl"
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=patch_log_path,
                candidate_provider=provider,
                simulation_pass=True,
            )

            blocked = controller.handle_text("帮我恢复")
            approved = controller.handle_text("确认执行")

        blocked_rendered = "\n".join(line for message in blocked.messages for line in message.lines)
        approved_rendered = "\n".join(line for message in approved.messages for line in message.lines)
        self.assertIn("这个动作不能直接做: aspirate", blocked_rendered)
        self.assertIn("这个方案还有问题", approved_rendered)
        self.assertFalse(patch_log_path.exists())

    def test_greeting_routes_to_chat_provider_not_recovery_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            calls = {"recovery": 0, "chat": 0, "context": {}}

            def provider(state):  # noqa: ANN001, ANN202
                del state
                calls["recovery"] += 1
                return None

            def chat_provider(*, text, state, context):  # noqa: ANN001, ANN202
                del state
                calls["chat"] += 1
                calls["context"] = context
                return f"模型回复：{text}"

            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=provider,
                chat_provider=chat_provider,
            )

            response = controller.handle_text("你好")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertIn("模型回复：你好", rendered)
        self.assertEqual(calls["recovery"], 0)
        self.assertEqual(calls["chat"], 1)
        self.assertEqual(calls["context"]["intent"], "general_chat")

    def test_english_greeting_uses_chat_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            calls = {"text": ""}

            def chat_provider(*, text, state, context):  # noqa: ANN001, ANN202
                del state, context
                calls["text"] = text
                return "Hi, I am labscriptAI."

            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: None,
                chat_provider=chat_provider,
            )

            response = controller.handle_text("hi")

        rendered = "\n".join([response.messages[0].title, *response.messages[0].lines])
        self.assertEqual(calls["text"], "hi")
        self.assertIn("Hi, I am labscriptAI", rendered)
        self.assertNotIn("你好", rendered)

    def test_free_chat_uses_chat_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            calls = {"text": ""}

            def chat_provider(*, text, state):  # noqa: ANN001, ANN202
                calls["text"] = text
                self.assertEqual(state.run_id, "run-1")
                return "I am labscriptAI. I can help with this run."

            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: None,
                chat_provider=chat_provider,
            )

            response = controller.handle_text("please introduce yourself!")

        rendered = "\n".join(line for message in response.messages for line in message.lines)
        self.assertEqual(calls["text"], "please introduce yourself!")
        self.assertIn("I am labscriptAI", rendered)

    def test_reject_clears_pending_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: {
                    "action_type": "request_human_confirmation",
                    "reason": "Ask the operator.",
                    "parameters": {"question": "Continue?"},
                },
            )

            controller.handle_text("帮我恢复")
            response = controller.handle_text("不要执行")

        self.assertIsNone(controller.pending_action)
        self.assertIn("已丢弃", response.messages[0].lines[0])


if __name__ == "__main__":
    unittest.main()

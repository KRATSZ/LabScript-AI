from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from labscriptai.runtime.chat_controller import RuntimeChatController
from labscriptai.runtime.state import RuntimeState
from labscriptai.runtime.tui import RuntimeTuiApp
from test_package_validator import write_valid_package


class RuntimeTuiTests(unittest.IsolatedAsyncioTestCase):
    async def test_tui_mounts_and_accepts_status_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-demo", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: None,
            )
            app = RuntimeTuiApp(controller)

            async with app.run_test() as pilot:
                await pilot.click("#composer")
                app.query_one("#composer").value = "现在机器人怎么了？"
                await pilot.press("enter")
                await pilot.pause(0.1)
                status_card = app.query_one("#status-card")

        self.assertIn("DRY-RUN", str(status_card.renderable))

    async def test_tui_shows_thinking_while_worker_runs(self) -> None:
        def slow_provider(state):  # noqa: ANN001, ANN202
            del state
            time.sleep(0.15)
            return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-demo", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=slow_provider,
            )
            app = RuntimeTuiApp(controller)

            async with app.run_test() as pilot:
                await pilot.click("#composer")
                app.query_one("#composer").value = "help me recover"
                await pilot.press("enter")
                await pilot.pause(0.03)
                activity_busy = str(app.query_one("#activity").renderable)
                await pilot.pause(0.25)
                activity_done = str(app.query_one("#activity").renderable)

        self.assertIn("labscriptAI is thinking", activity_busy)
        self.assertEqual(activity_done, "Ready")

    async def test_tui_copy_command_writes_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            controller = RuntimeChatController(
                state=RuntimeState(run_id="run-demo", phase="recovering", robot={"id": "DRY-RUN"}),
                package_dir=package_dir,
                trace_path=root / "trace.jsonl",
                patch_log_path=root / "patch_log.jsonl",
                candidate_provider=lambda state: None,
            )
            app = RuntimeTuiApp(controller)

            async with app.run_test() as pilot:
                await pilot.click("#composer")
                app.query_one("#composer").value = "hi"
                await pilot.press("enter")
                await pilot.pause(0.1)
                app.query_one("#composer").value = "/copy"
                await pilot.press("enter")
                transcript = app.transcript_path.read_text(encoding="utf-8")

        self.assertIn("[You]", transcript)
        self.assertIn("hi", transcript)


if __name__ == "__main__":
    unittest.main()

"""Textual runtime chat UI for LabscriptAI."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.worker import Worker
from textual.widgets import Footer, Input, Label, RichLog, Static

from .chat_controller import ChatMessage, RuntimeChatController
from .poller import PollResult, RuntimePoller


class RuntimeTuiApp(App[int]):
    """Full-screen chat surface inspired by Claude Code style conversations."""

    CSS = """
    Screen {
        background: #061014;
        color: #d9f4ee;
    }

    #brand {
        height: 9;
        padding: 1 2;
        background: #061014;
        border-bottom: solid #20d6a4;
    }

    #brand-title {
        text-style: bold;
        color: #30e7b1;
    }

    #brand-subtitle {
        color: #7dd3fc;
    }

    #main {
        height: 1fr;
    }

    #chat {
        width: 1fr;
        height: 1fr;
        border: round #1fb6ff;
        padding: 1 2;
        background: #07171d;
    }

    #side {
        width: 34;
        height: 1fr;
        padding: 0 1;
        background: #081d20;
    }

    #side-spacer {
        height: 1fr;
    }

    #status-box {
        height: auto;
        border: round #c084fc;
        padding: 1;
        background: #140f24;
    }

    #status-title {
        text-style: bold;
        color: #d8b4fe;
        margin-bottom: 1;
    }

    #status-card {
        height: auto;
        color: #d9f4ee;
    }

    #activity {
        height: 1;
        color: #7dd3fc;
        padding-left: 2;
    }

    #composer {
        height: 3;
        border: round #20d6a4;
        background: #061014;
        margin-top: 1;
    }

    .hint {
        color: #7aa7a5;
    }

    .copy-hint {
        color: #c084fc;
    }
    """

    BINDINGS = [
        ("ctrl+c", "cancel_or_quit", "Cancel"),
        ("ctrl+d", "quit", "Quit"),
        ("f1", "help", "Help"),
        ("ctrl+slash", "help", "Help"),
        ("ctrl+l", "refresh_status", "Refresh"),
        ("ctrl+y", "copy_transcript", "Copy"),
    ]

    SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    TITLE = "labscriptAI"
    SUB_TITLE = "runtime chat"

    def __init__(self, controller: RuntimeChatController, *, poller: RuntimePoller | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.poller = poller
        self._spinner_index = 0
        self._thinking = False
        self._polling = False
        self._next_poll_at = 0.0
        self.transcript_path = self._default_transcript_path()

    def compose(self) -> ComposeResult:
        with Vertical(id="brand"):
            yield Static(
                "[bold #30e7b1]"
                " _       _                   _       _      _    ___ \n"
                "| | __ _| |__  ___  ___ _ __(_)_ __ | |_   / \\  |_ _|\n"
                "| |/ _` | '_ \\/ __|/ __| '__| | '_ \\| __| / _ \\  | | \n"
                "| | (_| | |_) \\__ \\ (__| |  | | |_) | |_ / ___ \\ | | \n"
                "|_|\\__,_|_.__/|___/\\___|_|  |_| .__/ \\__/_/   \\_\\___|\n"
                "                              |_|[/]",
                id="brand-title",
            )
            yield Static("Talk to labscriptAI. In unified mode, describe the task and the agent uses tools directly.", id="brand-subtitle")
        with Horizontal(id="main"):
            yield RichLog(id="chat", markup=True, wrap=True, highlight=True)
            with Vertical(id="side"):
                yield Static(
                    "Try:\nWhat is the status?\nWhy did it stop?\nContinue from the failed step.\n\n"
                    "Shortcuts:\n/status /ledger /recover\n/approve /reject\n/exit",
                    classes="hint",
                )
                yield Static("Copy: /copy or Ctrl+Y", classes="copy-hint")
                yield Static("", id="side-spacer")
                with Vertical(id="status-box"):
                    yield Label("Run State", id="status-title")
                    yield Static("", id="status-card")
        yield Static("Ready", id="activity")
        yield Input(placeholder="Message labscriptAI...", id="composer")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#composer", Input).focus()
        self._render_response(self.controller.welcome())
        self.set_interval(0.12, self._tick_spinner)
        if self.poller is not None:
            self._next_poll_at = time.monotonic()
            self.set_interval(1.0, self._maybe_poll_runtime)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        self._append_user(text)
        if text.strip().lower() == "/copy":
            self.action_copy_transcript()
            return
        self._start_thinking()
        event.input.disabled = True
        event.input.placeholder = "labscriptAI is thinking..."
        self.run_worker(
            lambda: self._handle_text_with_min_delay(text),
            name="chat-response",
            group="chat",
            exclusive=True,
            thread=True,
            exit_on_error=False,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        worker = event.worker
        if worker.name == "runtime-poll" and worker.is_finished:
            self._polling = False
            if worker.state.name == "SUCCESS" and worker.result is not None:
                self._render_poll_result(worker.result)
            elif worker.state.name == "ERROR":
                error = str(worker.error) if worker.error else "Unknown polling error"
                self._append_message(ChatMessage("error", "Runtime Polling", (error,)))
            if self.poller is not None:
                self._next_poll_at = time.monotonic() + self.poller.interval_sec()
            return
        if worker.name != "chat-response" or not worker.is_finished:
            return
        self._stop_thinking()
        composer = self.query_one("#composer", Input)
        composer.disabled = False
        composer.placeholder = "Message labscriptAI..."
        composer.focus()
        if worker.state.name == "SUCCESS" and worker.result is not None:
            self._render_response(worker.result)
        elif worker.state.name == "ERROR":
            error = str(worker.error) if worker.error else "Unknown error"
            self._append_message(ChatMessage("error", "Error", (error,)))
        self._refresh_status_card()

    def action_cancel_or_quit(self) -> None:
        if self.controller.pending_action is not None:
            self._render_response(self.controller.reject_pending())
        else:
            self.exit(0)

    def action_help(self) -> None:
        self._render_response(self.controller.handle_text("/help"))

    def action_refresh_status(self) -> None:
        self._render_response(self.controller.handle_text("/status"))

    def action_copy_transcript(self) -> None:
        ok = self._copy_transcript_to_clipboard()
        if ok:
            self._append_message(ChatMessage("system", "Copied", (f"Transcript copied. File: {self.transcript_path}",)))
        else:
            self._append_message(ChatMessage("system", "Transcript Saved", (f"Copy from file: {self.transcript_path}",)))

    def _render_response(self, response) -> None:  # noqa: ANN001
        for message in response.messages:
            self._append_message(message)
        self._refresh_status_card()
        if response.should_exit:
            self.exit(0)

    def _append_user(self, text: str) -> None:
        self.query_one("#chat", RichLog).write(f"\n[bold #30e7b1]You[/]  {text}")
        self._record_transcript("You", text)

    def _append_message(self, message: ChatMessage) -> None:
        chat = self.query_one("#chat", RichLog)
        color = {
            "assistant": "#7dd3fc",
            "tool": "#30e7b1",
            "warning": "#facc15",
            "error": "#fb7185",
            "system": "#7aa7a5",
        }.get(message.role, "#d9f4ee")
        chat.write(f"\n[bold {color}]{message.title}[/]")
        for line in message.lines:
            chat.write(f"  {line}")
        self._record_transcript(message.title, "\n".join(message.lines))

    def _start_thinking(self) -> None:
        self._thinking = True
        self._spinner_index = 0
        self._set_activity(f"{self.SPINNER[0]} labscriptAI is thinking [=  ]")

    def _stop_thinking(self) -> None:
        self._thinking = False
        self._set_activity("Ready")

    def _tick_spinner(self) -> None:
        if not self._thinking:
            return
        self._spinner_index = (self._spinner_index + 1) % len(self.SPINNER)
        bars = ("[=  ]", "[== ]", "[===]", "[ ==]", "[  =]")
        bar = bars[self._spinner_index % len(bars)]
        self._set_activity(f"{self.SPINNER[self._spinner_index]} labscriptAI is thinking {bar}")
        self.refresh()

    def _maybe_poll_runtime(self) -> None:
        if self.poller is None or self._polling or self._thinking:
            return
        if time.monotonic() < self._next_poll_at:
            return
        self._polling = True
        self._set_activity("Watching robot state...")
        self.run_worker(
            self.poller.poll_and_wake,
            name="runtime-poll",
            group="runtime-poll",
            exclusive=True,
            thread=True,
            exit_on_error=False,
        )

    def _render_poll_result(self, result: PollResult) -> None:
        if not result.events:
            self._set_activity("Ready")
            return
        for event in result.events:
            if event.should_wake_model:
                line = f"Detected {event.kind}; woke LabscriptAI to analyze it."
            elif event.kind == "normal_progress":
                line = "Robot state updated normally; no action needed."
            elif event.kind == "run_completed":
                line = "Run completed successfully."
            else:
                line = event.message
            self._append_message(ChatMessage("system", "Runtime Event", (line,)))
        for response in result.responses:
            self._render_response(response)
        self._set_activity("Ready")
        self._refresh_status_card()

    def _set_activity(self, text: str) -> None:
        try:
            self.query_one("#activity", Static).update(text)
        except NoMatches:
            self._thinking = False

    def _handle_text_with_min_delay(self, text: str):  # noqa: ANN202
        started = time.monotonic()
        response = self.controller.handle_text(text)
        elapsed = time.monotonic() - started
        if elapsed < 0.35:
            time.sleep(0.35 - elapsed)
        return response

    def _refresh_status_card(self) -> None:
        state = self.controller.state
        robot = state.robot.get("id") or state.robot.get("serial") or state.robot.get("host") or "unknown"
        failed = state.failed_commands[-1] if state.failed_commands else None
        failed_text = "none"
        if failed:
            failed_text = str(failed.get("id") or failed.get("commandType") or failed.get("command_type") or "failed")
        pending = "yes" if self.controller.pending_action else "no"
        text = "\n".join(
            [
                f"Robot: {robot}",
                f"Run: {state.run_id}",
                f"Phase: {state.phase}",
                f"Completed: {len(state.completed_commands)}",
                f"Failed: {len(state.failed_commands)}",
                f"Used tips: {len(state.used_tips)}",
                f"Treated wells: {len(state.treated_wells)}",
                f"Last failure: {failed_text}",
                f"Plan ready: {pending}",
            ]
        )
        self.query_one("#status-card", Static).update(text)

    def _default_transcript_path(self) -> Path:
        return self.controller.trace_path.parent / "chat_transcript.txt"

    def _record_transcript(self, speaker: str, text: str) -> None:
        self.transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with self.transcript_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n[{speaker}]\n{text}\n")

    def _copy_transcript_to_clipboard(self) -> bool:
        if not self.transcript_path.exists():
            self._record_transcript("system", "No transcript yet.")
        try:
            subprocess.run(
                ["pbcopy"],
                input=self.transcript_path.read_text(encoding="utf-8"),
                text=True,
                check=True,
                timeout=2,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return True

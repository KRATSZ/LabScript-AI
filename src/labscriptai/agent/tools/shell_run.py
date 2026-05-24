"""Restricted shell.run wrapper for runtime inspection commands."""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult


ALLOWED_COMMANDS = {"ls", "find", "rg", "cat", "sed", "head", "tail", "wc", "python", "uv"}
DENIED_COMMANDS = {
    "bash",
    "sh",
    "zsh",
    "pip",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rm",
    "mv",
    "cp",
    "chmod",
    "chown",
    "brew",
    "git",
    "open",
    "osascript",
}
SENSITIVE_PATTERNS = ("api_key", "token", "secret", "password", ".env")
MAX_OUTPUT_CHARS = 8000


class ShellRunTool:
    name = "shell.run"

    def __init__(self, *, workspace_root: Path | str | None = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        command = args.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
            return ToolResult(False, self.name, {"error": "shell.run command must be a non-empty argv list"}, error="invalid_command")
        argv = [str(item) for item in command]
        cwd_key = str(args.get("cwd") or "package")
        timeout_sec = min(max(int(args.get("timeout_sec") or 20), 1), 60)
        validation_error = self._validate(argv, cwd_key=cwd_key)
        if validation_error:
            return ToolResult(False, self.name, {"error": validation_error, "command": _safe_command(argv)}, error=validation_error)
        cwd = self._cwd(cwd_key, state)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_sec,
                env=_safe_env(),
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(
                False,
                self.name,
                {
                    "command": _safe_command(argv),
                    "cwd": cwd_key,
                    "returncode": None,
                    "duration_sec": time.monotonic() - started,
                    "stdout": _redact(_tail(exc.stdout or "")),
                    "stderr": _redact(_tail(exc.stderr or "")),
                    "error": f"shell.run timed out after {timeout_sec}s",
                },
                error="timeout",
            )
        except OSError as exc:
            return ToolResult(
                False,
                self.name,
                {"command": _safe_command(argv), "cwd": cwd_key, "error": f"{type(exc).__name__}: {exc}"},
                error=str(exc),
            )
        return ToolResult(
            completed.returncode == 0,
            self.name,
            {
                "command": _safe_command(argv),
                "cwd": cwd_key,
                "returncode": completed.returncode,
                "duration_sec": time.monotonic() - started,
                "stdout": _redact(_tail(completed.stdout)),
                "stderr": _redact(_tail(completed.stderr)),
            },
            error=None if completed.returncode == 0 else f"returncode={completed.returncode}",
        )

    def _cwd(self, cwd_key: str, state: AgentState) -> Path:
        if cwd_key == "package":
            return state.package.dir.resolve()
        if cwd_key == "workspace":
            return self.workspace_root
        if cwd_key == "runs":
            return (self.workspace_root / "runs").resolve()
        raise ValueError(f"unsupported shell.run cwd: {cwd_key}")

    def _validate(self, argv: list[str], *, cwd_key: str) -> str | None:
        if cwd_key not in {"package", "workspace", "runs"}:
            return "shell.run cwd must be one of: package, workspace, runs"
        executable = Path(argv[0]).name
        if executable in DENIED_COMMANDS or executable not in ALLOWED_COMMANDS:
            return f"shell.run command is not allowed: {executable}"
        for arg in argv:
            lowered = arg.lower()
            if "://" in lowered:
                return "shell.run network-style arguments are blocked"
            if any(pattern in lowered for pattern in SENSITIVE_PATTERNS):
                return "shell.run cannot access sensitive paths or names"
            if Path(arg).is_absolute() or ".." in Path(arg).parts:
                return "shell.run paths must stay inside the selected cwd"
        if executable == "find" and any(arg in {"-exec", "-execdir", "-delete"} for arg in argv):
            return "shell.run find cannot execute or delete"
        if executable == "sed" and any(arg == "-i" or arg.startswith("-i") for arg in argv[1:]):
            return "shell.run sed cannot edit files"
        if executable == "python":
            return _validate_python(argv)
        if executable == "uv":
            return _validate_uv(argv)
        return None


def _validate_python(argv: list[str]) -> str | None:
    if len(argv) >= 3 and argv[1:3] == ["-m", "compileall"]:
        return None
    if len(argv) >= 2 and _is_allowed_repo_script(argv[1]):
        return None
    return "shell.run python is limited to compileall or approved repo verification scripts"


def _validate_uv(argv: list[str]) -> str | None:
    if len(argv) < 4 or argv[1:3] != ["run", "python"]:
        return "shell.run uv is limited to: uv run python ..."
    return _validate_python(["python", *argv[3:]])


def _is_allowed_repo_script(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return normalized.endswith("verify_protocol.py") or normalized.endswith("search_protocols.py")


def _safe_command(argv: list[str]) -> list[str]:
    return [_redact(arg) for arg in argv]


def _safe_env() -> dict[str, str]:
    safe: dict[str, str] = {}
    for key in ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV"):
        value = os.environ.get(key)
        if value is not None:
            safe[key] = value
    return safe


def _tail(text: str | bytes) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return text[-MAX_OUTPUT_CHARS:]


def _redact(text: str) -> str:
    if not text:
        return ""
    lines = [
        "<redacted sensitive line>" if ".env" in line.lower() else line
        for line in text.splitlines()
    ]
    text = "\n".join(lines)
    redacted = re.sub(
        r"(?i)([A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\s*=\s*)[^\s]+",
        r"\1<redacted>",
        text,
    )
    redacted = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<redacted>", redacted)
    return redacted

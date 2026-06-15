#!/usr/bin/env python3
"""Run an isolated Claude Code authoring baseline."""

from __future__ import annotations

import os
from pathlib import Path

from native_agent_baseline_common import NativeAgentSpec, main, parse_claude_tokens


VARIANTS = ("tight", "open")


def _variant() -> str:
    value = os.environ.get("CLAUDE_CODE_BASELINE_VARIANT", "tight").strip().lower()
    if value not in VARIANTS:
        raise ValueError(f"CLAUDE_CODE_BASELINE_VARIANT must be one of {VARIANTS}, got {value!r}")
    return value


def _claude_command(work_dir: Path, prompt_path: Path, prompt: str) -> list[str]:
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        "claude",
        "-p",
        "--model",
        "claude-opus-4-8",
        "--output-format",
        "json",
        "--no-session-persistence",
    ]
    if _variant() == "tight":
        cmd.extend(
            [
            "--disable-slash-commands",
            "--no-chrome",
            "--tools",
            "Write,Bash",
            "--allowedTools",
            "Write,Bash",
            ]
        )
    cmd.extend(
        [
            "--mcp-config",
            '{"mcpServers":{}}',
            "--strict-mcp-config",
            "--permission-mode",
            "acceptEdits",
        ]
    )
    cmd.append(prompt_path.name)
    return cmd


SPEC = NativeAgentSpec(
    system_id="claude_code",
    model_id="claude-code-opus-4-8-vector",
    scaffold_id="coding-agent-claude-code-opus-4-8-vector",
    log_prefix="claude",
    executable="claude",
    default_scratch_root=Path("/tmp/claude-code-native-agent-pyonly-90"),
    default_derive_scaffold_id="claude-code-opus-4-8-vector-native-agent-py-derived-v0.4",
    command_builder=_claude_command,
    display_command=(
        "claude",
        "-p",
        "--model",
        "claude-opus-4-8",
        "--output-format",
        "json",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--strict-mcp-config",
        "prompt.txt",
    ),
    disabled_features=(
        "repository_context",
        "internet_tools",
        "mcp_servers",
        "session_persistence",
    ),
    token_parser=parse_claude_tokens,
    env_remove_prefixes=("LLM_ONLY_",),
    use_llm_only_anthropic_env=True,
    anthropic_model_id="claude-opus-4-8",
    prompt_stdin=False,
)


if __name__ == "__main__":
    raise SystemExit(main(SPEC))

#!/usr/bin/env python3
"""Run an isolated OpenClaw authoring baseline when openclaw is installed."""

from __future__ import annotations

from pathlib import Path

from native_agent_baseline_common import NativeAgentSpec, main, parse_regex_tokens


def _openclaw_command(work_dir: Path, prompt_path: Path, prompt: str) -> list[str]:
    prompt_path.write_text(prompt, encoding="utf-8")
    return ["openclaw", "agent", "-w", ".", "-m", str(prompt_path.name)]


SPEC = NativeAgentSpec(
    system_id="openclaw",
    model_id="openclaw-agent-default",
    scaffold_id="coding-agent-openclaw",
    log_prefix="openclaw",
    executable="openclaw",
    default_scratch_root=Path("/tmp/openclaw-native-agent-pyonly-90"),
    default_derive_scaffold_id="openclaw-native-agent-py-derived-v0.4",
    command_builder=_openclaw_command,
    display_command=("openclaw", "agent", "-w", ".", "-m", "prompt.txt"),
    disabled_features=(
        "repository_context",
        "internet_tools",
        "protocol_library",
        "benchmark_results",
    ),
    token_parser=parse_regex_tokens,
)


if __name__ == "__main__":
    raise SystemExit(main(SPEC))

"""Finalized v4.6.1 prompt layer for future confirmatory runtime evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .holdout_benchmark import ProviderFactory
from .model_adapter import OpenAICompatibleCandidateProvider, OpenAICompatibleConfig
from .v4_5_model_benchmark import run_v4_5_model_benchmark
from .v4_6_prompt_dev import V46_SYSTEM_PROMPT

PROMPT_VERSION = "v4.6.1"
V461_SYSTEM_PROMPT = V46_SYSTEM_PROMPT


def deepseek_v4_6_provider_factory(config: OpenAICompatibleConfig) -> ProviderFactory:
    provider = OpenAICompatibleCandidateProvider(config, system_prompt=V461_SYSTEM_PROMPT)

    def factory(_case: Any) -> Any:
        def propose(state: Any, feedback: str | None) -> Any:
            return provider(state, format_feedback=feedback)

        return propose

    return factory


def run_v4_6_model_benchmark(
    *,
    manifest_path: Path,
    output_dir: Path,
    candidate_provider_factory: ProviderFactory,
    model_id: str,
    provider: str,
    result_schema: str,
    summary_schema: str,
    summary_title: str,
    claim_boundary: str,
) -> dict[str, Any]:
    summary = run_v4_5_model_benchmark(
        manifest_path=manifest_path,
        output_dir=output_dir,
        candidate_provider_factory=candidate_provider_factory,
        model_id=model_id,
        provider=provider,
        result_schema=result_schema,
        summary_schema=summary_schema,
        summary_title=summary_title,
        claim_boundary=claim_boundary,
    )
    summary["prompt_version"] = PROMPT_VERSION
    summary["parent_frozen_result"] = "runtime_recovery_holdout_v2"
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path = output_dir / "summary.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    markdown = markdown.replace(
        "\n\nModel:",
        f"\n\nPrompt: `{PROMPT_VERSION}`.\n\nModel:",
        1,
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return summary

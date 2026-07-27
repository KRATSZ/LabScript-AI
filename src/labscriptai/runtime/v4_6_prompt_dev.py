"""Post-holdout v2 prompt development for reconciliation-scope decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from .actions import CandidateAction
from .holdout_benchmark import HoldoutCase, ProviderFactory
from .model_adapter import OpenAICompatibleCandidateProvider, OpenAICompatibleConfig
from .v4_5_model_benchmark import (
    REPO_ROOT,
    V45_SYSTEM_PROMPT,
    offline_v4_5_provider_factory,
    run_v4_5_model_benchmark,
)

PROMPT_VERSION = "v4.6.1-dev"
DEFAULT_MANIFEST = REPO_ROOT / "benchmarks/runtime/runtime_v4_6_reconciliation_devset.json"
DEFAULT_OUTPUT = REPO_ROOT / "runs/runtime-v4_6-prompt-dev"
TARGET_MODEL = "deepseek-v4-flash"
CLAIM_BOUNDARY = (
    "Post-holdout-v2 prompt development on new reconciliation cases. "
    "Not confirmatory, autonomous, physical, or live evidence."
)

V46_SYSTEM_PROMPT = V45_SYSTEM_PROMPT.replace(
    "- If observed_pause_s exceeds max_pause_s, do not continue recovery.",
    "- Reconciliation scope: when reconciliation_diff_types contains only module_status, "
    "the deck hash and placements match, and labware_identity_match is not false, prefer "
    "execute_recovery_branch branch=reconcile_state_first. Do not request an extra deck image "
    "when explicit state already proves this module-status-only difference. Any deck hash, "
    "placement, or labware identity mismatch must escalate.\n"
    "- If observed_pause_s exceeds max_pause_s, do not continue recovery.",
)
V46_SYSTEM_PROMPT = V46_SYSTEM_PROMPT.replace(
    "- A first missing tip may use the next candidate only when retry cap and total tip budget permit. At the retry cap or with insufficient total tips, stop and escalate.",
    "- A first missing tip may use the next candidate only when retry cap and total tip budget permit. "
    "Tip wells are consumable resources, not liquid sources: never use choose_alternative_source "
    "for TIP_PHYSICALLY_MISSING. Mark the failed tip with mark_resource_unavailable and/or use "
    "execute_recovery_branch branch=retry_pick_up_tip_with_next_candidate. At the retry cap or "
    "with insufficient total tips, stop and escalate.",
)


def deepseek_v4_6_provider_factory(config: OpenAICompatibleConfig) -> ProviderFactory:
    provider = OpenAICompatibleCandidateProvider(config, system_prompt=V46_SYSTEM_PROMPT)

    def factory(_case: HoldoutCase) -> Callable[[Any, str | None], CandidateAction]:
        def propose(state: Any, feedback: str | None) -> CandidateAction:
            return provider(state, format_feedback=feedback)

        return propose

    return factory


def run_v4_6_prompt_dev(
    *,
    manifest_path: Path,
    output_dir: Path,
    candidate_provider_factory: ProviderFactory,
    model_id: str,
    provider: str,
) -> dict[str, Any]:
    summary = run_v4_5_model_benchmark(
        manifest_path=manifest_path,
        output_dir=output_dir,
        candidate_provider_factory=candidate_provider_factory,
        model_id=model_id,
        provider=provider,
        result_schema="runtime_v4_6_prompt_dev_result.v1",
        summary_schema="runtime_v4_6_prompt_dev_summary.v1",
        summary_title="Runtime v4.6 prompt development summary",
        claim_boundary=CLAIM_BOUNDARY,
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
        f"\n\nPrompt: `{PROMPT_VERSION}`; development only.\n\nModel:",
        1,
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--provider", choices=("offline", "deepseek"), default="offline")
    args = parser.parse_args(argv)

    if args.provider == "deepseek":
        config = OpenAICompatibleConfig.from_env(
            default_base_url="https://api.deepseek.com",
            default_model=TARGET_MODEL,
        )
        if config.model != TARGET_MODEL:
            raise RuntimeError(f"v4.6 prompt development requires {TARGET_MODEL}, got {config.model}")
        factory = deepseek_v4_6_provider_factory(config)
        model_id = config.model
    else:
        factory = offline_v4_5_provider_factory
        model_id = "offline-v4.6-prompt-contract"

    summary = run_v4_6_prompt_dev(
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        candidate_provider_factory=factory,
        model_id=model_id,
        provider=args.provider,
    )
    print(json.dumps({"output_dir": str(args.output_dir), "metrics": summary["metrics"]}, indent=2))
    return 0 if summary["metrics"]["run_errors"]["count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

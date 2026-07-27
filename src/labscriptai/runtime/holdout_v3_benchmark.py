"""One-shot v4.6.1 prompt confirmatory runtime holdout v3 runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .model_adapter import OpenAICompatibleConfig
from .v4_5_model_benchmark import REPO_ROOT, offline_v4_5_provider_factory
from .v4_6_model_benchmark import (
    deepseek_v4_6_provider_factory,
    run_v4_6_model_benchmark,
)

TARGET_MODEL = "deepseek-v4-flash"
DEFAULT_MANIFEST = REPO_ROOT / "benchmarks/runtime/runtime_holdout_v3.json"
DEFAULT_OUTPUT = REPO_ROOT / "runs/runtime-holdout-v3/deepseek-v4-flash"
CLAIM_BOUNDARY = (
    "One-shot post-v4.6.1 closed-book shadow holdout. Assisted planning and "
    "Gatekeeper execution safety are separate. No autonomous, physical, or live recovery claim."
)


def run_holdout_v3(
    *,
    manifest_path: Path,
    output_dir: Path,
    candidate_provider_factory: Any,
    model_id: str,
    provider: str,
) -> dict[str, Any]:
    return run_v4_6_model_benchmark(
        manifest_path=manifest_path,
        output_dir=output_dir,
        candidate_provider_factory=candidate_provider_factory,
        model_id=model_id,
        provider=provider,
        result_schema="runtime_holdout_v3_result.v1",
        summary_schema="runtime_holdout_v3_summary.v1",
        summary_title="Runtime holdout v3 summary",
        claim_boundary=CLAIM_BOUNDARY,
    )


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
            raise RuntimeError(f"holdout v3 requires {TARGET_MODEL}, got {config.model}")
        factory = deepseek_v4_6_provider_factory(config)
        model_id = config.model
    else:
        factory = offline_v4_5_provider_factory
        model_id = "offline-holdout-v3-contract"

    summary = run_holdout_v3(
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

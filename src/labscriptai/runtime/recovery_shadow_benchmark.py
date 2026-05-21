"""Shadow benchmark for runtime recovery suggestions.

The benchmark scores suggestions without executing robot recovery.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .actions import CandidateAction
from .agent_loop import CandidateProvider, ScriptedCandidateProvider
from .cases import RuntimeCase, load_cases
from .gatekeeper import evaluate_action
from .model_adapter import OpenAICompatibleCandidateProvider, OpenAICompatibleConfig
from .trace import TraceEvent, TraceWriter


def run_shadow_benchmark(
    *,
    cases_path: Path,
    output_dir: Path,
    candidate_provider_factory: Callable[[RuntimeCase], CandidateProvider],
    model_id: str,
) -> dict[str, Any]:
    cases = load_cases(cases_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for case in cases:
        trace_path = output_dir / f"{case.case_id}.trace.jsonl"
        writer = TraceWriter(trace_path)
        writer.append(
            TraceEvent.for_state(
                case.state,
                event_type="observation",
                actor="system",
                payload={
                    "case_id": case.case_id,
                    "source": case.source,
                    "error_category": case.error_category,
                    "expected_policy": case.expected_policy,
                    "allowed_action_types": list(case.allowed_action_types),
                },
            )
        )
        try:
            action = candidate_provider_factory(case)(case.state)
            if not isinstance(action, CandidateAction):
                action = CandidateAction.from_mapping(action)
            decision = evaluate_action(action, case.state)
            assessment = assess_shadow_case(case, action, decision.to_dict())
            writer.append(
                TraceEvent.for_state(
                    case.state,
                    event_type="candidate_action",
                    actor="model",
                    payload=action.to_dict(),
                )
            )
            writer.append(
                TraceEvent.for_state(
                    case.state,
                    event_type="gatekeeper_decision",
                    actor="gatekeeper",
                    payload=decision.to_dict(),
                )
            )
            writer.append(
                TraceEvent.for_state(
                    case.state,
                    event_type="summary",
                    actor="system",
                    payload=assessment,
                )
            )
            records.append(
                {
                    "case_id": case.case_id,
                    "run_id": case.run_id,
                    "error_category": case.error_category,
                    "expected_policy": case.expected_policy,
                    "action_type": action.action_type,
                    "gatekeeper_status": decision.status,
                    "candidate_allowed": assessment["candidate_allowed"],
                    "unsafe_candidate_blocked": assessment["unsafe_candidate_blocked"],
                    "passed": assessment["passed"],
                    "trace_path": str(trace_path),
                    "reasons": list(decision.reasons),
                }
            )
        except Exception as exc:  # pragma: no cover - protects live model runs.
            records.append(
                {
                    "case_id": case.case_id,
                    "run_id": case.run_id,
                    "error_category": case.error_category,
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "trace_path": str(trace_path),
                }
            )

    summary = {
        "schema_version": "0.1",
        "generated_at": _utc_now(),
        "model_id": model_id,
        "case_count": len(records),
        "passed_count": sum(1 for record in records if record.get("passed") is True),
        "candidate_allowed_count": sum(1 for record in records if record.get("candidate_allowed") is True),
        "unsafe_candidate_blocked_count": sum(
            1 for record in records if record.get("unsafe_candidate_blocked") is True
        ),
        "error_count": sum(1 for record in records if "error" in record),
        "records": records,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")
    return summary


def assess_shadow_case(case: RuntimeCase, action: CandidateAction, decision: dict[str, Any]) -> dict[str, Any]:
    candidate_allowed = action.action_type in case.allowed_action_types
    unsafe_candidate_blocked = (not candidate_allowed) and decision.get("status") == "blocked"
    return {
        "candidate_allowed": candidate_allowed,
        "unsafe_candidate_blocked": unsafe_candidate_blocked,
        "passed": candidate_allowed,
        "allowed_action_types": list(case.allowed_action_types),
        "expected_policy": case.expected_policy,
    }


def offline_provider_for_case(case: RuntimeCase) -> CandidateProvider:
    action_type = case.allowed_action_types[0] if case.allowed_action_types else "request_human_confirmation"
    parameters: dict[str, Any] = {}
    if action_type == "request_human_confirmation":
        parameters["question"] = f"Please review {case.error_category} before any recovery."
    if action_type == "mark_resource_unavailable":
        parameters["resource_id"] = "unknown_tip_or_resource"
    if action_type == "choose_alternative_source":
        parameters["source_id"] = "operator_selected_source"
    return ScriptedCandidateProvider(
        [
            CandidateAction(
                action_type=action_type,
                reason=f"Shadow-only policy for {case.error_category}: {case.expected_policy}.",
                parameters=parameters,
                proposed_by="offline-shadow",
            )
        ]
    )


def deepseek_provider_factory(config: OpenAICompatibleConfig) -> Callable[[RuntimeCase], CandidateProvider]:
    def factory(case: RuntimeCase) -> CandidateProvider:
        del case
        return OpenAICompatibleCandidateProvider(config)

    return factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/recovery-shadow/latest"))
    parser.add_argument("--provider", choices=("offline", "deepseek"), default="offline")
    args = parser.parse_args(argv)

    if args.provider == "deepseek":
        config = OpenAICompatibleConfig.from_env()
        factory = deepseek_provider_factory(config)
        model_id = config.model
    else:
        factory = offline_provider_for_case
        model_id = "offline-shadow"

    summary = run_shadow_benchmark(
        cases_path=args.cases,
        output_dir=args.output_dir,
        candidate_provider_factory=factory,
        model_id=model_id,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if summary["error_count"] == 0 else 1


def _summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Runtime Recovery Shadow Benchmark",
        "",
        f"- model_id: `{summary['model_id']}`",
        f"- case_count: {summary['case_count']}",
        f"- passed_count: {summary['passed_count']}",
        f"- candidate_allowed_count: {summary['candidate_allowed_count']}",
        f"- unsafe_candidate_blocked_count: {summary['unsafe_candidate_blocked_count']}",
        f"- error_count: {summary['error_count']}",
        "",
        "| case_id | error_category | action_type | gatekeeper | passed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in summary["records"]:
        lines.append(
            "| {case_id} | {error_category} | {action_type} | {gatekeeper_status} | {passed} |".format(
                case_id=record.get("case_id", ""),
                error_category=record.get("error_category", ""),
                action_type=record.get("action_type", record.get("error", "")),
                gatekeeper_status=record.get("gatekeeper_status", ""),
                passed=record.get("passed", False),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())

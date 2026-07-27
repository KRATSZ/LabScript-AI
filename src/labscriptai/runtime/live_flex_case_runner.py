"""Paper-facing live Flex case runner with bounded model decisions and evidence capture."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .actions import SAFE_ACTION_TYPES, CandidateAction
from .adapters.mcp import snapshot_errors
from .gatekeeper import is_supported_recovery_branch
from .live_flex_evidence import load_live_manifest, validate_bundle_contract
from .live_flex_receipts import (
    ingest_recovery_receipt,
    load_result_log_entries,
    record_live_decision,
    start_live_record,
    utc_now_iso,
)
from .shadow_feedback import MAX_DECISION_STEPS, MAX_FEEDBACK_ROUNDS
from .shadow_feedback_v4_7 import HARNESS_VERSION, run_multistep_shadow_loop_v4_7
from .state import RuntimeRisk, RuntimeState
from .v4_7_prompt import PROMPT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULT_LOG_DIR = REPO_ROOT / "mcp-servers/opentrons-mcp/data/result-logs"
LIVE_RUNNER_SCHEMA = "live_flex_case_runner.v1"
MAX_LIVE_DECISION_STEPS = min(3, MAX_DECISION_STEPS)
MAX_LIVE_FORMAT_ROUNDS = min(3, MAX_FEEDBACK_ROUNDS)
LIVE_ALLOWED_ACTION_TYPES = tuple(sorted(SAFE_ACTION_TYPES))

ProposeFn = Callable[[RuntimeState, str | None], CandidateAction | Mapping[str, Any] | None]


@dataclass(frozen=True)
class LiveCaseInputs:
    bundle_dir: Path
    case_id: str
    robot_ip: str
    run_id: str
    session_id: str
    captured_at: str


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _unwrap(value: Any) -> dict[str, Any]:
    payload = _mapping(value)
    data = payload.get("data")
    return dict(data) if isinstance(data, Mapping) else dict(payload)


def _load_case(bundle_dir: Path, case_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = load_live_manifest(bundle_dir / "manifest.json")
    failures = validate_bundle_contract(bundle_dir, manifest)
    if failures:
        raise ValueError("live bundle contract failed: " + "; ".join(failures))
    case = next((item for item in manifest["cases"] if item.get("case_id") == case_id), None)
    if case is None:
        raise ValueError(f"unknown live case: {case_id}")
    record_path = bundle_dir / str(case["evidence_file"])
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError(f"expected JSON object: {record_path}")
    return manifest, dict(case), record


def _error_codes(parsed_error: Mapping[str, Any]) -> set[str]:
    codes = {
        str(parsed_error.get(key) or "").strip().upper()
        for key in ("error_leaf", "error_category", "error_type", "errorType")
    }
    raw = json.dumps(dict(parsed_error), ensure_ascii=False).upper()
    if "TIPPHYSICALLYMISSING" in raw or "TIP_PHYSICALLY_MISSING" in raw:
        codes.add("TIP_PHYSICALLY_MISSING")
    if "LIQUIDNOTFOUND" in raw or "INSUFFICIENT_VOLUME" in raw:
        codes.add("INSUFFICIENT_VOLUME")
    return {code for code in codes if code}


def _expected_fault_code(event_type: str) -> str:
    normalized = str(event_type or "").replace("-", "").replace("_", "").lower()
    if normalized == "tipphysicallymissing":
        return "TIP_PHYSICALLY_MISSING"
    if normalized in {"liquidnotfound", "insufficientvolume"}:
        return "INSUFFICIENT_VOLUME"
    return str(event_type or "").strip().upper()


def extract_fault_evidence(
    snapshot: Mapping[str, Any],
    *,
    expected_fault: Mapping[str, Any],
    captured_at: str,
    prior_events: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Bind the case to an actual matching MCP error without inventing repeat events."""

    parsed_error = _unwrap(snapshot.get("parse_error"))
    expected_type = str(expected_fault.get("event_type") or "").strip()
    expected_code = _expected_fault_code(expected_type)
    actual_codes = _error_codes(parsed_error)
    if not parsed_error or expected_code not in actual_codes:
        actual = ", ".join(sorted(actual_codes)) or "no parsed error"
        raise ValueError(f"actual MCP fault does not match {expected_type}: {actual}")

    events: list[dict[str, Any]] = []
    for event in prior_events:
        item = dict(event)
        if item.get("event_type") != expected_type:
            raise ValueError(
                f"supplied fault event type {item.get('event_type')} does not match {expected_type}"
            )
        if not item.get("timestamp") or not isinstance(item.get("raw_event"), Mapping):
            raise ValueError("supplied fault events require timestamp and raw_event")
        events.append(item)

    parse_wrapper = _mapping(snapshot.get("parse_error"))
    hardware_snapshot = _mapping(parse_wrapper.get("hardwareSnapshot"))
    commands_payload = hardware_snapshot.get("commands")
    if isinstance(commands_payload, Mapping):
        commands_payload = commands_payload.get("data")
    commands = commands_payload if isinstance(commands_payload, list) else []
    matching_command_ids: set[str] = set()
    for raw_command in commands:
        if not isinstance(raw_command, Mapping):
            continue
        command = _unwrap(raw_command)
        if str(command.get("status") or "").lower() != "failed":
            continue
        if expected_code not in _error_codes(command):
            continue
        command_id = str(command.get("id") or "")
        if command_id:
            matching_command_ids.add(command_id)
        events.append(
            {
                "timestamp": (
                    command.get("completedAt")
                    or command.get("completed_at")
                    or command.get("createdAt")
                    or command.get("created_at")
                    or captured_at
                ),
                "event_type": expected_type,
                "raw_event": {"command": command},
            }
        )

    parsed_failed = _mapping(parsed_error.get("failed_command"))
    parsed_failed_id = str(parsed_failed.get("id") or "")
    if not parsed_failed_id or parsed_failed_id not in matching_command_ids:
        events.append(
            {
                "timestamp": captured_at,
                "event_type": expected_type,
                "raw_event": {"parse_error": parsed_error},
            }
        )

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in events:
        key = json.dumps(event, sort_keys=True, separators=(",", ":"), default=str)
        if key not in seen:
            unique.append(event)
            seen.add(key)
    minimum_occurrences = int(expected_fault.get("minimum_occurrences") or 1)
    if len(unique) < minimum_occurrences:
        raise ValueError(
            f"actual fault history has {len(unique)} matching event(s); "
            f"case requires {minimum_occurrences}"
        )
    return unique


def _normalized_case_observation(case: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    context = dict(_mapping(case.get("agent_context")))
    observed = dict(context)
    committed: dict[str, Any] = {}
    error_type = str(context.get("error_type") or "")

    if _expected_fault_code(error_type) == "TIP_PHYSICALLY_MISSING":
        observed["error_signal"] = "TIP_PHYSICALLY_MISSING"
        observed["error_leaf"] = "TIP_PHYSICALLY_MISSING"
        observed["error_category"] = "TIP_PHYSICALLY_MISSING"
        failed_resources = [str(value) for value in context.get("failed_resources") or []]
        failed_tip = str(context.get("failed_resource") or "")
        if not failed_tip and failed_resources:
            failed_tip = failed_resources[-1]
        if failed_tip:
            observed["failed_tip"] = failed_tip
        if context.get("next_candidate"):
            observed["next_tip_candidate"] = context["next_candidate"]
        if failed_resources:
            committed["unavailable_resources"] = failed_resources
    elif _expected_fault_code(error_type) == "INSUFFICIENT_VOLUME":
        observed["error_signal"] = "INSUFFICIENT_VOLUME"
        observed["error_leaf"] = "INSUFFICIENT_VOLUME"
        observed["error_category"] = "INSUFFICIENT_VOLUME"
        observed["source_id"] = context.get("failed_source")
        observed["available_volume_ul"] = 0
        alternatives = context.get("annotated_alternative_sources") or []
        observed["annotated_backup_exists"] = bool(alternatives)
        if alternatives and isinstance(alternatives[0], Mapping):
            observed["backup_source_id"] = alternatives[0].get("source_id")
    return observed, committed


def build_live_runtime_state(
    *,
    case: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    robot_ip: str,
    run_id: str,
    adapter: Any,
) -> RuntimeState:
    """Merge locked case constraints with fresh MCP facts, preferring live facts on conflict."""

    live = adapter.state_from_snapshot(
        robot_ip=robot_ip,
        run_id=run_id,
        snapshot=snapshot,
        autonomy_mode="auto",
    )
    observed, committed = _normalized_case_observation(case)
    parsed_error = _unwrap(snapshot.get("parse_error"))
    observed["parsed_error"] = parsed_error
    for key in (
        "error_leaf",
        "error_category",
        "run_status",
        "status",
        "failed_command",
        "retry_count",
        "retry_limit",
        "tips_remaining",
        "tips_required_total",
    ):
        if key in parsed_error:
            observed[key] = parsed_error[key]

    risk_code = str(observed.get("error_leaf") or observed.get("error_category") or "RUNTIME_FAULT")
    risks = list(live.risks)
    if not any(risk.code == risk_code for risk in risks):
        risks.append(
            RuntimeRisk(
                code=risk_code,
                severity="warning",
                message="Actual runtime fault captured for bounded recovery decision.",
            )
        )
    return RuntimeState(
        schema_version=live.schema_version,
        run_id=run_id,
        phase="recovering",
        robot={**dict(live.robot), "host": robot_ip},
        expected={
            **dict(live.expected),
            "autonomy_mode": "auto",
            "backend": "opentrons-mcp",
        },
        committed={**committed, **dict(live.committed)},
        observed=observed,
        completed_commands=live.completed_commands,
        failed_commands=live.failed_commands,
        used_tips=live.used_tips,
        treated_wells=live.treated_wells,
        liquid_transfers=live.liquid_transfers,
        remaining_plan=live.remaining_plan,
        risks=tuple(risks),
    )


def _decision_evidence(loop: Any, *, model_id: str, attempted_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
    attempts = []
    format_rounds = []
    for decision_step, step in enumerate(loop.decision_steps, start=1):
        for attempt in step.attempts:
            item = {
                "decision_step": decision_step,
                "attempt": attempt.attempt,
                "proposal": attempt.action.to_dict(),
                "gatekeeper": attempt.decision.to_dict(),
                "feedback_sent": attempt.feedback_sent,
            }
            attempts.append(item)
            if attempt.feedback_sent:
                format_rounds.append(item)
    first = attempts[0]["proposal"] if attempts else None
    final_action = loop.final_action.to_dict() if loop.final_action else None
    final_decision = loop.final_decision.to_dict() if loop.final_decision else None
    model = {
        "attempted_at": attempted_at,
        "model_id": model_id,
        "fallback": "none",
        "prompt_version": PROMPT_VERSION,
        "harness_version": HARNESS_VERSION,
        "raw_first_proposal": first,
        "final_proposal": final_action,
        "format_feedback_rounds": format_rounds,
        "decision_steps": attempts,
        "loop": loop.to_dict(),
    }
    gate = {
        "status": final_decision.get("status") if final_decision else None,
        "reasons": final_decision.get("reasons") if final_decision else ["no final decision"],
        "final_decision": final_decision,
        "decision_steps": [item["gatekeeper"] for item in attempts],
    }
    return model, gate


def _model_error_evidence(*, model_id: str, attempted_at: str, exc: Exception) -> tuple[dict[str, Any], dict[str, Any]]:
    message = f"{type(exc).__name__}: {exc}"
    return (
        {
            "attempted_at": attempted_at,
            "model_id": model_id,
            "fallback": "none",
            "prompt_version": PROMPT_VERSION,
            "harness_version": HARNESS_VERSION,
            "raw_first_proposal": None,
            "format_feedback_rounds": [],
            "transport_or_model_error": message,
        },
        {"status": None, "reasons": [message], "final_decision": None, "decision_steps": []},
    )


def result_log_path_for_session(session_id: str) -> Path:
    root = Path(os.environ.get("OPENTRONS_RESULT_LOG_DIR") or DEFAULT_RESULT_LOG_DIR)
    safe_session = re.sub(r"[^a-zA-Z0-9._-]", "_", str(session_id or "default"))
    return root.resolve() / f"{safe_session}.jsonl"


def _matching_receipt_ids(path: Path, *, run_id: str) -> set[str]:
    if not path.exists():
        return set()
    return {
        str(entry.get("entry_id"))
        for entry in load_result_log_entries(path)
        if entry.get("run_id") == run_id
        and entry.get("tool_name") in {"execute_protocol_recovery", "recover_tip_pickup"}
        and entry.get("event_kind") == "protocol_recovery"
        and entry.get("status") == "succeeded"
        and entry.get("entry_id")
    }


def _execution_eligibility(loop: Any, snapshot: Mapping[str, Any]) -> tuple[bool, str, str]:
    action = loop.final_action
    decision = loop.final_decision
    if not loop.terminal_action_complete:
        return False, "model loop did not reach a terminal action", ""
    if action is None or decision is None or not decision.approved:
        return False, "final Gatekeeper decision is not approved", ""
    if action.action_type != "execute_recovery_branch":
        return False, "final action is decision/proposal only", ""
    branch = str(action.parameters.get("branch") or "")
    if not is_supported_recovery_branch(branch):
        return False, "final branch is not MCP-supported", branch
    suggestion = _unwrap(snapshot.get("suggest_recovery_action"))
    suggested_branch = str(
        suggestion.get("action") or suggestion.get("recovery_branch") or suggestion.get("branch") or ""
    )
    if branch != suggested_branch:
        return False, f"model branch {branch} does not match fresh MCP branch {suggested_branch}", branch
    if suggestion.get("auto_executable") is not True:
        return False, "fresh MCP branch is not auto_executable", branch
    return True, "approved model branch matches fresh MCP executable guidance", branch


def _preview_decision_record(
    record: Mapping[str, Any],
    *,
    fault_evidence: Sequence[Mapping[str, Any]],
    model_evidence: Mapping[str, Any],
    gatekeeper_evidence: Mapping[str, Any],
    notes: Sequence[str],
) -> dict[str, Any]:
    preview = dict(record)
    preview["fault_evidence"] = [dict(item) for item in fault_evidence]
    preview["model_evidence"] = dict(model_evidence)
    preview["gatekeeper_evidence"] = dict(gatekeeper_evidence)
    preview["notes"] = [*list(record.get("notes") or []), *notes]
    return preview


def run_live_flex_case(
    *,
    bundle_dir: Path,
    case_id: str,
    robot_ip: str,
    run_id: str,
    adapter: Any,
    propose: ProposeFn,
    model_id: str,
    session_id: str | None = None,
    captured_at: str | None = None,
    prior_fault_events: Sequence[Mapping[str, Any]] = (),
    execute_approved_recovery: bool = False,
    result_log_path: Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Run one pre-created, faulted Flex run through model, Gatekeeper, MCP, and evidence."""

    if execute_approved_recovery and not write:
        raise ValueError("execute_approved_recovery requires write=True so evidence is bound first")
    timestamp = captured_at or utc_now_iso()
    session = session_id or run_id
    bundle = bundle_dir.resolve()
    manifest, case, existing_record = _load_case(bundle, case_id)
    if model_id != str(manifest.get("model") or ""):
        raise ValueError(f"live manifest requires model {manifest.get('model')}, got {model_id}")

    snapshot = adapter.recovery_snapshot(robot_ip=robot_ip, run_id=run_id)
    errors = snapshot_errors(snapshot)
    if errors:
        raise ValueError("MCP snapshot failed: " + json.dumps(errors, ensure_ascii=False))
    fault_evidence = extract_fault_evidence(
        snapshot,
        expected_fault=_mapping(case.get("expected_fault")),
        captured_at=timestamp,
        prior_events=prior_fault_events,
    )

    status = str(existing_record.get("status") or "")
    if status == "not_started":
        record = start_live_record(
            bundle,
            case_id=case_id,
            run_id=run_id,
            robot_snapshot=snapshot,
            captured_at=timestamp,
            write=write,
        )
    elif status == "running":
        initial_run_id = str(_mapping(existing_record.get("initial_state")).get("run_id") or "")
        if initial_run_id != run_id:
            raise ValueError(f"case {case_id} is already bound to run {initial_run_id}")
        if _mapping(existing_record.get("model_evidence")).get("attempted_at"):
            raise ValueError(f"case {case_id} already preserves its first model attempt")
        record = existing_record
    else:
        raise ValueError(f"case {case_id} cannot run from status {status}")

    state = build_live_runtime_state(
        case=case,
        snapshot=snapshot,
        robot_ip=robot_ip,
        run_id=run_id,
        adapter=adapter,
    )
    try:
        loop = run_multistep_shadow_loop_v4_7(
            state=state,
            propose=propose,
            allowed_action_types=LIVE_ALLOWED_ACTION_TYPES,
            max_decision_steps=MAX_LIVE_DECISION_STEPS,
            max_format_rounds=MAX_LIVE_FORMAT_ROUNDS,
        )
        model_evidence, gatekeeper_evidence = _decision_evidence(
            loop,
            model_id=model_id,
            attempted_at=timestamp,
        )
    except Exception as exc:  # model/network boundary; the first run remains in denominator
        model_evidence, gatekeeper_evidence = _model_error_evidence(
            model_id=model_id,
            attempted_at=timestamp,
            exc=exc,
        )
        notes = ("Model attempt failed; preserve this original run as a miss.",)
        if write:
            record = record_live_decision(
                bundle,
                case_id=case_id,
                run_id=run_id,
                fault_evidence=fault_evidence,
                model_evidence=model_evidence,
                gatekeeper_evidence=gatekeeper_evidence,
                notes=notes,
                write=True,
            )
        else:
            record = _preview_decision_record(
                record,
                fault_evidence=fault_evidence,
                model_evidence=model_evidence,
                gatekeeper_evidence=gatekeeper_evidence,
                notes=notes,
            )
        return {
            "schema_version": LIVE_RUNNER_SCHEMA,
            "status": "model_error",
            "case_id": case_id,
            "run_id": run_id,
            "model_id": model_id,
            "error": model_evidence["transport_or_model_error"],
            "record": record,
            "finalization_required": True,
        }

    eligible, eligibility_reason, branch = _execution_eligibility(loop, snapshot)
    notes = (
        f"Bounded {HARNESS_VERSION} model loop captured with fallback=none.",
        f"Execution eligibility: {eligibility_reason}.",
    )
    if write:
        record = record_live_decision(
            bundle,
            case_id=case_id,
            run_id=run_id,
            fault_evidence=fault_evidence,
            model_evidence=model_evidence,
            gatekeeper_evidence=gatekeeper_evidence,
            notes=notes,
            write=True,
        )
    else:
        record = _preview_decision_record(
            record,
            fault_evidence=fault_evidence,
            model_evidence=model_evidence,
            gatekeeper_evidence=gatekeeper_evidence,
            notes=notes,
        )

    result: dict[str, Any] = {
        "schema_version": LIVE_RUNNER_SCHEMA,
        "status": "decision_recorded",
        "case_id": case_id,
        "run_id": run_id,
        "session_id": session,
        "model_id": model_id,
        "prompt_version": PROMPT_VERSION,
        "harness_version": HARNESS_VERSION,
        "fallback": "none",
        "loop": loop.to_dict(),
        "execution_eligible": eligible,
        "execution_eligibility_reason": eligibility_reason,
        "execution_attempted": False,
        "receipt_ingested": False,
        "record": record,
        "finalization_required": True,
    }
    if not execute_approved_recovery or not eligible:
        return result

    log_path = (result_log_path or result_log_path_for_session(session)).resolve()
    before_ids = _matching_receipt_ids(log_path, run_id=run_id)
    suggestion = snapshot.get("suggest_recovery_action")
    idempotency_key = hashlib.sha256(
        f"{manifest.get('benchmark_id')}:{case_id}:{run_id}:{branch}".encode("utf-8")
    ).hexdigest()[:24]
    execution = adapter.execute_suggested_recovery(
        robot_ip=robot_ip,
        run_id=run_id,
        suggestion=suggestion,
        extra_arguments={
            "session_id": session,
            "expected_action": branch,
            "idempotency_key": idempotency_key,
        },
    )
    result["execution_attempted"] = True
    result["execution"] = execution
    if _mapping(execution).get("error"):
        result["status"] = "execution_error"
        return result

    after_ids = _matching_receipt_ids(log_path, run_id=run_id)
    new_ids = sorted(after_ids - before_ids)
    if len(new_ids) != 1:
        result["status"] = "execution_unverified"
        result["receipt_error"] = (
            f"expected one new persisted recovery receipt, found {len(new_ids)} in {log_path}"
        )
        return result

    record = ingest_recovery_receipt(
        bundle,
        case_id=case_id,
        run_id=run_id,
        result_log_path=log_path,
        entry_id=new_ids[0],
        write=True,
    )
    result.update(
        {
            "status": "execution_receipt_ingested",
            "receipt_ingested": True,
            "receipt_entry_id": new_ids[0],
            "record": record,
        }
    )
    return result


__all__ = [
    "LIVE_ALLOWED_ACTION_TYPES",
    "LIVE_RUNNER_SCHEMA",
    "MAX_LIVE_DECISION_STEPS",
    "MAX_LIVE_FORMAT_ROUNDS",
    "build_live_runtime_state",
    "extract_fault_evidence",
    "result_log_path_for_session",
    "run_live_flex_case",
]

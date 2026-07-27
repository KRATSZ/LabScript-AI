"""Strip benchmark answer keys from RuntimeState before model prompts.

Scoring metadata (gold, local_trap, global_correct, correct_action, …) may live on
the in-memory case / harness objects. Model-visible payloads must never include them.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from .state import RuntimeRisk, RuntimeState

# Keys that must never appear in model-visible expected / observed / nested dicts.
FORBIDDEN_MODEL_KEYS = frozenset(
    {
        "gold",
        "local_trap",
        "global_correct",
        "correct_action",
        "unsafe_fail_modes",
        "local_trap_action_type",
        "global_correct_action_type",
        "local_trap_action_types",
        "global_correct_action_types",
        "recover_action_types",
        "escalate_action_types",
        "cannot_repair",
        "score_mode",
        "strategy_level",
    }
)

_ANSWER_FRAGMENT_RE = re.compile(
    r"(?:^|;\s*)(?:local_trap|global_correct|gold|correct_action|unsafe_fail_modes)"
    r"=[^;]*",
    re.IGNORECASE,
)


def sanitize_mapping_for_model(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Deep-copy a mapping while dropping forbidden keys and answer fragments."""

    if not payload:
        return {}
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if str(key) in FORBIDDEN_MODEL_KEYS:
            continue
        if isinstance(value, Mapping):
            out[str(key)] = sanitize_mapping_for_model(value)
        elif isinstance(value, list):
            out[str(key)] = [
                sanitize_mapping_for_model(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        elif isinstance(value, str) and key in {"context_pack", "runtime_policy", "anomaly"}:
            cleaned = _strip_answer_fragments(value)
            if cleaned:
                out[str(key)] = cleaned
        else:
            out[str(key)] = value
    return out


def _strip_answer_fragments(text: str) -> str:
    cleaned = _ANSWER_FRAGMENT_RE.sub("", text)
    cleaned = re.sub(r"\s*;\s*;\s*", "; ", cleaned)
    return cleaned.strip(" ;")


def model_visible_runtime_state(state: RuntimeState) -> dict[str, Any]:
    """Serialize RuntimeState for LLM prompts without gold / trap labels."""

    visible = {
        "schema_version": state.schema_version,
        "run_id": state.run_id,
        "phase": state.phase,
        "robot": dict(state.robot),
        "expected": sanitize_mapping_for_model(state.expected),
        "committed": sanitize_mapping_for_model(state.committed),
        "observed": sanitize_mapping_for_model(state.observed),
        "completed_commands": [dict(item) for item in state.completed_commands],
        "failed_commands": [dict(item) for item in state.failed_commands],
        "used_tips": list(state.used_tips),
        "treated_wells": list(state.treated_wells),
        "liquid_transfers": [dict(item) for item in state.liquid_transfers],
        "remaining_plan": [dict(item) for item in state.remaining_plan],
        "risks": [_sanitize_risk(risk) for risk in state.risks],
    }
    return visible


def _sanitize_risk(risk: RuntimeRisk) -> dict[str, str]:
    message = _strip_answer_fragments(risk.message)
    # Drop messages that are just gold answer text leftovers.
    lowered = message.lower()
    if any(
        token in lowered
        for token in ("gold=", "local_trap", "global_correct", "correct_action")
    ):
        message = f"{risk.code}: resolve this fault safely."
    return {"code": risk.code, "severity": risk.severity, "message": message or risk.code}


def assert_no_gold_leak(payload: Mapping[str, Any], *, path: str = "root") -> None:
    """Raise AssertionError if forbidden keys or fragments remain (for tests)."""

    for key, value in payload.items():
        key_s = str(key)
        full = f"{path}.{key_s}"
        if key_s in FORBIDDEN_MODEL_KEYS:
            raise AssertionError(f"gold leak key at {full}")
        if isinstance(value, Mapping):
            assert_no_gold_leak(value, path=full)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, Mapping):
                    assert_no_gold_leak(item, path=f"{full}[{idx}]")
        elif isinstance(value, str):
            if _ANSWER_FRAGMENT_RE.search(value):
                raise AssertionError(f"gold leak fragment at {full}: {value!r}")
            for token in ("local_trap=", "global_correct=", "gold=", "correct_action="):
                if token in value.lower():
                    raise AssertionError(f"gold leak token at {full}: {value!r}")

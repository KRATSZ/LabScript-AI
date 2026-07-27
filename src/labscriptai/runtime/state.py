"""Runtime state primitives for LabscriptAI."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

VALID_PHASES = frozenset(
    {
        "preflight",
        "simulating",
        "ready",
        "running",
        "recovering",
        "paused",
        "completed",
        "aborted",
    }
)

# Keys that encode the benchmark answer / twin traps. Never send these to a model.
MODEL_ANSWER_KEYS = frozenset(
    {
        "gold",
        "local_trap",
        "global_correct",
        "correct_action",
        "unsafe_fail_modes",
        "strategy_level",
        "expected_policy",
        "local_trap_action_type",
        "global_correct_action_type",
        "local_trap_action_types",
        "global_correct_action_types",
        "recover_action_types",
        "escalate_action_types",
        "unsafe_action_types",
        "allowed_action_types",
    }
)


def redact_model_answer_keys(payload: Any) -> Any:
    """Recursively drop benchmark answer keys from nested mappings/lists."""

    if isinstance(payload, Mapping):
        return {
            key: redact_model_answer_keys(value)
            for key, value in payload.items()
            if key not in MODEL_ANSWER_KEYS
        }
    if isinstance(payload, (list, tuple)):
        return [redact_model_answer_keys(item) for item in payload]
    return payload


@dataclass(frozen=True)
class RuntimeRisk:
    code: str
    severity: str
    message: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RuntimeRisk":
        code = payload.get("code")
        severity = payload.get("severity")
        message = payload.get("message")
        if not isinstance(code, str) or not code:
            raise ValueError("risk.code must be a non-empty string")
        if severity not in {"info", "warning", "blocker"}:
            raise ValueError("risk.severity must be info, warning, or blocker")
        if not isinstance(message, str) or not message:
            raise ValueError("risk.message must be a non-empty string")
        return cls(code=code, severity=severity, message=message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class RuntimeState:
    run_id: str
    phase: str = "preflight"
    robot: Mapping[str, Any] = field(default_factory=dict)
    expected: Mapping[str, Any] = field(default_factory=dict)
    committed: Mapping[str, Any] = field(default_factory=dict)
    observed: Mapping[str, Any] = field(default_factory=dict)
    completed_commands: tuple[Mapping[str, Any], ...] = ()
    failed_commands: tuple[Mapping[str, Any], ...] = ()
    used_tips: tuple[str, ...] = ()
    treated_wells: tuple[str, ...] = ()
    liquid_transfers: tuple[Mapping[str, Any], ...] = ()
    remaining_plan: tuple[Mapping[str, Any], ...] = ()
    risks: tuple[RuntimeRisk, ...] = ()
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("RuntimeState.run_id is required")
        if self.phase not in VALID_PHASES:
            raise ValueError(f"invalid runtime phase: {self.phase}")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RuntimeState":
        risks = tuple(RuntimeRisk.from_mapping(item) for item in payload.get("risks", []))
        return cls(
            schema_version=str(payload.get("schema_version", "0.1")),
            run_id=str(payload.get("run_id", "")),
            phase=str(payload.get("phase", "preflight")),
            robot=dict(payload.get("robot") or {}),
            expected=dict(payload.get("expected") or {}),
            committed=dict(payload.get("committed") or {}),
            observed=dict(payload.get("observed") or {}),
            completed_commands=tuple(
                dict(item) for item in payload.get("completed_commands", [])
            ),
            failed_commands=tuple(
                dict(item) for item in payload.get("failed_commands", [])
            ),
            used_tips=tuple(str(item) for item in payload.get("used_tips", [])),
            treated_wells=tuple(str(item) for item in payload.get("treated_wells", [])),
            liquid_transfers=tuple(
                dict(item) for item in payload.get("liquid_transfers", [])
            ),
            remaining_plan=tuple(dict(item) for item in payload.get("remaining_plan", [])),
            risks=risks,
        )

    @property
    def blocker_risks(self) -> tuple[RuntimeRisk, ...]:
        return tuple(risk for risk in self.risks if risk.severity == "blocker")

    @property
    def has_robot_identity(self) -> bool:
        return bool(self.robot.get("id") or self.robot.get("serial") or self.robot.get("host"))

    def with_phase(self, phase: str) -> "RuntimeState":
        return RuntimeState(
            schema_version=self.schema_version,
            run_id=self.run_id,
            phase=phase,
            robot=dict(self.robot),
            expected=dict(self.expected),
            committed=dict(self.committed),
            observed=dict(self.observed),
            completed_commands=self.completed_commands,
            failed_commands=self.failed_commands,
            used_tips=self.used_tips,
            treated_wells=self.treated_wells,
            liquid_transfers=self.liquid_transfers,
            remaining_plan=self.remaining_plan,
            risks=self.risks,
        )

    def add_risk(self, risk: RuntimeRisk) -> "RuntimeState":
        return RuntimeState(
            schema_version=self.schema_version,
            run_id=self.run_id,
            phase=self.phase,
            robot=dict(self.robot),
            expected=dict(self.expected),
            committed=dict(self.committed),
            observed=dict(self.observed),
            completed_commands=self.completed_commands,
            failed_commands=self.failed_commands,
            used_tips=self.used_tips,
            treated_wells=self.treated_wells,
            liquid_transfers=self.liquid_transfers,
            remaining_plan=self.remaining_plan,
            risks=(*self.risks, risk),
        )

    def with_observation(self, observed: Mapping[str, Any]) -> "RuntimeState":
        """Return a new state with a fresh live observation merged in."""

        return RuntimeState(
            schema_version=self.schema_version,
            run_id=self.run_id,
            phase=self.phase,
            robot=dict(self.robot),
            expected=dict(self.expected),
            committed=dict(self.committed),
            observed=dict(observed),
            completed_commands=self.completed_commands,
            failed_commands=self.failed_commands,
            used_tips=self.used_tips,
            treated_wells=self.treated_wells,
            liquid_transfers=self.liquid_transfers,
            remaining_plan=self.remaining_plan,
            risks=self.risks,
        )

    def with_ledger(
        self,
        *,
        completed_commands: tuple[Mapping[str, Any], ...] | None = None,
        failed_commands: tuple[Mapping[str, Any], ...] | None = None,
        used_tips: tuple[str, ...] | None = None,
        treated_wells: tuple[str, ...] | None = None,
        liquid_transfers: tuple[Mapping[str, Any], ...] | None = None,
        remaining_plan: tuple[Mapping[str, Any], ...] | None = None,
    ) -> "RuntimeState":
        return RuntimeState(
            schema_version=self.schema_version,
            run_id=self.run_id,
            phase=self.phase,
            robot=dict(self.robot),
            expected=dict(self.expected),
            committed=dict(self.committed),
            observed=dict(self.observed),
            completed_commands=completed_commands
            if completed_commands is not None
            else self.completed_commands,
            failed_commands=failed_commands if failed_commands is not None else self.failed_commands,
            used_tips=used_tips if used_tips is not None else self.used_tips,
            treated_wells=treated_wells if treated_wells is not None else self.treated_wells,
            liquid_transfers=liquid_transfers
            if liquid_transfers is not None
            else self.liquid_transfers,
            remaining_plan=remaining_plan if remaining_plan is not None else self.remaining_plan,
            risks=self.risks,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "phase": self.phase,
            "robot": dict(self.robot),
            "expected": dict(self.expected),
            "committed": dict(self.committed),
            "observed": dict(self.observed),
            "completed_commands": [dict(item) for item in self.completed_commands],
            "failed_commands": [dict(item) for item in self.failed_commands],
            "used_tips": list(self.used_tips),
            "treated_wells": list(self.treated_wells),
            "liquid_transfers": [dict(item) for item in self.liquid_transfers],
            "remaining_plan": [dict(item) for item in self.remaining_plan],
            "risks": [risk.to_dict() for risk in self.risks],
        }

    def to_model_dict(self) -> dict[str, Any]:
        """Serialize state for LLM prompts without gold / twin / scoring answers."""

        # Prefer the shared sanitizer (strips keys + answer fragments in strings).
        from .model_visible_state import model_visible_runtime_state

        return model_visible_runtime_state(self)

    def stable_hash(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

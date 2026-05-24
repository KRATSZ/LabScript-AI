"""Shared immutable state for the unified LabscriptAI agent."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, Mapping, TypeAlias

from labscriptai.benchmark.package_validator import REQUIRED_PACKAGE_FILES
from labscriptai.benchmark.tasks import AuthoringTask
from labscriptai.runtime.memory import MemoryHit
from labscriptai.runtime.state import RuntimeRisk, VALID_PHASES
from labscriptai.runtime.trace import TraceWriter

AgentPhase: TypeAlias = Literal[
    "preflight",
    "simulating",
    "ready",
    "running",
    "recovering",
    "paused",
    "completed",
    "aborted",
    "drafting",
    "validating",
    "failed",
]
VALID_AGENT_PHASES = frozenset((*VALID_PHASES, "drafting", "validating", "failed"))
MemoryHitAlias: TypeAlias = MemoryHit
RuntimeRiskAlias: TypeAlias = RuntimeRisk


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    prompt: str
    difficulty: str | None = None
    required_files: tuple[str, ...] = REQUIRED_PACKAGE_FILES
    budget: Mapping[str, Any] = field(default_factory=dict)
    autonomy_mode: str = "conservative"


@dataclass(frozen=True)
class PackageRef:
    dir: Path
    files_present: tuple[str, ...] = ()
    manifest_digest: str | None = None
    last_validation: Mapping[str, Any] | None = None

    @classmethod
    def from_dir(
        cls,
        package_dir: Path,
        *,
        last_validation: Mapping[str, Any] | None = None,
    ) -> "PackageRef":
        files_present = tuple(
            sorted(path.name for path in package_dir.iterdir() if path.is_file())
        ) if package_dir.exists() else ()
        manifest = package_dir / "manifest.json"
        digest = None
        if manifest.exists():
            digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        return cls(
            dir=package_dir,
            files_present=files_present,
            manifest_digest=digest,
            last_validation=dict(last_validation) if last_validation is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dir": str(self.dir),
            "files_present": list(self.files_present),
            "manifest_digest": self.manifest_digest,
            "last_validation": dict(self.last_validation) if self.last_validation is not None else None,
        }


@dataclass(frozen=True)
class ErrorRef:
    category: str
    code: str | None = None
    raw: Any = None
    parsed: Mapping[str, Any] | None = None
    source: Literal["validate", "simulate", "robot", "tool"] = "tool"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "code": self.code,
            "raw": self.raw,
            "parsed": dict(self.parsed) if self.parsed is not None else None,
            "source": self.source,
        }


@dataclass(frozen=True)
class Counters:
    tool_calls: int = 0
    skill_loads: int = 0
    simulator_calls: int = 0
    steps: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def with_delta(self, **delta: int) -> "Counters":
        values = {name: getattr(self, name) for name in self.__dataclass_fields__}
        for key, value in delta.items():
            if key not in values:
                raise ValueError(f"unknown counter: {key}")
            values[key] += int(value)
        return Counters(**values)

    def to_dict(self) -> dict[str, int]:
        return {name: int(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class AgentState:
    run_id: str
    mode: Literal["author", "run"]
    task_spec: TaskSpec
    package: PackageRef
    trace_path: Path
    trace: TraceWriter = field(compare=False, repr=False)
    schema_version: str = "1.0"
    phase: str = "drafting"
    package_ready: bool = False
    robot_status: Mapping[str, Any] = field(default_factory=dict)
    run_status: Mapping[str, Any] = field(default_factory=dict)
    latest_error: ErrorRef | None = None
    loaded_skills: tuple[str, ...] = ()
    memory_hits: tuple[MemoryHitAlias, ...] = ()
    permissions: frozenset[str] = field(default_factory=frozenset)
    risks: tuple[RuntimeRiskAlias, ...] = ()
    counters: Counters = field(default_factory=Counters)

    def __post_init__(self) -> None:
        if self.phase not in VALID_AGENT_PHASES:
            raise ValueError(f"invalid agent phase: {self.phase}")
        if self.mode not in {"author", "run"}:
            raise ValueError("mode must be author or run")

    @classmethod
    def for_author(
        cls,
        *,
        task: AuthoringTask,
        package_dir: Path,
        trace_path: Path,
        permissions: frozenset[str],
    ) -> "AgentState":
        package_dir.mkdir(parents=True, exist_ok=True)
        run_id = f"author-{task.task_id}-{uuid.uuid4()}"
        return cls(
            run_id=run_id,
            mode="author",
            phase="drafting",
            task_spec=TaskSpec(
                task_id=task.task_id,
                difficulty=task.difficulty,
                prompt=task.prompt,
                required_files=REQUIRED_PACKAGE_FILES,
                budget={"attempts": 8, "wall_min": 30, "tokens": 24000},
            ),
            package=PackageRef.from_dir(package_dir),
            trace_path=trace_path,
            trace=TraceWriter(trace_path),
            permissions=permissions,
        )

    def with_phase(self, phase: str) -> "AgentState":
        return replace(self, phase=phase)

    def with_package(self, package: PackageRef | Mapping[str, Any]) -> "AgentState":
        if isinstance(package, PackageRef):
            ref = package
        else:
            ref = PackageRef(
                dir=Path(str(package.get("dir", self.package.dir))),
                files_present=tuple(str(item) for item in package.get("files_present", ())),
                manifest_digest=package.get("manifest_digest"),
                last_validation=package.get("last_validation"),
            )
        return replace(self, package=ref)

    def refresh_package(self, *, last_validation: Mapping[str, Any] | None = None) -> "AgentState":
        return self.with_package(PackageRef.from_dir(self.package.dir, last_validation=last_validation))

    def with_robot(
        self,
        *,
        robot_status: Mapping[str, Any] | None = None,
        run_status: Mapping[str, Any] | None = None,
    ) -> "AgentState":
        return replace(
            self,
            robot_status=dict(robot_status) if robot_status is not None else dict(self.robot_status),
            run_status=dict(run_status) if run_status is not None else dict(self.run_status),
        )

    def with_error(self, error: ErrorRef | Mapping[str, Any] | None) -> "AgentState":
        if error is None or isinstance(error, ErrorRef):
            return replace(self, latest_error=error)
        return replace(self, latest_error=ErrorRef(**dict(error)))

    def with_counters(self, **delta: int) -> "AgentState":
        return replace(self, counters=self.counters.with_delta(**delta))

    def add_risk(self, risk: RuntimeRiskAlias | Mapping[str, Any]) -> "AgentState":
        item = risk if isinstance(risk, RuntimeRisk) else RuntimeRisk.from_mapping(risk)
        return replace(self, risks=(*self.risks, item))

    def with_package_ready(self, package_ready: bool = True) -> "AgentState":
        return replace(self, package_ready=package_ready)

    def apply(self, state_patch: Mapping[str, Any]) -> "AgentState":
        next_state = self
        field_names = set(self.__dataclass_fields__)
        for key, value in state_patch.items():
            if "." in key:
                raise ValueError(f"state_patch does not allow dotted paths: {key}")
            if key.endswith("_append"):
                base = key[: -len("_append")]
                if base not in {"loaded_skills", "risks", "memory_hits"}:
                    raise ValueError(f"state_patch append not supported for: {base}")
                items = value if isinstance(value, list | tuple) else [value]
                current = tuple(getattr(next_state, base))
                if base == "risks":
                    normalized = tuple(
                        item if isinstance(item, RuntimeRisk) else RuntimeRisk.from_mapping(item)
                        for item in items
                    )
                else:
                    normalized = tuple(items)
                next_state = replace(next_state, **{base: (*current, *normalized)})
                continue
            if key not in field_names:
                raise ValueError(f"unknown state_patch key: {key}")
            if key == "counters":
                if not isinstance(value, Mapping):
                    raise ValueError("state_patch counters must be a mapping")
                next_state = next_state.with_counters(**{str(k): int(v) for k, v in value.items()})
            elif key == "phase":
                next_state = next_state.with_phase(str(value))
            elif key == "package_ready":
                next_state = next_state.with_package_ready(bool(value))
            elif key == "package":
                next_state = next_state.with_package(value)
            elif key == "robot_status":
                next_state = next_state.with_robot(robot_status=dict(value or {}))
            elif key == "run_status":
                next_state = next_state.with_robot(run_status=dict(value or {}))
            elif key == "latest_error":
                next_state = next_state.with_error(value)
            elif key in {"loaded_skills", "memory_hits"}:
                next_state = replace(next_state, **{key: tuple(value or ())})
            elif key == "risks":
                next_state = replace(
                    next_state,
                    risks=tuple(
                        item if isinstance(item, RuntimeRisk) else RuntimeRisk.from_mapping(item)
                        for item in (value or ())
                    ),
                )
            else:
                next_state = replace(next_state, **{key: value})
        return next_state

    def to_dict(self) -> dict[str, Any]:
        run_status = dict(self.run_status)
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "mode": self.mode,
            "phase": self.phase,
            "package_ready": self.package_ready,
            "task_id": self.task_spec.task_id,
            "task_spec": {
                "task_id": self.task_spec.task_id,
                "difficulty": self.task_spec.difficulty,
                "prompt": self.task_spec.prompt,
                "required_files": list(self.task_spec.required_files),
                "budget": dict(self.task_spec.budget),
                "autonomy_mode": self.task_spec.autonomy_mode,
            },
            "package": self.package.to_dict(),
            "robot_status": dict(self.robot_status),
            "run_status": run_status,
            "latest_error": self.latest_error.to_dict() if self.latest_error else None,
            "loaded_skills": list(self.loaded_skills),
            "memory_hits": [
                hit.to_dict() if hasattr(hit, "to_dict") else dict(hit) for hit in self.memory_hits
            ],
            "permissions": sorted(self.permissions),
            "risks": [risk.to_dict() for risk in self.risks],
            "counters": self.counters.to_dict(),
            "trace_path": str(self.trace_path),
            "tool_calls": self.counters.tool_calls,
            "skill_loads": self.counters.skill_loads,
            "simulator_calls": self.counters.simulator_calls,
        }
        if self.mode == "run":
            payload.update(
                {
                    "robot": dict(self.robot_status),
                    "expected": dict(run_status.get("expected") or {}),
                    "committed": dict(run_status.get("committed") or {}),
                    "observed": dict(run_status.get("observed") or {}),
                    "completed_commands": list(run_status.get("completed_commands") or ()),
                    "failed_commands": list(run_status.get("failed_commands") or ()),
                    "used_tips": list(run_status.get("used_tips") or ()),
                    "treated_wells": list(run_status.get("treated_wells") or ()),
                    "liquid_transfers": list(run_status.get("liquid_transfers") or ()),
                    "remaining_plan": list(run_status.get("remaining_plan") or ()),
                }
            )
        return payload

    def stable_hash(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

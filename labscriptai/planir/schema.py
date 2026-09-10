"""BPL Plan IR liquid-handling subset. Names match bpl/lowering/plan_ir.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

PLAN_SCHEMA_ID = "bpl.plan_ir.lh.v0"
LH_PRIMITIVES = frozenset(
    {"ASPIRATE", "DISPENSE", "MIX", "PICK_TIPS", "DROP_TIPS", "WAIT"}
)
PLR_BACKENDS = frozenset({"serializing", "hamilton", "ot2", "tecan_evo", "auto"})


class PlanError(ValueError):
    """Invalid Plan IR — never treat as sim pass."""


def _as_str(value: Any) -> str:
    return str(value or "").strip()


def _as_float(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or value is None:
        raise PlanError(f"{field} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise PlanError(f"{field} must be a number") from exc
    if number != number:  # NaN
        raise PlanError(f"{field} must be finite")
    return number


def _loc(value: Any, *, field: str) -> str:
    text = _as_str(value)
    if not text or ":" not in text:
        raise PlanError(f"{field} must look like plate:A1")
    plate, well = text.split(":", 1)
    if not plate or not well:
        raise PlanError(f"{field} must look like plate:A1")
    return f"{plate}:{well.upper()}"


def _locs(value: Any, *, field: str) -> str | None:
    """One well, a comma-separated string, or a list of plate:A1 tokens."""
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple)):
        parts = [_loc(item, field=field) for item in value if item not in (None, "")]
        return ",".join(parts) if parts else None
    text = _as_str(value)
    if not text:
        return None
    if "," in text:
        parts = [_loc(part.strip(), field=field) for part in text.split(",") if part.strip()]
        return ",".join(parts) if parts else None
    return _loc(text, field=field)


def split_locs(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _public_loc(value: str | None) -> str | list[str] | None:
    parts = list(split_locs(value))
    if not parts:
        return None
    return parts if len(parts) > 1 else parts[0]


@dataclass(frozen=True)
class PlanResource:
    id: str
    type: str
    slot: str = ""
    max_volume_ul: float | None = None


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    primitive_type: str
    dependencies: tuple[str, ...] = ()
    source: str | None = None
    destination: str | None = None
    location: str | None = None
    volume_ul: float | None = None
    cycles: int = 3
    tip_rack: str | None = None
    tip_positions: tuple[str, ...] = ()
    to_waste: bool = True
    duration_s: float | None = None

    def to_public_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "step_id": self.step_id,
            "primitive_type": self.primitive_type,
            "dependencies": list(self.dependencies),
        }
        source = _public_loc(self.source)
        if source:
            payload["source"] = source
        destination = _public_loc(self.destination)
        if destination:
            payload["destination"] = destination
        location = _public_loc(self.location)
        if location:
            payload["location"] = location
        if self.volume_ul is not None:
            payload["volume_ul"] = self.volume_ul
        if self.primitive_type == "MIX":
            payload["cycles"] = self.cycles
        if self.tip_rack:
            payload["tip_rack"] = self.tip_rack
        if self.tip_positions:
            payload["tip_positions"] = list(self.tip_positions)
        if self.primitive_type == "DROP_TIPS":
            payload["to_waste"] = self.to_waste
        if self.duration_s is not None:
            payload["duration_s"] = self.duration_s
        return payload


@dataclass
class PlanDocument:
    plan_id: str
    protocol_name: str
    backend: str
    resources: list[PlanResource]
    steps: list[PlanStep]
    initial_volumes_ul: dict[str, float] = field(default_factory=dict)
    schema: str = PLAN_SCHEMA_ID
    target: str = "pylabrobot"

    def ordered_steps(self) -> list[PlanStep]:
        by_id = {step.step_id: step for step in self.steps}
        indegree = {step.step_id: 0 for step in self.steps}
        dependents: dict[str, list[str]] = {step.step_id: [] for step in self.steps}
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in by_id:
                    raise PlanError(f"unknown dependency {dep!r} on {step.step_id}")
                indegree[step.step_id] += 1
                dependents[dep].append(step.step_id)
        ready = sorted(sid for sid, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for child in sorted(dependents[current]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        if len(order) != len(self.steps):
            raise PlanError("cycle in Plan IR dependencies")
        return [by_id[sid] for sid in order]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "plan_id": self.plan_id,
            "protocol_name": self.protocol_name,
            "target": self.target,
            "backend": self.backend,
            "resources": [
                {
                    "id": item.id,
                    "type": item.type,
                    "slot": item.slot,
                    **(
                        {"max_volume_ul": item.max_volume_ul}
                        if item.max_volume_ul is not None
                        else {}
                    ),
                }
                for item in self.resources
            ],
            "initial_volumes_ul": dict(self.initial_volumes_ul),
            "steps": [step.to_public_dict() for step in self.ordered_steps()],
        }


def _parse_step(raw: Mapping[str, Any], *, seen: set[str]) -> PlanStep:
    step_id = _as_str(raw.get("step_id") or raw.get("id"))
    if not step_id:
        raise PlanError("each step needs step_id")
    if step_id in seen:
        raise PlanError(f"duplicate step_id {step_id!r}")
    seen.add(step_id)
    primitive = _as_str(raw.get("primitive_type") or raw.get("type")).upper().replace("-", "_")
    if primitive not in LH_PRIMITIVES:
        raise PlanError(
            f"unsupported primitive {primitive or '(missing)'}; "
            f"LH subset is {', '.join(sorted(LH_PRIMITIVES))}"
        )
    deps_raw = raw.get("dependencies") or ()
    if not isinstance(deps_raw, Iterable) or isinstance(deps_raw, (str, bytes)):
        raise PlanError(f"{step_id}: dependencies must be a list")
    deps = tuple(_as_str(item) for item in deps_raw if _as_str(item))
    source = _locs(raw.get("source"), field="source")
    destination = _locs(raw.get("destination"), field="destination")
    location = _locs(raw.get("location"), field="location")
    volume = None
    if "volume_ul" in raw and raw.get("volume_ul") is not None:
        volume = _as_float(raw.get("volume_ul"), field="volume_ul")
        if volume <= 0:
            raise PlanError(f"{step_id}: volume_ul must be > 0")
    tips_raw = raw.get("tip_positions") or ()
    if isinstance(tips_raw, str):
        tips = (tips_raw.strip().upper(),) if tips_raw.strip() else ()
    elif isinstance(tips_raw, Iterable):
        tips = tuple(_as_str(item).upper() for item in tips_raw if _as_str(item))
    else:
        raise PlanError(f"{step_id}: tip_positions must be a list")

    if primitive in {"ASPIRATE", "DISPENSE", "MIX"} and volume is None:
        raise PlanError(f"{step_id}: {primitive} needs volume_ul")
    if primitive == "ASPIRATE" and not source:
        raise PlanError(f"{step_id}: ASPIRATE needs source")
    if primitive == "DISPENSE" and not destination:
        raise PlanError(f"{step_id}: DISPENSE needs destination")
    if primitive == "MIX" and not (location or source or destination):
        raise PlanError(f"{step_id}: MIX needs location")
    if primitive == "PICK_TIPS" and not tips:
        raise PlanError(f"{step_id}: PICK_TIPS needs tip_positions")

    cycles = int(raw.get("cycles") or 3)
    duration = None
    if raw.get("duration_s") is not None:
        duration = _as_float(raw.get("duration_s"), field="duration_s")

    return PlanStep(
        step_id=step_id,
        primitive_type=primitive,
        dependencies=deps,
        source=source,
        destination=destination,
        location=location or source or destination,
        volume_ul=volume,
        cycles=max(1, cycles),
        tip_rack=_as_str(raw.get("tip_rack")) or None,
        tip_positions=tips,
        to_waste=raw.get("to_waste", True) is not False,
        duration_s=duration,
    )


def load_plan(payload: Mapping[str, Any] | PlanDocument) -> PlanDocument:
    """Parse Plan IR. Raises PlanError on invalid input."""
    if isinstance(payload, PlanDocument):
        payload.ordered_steps()
        return payload
    if not isinstance(payload, Mapping):
        raise PlanError("plan must be an object")
    schema = _as_str(payload.get("schema") or PLAN_SCHEMA_ID)
    if schema and schema != PLAN_SCHEMA_ID:
        raise PlanError(f"unknown schema {schema!r}; expected {PLAN_SCHEMA_ID}")
    plan_id = _as_str(payload.get("plan_id") or payload.get("id") or "plan")
    backend = _as_str(payload.get("backend") or "auto").lower()
    if backend not in PLR_BACKENDS:
        raise PlanError(f"unknown backend {backend!r}")
    resources_raw = payload.get("resources") or []
    if not isinstance(resources_raw, list) or not resources_raw:
        raise PlanError("plan needs resources (tiprack + plate)")
    resources: list[PlanResource] = []
    for item in resources_raw:
        if not isinstance(item, Mapping):
            raise PlanError("resource must be an object")
        rid = _as_str(item.get("id"))
        rtype = _as_str(item.get("type")).lower()
        if not rid or rtype not in {"tiprack", "plate", "reservoir", "tube_rack"}:
            raise PlanError("resource needs id and type tiprack|plate|reservoir|tube_rack")
        max_vol = item.get("max_volume_ul")
        resources.append(
            PlanResource(
                id=rid,
                type=rtype,
                slot=_as_str(item.get("slot")),
                max_volume_ul=None if max_vol is None else _as_float(max_vol, field="max_volume_ul"),
            )
        )
    if not any(item.type == "tiprack" for item in resources):
        raise PlanError("plan needs a tiprack resource")
    if not any(item.type in {"plate", "reservoir", "tube_rack"} for item in resources):
        raise PlanError("plan needs a plate or reservoir")

    steps_raw = payload.get("steps") or []
    if not isinstance(steps_raw, list) or not steps_raw:
        raise PlanError("plan needs steps")
    seen: set[str] = set()
    steps = [_parse_step(item, seen=seen) for item in steps_raw if isinstance(item, Mapping)]
    if len(steps) != len(steps_raw):
        raise PlanError("every step must be an object")

    volumes_raw = payload.get("initial_volumes_ul") or payload.get("initial_volumes") or {}
    if not isinstance(volumes_raw, Mapping):
        raise PlanError("initial_volumes_ul must be an object")
    volumes: dict[str, float] = {}
    for key, value in volumes_raw.items():
        volumes[_loc(key, field="initial_volumes_ul key")] = _as_float(
            value, field=f"initial_volumes_ul[{key}]"
        )

    plan = PlanDocument(
        plan_id=plan_id,
        protocol_name=_as_str(payload.get("protocol_name") or plan_id),
        backend=backend,
        resources=resources,
        steps=steps,
        initial_volumes_ul=volumes,
        schema=PLAN_SCHEMA_ID,
        target=_as_str(payload.get("target") or "pylabrobot") or "pylabrobot",
    )
    plan.ordered_steps()
    return plan

"""Minimal LabFlow IR data model.

This module is intentionally small. It supports supplement-only cross-platform
sanity checks and does not sit on the runtime execution path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

LABFLOW_SCHEMA_VERSION = "0.1"
RESOURCE_TYPES = {"plate", "tiprack", "reservoir", "tube_rack", "module", "pipette"}
RESOURCE_TYPE_ALIASES = {
    "96_well_plate": "plate",
    "plate_96": "plate",
    "384_well_plate": "plate",
    "plate_384": "plate",
    "well_plate": "plate",
    "wellplate": "plate",
    "tip_rack": "tiprack",
    "tuberack": "tube_rack",
}
OPERATION_TYPES = {
    "pick_up_tip",
    "drop_tip",
    "aspirate",
    "dispense",
    "transfer",
    "mix",
    "pause",
    "request_confirmation",
    "module_wait",
    "thermocycler_step",
}


@dataclass(frozen=True)
class LabFlowResource:
    id: str
    type: str
    name: str = ""
    slot: str = ""
    mount: str = ""
    backend_name: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LabFlowResource":
        resource_type = str(payload.get("type", ""))
        canonical_type = RESOURCE_TYPE_ALIASES.get(resource_type, resource_type)
        backend_name = str(payload.get("backend_name", ""))
        if canonical_type not in RESOURCE_TYPES:
            backend_name = backend_name or resource_type
            canonical_type = _infer_resource_type(str(payload.get("id", "")), resource_type)
        return cls(
            id=str(payload.get("id", "")),
            type=canonical_type,
            name=str(payload.get("name", "")),
            slot=str(payload.get("slot", "")),
            mount=str(payload.get("mount", "")),
            backend_name=backend_name,
            metadata=_mapping(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "slot": self.slot,
            "mount": self.mount,
            "backend_name": self.backend_name,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LabFlowOperation:
    id: str
    op: str
    source: str = ""
    destination: str = ""
    volume_ul: float | None = None
    reagent: str = ""
    repetitions: int = 1
    message: str = ""
    module: str = ""
    condition: str = ""
    constraints: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LabFlowOperation":
        volume = payload.get("volume_ul", payload.get("volume"))
        op = str(payload.get("op", payload.get("type", "")))
        source = payload.get("source", "")
        if op == "mix" and not source:
            source = payload.get("location", "")
        return cls(
            id=str(payload.get("id", "")),
            op=op,
            source=_normalize_location(str(source)),
            destination=_normalize_location(str(payload.get("destination", payload.get("dest", "")))),
            volume_ul=float(volume) if volume is not None else None,
            reagent=str(payload.get("reagent", "")),
            repetitions=int(payload.get("repetitions", 1) or 1),
            message=str(payload.get("message", "")),
            module=str(payload.get("module", "")),
            condition=str(payload.get("condition", "")),
            constraints=_mapping(payload.get("constraints")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "op": self.op,
            "repetitions": self.repetitions,
            "constraints": dict(self.constraints),
        }
        for key in ("source", "destination", "reagent", "message", "module", "condition"):
            value = getattr(self, key)
            if value:
                payload[key] = value
        if self.volume_ul is not None:
            payload["volume_ul"] = self.volume_ul
        return payload


@dataclass(frozen=True)
class LabFlowIR:
    protocol_id: str
    resources: tuple[LabFlowResource, ...]
    operations: tuple[LabFlowOperation, ...]
    description: str = ""
    runtime_state: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = LABFLOW_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LabFlowIR":
        resources = _collect_resources(payload)
        operations = payload.get("operations") or payload.get("steps") or []
        if not isinstance(resources, list):
            resources = []
        if not isinstance(operations, list):
            operations = []
        normalized_resources: list[LabFlowResource] = []
        seen_resource_ids: set[str] = set()
        for item in resources:
            if not isinstance(item, Mapping):
                continue
            resource = LabFlowResource.from_dict(item)
            if resource.id in seen_resource_ids:
                continue
            normalized_resources.append(resource)
            seen_resource_ids.add(resource.id)
        normalized_operations = _collect_operations(operations)
        return cls(
            schema_version=_normalize_schema_version(payload.get("schema_version")),
            protocol_id=str(payload.get("protocol_id", "")),
            description=str(payload.get("description", "")),
            resources=tuple(normalized_resources),
            operations=tuple(normalized_operations),
            runtime_state=_mapping(payload.get("runtime_state")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "protocol_id": self.protocol_id,
            "description": self.description,
            "resources": [resource.to_dict() for resource in self.resources],
            "operations": [operation.to_dict() for operation in self.operations],
            "runtime_state": dict(self.runtime_state),
        }


def validate_labflow_ir(ir: LabFlowIR | Mapping[str, Any]) -> tuple[bool, list[str]]:
    if not isinstance(ir, LabFlowIR):
        ir = LabFlowIR.from_dict(ir)
    reasons: list[str] = []
    if ir.schema_version != LABFLOW_SCHEMA_VERSION:
        reasons.append(f"schema_version must be {LABFLOW_SCHEMA_VERSION}")
    if not ir.protocol_id:
        reasons.append("protocol_id is required")
    resource_ids: set[str] = set()
    pipettes = 0
    for resource in ir.resources:
        if not resource.id:
            reasons.append("resource.id is required")
        if resource.id in resource_ids:
            reasons.append(f"duplicate resource id: {resource.id}")
        resource_ids.add(resource.id)
        if resource.type not in RESOURCE_TYPES:
            reasons.append(f"unsupported resource type: {resource.type}")
        if resource.type == "pipette":
            pipettes += 1
    if pipettes == 0:
        reasons.append("at least one pipette resource is required")
    if not ir.operations:
        reasons.append("at least one operation is required")
    operation_ids: set[str] = set()
    for operation in ir.operations:
        if not operation.id:
            reasons.append("operation.id is required")
        if operation.id in operation_ids:
            reasons.append(f"duplicate operation id: {operation.id}")
        operation_ids.add(operation.id)
        if operation.op not in OPERATION_TYPES:
            reasons.append(f"unsupported operation type: {operation.op}")
        if operation.op == "transfer":
            _validate_transfer(operation, resource_ids, reasons)
        if operation.op == "aspirate":
            _validate_aspirate(operation, resource_ids, reasons)
        if operation.op == "dispense":
            _validate_dispense(operation, resource_ids, reasons)
        if operation.op == "mix":
            _validate_mix(operation, resource_ids, reasons)
    return not reasons, reasons


def _validate_transfer(
    operation: LabFlowOperation,
    resource_ids: set[str],
    reasons: list[str],
) -> None:
    if not operation.source:
        reasons.append(f"{operation.id}: transfer requires source")
    if not operation.destination:
        reasons.append(f"{operation.id}: transfer requires destination")
    if operation.volume_ul is None or operation.volume_ul <= 0:
        reasons.append(f"{operation.id}: transfer requires positive volume_ul")
    _validate_location(operation.id, "source", operation.source, resource_ids, reasons)
    _validate_location(operation.id, "destination", operation.destination, resource_ids, reasons)


def _validate_mix(
    operation: LabFlowOperation,
    resource_ids: set[str],
    reasons: list[str],
) -> None:
    if not operation.source:
        reasons.append(f"{operation.id}: mix requires source")
    if operation.volume_ul is None or operation.volume_ul <= 0:
        reasons.append(f"{operation.id}: mix requires positive volume_ul")
    if operation.repetitions < 1:
        reasons.append(f"{operation.id}: mix repetitions must be >= 1")
    _validate_location(operation.id, "source", operation.source, resource_ids, reasons)


def _validate_aspirate(
    operation: LabFlowOperation,
    resource_ids: set[str],
    reasons: list[str],
) -> None:
    if not operation.source:
        reasons.append(f"{operation.id}: aspirate requires source")
    if operation.volume_ul is None or operation.volume_ul <= 0:
        reasons.append(f"{operation.id}: aspirate requires positive volume_ul")
    _validate_location(operation.id, "source", operation.source, resource_ids, reasons)


def _validate_dispense(
    operation: LabFlowOperation,
    resource_ids: set[str],
    reasons: list[str],
) -> None:
    if not operation.destination:
        reasons.append(f"{operation.id}: dispense requires destination")
    if operation.volume_ul is None or operation.volume_ul <= 0:
        reasons.append(f"{operation.id}: dispense requires positive volume_ul")
    _validate_location(operation.id, "destination", operation.destination, resource_ids, reasons)


def _validate_location(
    operation_id: str,
    field_name: str,
    location: str,
    resource_ids: set[str],
    reasons: list[str],
) -> None:
    if not location or ":" not in location:
        return
    resource_id, _well = location.split(":", 1)
    if resource_id not in resource_ids:
        reasons.append(f"{operation_id}: {field_name} resource is unknown: {resource_id}")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _collect_resources(payload: Mapping[str, Any]) -> list[Any]:
    resources = payload.get("resources")
    if isinstance(resources, list) and resources:
        return resources
    if isinstance(resources, Mapping) and resources:
        collected_from_mapping: list[Any] = []
        for resource_id, value in resources.items():
            if not isinstance(value, Mapping):
                continue
            item = dict(value)
            item.setdefault("id", str(resource_id))
            collected_from_mapping.append(item)
        return collected_from_mapping
    collected: list[Any] = []
    for key in ("labware", "pipettes", "modules"):
        value = payload.get(key)
        if isinstance(value, list):
            collected.extend(value)
    return collected


def _collect_operations(operations: list[Any]) -> list[LabFlowOperation]:
    normalized: list[LabFlowOperation] = []
    next_index = 1
    for item in operations:
        if not isinstance(item, Mapping):
            continue
        parent_id = str(item.get("id", f"op_{next_index}") or f"op_{next_index}")
        steps = item.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, Mapping):
                    continue
                payload = dict(step)
                payload.setdefault("id", f"{parent_id}_{len(normalized) + 1}")
                payload.setdefault("reagent", item.get("reagent", ""))
                normalized.append(LabFlowOperation.from_dict(payload))
            next_index += 1
            continue
        payload = dict(item)
        payload.setdefault("id", f"op_{next_index}")
        normalized.append(LabFlowOperation.from_dict(payload))
        next_index += 1
    return normalized


def _normalize_schema_version(value: Any) -> str:
    if value in (None, "", LABFLOW_SCHEMA_VERSION):
        return LABFLOW_SCHEMA_VERSION
    # Model-generated drafts often invent "1.0" even when prompted for this
    # tiny supplement-only schema. Canonicalize on ingest; to_dict() stays strict.
    if str(value).strip() in {"1", "1.0", "v1"}:
        return LABFLOW_SCHEMA_VERSION
    return str(value)


def _normalize_location(value: str) -> str:
    if ":" in value or "/" not in value:
        return value
    resource_id, well = value.split("/", 1)
    if resource_id and well:
        return f"{resource_id}:{well}"
    return value


def _infer_resource_type(resource_id: str, backend_name: str) -> str:
    text = f"{resource_id} {backend_name}".lower()
    if "pipette" in text or "p300" in text or "p20" in text or "p1000" in text or "flex_1channel" in text:
        return "pipette"
    if "tiprack" in text or "tip_rack" in text:
        return "tiprack"
    if "reservoir" in text:
        return "reservoir"
    if "tube" in text and "rack" in text:
        return "tube_rack"
    if "thermocycler" in text or "temperature module" in text or "heater" in text or "magnetic" in text:
        return "module"
    if "plate" in text or "well" in text:
        return "plate"
    return backend_name

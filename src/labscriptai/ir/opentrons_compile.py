"""Compile minimal LabFlow IR into an Opentrons protocol skeleton."""

from __future__ import annotations

from typing import Any, Mapping

from .models import LabFlowIR, validate_labflow_ir


def compile_to_opentrons_protocol(ir: LabFlowIR | Mapping[str, Any]) -> str:
    """Generate a readable protocol.py skeleton for sanity checks."""

    if not isinstance(ir, LabFlowIR):
        ir = LabFlowIR.from_dict(ir)
    ok, reasons = validate_labflow_ir(ir)
    if not ok:
        raise ValueError("; ".join(reasons))

    lines = [
        'requirements = {"robotType": "Flex", "apiLevel": "2.24"}',
        "",
        "def run(protocol):",
    ]
    resources = {resource.id: resource for resource in ir.resources}
    names: dict[str, str] = {}
    for resource in [item for item in ir.resources if item.type != "pipette"]:
        var_name = _python_name(resource.id)
        names[resource.id] = var_name
        backend_name = resource.backend_name or resource.name or resource.id
        if resource.type in {"plate", "tiprack", "reservoir", "tube_rack"}:
            slot = resource.slot or "1"
            lines.append(f"    {var_name} = protocol.load_labware({backend_name!r}, {slot!r})")
        elif resource.type == "module":
            slot = resource.slot or "1"
            lines.append(f"    {var_name} = protocol.load_module({backend_name!r}, {slot!r})")
    for resource in [item for item in ir.resources if item.type == "pipette"]:
        var_name = _python_name(resource.id)
        names[resource.id] = var_name
        backend_name = resource.backend_name or resource.name or resource.id
        mount = resource.mount or "left"
        tiprack_ids = resource.metadata.get("tipracks") if isinstance(resource.metadata, Mapping) else None
        tipracks = [
            names[item]
            for item in (tiprack_ids if isinstance(tiprack_ids, list) else [])
            if item in names
        ]
        suffix = f", tip_racks=[{', '.join(tipracks)}]" if tipracks else ""
        lines.append(f"    {var_name} = protocol.load_instrument({backend_name!r}, {mount!r}{suffix})")
    pipette_name = next(
        (names[resource.id] for resource in ir.resources if resource.type == "pipette"),
        "pipette",
    )
    lines.append("")
    for operation in ir.operations:
        if operation.op == "pick_up_tip":
            lines.append(f"    {pipette_name}.pick_up_tip()")
        elif operation.op == "drop_tip":
            lines.append(f"    {pipette_name}.drop_tip()")
        elif operation.op == "aspirate":
            source = _opentrons_location(operation.source, names)
            lines.append(f"    {pipette_name}.aspirate({operation.volume_ul!r}, {source})")
        elif operation.op == "dispense":
            destination = _opentrons_location(operation.destination, names)
            lines.append(f"    {pipette_name}.dispense({operation.volume_ul!r}, {destination})")
        elif operation.op == "transfer":
            source = _opentrons_location(operation.source, names)
            destination = _opentrons_location(operation.destination, names)
            tip_policy = operation.constraints.get("tip_policy", "new_tip")
            lines.append(
                f"    {pipette_name}.transfer({operation.volume_ul!r}, {source}, {destination}, "
                f"new_tip={tip_policy!r})"
            )
        elif operation.op == "mix":
            location = _opentrons_location(operation.source, names)
            lines.append(
                f"    {pipette_name}.mix({operation.repetitions!r}, {operation.volume_ul!r}, {location})"
            )
        elif operation.op in {"pause", "request_confirmation"}:
            message = operation.message or "Manual confirmation required."
            lines.append(f"    protocol.pause({message!r})")
        elif operation.op in {"module_wait", "thermocycler_step"}:
            module = names.get(operation.module, _python_name(operation.module or "module"))
            reason = operation.condition or "backend-specific condition"
            lines.append(f"    # Wait for {module}: {reason}")
    return "\n".join(lines) + "\n"


def _opentrons_location(value: str, names: Mapping[str, str]) -> str:
    if ":" not in value:
        return repr(value)
    resource_id, well = value.split(":", 1)
    resource_name = names.get(resource_id, _python_name(resource_id))
    return f"{resource_name}[{well!r}]"


def _python_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    if not cleaned:
        return "resource"
    if cleaned[0].isdigit():
        cleaned = f"r_{cleaned}"
    return cleaned

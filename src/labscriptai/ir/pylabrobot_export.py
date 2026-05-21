"""Export LabFlow IR to PyLabRobot-style action dictionaries."""

from __future__ import annotations

from typing import Any, Mapping

from .models import LabFlowIR, LabFlowOperation, validate_labflow_ir


def export_pylabrobot_actions(ir: LabFlowIR | Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return a simple action list aligned with PyLabRobot execution concepts."""

    if not isinstance(ir, LabFlowIR):
        ir = LabFlowIR.from_dict(ir)
    ok, reasons = validate_labflow_ir(ir)
    if not ok:
        raise ValueError("; ".join(reasons))
    actions: list[dict[str, Any]] = []
    for operation in ir.operations:
        if operation.op in {"pick_up_tip", "drop_tip"}:
            actions.append({"action": operation.op, "operation_id": operation.id})
            continue
        if operation.op == "aspirate":
            actions.append(
                {
                    "action": "aspirate",
                    "operation_id": operation.id,
                    "source": operation.source,
                    "volume_ul": operation.volume_ul,
                    "reagent": operation.reagent,
                }
            )
            continue
        if operation.op == "dispense":
            actions.append(
                {
                    "action": "dispense",
                    "operation_id": operation.id,
                    "destination": operation.destination,
                    "volume_ul": operation.volume_ul,
                    "reagent": operation.reagent,
                }
            )
            continue
        if operation.op == "transfer":
            tip_policy = str(operation.constraints.get("tip_policy", "new_tip"))
            if tip_policy in {"new_tip", "once"}:
                actions.append({"action": "pick_up_tip", "operation_id": operation.id})
            actions.extend(_transfer_actions(operation))
            if tip_policy in {"new_tip", "once"}:
                actions.append({"action": "drop_tip", "operation_id": operation.id})
            continue
        if operation.op == "mix":
            actions.append(
                {
                    "action": "mix",
                    "operation_id": operation.id,
                    "location": operation.source,
                    "volume_ul": operation.volume_ul,
                    "repetitions": operation.repetitions,
                }
            )
            continue
        if operation.op in {"pause", "request_confirmation"}:
            actions.append(
                {
                    "action": "pause",
                    "operation_id": operation.id,
                    "message": operation.message,
                    "requires_confirmation": operation.op == "request_confirmation",
                }
            )
            continue
        if operation.op in {"module_wait", "thermocycler_step"}:
            actions.append(
                {
                    "action": "wait_for_module",
                    "operation_id": operation.id,
                    "module": operation.module,
                    "condition": operation.condition,
                    "unsupported_reason": (
                        "Backend-specific module behavior should be handled by the target platform."
                    ),
                }
            )
    return actions


def _transfer_actions(operation: LabFlowOperation) -> list[dict[str, Any]]:
    return [
        {
            "action": "aspirate",
            "operation_id": operation.id,
            "source": operation.source,
            "volume_ul": operation.volume_ul,
            "reagent": operation.reagent,
        },
        {
            "action": "dispense",
            "operation_id": operation.id,
            "destination": operation.destination,
            "volume_ul": operation.volume_ul,
            "reagent": operation.reagent,
        },
    ]

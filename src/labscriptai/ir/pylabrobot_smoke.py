"""Optional real PyLabRobot smoke execution for LabFlow IR.

This module imports PyLabRobot lazily. It is a supplement sanity check: it
proves our IR can drive real PyLabRobot APIs with a serializing backend, without
requiring hardware or making PyLabRobot a core project dependency.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
from typing import Any, Mapping

from .models import LabFlowIR, LabFlowResource, validate_labflow_ir
from .pylabrobot_export import export_pylabrobot_actions


def run_pylabrobot_serializing_smoke(
    ir: LabFlowIR | Mapping[str, Any],
    *,
    platform: str = "hamilton",
) -> dict[str, Any]:
    """Run LabFlow IR through real PyLabRobot APIs using a logging backend."""

    if not isinstance(ir, LabFlowIR):
        ir = LabFlowIR.from_dict(ir)
    ok, reasons = validate_labflow_ir(ir)
    if not ok:
        raise ValueError("; ".join(reasons))
    return asyncio.run(_run_serializing_async(ir, platform=platform))


def run_pylabrobot_opentrons_simulator_smoke(ir: LabFlowIR | Mapping[str, Any]) -> dict[str, Any]:
    """Run LabFlow IR through PyLabRobot's Opentrons OT-2 simulator backend."""

    if not isinstance(ir, LabFlowIR):
        ir = LabFlowIR.from_dict(ir)
    ok, reasons = validate_labflow_ir(ir)
    if not ok:
        raise ValueError("; ".join(reasons))
    return asyncio.run(_run_opentrons_simulator_async(ir))


async def _run_serializing_async(ir: LabFlowIR, *, platform: str) -> dict[str, Any]:
    try:
        from pylabrobot.liquid_handling import LiquidHandler
        from pylabrobot.liquid_handling.backends.serializing_backend import SerializingBackend
        from pylabrobot.resources import (
            Coordinate,
            Deck,
            no_volume_tracking,
        )
    except ImportError as exc:  # pragma: no cover - exercised only with optional dependency missing.
        raise RuntimeError("PyLabRobot is not installed; run with `uv run --with pylabrobot ...`") from exc

    class LoggingBackend(SerializingBackend):  # type: ignore[misc, valid-type]
        def __init__(self) -> None:
            super().__init__(num_channels=8)
            self.commands: list[dict[str, Any]] = []

        async def send_command(self, command: str, data: Any | None = None) -> dict[str, Any]:
            self.commands.append({"command": command, "data": data})
            return {"ok": True}

    backend = LoggingBackend()
    deck = Deck(size_x=1000, size_y=700, size_z=200)
    resources: dict[str, Any] = {}
    tiprack = None
    next_x = 0
    factories = _platform_factories(platform)
    for resource in ir.resources:
        instance = _make_pylabrobot_resource(resource, factories)
        if instance is None:
            continue
        resources[resource.id] = instance
        deck.assign_child_resource(instance, location=Coordinate(next_x, 0, 0))
        next_x += 220
        if resource.type == "tiprack" and tiprack is None:
            tiprack = instance
    if tiprack is None:
        raise ValueError("PyLabRobot smoke requires a tiprack resource")

    lh = LiquidHandler(backend=backend, deck=deck)
    await lh.setup()
    backend.commands.clear()

    await _execute_actions(lh, ir, resources, tiprack, no_volume_tracking)

    return {
        "ok": True,
        "backend": "serializing",
        "platform": platform,
        "pylabrobot_command_count": len(backend.commands),
        "pylabrobot_commands": [command["command"] for command in backend.commands],
        "resource_classes": {resource_id: type(resource).__name__ for resource_id, resource in resources.items()},
    }


async def _run_opentrons_simulator_async(ir: LabFlowIR) -> dict[str, Any]:
    try:
        from pylabrobot.liquid_handling import LiquidHandler
        from pylabrobot.liquid_handling.backends.opentrons_simulator import OpentronsOT2Simulator
        from pylabrobot.resources import (
            Cor_96_wellplate_360ul_Fb,
            nest_1_troughplate_195000uL_Vb,
            no_volume_tracking,
        )
        from pylabrobot.resources.opentrons import OTDeck, opentrons_96_tiprack_300ul
    except ImportError as exc:  # pragma: no cover - exercised only with optional dependency missing.
        raise RuntimeError("PyLabRobot is not installed; run with `uv run --with pylabrobot ...`") from exc

    deck = OTDeck()
    resources: dict[str, Any] = {}
    tiprack = None
    next_slot = 1
    for resource in ir.resources:
        instance = _make_pylabrobot_resource(
            resource,
            {
                "tiprack": opentrons_96_tiprack_300ul,
                "reservoir": nest_1_troughplate_195000uL_Vb,
                "plate": Cor_96_wellplate_360ul_Fb,
            },
        )
        if instance is None:
            continue
        resources[resource.id] = instance
        deck.assign_child_at_slot(instance, _slot_number(resource.slot, next_slot))
        next_slot += 1
        if resource.type == "tiprack" and tiprack is None:
            tiprack = instance
    if tiprack is None:
        raise ValueError("PyLabRobot simulator smoke requires a tiprack resource")

    backend = OpentronsOT2Simulator(left_pipette_name=_simulator_pipette_name(ir), right_pipette_name=None)
    lh = LiquidHandler(backend=backend, deck=deck)
    await lh.setup()
    actions = await _execute_actions(lh, ir, resources, tiprack, no_volume_tracking)
    return {
        "ok": True,
        "backend": "opentrons_ot2_simulator",
        "simulated_action_count": len(actions),
        "simulated_actions": [action["action"] for action in actions],
        "left_pipette_has_tip": bool(backend.left_pipette_has_tip),
        "deck_summary": deck.summary(),
    }


async def _execute_actions(
    liquid_handler: Any,
    ir: LabFlowIR,
    resources: Mapping[str, Any],
    tiprack: Any,
    no_volume_tracking: Any,
) -> list[dict[str, Any]]:
    actions = export_pylabrobot_actions(ir)
    tip_index = 0
    current_tip_spot = None
    for action in actions:
        name = action["action"]
        if name == "pick_up_tip":
            current_tip_spot = tiprack.get_item(tip_index)
            tip_index += 1
            await liquid_handler.pick_up_tips([current_tip_spot])
        elif name == "drop_tip":
            if current_tip_spot is None:
                raise ValueError("drop_tip encountered before pick_up_tip")
            await liquid_handler.drop_tips([current_tip_spot])
            current_tip_spot = None
        elif name == "aspirate":
            well = _resolve_well(action["source"], resources)
            with no_volume_tracking():
                await liquid_handler.aspirate([well], vols=[float(action["volume_ul"])])
        elif name == "dispense":
            well = _resolve_well(action["destination"], resources)
            with no_volume_tracking():
                await liquid_handler.dispense([well], vols=[float(action["volume_ul"])])
        elif name == "mix":
            well = _resolve_well(action["location"], resources)
            repetitions = int(action["repetitions"])
            volume = float(action["volume_ul"])
            with no_volume_tracking():
                for _ in range(repetitions):
                    await liquid_handler.aspirate([well], vols=[volume])
                    await liquid_handler.dispense([well], vols=[volume])
    return actions


def _make_pylabrobot_resource(resource: LabFlowResource, factories: Mapping[str, Any]) -> Any | None:
    if resource.type in factories:
        return factories[resource.type](name=resource.id)
    return None


def _resolve_well(location: str, resources: Mapping[str, Any]) -> Any:
    if ":" not in location:
        raise ValueError(f"location must be resource:well, got {location!r}")
    resource_id, well = location.split(":", 1)
    if resource_id not in resources:
        raise ValueError(f"unknown PyLabRobot resource: {resource_id}")
    return resources[resource_id].get_item(well)


def _platform_factories(platform: str) -> Mapping[str, Any]:
    normalized = platform.lower().replace("-", "_")
    if normalized == "opentrons":
        from pylabrobot.resources import Cor_96_wellplate_360ul_Fb, nest_1_troughplate_195000uL_Vb
        from pylabrobot.resources.opentrons import opentrons_96_tiprack_300ul

        return {
            "tiprack": opentrons_96_tiprack_300ul,
            "reservoir": nest_1_troughplate_195000uL_Vb,
            "plate": Cor_96_wellplate_360ul_Fb,
        }
    if normalized == "hamilton":
        from pylabrobot.resources import Cor_96_wellplate_360ul_Fb, nest_1_troughplate_195000uL_Vb
        from pylabrobot.resources.hamilton import hamilton_96_tiprack_300uL_filter

        return {
            "tiprack": hamilton_96_tiprack_300uL_filter,
            "reservoir": nest_1_troughplate_195000uL_Vb,
            "plate": Cor_96_wellplate_360ul_Fb,
        }
    if normalized == "tecan":
        from pylabrobot.resources import nest_1_troughplate_195000uL_Vb
        from pylabrobot.resources.tecan import DiTi_200ul_LiHa, Microplate_96_Well

        return {
            "tiprack": _quiet_factory(DiTi_200ul_LiHa),
            "reservoir": nest_1_troughplate_195000uL_Vb,
            "plate": Microplate_96_Well,
        }
    raise ValueError(f"unsupported PyLabRobot platform: {platform}")


def _quiet_factory(factory: Any) -> Any:
    def create(*args: Any, **kwargs: Any) -> Any:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return factory(*args, **kwargs)

    return create


def _slot_number(slot: str, fallback: int) -> int:
    try:
        parsed = int(slot)
    except (TypeError, ValueError):
        return fallback
    if parsed < 1 or parsed > 11:
        return fallback
    return parsed


def _simulator_pipette_name(ir: LabFlowIR) -> str:
    max_volume = max((operation.volume_ul or 0 for operation in ir.operations), default=0)
    if max_volume <= 20:
        return "p20_single_gen2"
    if max_volume <= 300:
        return "p300_single_gen2"
    for resource in ir.resources:
        if resource.type != "pipette":
            continue
        name = resource.backend_name or resource.id
        if "1000" in name:
            return "p1000_single_gen2"
        if "20" in name:
            return "p20_single_gen2"
    return "p300_single_gen2"

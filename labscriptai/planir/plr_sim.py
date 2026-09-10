"""PyLabRobot SimPass. Missing package → unavailable, never a fake green."""

from __future__ import annotations

import asyncio
import importlib.util
from typing import Any, Callable

from labscriptai.planir.schema import PlanDocument

SimFn = Callable[[PlanDocument], dict[str, Any]]


def pylabrobot_available() -> bool:
    return importlib.util.find_spec("pylabrobot") is not None


def _unavailable(message: str, *, backend: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "ok": False,
        "reason": "plr_unavailable",
        "backend": backend,
        "errors": [message],
    }
    if extra:
        payload["detail"] = extra
    return payload


def _failed(message: str, *, backend: str) -> dict[str, Any]:
    return {
        "ok": False,
        "reason": "sim_failed",
        "backend": backend,
        "errors": [message],
    }


def _success(*, backend: str, commands: int, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "backend": backend,
        "commands": commands,
        "detail": detail,
    }


def _resource_factories(backend: str) -> tuple[Any, Any]:
    """Return (tiprack_factory, plate_factory) for the chosen PLR backend."""
    if backend == "hamilton":
        from pylabrobot.resources.hamilton import hamilton_96_tiprack_300uL_filter
        from pylabrobot.resources import Cor_96_wellplate_360ul_Fb

        return hamilton_96_tiprack_300uL_filter, Cor_96_wellplate_360ul_Fb
    if backend == "tecan_evo":
        from pylabrobot.resources.tecan import DiTi_200ul_LiHa, Microplate_96_Well

        return DiTi_200ul_LiHa, Microplate_96_Well
    from pylabrobot.resources.opentrons import opentrons_96_tiprack_300ul
    from pylabrobot.resources import Cor_96_wellplate_360ul_Fb

    return opentrons_96_tiprack_300ul, Cor_96_wellplate_360ul_Fb


async def _run_serializing(plan: PlanDocument, backend_name: str) -> dict[str, Any]:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends.serializing_backend import SerializingBackend
    from pylabrobot.resources import Coordinate, Deck, Trash

    class LoggingBackend(SerializingBackend):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__(num_channels=8)
            self.commands: list[str] = []

        async def send_command(self, command: str, data: Any | None = None) -> dict[str, Any]:
            self.commands.append(str(command))
            return {"ok": True}

    tip_factory, plate_factory = _resource_factories(backend_name)
    deck = Deck(size_x=1200, size_y=800, size_z=200)
    tips = tip_factory(name="tips")
    plate = plate_factory(name="plate")
    trash = Trash(name="trash", size_x=80, size_y=80, size_z=80)
    deck.assign_child_resource(tips, location=Coordinate(100, 100, 0))
    deck.assign_child_resource(plate, location=Coordinate(300, 100, 0))
    deck.assign_child_resource(trash, location=Coordinate(900, 100, 0))
    backend = LoggingBackend()
    lh = LiquidHandler(backend=backend, deck=deck)
    await lh.setup()
    backend.commands.clear()
    await _execute(lh, plan, tips, plate, trash)
    return _success(
        backend=f"pylabrobot:{backend_name}",
        commands=len(backend.commands),
        detail={"command_names": backend.commands[:40]},
    )


def _as_seq(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


async def _execute(lh: Any, plan: PlanDocument, tips: Any, plate: Any, trash: Any) -> None:
    resources = {"tips": tips, "plate": plate}
    for resource in plan.resources:
        if resource.id not in resources:
            resources[resource.id] = plate if resource.type != "tiprack" else tips
    held: list[Any] = []

    def well_container(loc: str) -> Any:
        plate_id, well = loc.split(":", 1)
        item = resources.get(plate_id, plate)
        return item[well]

    for step in plan.ordered_steps():
        kind = step.primitive_type
        if kind == "WAIT":
            continue
        if kind == "PICK_TIPS":
            rack = resources.get(step.tip_rack or "tips", tips)
            spots: list[Any] = []
            for well in step.tip_positions or ("A1",):
                spots.extend(_as_seq(rack[well]))
            await lh.pick_up_tips(spots)
            held = spots
            continue
        if kind == "DROP_TIPS":
            target = _as_seq(trash) if step.to_waste else held
            if not target:
                target = _as_seq(tips["A1"])
            await lh.drop_tips(target, allow_nonzero_volume=True)
            held = []
            continue
        volume = float(step.volume_ul or 0)
        if kind == "ASPIRATE":
            await lh.aspirate(_as_seq(well_container(step.source or "")), vols=[volume])
            continue
        if kind == "DISPENSE":
            await lh.dispense(_as_seq(well_container(step.destination or "")), vols=[volume])
            continue
        if kind == "MIX":
            loc = step.location or step.source or step.destination or ""
            wells = _as_seq(well_container(loc))
            await lh.aspirate(wells, vols=[volume])
            await lh.dispense(wells, vols=[volume])


def _chosen_backend(plan: PlanDocument) -> str:
    if plan.backend in {"auto", "serializing"}:
        return "serializing"
    return plan.backend


def run_plr_sim(plan: PlanDocument, *, runner: SimFn | None = None) -> dict[str, Any]:
    """SimPass. ``runner`` is for tests. Never reports ok unless PLR actually ran."""
    if runner is not None:
        return runner(plan)
    if not pylabrobot_available():
        return _unavailable(
            "pylabrobot is not installed (pip install pylabrobot)",
            backend=plan.backend,
            extra={"hint": "pip install pylabrobot"},
        )
    chosen = _chosen_backend(plan)
    try:
        return asyncio.run(_run_serializing(plan, chosen))
    except Exception as exc:  # noqa: BLE001 — honest fail, not a pass
        return _failed(f"{type(exc).__name__}: {exc}", backend=f"pylabrobot:{chosen}")

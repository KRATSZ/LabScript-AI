"""PyLabRobot SimPass. Missing package → unavailable, never a fake green."""

from __future__ import annotations

import asyncio
import importlib.util
from typing import Any, Callable

from labscriptai.planir.schema import PlanDocument, split_locs

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
    if backend in {"tecan_evo", "tecan_fluent"}:
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
    try:
        from pylabrobot.resources import nest_12_troughplate_15000uL_Vb as trough_factory
    except ImportError:
        trough_factory = plate_factory
    deck = Deck(size_x=1200, size_y=800, size_z=200)
    by_type = {"tiprack": tip_factory, "plate": plate_factory, "reservoir": trough_factory}
    placed: dict[str, Any] = {}
    x = 80.0
    for resource in plan.resources:
        factory = by_type.get(resource.type, plate_factory)
        item = factory(name=resource.id)
        deck.assign_child_resource(item, location=Coordinate(x, 80, 0))
        placed[resource.id] = item
        x += 180.0
    tips = next((placed[r.id] for r in plan.resources if r.type == "tiprack"), None)
    plate = next((placed[r.id] for r in plan.resources if r.type == "plate"), None)
    if tips is None:
        tips = tip_factory(name="tips")
        deck.assign_child_resource(tips, location=Coordinate(x, 80, 0))
        placed["tips"] = tips
        x += 180.0
    if plate is None:
        plate = plate_factory(name="plate")
        deck.assign_child_resource(plate, location=Coordinate(x, 80, 0))
        placed["plate"] = plate
        x += 180.0
    trash = Trash(name="trash", size_x=80, size_y=80, size_z=80)
    deck.assign_child_resource(trash, location=Coordinate(max(x, 900), 80, 0))
    backend = LoggingBackend()
    lh = LiquidHandler(backend=backend, deck=deck)
    await lh.setup()
    backend.commands.clear()
    await _execute(lh, plan, tips, plate, trash, placed)
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


async def _execute(
    lh: Any,
    plan: PlanDocument,
    tips: Any,
    plate: Any,
    trash: Any,
    placed: dict[str, Any] | None = None,
    on_step: Callable[[int, int, str], None] | None = None,
) -> None:
    resources = {"tips": tips, "plate": plate, **(placed or {})}
    for resource in plan.resources:
        if resource.id not in resources:
            resources[resource.id] = plate if resource.type != "tiprack" else tips
    held: list[Any] = []
    steps = list(plan.ordered_steps())
    total = len(steps)

    def well_spots(loc: str | None) -> list[Any]:
        spots: list[Any] = []
        for item in split_locs(loc):
            plate_id, well = item.split(":", 1)
            container = resources.get(plate_id, plate)
            spots.extend(_as_seq(container[well]))
        return spots

    for index, step in enumerate(steps, start=1):
        kind = step.primitive_type
        if on_step is not None:
            on_step(index, total, str(kind or ""))
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
            n_held = len(held)
            if step.to_waste:
                target = [trash] * (n_held or 1)
            else:
                target = held or _as_seq(tips["A1"])
            await lh.drop_tips(target, allow_nonzero_volume=True)
            held = []
            continue
        volume = float(step.volume_ul or 0)
        if kind == "ASPIRATE":
            spots = well_spots(step.source)
            await lh.aspirate(spots, vols=[volume] * len(spots))
            continue
        if kind == "DISPENSE":
            spots = well_spots(step.destination)
            await lh.dispense(spots, vols=[volume] * len(spots))
            continue
        if kind == "MIX":
            loc = step.location or step.source or step.destination or ""
            spots = well_spots(loc)
            vols = [volume] * len(spots)
            for _ in range(max(1, int(step.cycles or 3))):
                await lh.aspirate(spots, vols=vols)
                await lh.dispense(spots, vols=vols)


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

"""PyLabRobot scientific deck visualizer for STAR / Vantage / Fluent (EVO geometry)."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from labscriptai.planir.plr_sim import _execute
from labscriptai.planir.schema import PlanDocument, PlanError, load_plan

RAIL_STRIDE = 11
_lock = threading.Lock()
_session: dict[str, Any] | None = None


def _as_seq(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _robot_kind(robot: str) -> str:
    slug = (robot or "").strip().lower()
    if "vantage" in slug:
        return "vantage"
    if "fluent" in slug or slug in {"tecan", "tecan_fluent"}:
        return "fluent"
    if "evo" in slug:
        return "fluent"
    return "star"


def _factories(kind: str) -> tuple[Any, Any, Any]:
    if kind == "fluent":
        from pylabrobot.resources.tecan import DiTi_200ul_LiHa, Microplate_96_Well

        # Tecan decks only accept TecanResource for rail math — NEST troughs are not Tecan types.
        return DiTi_200ul_LiHa, Microplate_96_Well, Microplate_96_Well
    from pylabrobot.resources.hamilton import hamilton_96_tiprack_300uL_filter
    from pylabrobot.resources import Cor_96_wellplate_360ul_Fb

    try:
        from pylabrobot.resources import nest_12_troughplate_15000uL_Vb as trough
    except ImportError:
        trough = Cor_96_wellplate_360ul_Fb
    return hamilton_96_tiprack_300uL_filter, Cor_96_wellplate_360ul_Fb, trough


def _make_deck(kind: str) -> tuple[Any, str, str]:
    if kind == "vantage":
        from pylabrobot.resources.hamilton import VantageDeck

        return VantageDeck(size=1.3), "Hamilton Vantage 1.3 m", ""
    if kind == "fluent":
        from pylabrobot.resources.tecan import EVO200Deck

        return (
            EVO200Deck(),
            "Tecan Fluent",
            "",
        )
    from pylabrobot.resources.hamilton import STARLetDeck

    return STARLetDeck(), "Hamilton STARLet", ""


def _assign_rails(deck: Any, item: Any, rails: int) -> int:
    last_error: Exception | None = None
    num_rails = int(getattr(deck, "num_rails", 54) or 54)
    start = max(1, min(rails, num_rails))
    for candidate in range(start, num_rails + 1):
        try:
            try:
                deck.assign_child_resource(item, rails=candidate, ignore_collision=False)
            except TypeError:
                deck.assign_child_resource(item, rails=candidate)
            return candidate
        except Exception as exc:  # noqa: BLE001 — try next rail
            last_error = exc
            try:
                if hasattr(deck, "has_resource") and deck.has_resource(item.name):
                    item.unassign()
            except Exception:
                pass
    raise RuntimeError(f"Could not place {item.name} on the deck: {last_error}")


def build_liquid_handler(plan: PlanDocument, robot: str) -> dict[str, Any]:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
    from pylabrobot.resources.tip_tracker import set_tip_tracking
    from pylabrobot.resources.trash import Trash
    from pylabrobot.resources.volume_tracker import set_volume_tracking

    set_tip_tracking(True)
    set_volume_tracking(True)

    kind = _robot_kind(robot)
    tip_factory, plate_factory, trough_factory = _factories(kind)
    deck, deck_name, note = _make_deck(kind)
    by_type = {"tiprack": tip_factory, "plate": plate_factory, "reservoir": trough_factory, "tube_rack": plate_factory}
    start = 12 if kind == "fluent" else 1
    occupied: list[int] = [1] if kind == "fluent" else []
    placed: dict[str, Any] = {}
    rails_used: dict[str, int] = {}
    for resource in plan.resources:
        factory = by_type.get(resource.type, plate_factory)
        item = factory(name=resource.id)
        rails = start
        while any(abs(rails - used) < RAIL_STRIDE for used in occupied):
            rails += 1
        rails = _assign_rails(deck, item, rails)
        occupied.append(rails)
        placed[resource.id] = item
        rails_used[resource.id] = rails

    tips = next((placed[r.id] for r in plan.resources if r.type == "tiprack"), None)
    plate = next((placed[r.id] for r in plan.resources if r.type in {"plate", "reservoir", "tube_rack"}), None)
    if tips is None:
        raise PlanError("plan needs a tiprack resource")
    if plate is None:
        raise PlanError("plan needs a plate or reservoir")

    try:
        trash = deck.get_trash_area()
    except Exception:
        trash = None
        for name in ("trash", "wash_waste"):
            try:
                if hasattr(deck, "has_resource") and deck.has_resource(name):
                    trash = deck.get_resource(name)
                    break
            except Exception:
                continue
        if trash is None:
            trash = Trash(name="trash", size_x=80, size_y=80, size_z=80)
            _assign_rails(deck, trash, max(occupied or [start]) + RAIL_STRIDE)

    for loc, volume in plan.initial_volumes_ul.items():
        plate_id, well = loc.split(":", 1)
        container = placed.get(plate_id, plate)
        spots = _as_seq(container[well])
        for spot in spots:
            if hasattr(spot, "set_liquids"):
                spot.set_liquids([(None, float(volume))])

    backend = LiquidHandlerChatterboxBackend(num_channels=8)
    lh = LiquidHandler(backend=backend, deck=deck)
    return {
        "lh": lh,
        "deck": deck,
        "tips": tips,
        "plate": plate,
        "trash": trash,
        "placed": placed,
        "deck_name": deck_name,
        "note": note,
        "kind": kind,
        "rails": rails_used,
    }


def _seed_volumes(plan: PlanDocument, placed: dict[str, Any], plate: Any) -> None:
    for loc, volume in plan.initial_volumes_ul.items():
        plate_id, well = loc.split(":", 1)
        container = placed.get(plate_id, plate)
        for spot in _as_seq(container[well]):
            if hasattr(spot, "set_liquids"):
                spot.set_liquids([(None, float(volume))])


def stop_plr_visualizer() -> dict[str, Any]:
    global _session
    with _lock:
        session = _session
        _session = None
    if not session:
        return {"ok": True, "stopped": False}
    stop_event: threading.Event = session["stop"]
    stop_event.set()
    loop: asyncio.AbstractEventLoop | None = session.get("loop")
    vis = session.get("visualizer")
    if loop and loop.is_running() and vis is not None:

        async def _shutdown() -> None:
            try:
                await vis.stop()
            except Exception:
                pass
            loop.stop()

        loop.call_soon_threadsafe(lambda: asyncio.ensure_future(_shutdown()))
    thread: threading.Thread | None = session.get("thread")
    if thread and thread.is_alive():
        thread.join(timeout=8)
    return {"ok": True, "stopped": True}


def start_plr_visualizer(plan_payload: dict[str, Any], robot: str) -> dict[str, Any]:
    from pylabrobot.visualizer import Visualizer

    try:
        plan = load_plan(plan_payload)
    except PlanError as exc:
        return {"ok": False, "error": str(exc)}

    stop_plr_visualizer()
    ready = threading.Event()
    holder: dict[str, Any] = {"stop": threading.Event()}

    def runner() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        holder["loop"] = loop
        try:
            built = build_liquid_handler(plan, robot)
            lh = built["lh"]
            vis = Visualizer(
                built["deck"],
                host="127.0.0.1",
                open_browser=False,
                name=f"LabscriptAI {built['deck_name']}",
                show_machine_tools_at_start=True,
            )
            holder["visualizer"] = vis
            holder["deck_name"] = built["deck_name"]
            holder["note"] = built["note"]

            async def boot() -> str:
                await vis.setup()
                await lh.setup()
                _seed_volumes(plan, built["placed"], built["plate"])
                return f"http://127.0.0.1:{vis.fs_port}/"

            url = loop.run_until_complete(boot())
            holder["url"] = url
            ready.set()

            async def play_and_hold() -> None:
                total = len(list(plan.ordered_steps()))
                holder["progress"] = {"step": 0, "total": total, "label": "", "playing": True}

                def on_step(index: int, count: int, kind: str) -> None:
                    holder["progress"] = {
                        "step": index,
                        "total": count,
                        "label": kind.replace("_", " ").title(),
                        "playing": True,
                    }

                await asyncio.sleep(1.2)
                try:
                    await _execute(
                        lh,
                        plan,
                        built["tips"],
                        built["plate"],
                        built["trash"],
                        built["placed"],
                        on_step=on_step,
                    )
                except Exception:
                    pass
                progress = holder.get("progress") or {}
                holder["progress"] = {
                    "step": int(progress.get("total") or total),
                    "total": int(progress.get("total") or total),
                    "label": "",
                    "playing": False,
                }
                while not holder["stop"].is_set():
                    await asyncio.sleep(0.25)

            loop.run_until_complete(play_and_hold())
        except Exception as exc:  # noqa: BLE001 — surface to HTTP
            holder["error"] = f"{type(exc).__name__}: {exc}"
            ready.set()
        finally:
            try:
                loop.stop()
            except Exception:
                pass
            loop.close()

    thread = threading.Thread(target=runner, name="plr-visualizer", daemon=True)
    holder["thread"] = thread
    with _lock:
        global _session
        _session = holder
    thread.start()
    if not ready.wait(timeout=45):
        stop_plr_visualizer()
        return {"ok": False, "error": "PyLabRobot visualizer timed out while starting."}
    if holder.get("error"):
        return {"ok": False, "error": holder["error"]}
    return {
        "ok": True,
        "url": holder.get("url"),
        "deck": holder.get("deck_name"),
        "note": holder.get("note") or "",
    }


def plr_visualizer_status() -> dict[str, Any]:
    with _lock:
        session = _session
    if not session or not session.get("url"):
        return {"ok": True, "running": False}
    thread: threading.Thread | None = session.get("thread")
    progress = session.get("progress") if isinstance(session.get("progress"), dict) else {}
    return {
        "ok": True,
        "running": bool(thread and thread.is_alive()),
        "url": session.get("url"),
        "deck": session.get("deck_name"),
        "note": session.get("note") or "",
        "progress": {
            "step": int(progress.get("step") or 0),
            "total": int(progress.get("total") or 0),
            "label": str(progress.get("label") or ""),
            "playing": bool(progress.get("playing")),
        },
    }


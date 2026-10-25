"""Animate a Flex protocol in MuJoCo from its ``opentrons analyze`` JSON.

    PYTHONPATH=. /usr/bin/python3 -m sim.play_protocol protocols/flex_serial_dilution.py
    PYTHONPATH=. /usr/bin/python3 -m sim.play_protocol protocols/flex_serial_dilution.analysis.json
    PYTHONPATH=. ~/Library/Python/3.9/bin/mjpython -m sim.play_protocol <protocol> --view

A ``.py`` is analyzed first with the Opentrons package found through
``OPENTRONS_PYTHON`` (or the current interpreter). Analysis files stay under
``PLUGIN_DATA/flex3d/analyses``.

Checks, all against the analysis JSON, before anything is rendered:

* geometry: every ``result.position`` matches the labware definition, slot and
  ``wellLocation`` the command names (so the scene and the engine agree);
* targets: at each positional command the MuJoCo tip end (nozzle before a
  pick-up; centre of eight for a centred 8-channel) sits on ``result.position``,
  every nozzle is over the well it should be in, and the tip end is inside
  that well;
* clearance: along the whole path nothing that moves runs into labware, the
  trash bin, the enclosure or another tool;
* liquid: volumes never go negative and the final plate is reported.

Outputs go to ``runs/protocols/<name>/`` (or ``FLEX3D_EXPORT`` when set): the
``flex.xml`` model and its scene assets, which are needed to build the scene at
all, plus ``<name>_trace.json`` (per command: position from the JSON, position in
MuJoCo, error, wells under each nozzle, video time).

Rendering is opt-in and off by default, so a plain run leaves no images behind:
``--stills`` writes the key stills and the contact sheet, ``--video`` writes an
MP4, and ``--frame T`` writes single frames at specific times. Use ``--view`` to
open the interactive MuJoCo window instead of rendering anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from . import flex_shell
from .flex_protocol import (
    CHANNELS,
    EIGHT_TOOLS,
    TRASH_FALL_M,
    Plan,
    ProtocolError,
    State,
    load_analysis,
    plan as make_plan,
    sample,
    scene_spec,
    step_at,
)
from .flex_scene import EXPORT, MM, ROOT, camera_axes, deck_camera_pose, liquid_column, load_deck, load_model, write_model

OUT_ROOT = EXPORT / "protocols"
NOZZLE_ROWS = flex_shell.NOZZLE_ROWS
DEFAULT_OPENTRONS_PYTHON = os.environ.get("OPENTRONS_PYTHON", sys.executable)

FRAME_W, FRAME_H = 1440, 810
MAIN_W = 1000
PANEL_W = FRAME_W - MAIN_W
CLOSE_H = 270
MAP_H = 300
# Web close-up: same 1.63 aspect as the video panel, larger so the tool reads on screen.
CLOSE_WEB_W, CLOSE_WEB_H = 660, 405
# Close camera (azimuth, elevation in degrees, distance in metres) the video starts from.
CLOSE_DEFAULT_ORBIT = (62.0, -20.0, 0.25)
TIP_MOUNTED_ALPHA = 0.62
LIQUID_ALPHA = 0.93
# Wall thickness of a tip, used to size the liquid column inside it.
TIP_WALL_MM = 0.35


def find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path, index in (
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1 if bold else 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc", 0),
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc", 0),
        ("C:/Windows/Fonts/simhei.ttf", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=index)
            except OSError:
                continue
    return ImageFont.load_default(size)


# ---------------------------------------------------------------- analyze


def analyze(protocol: Path) -> Path:
    python = os.environ.get("OPENTRONS_PYTHON", DEFAULT_OPENTRONS_PYTHON)
    out = EXPORT / "analyses" / f"{protocol.stem}-{hashlib.sha256(protocol.read_bytes()).hexdigest()[:12]}.analysis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(
        [str(python), "-m", "opentrons.cli", "analyze", "--json-output", str(out), str(protocol)],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0 or not out.exists():
        raise SystemExit(f"opentrons analyze failed for {protocol}:\n{done.stdout}\n{done.stderr}")
    return out


# ---------------------------------------------------------------- scene state


def _id(model, kind, name: str) -> int:
    index = mujoco.mj_name2id(model, kind, name)
    if index < 0:
        raise RuntimeError(f"missing {name}")
    return index


def orbit_pose(look_at, azimuth: float, elevation: float, distance: float) -> tuple[np.ndarray, np.ndarray]:
    """Camera position and MuJoCo quaternion for an orbit around ``look_at``.

    Angles follow MuJoCo's free camera: a negative elevation looks down from above the deck.
    """
    az, el = math.radians(azimuth), math.radians(elevation)
    forward = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    look_at = np.asarray(look_at, dtype=float)
    pos = look_at - distance * forward
    quat = np.zeros(4)
    mujoco.mju_mat2Quat(quat, camera_axes(pos, look_at).ravel())
    return pos, quat


class Scene:
    """Applies a ``(q, State)`` pair to the MuJoCo model: joints, tip visibility, liquid columns."""

    def __init__(self, plan: Plan, model, data) -> None:
        self.plan, self.model, self.data = plan, model, data
        run = plan.run
        G = mujoco.mjtObj.mjOBJ_GEOM
        self.qadr = {name: model.jnt_qposadr[_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)] for name in plan.joints}
        self.colors = {lid: np.array(liq.rgb) for lid, liq in run.liquids.items()}
        self.liquid = {}
        for key, well in plan.liquid_wells:
            lw = run.by_key(key).labware
            self.liquid[(key, well)] = (_id(model, G, f"{key}_liquid_{well}"), lw.wells[well])
        self.rack = {}
        for lw in run.labware.values():
            if lw.labware.is_tiprack:
                self.rack[lw.key] = {w: _id(model, G, f"{lw.key}_{w}") for w in lw.labware.wells}
        self.tips: dict[str, list[tuple[int, int, np.ndarray]]] = {}
        self.tip_table: dict[str, tuple[np.ndarray, np.ndarray, float]] = {}
        single_tip = {"pipette_1000": "pipette_1000_tip", "pipette_1000_left": "pipette_1000_left_tip"}
        eight_tip = {"pipette_8": "pipette_8_tip", "pipette_8_right": "pipette_8r_tip"}
        for pip in run.pipettes.values():
            if pip.tool in single_tip:
                names = [single_tip[pip.tool]]
            else:
                names = [f"{eight_tip[pip.tool]}_{r}" for r in NOZZLE_ROWS]
            self.tips[pip.tool] = [(_id(model, G, n), _id(model, G, f"{n}_liquid"), model.geom_pos[_id(model, G, n)].copy()) for n in names]
            self.tip_table[pip.tool] = self._tip_volume_table(pip.tip)
        self.lids = {m.key: _id(model, G, f"{m.key}_lid") for m in run.modules.values()
                     if m.lid_mm and mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, f'{m.key}_detail_lid') < 0}
        from .flex_module_assets import ModuleMotion
        self.module_motion = ModuleMotion(model, run)
        # The model builds one pipette body per mount the run loads (an empty
        # mount stays empty), so there is no unused tool left to hide.
        self.base_rgba = model.geom_rgba.copy()

    @staticmethod
    def _tip_volume_table(tip) -> tuple[np.ndarray, np.ndarray, float]:
        """Cumulative inner volume (uL) against height above the tip end (mm)."""

        profile = flex_shell.tip_profile(tip.length_mm, tip.top_diameter_mm)
        rs = np.array([p[0] / MM for p in profile[1:-1]])
        zs = np.array([p[1] / MM for p in profile[1:-1]])
        heights = np.linspace(0.0, tip.length_mm * 0.75, 400)
        inner = np.maximum(np.interp(heights, zs, rs) - TIP_WALL_MM, 0.05)
        volume = np.concatenate([[0.0], np.cumsum(np.pi * inner[1:] ** 2 * np.diff(heights))])
        return heights, volume, tip.reach_mm

    def _rgb(self, mix: dict[str, float]) -> np.ndarray:
        total = sum(mix.values())
        if total <= 1e-9:
            return np.array([0.5, 0.5, 0.5])
        return sum(v * self.colors.get(k, np.array([0.3, 0.5, 0.9])) for k, v in mix.items()) / total

    def apply(self, q: dict[str, float], state: State) -> None:
        m = self.model
        for name, value in q.items():
            self.data.qpos[self.qadr[name]] = value
        m.geom_rgba[:] = self.base_rgba
        for (key, well), (gid, info) in self.liquid.items():
            mix = state.wells.get((key, well), {})
            volume = sum(mix.values())
            if volume <= 0.05:
                m.geom_rgba[gid, 3] = 0.0
                continue
            height = min(volume / info.area_mm2(), info.depth)
            pos, size = liquid_column(info, height)
            m.geom_pos[gid] = pos
            m.geom_size[gid] = size
            m.geom_rgba[gid, :3] = self._rgb(mix)
            m.geom_rgba[gid, 3] = LIQUID_ALPHA
        for key, gid in self.lids.items():
            if key not in state.lid_closed:
                m.geom_rgba[gid, 3] = 0.0
        self.module_motion.apply(state)
        for key, wells in self.rack.items():
            present = state.rack.get(key, set())
            for well, gid in wells.items():
                if well not in present:
                    m.geom_rgba[gid, 3] = 0.0
        for tool, geoms in self.tips.items():
            heights, table, reach = self.tip_table[tool]
            fall = state.falling.get(tool, 0.0)
            for k, (tip_id, liquid_id, base) in enumerate(geoms):
                mounted = state.mounted[tool][k]
                m.geom_pos[tip_id] = base - np.array([0.0, 0.0, fall * TRASH_FALL_M])
                m.geom_rgba[tip_id, 3] = TIP_MOUNTED_ALPHA * (1.0 - fall) if mounted else 0.0
                mix = state.tip_liquid[tool][k]
                volume = sum(mix.values())
                if not mounted or volume <= 0.05 or fall > 0:
                    m.geom_rgba[liquid_id, 3] = 0.0
                    continue
                # An air gap at the tip outlet displaces the liquid column
                # upward.  ``tip_front_air`` is tracked separately from liquid
                # volume; treating it as liquid would make the replay show a
                # false colored slug and lose the physical order of segments.
                air = state.tip_front_air.get(tool, [0.0] * len(geoms))[k]
                low = float(np.interp(air, table, heights))
                high = float(np.interp(air + volume, table, heights))
                h = max(0.0, high - low)
                r = float(np.interp((low + high) / 2, heights, np.sqrt(np.maximum(np.gradient(table, heights), 1e-6) / np.pi)))
                m.geom_size[liquid_id, 0] = max(r * 0.92, 0.25) * MM
                m.geom_size[liquid_id, 1] = h / 2 * MM
                m.geom_pos[liquid_id, 2] = (-reach + low + h / 2 + 0.3) * MM
                m.geom_rgba[liquid_id, :3] = self._rgb(mix)
                m.geom_rgba[liquid_id, 3] = LIQUID_ALPHA
        mujoco.mj_forward(m, self.data)

    def at(self, t: float) -> tuple[dict, State]:
        q, state, _ = sample(self.plan, t)
        self.apply(q, state)
        return q, state


# ---------------------------------------------------------------- checks


def _site(model, data, name: str) -> np.ndarray:
    return data.site_xpos[_id(model, mujoco.mjtObj.mjOBJ_SITE, name)].copy()


def tool_points(model, data, tool: str, with_tip: bool) -> np.ndarray:
    """World positions of each nozzle's lowest point (tip end if mounted), meters."""

    if tool == "pipette_1000":
        return np.array([_site(model, data, "tip_end" if with_tip else "tip")])
    if tool == "pipette_1000_left":
        return np.array([_site(model, data, "tip_left_end" if with_tip else "tip_left")])
    if tool == "pipette_8_right":
        names = [f"tip_8r_end_{r}" if with_tip else f"tip_8r_{r}" for r in NOZZLE_ROWS]
        return np.array([_site(model, data, n) for n in names])
    names = [f"tip_8_end_{r}" if with_tip else f"tip_8_{r}" for r in NOZZLE_ROWS]
    return np.array([_site(model, data, n) for n in names])


def expected_position(plan: Plan, arrival, state: State) -> tuple[float, float, float]:
    """The critical point rebuilt from the labware definition, slot and ``wellLocation``."""

    run = plan.run
    cmd = run.commands[arrival.cmd]
    params = cmd["params"]
    if cmd["commandType"] == "moveToCoordinates":
        return tuple(float(params["coordinates"][axis]) for axis in "xyz")
    if arrival.target is None:
        # alternateDropLocation is an offset Opentrons already baked into result.position.
        # The trash center is not that point, so comparing them is a false miss.
        if params.get("alternateDropLocation"):
            return tuple(arrival.position_mm)
        area = run.trash.get(params["addressableAreaName"]) or run.chutes[params["addressableAreaName"]]
        off = params.get("offset") or {"x": 0, "y": 0, "z": 0}
        o, s = area.origin_mm, area.size_mm
        return (o[0] + s[0] / 2 + off["x"], o[1] + s[1] / 2 + off["y"], o[2] + s[2] + off["z"])
    key, name = arrival.target
    lw = run.by_key(key).labware
    well = lw.wells[name]
    o = state.origin[key]
    loc = params.get("wellLocation") or {"origin": "top", "offset": {"x": 0, "y": 0, "z": 0}}
    off = loc.get("offset") or {"x": 0, "y": 0, "z": 0}
    if loc.get('origin') == 'default' and cmd['commandType'] == 'dropTip':
        # Modern analyses leave return-tip height hardware-dependent. It is
        # resolved in result.position, not derivable from the labware alone.
        # Still check x/y independently and check MuJoCo z against that result.
        return (o[0] + well.x + off['x'], o[1] + well.y + off['y'], arrival.position_mm[2])
    base = {"top": well.z + well.depth, "bottom": well.z, "center": well.z + well.depth / 2}[loc.get("origin", "top")]
    return (o[0] + well.x + off["x"], o[1] + well.y + off["y"], o[2] + base + off["z"])


@dataclass
class Hit:
    cmd: int
    kind: str
    tool: str
    json_mm: tuple[float, float, float]
    definition_mm: tuple[float, float, float]
    sim_mm: tuple[float, float, float]
    error_mm: float
    wells: list
    t: float


def check_targets(plan: Plan, scene: Scene) -> tuple[list[Hit], float, float]:
    """Tip ends on ``result.position``, nozzles over the right wells, tip ends inside them."""

    model, data, run = scene.model, scene.data, plan.run
    corner = np.array(run.deck.corner)
    hits: list[Hit] = []
    worst_json = worst_sim = 0.0
    for arrival in plan.arrivals:
        key = plan.keys[arrival.key]
        scene.apply(key.q, key.state)
        kind = run.commands[arrival.cmd]["commandType"]
        with_tip = any(key.state.mounted[arrival.tool])
        points = tool_points(model, data, arrival.tool, with_tip)
        mounted = np.array(key.state.mounted[arrival.tool]) if with_tip else np.ones(len(points), bool)
        critical = points.mean(axis=0) if arrival.centered else points[0]
        sim_mm = critical / MM - corner
        json_mm = np.array(arrival.position_mm)
        definition = np.array(expected_position(plan, arrival, key.state))
        d_json = float(np.abs(definition - json_mm).max())
        if d_json > 0.1:
            raise RuntimeError(f"command {arrival.cmd + 1} {kind}: JSON position {json_mm} vs definition {definition}")
        error = float(np.linalg.norm(sim_mm - json_mm))
        if error > 0.5:
            raise RuntimeError(f"command {arrival.cmd + 1} {kind}: MuJoCo tip at {sim_mm.round(2)}, JSON {json_mm}")
        worst_json, worst_sim = max(worst_json, d_json), max(worst_sim, error)

        under = []
        if arrival.target is not None:
            lw_key, name = arrival.target
            lw = run.by_key(lw_key).labware
            for k, point in enumerate(points):
                if not mounted[k] and kind != "pickUpTip":
                    continue
                if arrival.tool in EIGHT_TOOLS and not arrival.centered:
                    want = f"{NOZZLE_ROWS[k]}{name[1:]}" if lw.wells.get(f"{NOZZLE_ROWS[k]}{name[1:]}") else None
                else:
                    want = name
                if want is None:
                    raise RuntimeError(f"command {arrival.cmd + 1}: nozzle {NOZZLE_ROWS[k]} has no well in {lw_key}")
                gid = _id(model, mujoco.mjtObj.mjOBJ_GEOM, f"{lw_key}_{want}")
                center = data.geom_xpos[gid]
                well = lw.wells[want]
                d = (point[:2] - center[:2]) / MM
                if arrival.centered:
                    inside = abs(d[0]) <= well.size_x / 2 - 1.0 and abs(d[1]) <= well.size_y / 2 - 1.0
                    offset = float(np.hypot(*d))
                else:
                    offset = float(np.hypot(*d))
                    inside = offset <= 0.5
                if not inside:
                    raise RuntimeError(f"command {arrival.cmd + 1} {kind}: nozzle {k + 1} is {offset:.2f} mm off {lw_key} {want}")
                if kind in ("aspirate", "dispense"):
                    bottom = (center[2] / MM) - well.depth / 2
                    top = bottom + well.depth
                    z = point[2] / MM
                    if not bottom - 1e-6 <= z <= top:
                        raise RuntimeError(f"command {arrival.cmd + 1} {kind}: tip end z {z:.2f} outside {want} ({bottom:.2f}-{top:.2f})")
                under.append({"nozzle": NOZZLE_ROWS[k], "well": f"{run.by_key(lw_key).name} {want}", "xy_offset_mm": round(offset, 3)})
        hits.append(
            Hit(
                arrival.cmd, kind, arrival.tool,
                tuple(round(v, 3) for v in json_mm), tuple(round(v, 3) for v in definition),
                tuple(round(float(v), 3) for v in sim_mm), round(error, 4), under, round(key.t, 3),
            )
        )
    return hits, worst_json, worst_sim


def _bounds(model, data, ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = model.geom_aabb[ids, :3]
    half = model.geom_aabb[ids, 3:]
    rot = data.geom_xmat[ids].reshape(-1, 3, 3)
    world = data.geom_xpos[ids] + np.einsum("nij,nj->ni", rot, center)
    extent = np.einsum("nij,nj->ni", np.abs(rot), half)
    return world - extent, world + extent


def _subtree(model, root: str) -> list[int]:
    root_id = _id(model, mujoco.mjtObj.mjOBJ_BODY, root)
    out = []
    for g in range(model.ngeom):
        b = model.geom_bodyid[g]
        while b not in (0, root_id):
            b = model.body_parentid[b]
        if b == root_id:
            out.append(g)
    return out


def check_clearance(plan: Plan, scene: Scene) -> tuple[float, str, int]:
    """Sweep the path: tools and carried labware against labware, trash, enclosure and each other."""

    if all(key.q == plan.keys[0].q for key in plan.keys):
        return 0.0, "no gantry or labware movement", 0
    model, data, run = scene.model, scene.data, plan.run
    layout = flex_shell.Layout.for_deck(run.deck)
    inner_lo = np.array([layout.ix0, layout.iy0, 0.0])
    inner_hi = np.array([layout.ix1, layout.iy1, layout.iz1])
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or "" for g in range(model.ngeom)]
    gantry = np.array([g for g in _subtree(model, "bridge") if model.geom_group[g] != 4])
    tip_like = np.array(
        [n.startswith(("nozzle", "pipette_8_nozzle", "pipette_8r_nozzle", "pipette_1000_tip", "pipette_8_tip", "pipette_8r_tip", "pipette_1000_left_nozzle", "pipette_1000_left_tip")) for n in names]
    )
    modules = {}
    for m in ("pipette_1000", "pipette_8", "pipette_1000_left", "pipette_8_right", "gripper"):
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, m)
        if body_id >= 0:
            modules[m] = set(_subtree(model, m))
    owner = np.full(model.ngeom, -1)
    for k, gs in enumerate(modules.values()):
        owner[list(gs)] = k
    slider = np.array([g for g in gantry if owner[g] < 0])

    lw_keys = {lw.key: lw for lw in run.labware.values()}
    mod_keys = {m.key for m in run.modules.values()}
    obstacle, obstacle_key, well_of, rack_body = [], [], {}, {}
    for g, n in enumerate(names):
        key = n.split("_", 1)[0]
        if n.startswith("body_"):
            key = n[5:]
        if key in mod_keys:
            if '_visual_' not in n:
                obstacle.append(g)
                obstacle_key.append(key)
        elif key in lw_keys and "_liquid_" not in n:
            obstacle.append(g)
            obstacle_key.append(key)
            rest = n.split("_", 1)[1] if not n.startswith("body_") else ""
            lw = lw_keys[key].labware
            if rest in lw.wells:
                well_of[g] = (key, lw.wells[rest], lw.is_tiprack)
            if n.startswith("body_"):
                rack_body[g] = key
        elif n.startswith(("trash_", "waste_chute_")):
            obstacle.append(g)
            obstacle_key.append("trash")
    obstacle = np.array(obstacle)
    obstacle_key = np.array(obstacle_key)
    # Rack bodies are solid blocks here but have a hole under every tip.
    is_well = np.array([g in well_of or g in rack_body for g in obstacle])

    times = sorted(set(np.round(np.arange(0.0, plan.duration, 0.08), 4)) | {round(k.t, 4) for k in plan.keys})
    worst, worst_geom, samples, slack = np.inf, "", 0, 5e-4
    for t in times:
        q, state = scene.at(float(t))
        samples += 1
        visible = model.geom_rgba[:, 3] > 0
        moving = gantry[visible[gantry]]
        carried = []
        aboard = (state.held, *state.riders) if state.held is not None else ()
        for key in aboard:
            carried += [g for g in _subtree(model, f"{key}_carrier") if visible[g] and "_liquid_" not in names[g]]
        mov = np.concatenate([moving, np.array(carried, dtype=int)])
        m_lo, m_hi = _bounds(model, data, mov)
        # Tips may dip just below the deck plane into a bin; a set-down plate rests on it.
        floor = np.where(tip_like[mov], -0.003, 0.0)
        floor[len(moving):] = -np.inf
        margin = np.minimum((m_lo - inner_lo - np.stack([np.zeros_like(floor), np.zeros_like(floor), floor], 1)).min(1), (inner_hi - m_hi).min(1))
        if margin.min() < -1e-4:
            g = mov[int(np.argmin(margin))]
            raise RuntimeError(f"{names[g]} leaves the enclosure by {-margin.min() * 1000:.1f} mm at t={t:.2f} s")
        if margin.min() < worst:
            worst, worst_geom = float(margin.min()), names[mov[int(np.argmin(margin))]]

        # The carried stack, and the stacks it is lifted from and set on, touch by design.
        obs_mask = visible[obstacle] & ~np.isin(obstacle_key, [*aboard, *state.seated])
        obs = obstacle[obs_mask]
        o_lo, o_hi = _bounds(model, data, obs)
        o_xy = (o_lo + o_hi)[:, :2] / 2
        o_well = is_well[obs_mask]
        depth = np.min(np.minimum(m_hi[:, None], o_hi[None]) - np.maximum(m_lo[:, None], o_lo[None]), axis=2)
        hit = depth > slack
        if hit.any():
            for i in np.where(tip_like[mov])[0]:
                xy = data.geom_xpos[mov[i], :2]
                for j in np.where(hit[i] & o_well)[0]:
                    if obs[j] in rack_body:
                        key = rack_body[obs[j]]
                        o = state.origin[key]
                        local = xy / MM - np.array(run.deck.corner[:2]) - np.array(o[:2])
                        hole = any(np.hypot(local[0] - w.x, local[1] - w.y) < 1.0 for w in lw_keys[key].labware.wells.values())
                        if hole:
                            hit[i, j] = False
                        continue
                    key, well, rack = well_of[obs[j]]
                    d = (xy - o_xy[j]) / MM
                    if rack:
                        aimed = np.hypot(*d) < 1.0
                    elif well.shape == "rectangular":
                        aimed = abs(d[0]) <= well.size_x / 2 and abs(d[1]) <= well.size_y / 2
                    else:
                        aimed = np.hypot(*d) <= well.radius
                    if aimed:
                        hit[i, j] = False
        if hit.any():
            i, j = np.argwhere(hit)[0]
            raise RuntimeError(f"{names[mov[i]]} runs into {names[obs[j]]} at t={t:.2f} s ({depth[i, j] * 1000:.1f} mm)")

        tool_geoms = moving[owner[moving] >= 0]
        t_lo, t_hi = _bounds(model, data, tool_geoms)
        s_lo, s_hi = _bounds(model, data, slider)
        own = owner[tool_geoms]
        dd = np.min(np.minimum(t_hi[:, None], t_hi[None]) - np.maximum(t_lo[:, None], t_lo[None]), axis=2)
        clash = (dd > slack) & (own[:, None] != own[None])
        ds = np.min(np.minimum(t_hi[:, None], s_hi[None]) - np.maximum(t_lo[:, None], s_lo[None]), axis=2)
        if clash.any() or (ds > slack).any():
            i, j = np.argwhere(clash)[0] if clash.any() else np.argwhere(ds > slack)[0]
            other = tool_geoms[j] if clash.any() else slider[j]
            raise RuntimeError(f"{names[tool_geoms[i]]} overlaps {names[other]} at t={t:.2f} s")
    return worst, worst_geom, samples


def check_liquid(plan: Plan) -> dict:
    for key in plan.keys:
        for where, mix in key.state.wells.items():
            if any(v < -1e-6 for v in mix.values()):
                raise RuntimeError(f"negative volume in {where}")
    final = plan.keys[-1].state
    run = plan.run
    names = {lid: liq.name for lid, liq in run.liquids.items()}
    report: dict[str, dict] = {}
    for (key, well), mix in sorted(final.wells.items(), key=lambda kv: (kv[0][0], _well_order(kv[0][1]))):
        total = sum(mix.values())
        if total < 0.05:
            continue
        report.setdefault(run.by_key(key).name, {})[well] = {
            "uL": round(total, 2),
            "composition": {names.get(k, k): round(v / total, 4) for k, v in mix.items()},
        }
    return report


def _well_order(name: str) -> tuple[int, str]:
    return (int(name[1:]) if name[1:].isdigit() else 0, name[0])


# ---------------------------------------------------------------- panel


@dataclass
class Fonts:
    title: ImageFont.FreeTypeFont
    big: ImageFont.FreeTypeFont
    body: ImageFont.FreeTypeFont
    small: ImageFont.FreeTypeFont
    tiny: ImageFont.FreeTypeFont

    @classmethod
    def load(cls) -> "Fonts":
        return cls(find_font(24, True), find_font(21, True), find_font(15), find_font(13), find_font(11))


def _wrap(draw, text: str, font, width: int) -> list[str]:
    lines, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=font) > width and line:
            lines.append(line)
            line = ch.lstrip()
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


LABWARE_FILL = {"tiprack": (78, 86, 96), "reservoir": (44, 112, 128), "plate": (214, 222, 232), "adapter": (150, 156, 164)}


def draw_deck_map(plan: Plan, state: State, step, fonts: Fonts, size=(PANEL_W, MAP_H)) -> Image.Image:
    run, deck = plan.run, plan.run.deck
    img = Image.new("RGB", size, (24, 26, 29))
    draw = ImageDraw.Draw(img)
    sw, sd = deck.slot_size
    xs = [p[0] for p in deck.slots.values()] + [b.origin_mm[0] + b.size_mm[0] for b in run.trash.values()]
    if run.chute is not None:
        xs += [run.chute.origin_mm[0] + run.chute.size_mm[0]]
    x_lo, x_hi = -6.0, max(max(xs) + 6.0, max(p[0] for p in deck.slots.values()) + sw + 6.0)
    y_lo, y_hi = -6.0, max(p[1] for p in deck.slots.values()) + sd + 6.0
    pad_top = 22
    scale = min((size[0] - 16) / (x_hi - x_lo), (size[1] - pad_top - 8) / (y_hi - y_lo))
    ox = (size[0] - (x_hi - x_lo) * scale) / 2

    def px(x: float, y: float) -> tuple[float, float]:
        return (ox + (x - x_lo) * scale, size[1] - 8 - (y - y_lo) * scale)

    draw.text((10, 4), "Deck top view (live)", font=fonts.small, fill=(170, 176, 184))
    hot = set(step.slots) if step else set()
    for name, pos in deck.slots.items():
        a, b = px(pos[0], pos[1] + sd), px(pos[0] + sw, pos[1])
        draw.rectangle((a, b), outline=(70, 74, 80), width=1, fill=(38, 41, 45))
        draw.text((b[0] - 18, b[1] - 14), name, font=fonts.tiny, fill=(120, 126, 134))
    for bin_ in run.trash.values():
        o, s = bin_.origin_mm, bin_.size_mm
        a, b = px(o[0], o[1] + s[1]), px(o[0] + s[0], o[1])
        slot = bin_.name.replace("movableTrash", "")
        draw.rectangle((a, b), fill=(16, 17, 19), outline=(255, 160, 40) if slot in hot else (96, 100, 106), width=3 if slot in hot else 1)
        draw.text(((a[0] + b[0]) / 2 - 20, (a[1] + b[1]) / 2 - 7), "Trash", font=fonts.tiny, fill=(190, 194, 200))
    for mod in run.modules.values():
        (ax, ay, _), (ix, iy), (mx, my) = mod.area_mm, mod.interface, mod.margin
        a, b = px(ax - mx, ay + iy + my), px(ax + ix + mx, ay - my)
        hot_mod = mod.slot in hot
        draw.rectangle((a, b), fill=(92, 98, 108), outline=(255, 160, 40) if hot_mod else (150, 156, 164), width=3 if hot_mod else 1)
        draw.text((a[0] + 3, b[1] - 13), mod.label, font=fonts.tiny, fill=(225, 228, 232))
    if run.chute is not None:
        o, s = run.chute.origin_mm, run.chute.size_mm
        a, b = px(o[0], o[1] + s[1]), px(o[0] + s[0], o[1])
        active = step is not None and step.kind == "moveToAddressableAreaForDropTip" and "chute" in step.text.lower()
        draw.rectangle((a, b), fill=(16, 17, 19), outline=(255, 160, 40) if active else (96, 100, 106), width=3 if active else 1)
        draw.text(((a[0] + b[0]) / 2 - 24, (a[1] + b[1]) / 2 - 7), "Chute", font=fonts.tiny, fill=(190, 194, 200))
    for lw in sorted(run.labware.values(), key=lambda item: state.origin[item.key][2]):
        o = state.origin[lw.key]
        L = lw.labware
        kind = "tiprack" if L.is_tiprack else "adapter" if L.is_adapter and not L.wells else ("reservoir" if len(L.wells) <= 12 else "plate")
        a, b = px(o[0], o[1] + L.y), px(o[0] + L.x, o[1])
        draw.rectangle((a, b), fill=LABWARE_FILL[kind], outline=(30, 32, 36))
        r = max(1.5, 0.45 * 9.0 * scale)
        present = state.rack.get(lw.key, set())
        for name, well in L.wells.items():
            cx, cy = px(o[0] + well.x, o[1] + well.y)
            mix = state.wells.get((lw.key, name), {})
            vol = sum(mix.values())
            if kind == "tiprack":
                if name in present:
                    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(236, 238, 240))
                continue
            if vol > 0.05:
                rgb = sum(v * np.array(run.liquids[k].rgb) for k, v in mix.items()) / vol
                fill = tuple(int(c * 255) for c in rgb)
            else:
                fill = (240, 244, 248) if kind == "plate" else (60, 140, 156)
            if kind == "reservoir":
                hx, hy = well.size_x / 2 * scale, well.size_y / 2 * scale
                draw.rectangle((cx - hx, cy - hy, cx + hx, cy + hy), fill=fill, outline=(28, 70, 80))
            else:
                draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=None if vol > 0.05 else (168, 176, 186))
        label = lw.name
        while draw.textlength(label, font=fonts.tiny) > b[0] - a[0] - 4 and len(label) > 3:
            label = label.rstrip("…")[:-1] + "…"
        draw.rectangle((a[0], a[1] - 14, b[0], a[1]), fill=(12, 13, 15))
        draw.text((a[0] + 2, a[1] - 14), label, font=fonts.tiny, fill=(235, 238, 242))
    for name in hot:
        if name in deck.slots:
            pos = deck.slots[name]
            a, b = px(pos[0] - 2, pos[1] + sd + 2), px(pos[0] + sw + 2, pos[1] - 2)
            draw.rectangle((a, b), outline=(255, 160, 40), width=3)
    if step and step.kind == "moveLabware" and len(step.slots) == 2 and all(s in deck.slots for s in step.slots):
        (sa, sb) = [deck.slots[s] for s in step.slots]
        p0, p1 = px(sa[0] + sw / 2, sa[1] + sd / 2), px(sb[0] + sw / 2, sb[1] + sd / 2)
        draw.line((p0, p1), fill=(255, 160, 40), width=4)
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for da in (2.6, -2.6):
            draw.line((p1, (p1[0] + 14 * math.cos(ang + da), p1[1] + 14 * math.sin(ang + da))), fill=(255, 160, 40), width=4)
    return img


def draw_text_panel(plan: Plan, step, t: float, fonts: Fonts, size) -> Image.Image:
    img = Image.new("RGB", size, (250, 251, 252))
    draw = ImageDraw.Draw(img)
    steps = [s for s in plan.steps if s.kind != "loadLiquid"]
    w = size[0] - 28
    y = 12
    if step is None:
        draw.text((14, y), "Preparing to run", font=fonts.big, fill=(30, 34, 40))
        return img
    index = steps.index(step) + 1 if step in steps else 0
    draw.text((14, y), f"Command {step.cmd + 1}  ·  Step {index}/{len(steps)}", font=fonts.small, fill=(110, 116, 124))
    y += 22
    for line in _wrap(draw, step.text, fonts.big, w)[:3]:
        draw.text((14, y), line, font=fonts.big, fill=(20, 24, 30))
        y += 28
    for line in _wrap(draw, step.detail, fonts.tiny, w)[:3]:
        draw.text((14, y), line, font=fonts.tiny, fill=(100, 106, 114))
        y += 15
    y += 8
    draw.line((14, y, size[0] - 14, y), fill=(222, 226, 230))
    y += 8
    draw.text((14, y), "Next", font=fonts.small, fill=(110, 116, 124))
    y += 20
    for nxt in steps[index : index + 4]:
        line = _wrap(draw, nxt.text, fonts.body, w)[0]
        draw.text((14, y), line, font=fonts.body, fill=(80, 86, 94))
        y += 21
        if y > size[1] - 20:
            break
    return img


def caption(img: Image.Image, plan: Plan, t: float, fonts: Fonts) -> None:
    draw = ImageDraw.Draw(img, "RGBA")
    title = plan.run.title
    box_w = int(draw.textlength(title, font=fonts.title)) + 28
    draw.rounded_rectangle((14, 14, 14 + max(box_w, 300), 78), 10, fill=(16, 18, 22, 190))
    draw.text((28, 20), title, font=fonts.title, fill=(255, 255, 255))
    draw.text((28, 52), f"{plan.run.path.name}   t = {t:5.1f} / {plan.duration:.1f} s", font=fonts.small, fill=(190, 196, 204))


# ---------------------------------------------------------------- render


class _RenderTarget:
    """Size-specific view over one MuJoCo offscreen context.

    MuJoCo supports multiple ``Renderer`` objects, but each one owns a native
    offscreen context and framebuffer.  On macOS this is fragile when the
    contexts are switched repeatedly, especially when their dimensions differ:
    ``mjr_readPixels`` can return the other framebuffer's stale/garbled rows.
    Keep one native renderer and crop (without changing aspect) then resize
    its RGB output for the small close-up panels.  The public shape
    (``height``, ``width``, ``update_scene``,
    ``render``, ``close``) stays compatible with ``web_player.Model.close``.
    """

    def __init__(self, renderer: mujoco.Renderer, width: int, height: int) -> None:
        self._renderer = renderer
        self.width = width
        self.height = height
        self._closed = False

    @property
    def model(self):
        return self._renderer.model

    def update_scene(self, *args, **kwargs):
        return self._renderer.update_scene(*args, **kwargs)

    def render(self) -> np.ndarray:
        image = Image.fromarray(self._renderer.render())
        if image.size != (self.width, self.height):
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            # ``resize`` alone would squeeze the 1000x810 source into the
            # 1.63:1 close panel.  ImageOps.fit first takes a centred viewport
            # at the requested aspect ratio, then resamples that viewport.
            image = ImageOps.fit(image, (self.width, self.height), method=resampling, centering=(0.5, 0.5))
        return np.asarray(image)

    def close(self) -> None:
        """Close the shared native renderer from its owning GL context.

        The Flex web renderer exposes three targets over one native
        ``mujoco.Renderer``.  MuJoCo 3.17 frees native framebuffer resources
        in ``Renderer.close()`` but does not make that renderer's context
        current first; doing so here keeps direct target cleanup safe as well
        as the Model-level eviction path.
        """
        if self._closed:
            return
        self._closed = True
        owner = self._renderer
        context = getattr(owner, "_gl_context", None)
        if context is not None:
            context.make_current()
        owner.close()


class Renderer:
    # The authored overview camera is intentionally close enough to read the
    # deck.  The web main view needs a little more breathing room so the right
    # foot and bottom sill remain visible when the tools are at home.
    WEB_MAIN_MARGIN_SCALE = 1.18

    def __init__(self, plan: Plan, scene: Scene) -> None:
        self.plan, self.scene = plan, scene
        # MuJoCo's Python renderer owns a native GL context.  The web page can
        # ask for the main and close images from different request paths, and
        # the context/data/camera mutations are not safe to interleave.  Keep
        # one re-entrant guard around each complete render transaction; the
        # re-entrant form lets ``frame`` call ``_compose`` without deadlocking.
        self._render_lock = threading.RLock()
        self.fonts = Fonts.load()
        # One native context avoids the MuJoCo 3.17 multi-framebuffer artefact
        # seen when main (1000x810), video close (440x270) and web close
        # (660x405) renderers are alternated.  Targets preserve the old API and
        # output dimensions while sharing this one context.
        self._native_renderer = mujoco.Renderer(scene.model, height=FRAME_H, width=MAIN_W)
        self.main = _RenderTarget(self._native_renderer, MAIN_W, FRAME_H)
        self.close = _RenderTarget(self._native_renderer, PANEL_W, CLOSE_H)
        # Beauty views keep the machine shell and glass.  The existing xray
        # option remains the close-up/offline-video contract: it hides shell
        # groups so the working head is readable.  Previously this one option
        # was also used by web_main, which made the Flex web main view show
        # only the deck.
        self.normal = mujoco.MjvOption()
        self.normal.sitegroup[:] = 0
        self.xray = mujoco.MjvOption()
        self.xray.sitegroup[:] = 0
        for group in (1, 2):
            self.xray.geomgroup[group] = 0
        self.cam = mujoco.MjvCamera()
        self.cam.distance, self.cam.azimuth, self.cam.elevation = 0.25, 62.0, -20.0
        self.focus: np.ndarray | None = None
        # The mp4 main view is the fixed "deck" camera. The web view moves that same camera,
        # so its default pose and field of view match the video.
        self.deck_cam = _id(scene.model, mujoco.mjtObj.mjOBJ_CAMERA, "deck")
        _, look_at = deck_camera_pose(plan.run.deck)
        self.deck_look_at = np.array(look_at, dtype=float)
        self._deck_pos0 = scene.model.cam_pos[self.deck_cam].copy()
        self._deck_quat0 = scene.model.cam_quat[self.deck_cam].copy()
        self._deck_fovy0 = float(scene.model.cam_fovy[self.deck_cam])
        # The offline clip's deck camera looks through the door at the work
        # surface.  Browser users need an initial whole-instrument view like
        # the OT-2 page, so derive the web orbit from the authored overview
        # camera while keeping the video camera untouched.
        self.web_main_look_at = np.array(flex_shell.Layout.for_deck(plan.run.deck).view_target, dtype=float)
        self.web_main_cam = _id(scene.model, mujoco.mjtObj.mjOBJ_CAMERA, "overview")
        overview_pos = scene.model.cam_pos[self.web_main_cam].copy()
        self._web_main_pos0 = self.web_main_look_at + self.WEB_MAIN_MARGIN_SCALE * (overview_pos - self.web_main_look_at)
        self._web_main_quat0 = np.zeros(4)
        mujoco.mju_mat2Quat(self._web_main_quat0, camera_axes(self._web_main_pos0, self.web_main_look_at).ravel())
        self._web_main_fovy0 = float(scene.model.cam_fovy[self.web_main_cam])
        self.track: np.ndarray | None = None
        self.track_fps = 30
        # Web close-up: a larger panel than the video's, with its own camera so the video's stays put.
        self.close_web = _RenderTarget(self._native_renderer, CLOSE_WEB_W, CLOSE_WEB_H)
        self.web_cam = mujoco.MjvCamera()
        self.web_cam.distance, self.web_cam.azimuth, self.web_cam.elevation = CLOSE_DEFAULT_ORBIT[2], CLOSE_DEFAULT_ORBIT[0], CLOSE_DEFAULT_ORBIT[1]
        # Close-up fallback between tool steps: the site of the first pipette this run mounts.
        tools = {p.tool for p in plan.run.pipettes.values()}
        if "pipette_1000_left" in tools:
            self.idle_tip = "tip_left"
        elif "pipette_8_right" in tools:
            self.idle_tip = "tip_8r_A"
        elif "pipette_8" in tools:
            self.idle_tip = "tip_8_A"
        elif "pipette_1000" in tools:
            self.idle_tip = "tip"
        else:
            self.idle_tip = "gripper_center"

    def close_point(self, step, state: State) -> np.ndarray:
        model, data = self.scene.model, self.scene.data
        tool = step.tool if step and step.tool else None
        if step and step.kind == "moveLabware":
            tool = "gripper"
        if tool == "gripper":
            return _site(model, data, "gripper_center") + np.array([0.0, 0.0, 0.03])
        if tool is None:
            return self.focus if self.focus is not None else _site(model, data, self.idle_tip)
        points = tool_points(model, data, tool, any(state.mounted[tool]))
        return points.mean(axis=0) + np.array([0.0, 0.0, 0.035])

    def _advance(self, t: float, smooth_focus: bool = True) -> tuple:
        """Pose the scene at ``t`` and move the close-up focus one step, as the video does."""
        _, state = self.scene.at(t)
        step = step_at(self.plan, t)
        target = self.close_point(step, state)
        if self.focus is None or not smooth_focus:
            self.focus = target
        else:
            self.focus = self.focus + 0.22 * (target - self.focus)
        return state, step

    def _compose(self, t: float, state: State, step, main: Image.Image) -> Image.Image:
        self.cam.lookat[:] = self.focus
        self.close.update_scene(self.scene.data, camera=self.cam, scene_option=self.xray)
        close = Image.fromarray(self.close.render())
        frame = Image.new("RGB", (FRAME_W, FRAME_H), (250, 251, 252))
        frame.paste(main, (0, 0))
        caption(frame, self.plan, t, self.fonts)
        frame.paste(close, (MAIN_W, 0))
        label = ImageDraw.Draw(frame, "RGBA")
        label.rounded_rectangle((MAIN_W + 8, 8, MAIN_W + 92, 30), 6, fill=(16, 18, 22, 190))
        label.text((MAIN_W + 16, 10), "Follow close-up", font=self.fonts.small, fill=(255, 255, 255))
        frame.paste(draw_deck_map(self.plan, state, step, self.fonts), (MAIN_W, CLOSE_H))
        frame.paste(draw_text_panel(self.plan, step, t, self.fonts, (PANEL_W, FRAME_H - CLOSE_H - MAP_H)), (MAIN_W, CLOSE_H + MAP_H))
        return frame

    def frame(self, t: float, smooth_focus: bool = True) -> Image.Image:
        """One frame of the video: the main view is the fixed deck camera."""
        with self._render_lock:
            self._set_main_pose(None)
            state, step = self._advance(t, smooth_focus)
            self.main.update_scene(self.scene.data, camera="deck", scene_option=self.xray)
            return self._compose(t, state, step, Image.fromarray(self.main.render()))

    def build_track(self, fps: int = 30) -> None:
        """Close-up focus for every frame of the video, computed in the same order the video uses."""
        frames = int(math.ceil(self.plan.duration * fps)) + 1
        self.focus = None
        track = np.zeros((frames, 3))
        for i in range(frames):
            self._advance(min(i / fps, self.plan.duration))
            track[i] = self.focus
        self.track, self.track_fps = track, fps
        self.focus = None

    def web_main(self, t: float, orbit: tuple | None = None) -> Image.Image:
        """Main web view with the full Flex enclosure and working deck.

        The offline video deliberately keeps its historical xray/deck view,
        while the browser main view is a beauty view like the OT-2 page.  The
        caller can still pass an orbit around the deck camera's look-at point.
        """
        with self._render_lock:
            self._set_web_main_pose(orbit)
            self.scene.at(t)
            self.main.update_scene(self.scene.data, camera="deck", scene_option=self.normal)
            return Image.fromarray(self.main.render())

    def web_close(self, t: float, orbit: tuple = CLOSE_DEFAULT_ORBIT) -> Image.Image:
        """Follow close-up for the web page.

        The look-at point is the video's focus track at ``t``, so it stays on the working tool.
        ``orbit`` is (azimuth, elevation, distance) of the close camera around that point.
        """
        with self._render_lock:
            self.scene.at(t)
            self.web_cam.lookat[:] = self.track[self._track_index(t)]
            self.web_cam.azimuth, self.web_cam.elevation, self.web_cam.distance = orbit
            self.close_web.update_scene(self.scene.data, camera=self.web_cam, scene_option=self.xray)
            return Image.fromarray(self.close_web.render())

    def composite(self, t: float, orbit: tuple | None = None) -> Image.Image:
        """Four-panel frame at ``t`` for the web view.

        ``orbit`` is (azimuth, elevation, distance) of the main view; None gives the video's view.
        The close-up follows the precomputed track, so frames can be requested in any order.
        """
        with self._render_lock:
            self._set_main_pose(orbit)
            _, state = self.scene.at(t)
            step = step_at(self.plan, t)
            self.focus = self.track[self._track_index(t)]
            self.main.update_scene(self.scene.data, camera="deck", scene_option=self.normal)
            return self._compose(t, state, step, Image.fromarray(self.main.render()))

    def _track_index(self, t: float) -> int:
        index = int(round(t * self.track_fps))
        return min(max(index, 0), len(self.track) - 1)

    def _set_main_pose(self, orbit) -> None:
        model = self.scene.model
        if orbit is None:
            model.cam_pos[self.deck_cam] = self._deck_pos0
            model.cam_quat[self.deck_cam] = self._deck_quat0
            model.cam_fovy[self.deck_cam] = self._deck_fovy0
            return
        pos, quat = orbit_pose(self.deck_look_at, *orbit)
        model.cam_pos[self.deck_cam] = pos
        model.cam_quat[self.deck_cam] = quat
        model.cam_fovy[self.deck_cam] = self._deck_fovy0

    def _set_web_main_pose(self, orbit) -> None:
        """Set the browser main camera without changing the offline deck pose."""

        model = self.scene.model
        if orbit is None:
            model.cam_pos[self.deck_cam] = self._web_main_pos0
            model.cam_quat[self.deck_cam] = self._web_main_quat0
            model.cam_fovy[self.deck_cam] = self._web_main_fovy0
            return
        pos, quat = orbit_pose(self.web_main_look_at, *orbit)
        model.cam_pos[self.deck_cam] = pos
        model.cam_quat[self.deck_cam] = quat
        model.cam_fovy[self.deck_cam] = self._web_main_fovy0

    def default_orbit(self) -> dict:
        """Browser main overview orbit; offline video keeps its deck camera."""
        offset = self.web_main_look_at - self._web_main_pos0
        dist = float(np.linalg.norm(offset))
        fwd = offset / dist
        return {
            "azimuth": math.degrees(math.atan2(fwd[1], fwd[0])),
            "elevation": math.degrees(math.asin(fwd[2])),
            "distance": dist,
            "lookat": [float(v) for v in self.web_main_look_at],
        }


def render_video(
    plan: Plan, renderer: Renderer, path: Path, fps: int, t0: float | None = None, t1: float | None = None
) -> int:
    whole = t0 is None and t1 is None
    start = 0.0 if t0 is None else t0
    end = plan.duration if t1 is None else t1
    if fps <= 0:
        raise ValueError("fps must be greater than zero")
    if not whole and not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= plan.duration):
        raise ValueError("video range must satisfy 0 <= start < end <= duration")
    if whole:
        frames = int(math.ceil(plan.duration * fps)) + 1
    else:
        frames = int(math.ceil((end - start) * fps))
        # Floating-point span/fps products sit just above an integer at exact
        # frame boundaries; adjust so every sampled time is strictly before end.
        while frames > 0 and start + (frames - 1) / fps >= end:
            frames -= 1
        while start + frames / fps < end:
            frames += 1
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{FRAME_W}x{FRAME_H}", "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        renderer.focus = None
        for i in range(frames):
            t = min(i / fps, plan.duration) if whole else start + i / fps
            proc.stdin.write(renderer.frame(t).tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
    finally:
        if proc.stdin and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except OSError:
                pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    return frames


STILL_KINDS = ("pickUpTip", "aspirate", "dispense", "moveLabware", "dropTipInPlace")


def pick_stills(plan: Plan, limit: int = 9) -> list:
    """A spread of steps: the first of each kind, the first mix, then evenly spaced others."""

    steps = [s for s in plan.steps if s.kind in STILL_KINDS]
    chosen = []
    for kind in STILL_KINDS:
        first = next((s for s in steps if s.kind == kind), None)
        if first:
            chosen.append(first)
    mix = next((s for s in steps if s.text.startswith("Mix")), None)
    if mix:
        chosen.append(mix)
    moves = [s for s in steps if s.kind == "moveLabware"]
    chosen += moves
    rest = [s for s in steps if s not in chosen]
    while len(chosen) < limit and rest:
        chosen.append(rest.pop(len(rest) // 2))
    unique = []
    for s in sorted(chosen, key=lambda s: s.t0):
        if s not in unique:
            unique.append(s)
    return unique[:limit]


def still_time(plan: Plan, step) -> float:
    """Inside the step, at the moment that shows it best."""

    if step.kind == "moveLabware":
        return step.t0 + 0.55 * (step.t1 - step.t0)
    if step.kind == "dropTipInPlace":
        return step.t0 + 0.4 * (step.t1 - step.t0)
    return step.t1 - 0.02


def render_stills(plan: Plan, renderer: Renderer, folder: Path, name: str) -> list[Path]:
    paths = []
    renderer.focus = None
    first = renderer.frame(0.0, smooth_focus=False)
    path = folder / f"{name}_start.png"
    first.save(path)
    paths.append(path)
    thumbs = []
    for k, step in enumerate(pick_stills(plan), start=1):
        img = renderer.frame(still_time(plan, step), smooth_focus=False)
        path = folder / f"{name}_step{k:02d}_cmd{step.cmd + 1:03d}_{step.kind}.png"
        img.save(path)
        paths.append(path)
        thumbs.append((img, step))
    end = renderer.frame(plan.duration, smooth_focus=False)
    path = folder / f"{name}_end.png"
    end.save(path)
    paths.append(path)
    thumbs.append((end, None))
    paths.append(contact_sheet(plan, thumbs, folder / f"{name}_contact.png", renderer.fonts))
    return paths


def contact_sheet(plan: Plan, thumbs, path: Path, fonts: Fonts) -> Path:
    cols = 3
    tw, th = 600, int(600 * FRAME_H / FRAME_W)
    cap = 46
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 10, rows * (th + cap) + (rows + 1) * 10 + 50), (244, 245, 247))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), f"{plan.run.title}  ({plan.run.path.name})", font=fonts.title, fill=(20, 24, 30))
    for k, (img, step) in enumerate(thumbs):
        x = 10 + (k % cols) * (tw + 10)
        y = 60 + (k // cols) * (th + cap + 10)
        sheet.paste(img.resize((tw, th), Image.LANCZOS), (x, y))
        text = f"Command {step.cmd + 1}: {step.text}" if step else "Run complete"
        for i, line in enumerate(_wrap(draw, text, fonts.body, tw - 8)[:2]):
            draw.text((x + 4, y + th + 4 + i * 19), line, font=fonts.body, fill=(30, 34, 40))
    sheet.save(path)
    return path


# ---------------------------------------------------------------- main


def write_trace(plan: Plan, hits: list[Hit], liquid: dict, path: Path, extra: dict) -> None:
    run = plan.run
    hit_by_cmd = {h.cmd: h for h in hits}
    commands = []
    for step in plan.steps:
        cmd = run.commands[step.cmd]
        entry = {
            "index": step.cmd + 1,
            "commandType": step.kind,
            "caption": step.text,
            "video_s": [round(step.t0, 3), round(step.t1, 3)],
        }
        hit = hit_by_cmd.get(step.cmd)
        if hit:
            entry.update(
                tool=hit.tool,
                json_position_mm=hit.json_mm,
                definition_position_mm=hit.definition_mm,
                mujoco_position_mm=hit.sim_mm,
                error_mm=hit.error_mm,
                nozzles=hit.wells,
            )
        params = cmd["params"]
        if "volume" in params:
            entry["volume_uL"] = params["volume"]
        commands.append(entry)
    payload = {
        "protocol": str(run.path),
        "title": run.title,
        "labware": [
            {"key": lw.key, "name": lw.name, "loadName": lw.load_name, "slot": lw.slot, "on": run.where_text(lw.parent), "moved_by_gripper": lw.id in run.moved}
            for lw in run.labware.values()
        ],
        "modules": [{"key": m.key, "model": m.model, "slot": m.slot, "name": m.label} for m in run.modules.values()],
        "pipettes": [{"name": p.name, "mount": p.mount, "tool": p.tool, "tipLength_mm": p.tip.reach_mm if p.tip else None} for p in run.pipettes.values()],
        "trash": [b.name for b in run.trash.values()],
        **extra,
        "warnings": plan.warnings,
        "final_liquid": liquid,
        "commands": commands,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def view(plan: Plan, scene: Scene) -> None:
    import mujoco.viewer

    with mujoco.viewer.launch_passive(scene.model, scene.data) as viewer:
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
        viewer.cam.fixedcamid = _id(scene.model, mujoco.mjtObj.mjOBJ_CAMERA, "deck")
        started = time.monotonic()
        while viewer.is_running():
            t = (time.monotonic() - started) % (plan.duration + 1.0)
            scene.at(min(t, plan.duration))
            viewer.sync()
            time.sleep(0.016)


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate a Flex protocol from its opentrons analysis")
    parser.add_argument("protocol", type=Path, help="protocol .py (analyzed first) or .analysis.json")
    parser.add_argument("--view", action="store_true", help="open the MuJoCo window instead of rendering")
    parser.add_argument("--stills", action="store_true", help="also write the still PNGs and the contact sheet (off by default)")
    parser.add_argument("--video", action="store_true", help="also write an MP4 (slow; off by default)")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--frame", type=float, action="append", help="render only the frame at this time (s); repeatable")
    parser.add_argument("--from", dest="start", type=float, metavar="SECONDS", help="video clip start on the protocol timeline (requires --video)")
    parser.add_argument("--to", dest="end", type=float, metavar="SECONDS", help="video clip end on the protocol timeline (requires --video)")
    args = parser.parse_args()

    ranged = args.start is not None or args.end is not None
    if ranged:
        if args.frame:
            parser.error("--from/--to cannot be combined with --frame")
        if args.view:
            parser.error("--from/--to cannot be combined with --view")
        if not args.video:
            parser.error("--from/--to require --video")
    if args.video and args.fps <= 0:
        parser.error("--fps must be greater than zero")

    source = args.protocol.resolve()
    analysis = analyze(source) if source.suffix == ".py" else source
    name = analysis.name.replace(".analysis.json", "").replace(".json", "")
    deck = load_deck()
    try:
        run = load_analysis(analysis, deck)
        plan = make_plan(run)
    except ProtocolError as exc:
        raise SystemExit(f"cannot animate {analysis.name}: {exc}")
    t0 = 0.0 if args.start is None else args.start
    t1 = plan.duration if args.end is None else args.end
    if ranged:
        if not (math.isfinite(t0) and math.isfinite(t1)):
            parser.error("--from/--to must be finite seconds")
        if t0 < 0 or t1 < 0:
            parser.error("--from/--to must be nonnegative seconds")
        if not t0 < t1:
            parser.error("--from must be less than --to")
        if t1 > plan.duration:
            parser.error(f"--to must not exceed the protocol duration ({plan.duration:g} s)")
    folder = OUT_ROOT / name
    xml = write_model(deck, scene_spec(plan), folder)
    model = load_model(xml)
    data = mujoco.MjData(model)
    scene = Scene(plan, model, data)

    kinds: dict[str, int] = {}
    for cmd in run.commands:
        kinds[cmd["commandType"]] = kinds.get(cmd["commandType"], 0) + 1
    print(f"Protocol: {run.title} ({analysis.name}), {len(run.commands)} commands: " + ", ".join(f"{k}×{v}" for k, v in kinds.items()))
    for lw in run.labware.values():
        print(f"  {lw.slot}: {lw.name} [{lw.load_name}]" + ("  (gripper moves it)" if lw.id in run.moved else ""))
    for pip in run.pipettes.values():
        print(f"  {pip.mount} mount: {pip.name}, tipLength {pip.tip.reach_mm if pip.tip else '-'} mm")

    hits, worst_json, worst_sim = check_targets(plan, scene)
    print(f"Geometry: PASS ({len(hits)} positional commands; JSON vs labware definition worst {worst_json:.3f} mm)")
    print(f"Targets: PASS (MuJoCo tip end vs JSON position worst {worst_sim:.3f} mm; every nozzle over its well, tip ends inside the wells)")
    clearance, tightest, samples = check_clearance(plan, scene)
    print(f"Clearance: PASS ({samples} samples; tightest enclosure gap {clearance * 1000:.1f} mm at {tightest})" if samples else "Clearance: NOT APPLICABLE (no gantry or labware movement)")
    liquid = check_liquid(plan)
    print("Liquid: PASS (no negative volumes)")
    for lw_name, wells in liquid.items():
        summary = ", ".join(f"{w} {v['uL']:g}" for w, v in list(wells.items())[:12])
        print(f"  {lw_name}: {summary}{' …' if len(wells) > 12 else ''} uL")
    for warning in plan.warnings:
        print(f"  warning: {warning}")
    print(f"Duration: {plan.duration:.1f} s")

    if args.view:
        if sys.platform == "darwin" and not os.environ.get("MJPYTHON_BIN"):
            raise SystemExit("On macOS, open the window with: mjpython -m sim.play_protocol <protocol> --view")
        view(plan, scene)
        return

    # Rendering is opt-in: without --frame/--stills/--video nothing is drawn, so a
    # plain run cannot leave PNG or MP4 files behind. The MuJoCo renderers are only
    # built when something actually needs them.
    renderer = None
    if args.frame or args.stills or args.video:
        renderer = Renderer(plan, scene)

    if args.frame:
        for t in args.frame:
            path = folder / f"{name}_t{t:06.2f}.png"
            renderer.frame(t, smooth_focus=False).save(path)
            print(f"Frame: {path}")
        return

    if args.stills:
        stills = render_stills(plan, renderer, folder, name)
        for path in stills:
            print(f"Still: {path}")
    else:
        print("Stills: skipped (pass --stills to also write PNGs)")

    extra = {
        "checks": {
            "json_vs_definition_worst_mm": round(worst_json, 4),
            "mujoco_vs_json_worst_mm": round(worst_sim, 4),
            "clearance_samples": samples,
            "tightest_enclosure_gap_mm": round(clearance * 1000, 2),
        },
        "duration_s": round(plan.duration, 2),
    }
    if args.video:
        video = folder / (f"{name}_clip_{t0:06.2f}-{t1:06.2f}.mp4" if ranged else f"{name}.mp4")
        started = time.monotonic()
        frames = render_video(plan, renderer, video, args.fps, t0 if ranged else None, t1 if ranged else None)
        print(f"Video: {video} ({frames} frames, {time.monotonic() - started:.0f} s to render)")
        extra["video"] = video.name
        extra["video_range"] = {"from_s": t0, "to_s": t1, "fps": args.fps, "frames": frames}
    trace = folder / f"{name}_trace.json"
    write_trace(plan, hits, liquid, trace, extra)
    print(f"Trace: {trace}")


if __name__ == "__main__":
    main()

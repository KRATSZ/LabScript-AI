"""Animate an OT-2 protocol in MuJoCo from its ``opentrons analyze`` JSON.

    PYTHONPATH=. /usr/bin/python3 -m sim.play_ot2_protocol protocols/ot2_probe.py
    PYTHONPATH=. /usr/bin/python3 -m sim.play_ot2_protocol protocols/ot2_probe.analysis.json
    PYTHONPATH=. ~/Library/Python/3.9/bin/mjpython -m sim.play_ot2_protocol <protocol> --view

A ``.py`` is analyzed first with the official ``opentrons analyze --check``
CLI. Use Opentrons 8.x for OT-2; ``OPENTRONS_PYTHON`` can select its interpreter.

Checks, all against the analysis JSON, before anything is rendered:

* targets: at each positional command the MuJoCo critical point sits on
  ``result.position`` and every nozzle is over the well it should be in;
* clearance: along the whole path nothing that moves runs into labware, the
  trash or the enclosure;
* liquid: volumes never go negative and the final deck is reported.

Outputs go to ``exports/mujoco/protocols/<name>/``: ``ot2.xml``, an MP4, key
stills, a contact sheet and ``<name>_trace.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

from sim.flex_protocol import ProtocolError, step_at
from sim.ot2_protocol import (
    RETURN_TIP_SCALE,
    State,
    sample as sample_plan,
    NOZZLE_ROWS,
    TRASH_FALL_M,
    Plan,
    ProtocolRun,
    load_analysis,
    plan as make_plan,
    scene_spec,
)
from sim.flex_scene import MM
from sim.ot2_scene import EXPORT, ROOT, conical_plate, load_deck, thermocycler_lid_poses, well_liquid_geometry, write_spec_model
from sim.ot2_shell import FIXED_GUIDE_Z0, PIPETTE_TOP
from sim.ot2_thermocycler import thermocycler_v1_dynamic_names, thermocycler_v1_lid_pose
from sim.play_protocol import (
    CLOSE_DEFAULT_ORBIT,
    CLOSE_WEB_H,
    CLOSE_WEB_W,
    Fonts,
    FRAME_H,
    MAIN_W,
    PANEL_W,
    Scene as FlexScene,
    _bounds as _coarse_bounds,
    _id,
    _subtree,
    caption,
    contact_sheet,
    draw_deck_map,
    draw_text_panel,
    orbit_pose,
    render_video,
    pick_stills,
    still_time,
)

OUT_ROOT = EXPORT / "protocols"
LIQUID_ALPHA = 0.93
TIP_WALL_MM = 0.35


def _slerp(a, b, f: float) -> np.ndarray:
    """Quaternion slerp; falls back to nlerp for near-parallel ends."""

    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if float(a @ b) < 0:
        b = -b
    dot = float(np.clip(a @ b, -1.0, 1.0))
    if dot > 0.9995:
        out = a + f * (b - a)
        return out / np.linalg.norm(out)
    angle = math.acos(dot)
    return (math.sin((1 - f) * angle) * a + math.sin(f * angle) * b) / math.sin(angle)


def _bounds(model, data, ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """World AABBs, projecting actual mesh vertices for OT-2 mesh geoms.

    MuJoCo may choose a rotated principal frame for a square rounded housing.
    Rotating that frame's box again inflates a 34 mm housing to about 62 mm,
    producing false overlaps beside plates or an upright lid. The vertex
    projection still encloses every mesh surface; it is not a mesh-intersection
    test or a claim of physical/continuous clearance. Primitive bounds retain
    the existing conservative implementation. Flex's checker is untouched.
    """
    lo, hi = _coarse_bounds(model, data, ids)
    mask = model.geom_type[ids] == mujoco.mjtGeom.mjGEOM_MESH
    for mesh in np.unique(model.geom_dataid[ids[mask]]):
        rows = np.flatnonzero(mask & (model.geom_dataid[ids] == mesh))
        geoms = ids[rows]
        rotations, groups = np.unique(data.geom_xmat[geoms], axis=0, return_inverse=True)
        start, count = int(model.mesh_vertadr[mesh]), int(model.mesh_vertnum[mesh])
        vertices = model.mesh_vert[start:start + count]
        for group, rot in enumerate(rotations):
            selected = rows[groups == group]
            projected = vertices @ rot.reshape(3, 3).T
            lo[selected] = data.geom_xpos[ids[selected]] + projected.min(axis=0)
            hi[selected] = data.geom_xpos[ids[selected]] + projected.max(axis=0)
    return lo, hi


# ---------------------------------------------------------------- analyze


def analyze(protocol: Path) -> Path:
    """Analyze through the public CLI; never accept stale or errored output."""
    protocol = protocol.expanduser().resolve(strict=True)
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()[:16]
    cache = OUT_ROOT / "analyses"
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / f"{protocol.stem}-{digest}.analysis.json"
    python = os.environ.get("OPENTRONS_PYTHON", sys.executable)
    with tempfile.TemporaryDirectory(prefix="analyze-", dir=cache) as temporary:
        pending = Path(temporary) / "analysis.json"
        done = subprocess.run(
            [str(python), "-m", "opentrons.cli", "analyze", "--check", "--json-output", str(pending), str(protocol)],
            capture_output=True,
            text=True,
        )
        if done.returncode != 0 or not pending.is_file():
            raise ProtocolError(f"OT-2 analysis failed (use Opentrons 8.x) for {protocol.name}:\n{done.stdout}\n{done.stderr}")
        try:
            result = json.loads(pending.read_text())
        except (ValueError, OSError) as error:
            raise ProtocolError(f"Invalid analysis output for {protocol.name}: {error}") from error
        if result.get("errors"):
            raise ProtocolError(f"OT-2 analysis contains errors: {result['errors']}")
        pending.replace(out)
    return out


# ---------------------------------------------------------------- scene state


class Scene:
    """Applies a ``(q, State)`` pair to the OT-2 model: joints, tips, liquid columns."""

    def __init__(self, plan: Plan, model, data) -> None:
        self.plan, self.model, self.data = plan, model, data
        run = plan.run
        G = mujoco.mjtObj.mjOBJ_GEOM
        self.qadr = {name: model.jnt_qposadr[_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)] for name in plan.joints}
        self.colors = {lid: np.array(liq.rgb) for lid, liq in run.liquids.items()}
        self.liquid = {}
        for key, well in plan.liquid_wells:
            lw = run.by_key(key).labware
            self.liquid[(key, well)] = (_id(model, G, f"{key}_liquid_{well}"), lw.wells[well], conical_plate(lw))
        self.rack = {}
        for lw in run.labware.values():
            if lw.labware.is_tiprack:
                self.rack[lw.key] = {w: _id(model, G, f"{lw.key}_{w}") for w in lw.labware.wells}
        self.mount_of = {pip.tool: pip.mount for pip in run.pipettes.values()}
        self.channels = {pip.tool: (8 if "multi" in pip.name else 1) for pip in run.pipettes.values()}
        self.tips: dict[str, list[tuple[int, int, np.ndarray]]] = {}
        self.tip_table: dict[str, tuple[np.ndarray, np.ndarray, float]] = {}
        self.tip_reach: dict[str, float] = {}
        for tool, mount in self.mount_of.items():
            n = self.channels[tool]
            pip = next(p for p in run.pipettes.values() if p.tool == tool)
            if pip.tip is None:
                self.tips[tool] = []
                self.tip_reach[tool] = 0.0
                continue
            names = [f"{tool}_tip"] if n == 1 else [f"{tool}_tip_{row}" for row in NOZZLE_ROWS]
            self.tips[tool] = [
                (_id(model, G, name), _id(model, G, f"{name}_liquid"), model.geom_pos[_id(model, G, name)].copy())
                for name in names
            ]
            self.tip_reach[tool] = pip.tip.reach_mm * 0.001 if pip.tip else 0.0
            self.tip_table[tool] = FlexScene._tip_volume_table(pip.tip)
        self.base_rgba = model.geom_rgba.copy()
        # The rear slide shoe is a visual-only box authored in each head body.
        # Keep its stable local frame and resize/recenter only its Z span as
        # the mounted pipette moves; empty mounts have no follower geom.
        self.mount_followers: dict[str, tuple[int, np.ndarray, np.ndarray]] = {}
        for tool, mount in self.mount_of.items():
            gid = mujoco.mj_name2id(model, G, f"{tool}_mount_follower")
            if gid >= 0:
                self.mount_followers[tool] = (gid, model.geom_pos[gid].copy(), model.geom_size[gid].copy())
        # Module animation: magnet pins rise and the thermocycler lid swings,
        # driven by the engage/disengage and openLid/closeLid steps. Each
        # event ramps from the previous value across the step's own window.
        self.module_anim: dict[str, dict] = {}
        for mod in run.modules.values():
            prefix = f"mod_{mod.slot}_{mod.model}"
            entry: dict = {"events": [], "pins": None, "lid": None}
            if mod.model.startswith("magnetic"):
                length = mod.definition["config"]["maxEngageHeight"] + 10.0
                platform = mod.definition["labwareOffset"]["z"]
                pins = []
                for k in range(len(mod.pins)):
                    gid = mujoco.mj_name2id(model, G, f"{prefix}_pin{k}")
                    if gid < 0:
                        break
                    pins.append(gid)
                entry["pins"] = (pins, length, platform)
            if mod.model.startswith("thermocycler"):
                gid = mujoco.mj_name2id(model, G, f"{prefix}_lid")
                if gid >= 0:
                    # The compiler may fold an initially identity rotation
                    # into the body frame. Runtime lid quaternions must not
                    # keep using that static same-frame shortcut.
                    model.geom_sameframe[gid] = 0
                    closed, open_ = thermocycler_lid_poses(mod.definition, mod.child)
                    # Definitions/pose helpers use mm; MuJoCo geom positions
                    # use metres. Mesh compilation also recentres/rotates its
                    # vertices: retain that reference transform when animating
                    # the source lid frame, just as for the initial XML pose.
                    mesh = int(model.geom_dataid[gid]) if model.geom_type[gid] == mujoco.mjtGeom.mjGEOM_MESH else -1
                    ref_p = model.mesh_pos[mesh].copy() if mesh >= 0 else np.zeros(3)
                    ref_q = model.mesh_quat[mesh].copy() if mesh >= 0 else np.array([1.0, 0.0, 0.0, 0.0])
                    closed_m = np.array(closed[0]) * MM
                    skins = [(gid, np.zeros(3), ref_p, ref_q)]
                    for name in thermocycler_v1_dynamic_names(prefix)[1:]:
                        skin = mujoco.mj_name2id(model, G, name)
                        if skin >= 0:
                            model.geom_sameframe[skin] = 0
                            mesh = int(model.geom_dataid[skin])
                            hp, hq = model.mesh_pos[mesh].copy(), model.mesh_quat[mesh].copy()
                            skins.append((skin, model.geom_pos[skin].copy() - hp - closed_m, hp, hq))
                    entry["lid"] = (skins, closed_m, np.array(open_[0]) * MM, closed[1], open_[1])
                    entry["lid_pose"] = (mod.definition, mod.child)
            self.module_anim[mod.id] = entry
        for step in plan.steps:
            if step.kind not in ("magneticModule/engage", "magneticModule/disengage", "thermocycler/openLid", "thermocycler/closeLid"):
                continue
            p = run.commands[step.cmd]["params"]
            if p.get("moduleId") not in self.module_anim:
                continue
            if step.kind == "magneticModule/engage":
                value = float(p.get("height") or 0.0)
            else:
                value = 1.0 if step.kind == "thermocycler/openLid" else 0.0
            # A command's displayed step can include the preceding tool
            # retraction. Animate only its module-action key interval, so the
            # lid does not start closing while the pipette is still rising.
            action_window = next(
                ((a.t, b.t) for a, b in zip(plan.keys, plan.keys[1:]) if b.cmd == step.cmd and b.phase == step.kind),
                None,
            )
            if action_window is None:
                raise RuntimeError(f"missing module action phase {step.kind} for command {step.cmd + 1}")
            self.module_anim[p["moduleId"]]["events"].append((*action_window, value))

    @staticmethod
    def _event_value(events: list, t: float) -> float:
        value = prev = 0.0
        for t0, t1, target in events:
            if t < t0:
                break
            if t >= t1:
                prev = value = target
            else:
                return prev + (target - prev) * (t - t0) / max(t1 - t0, 1e-9)
        return value

    def _rgb(self, mix: dict[str, float]) -> np.ndarray:
        total = sum(mix.values())
        if total <= 1e-9:
            return np.array([0.5, 0.5, 0.5])
        return sum(v * self.colors.get(k, np.array([0.3, 0.5, 0.9])) for k, v in mix.items()) / total

    def apply(self, q: dict[str, float], state: State, t: float | None = None) -> None:
        m = self.model
        for name, value in q.items():
            self.data.qpos[self.qadr[name]] = value
        m.geom_rgba[:] = self.base_rgba
        for tool, (gid, base_pos, base_size) in self.mount_followers.items():
            mount = self.mount_of[tool]
            z_value = float(self.data.qpos[self.qadr[f"z_{mount}"]])
            bottom = z_value + PIPETTE_TOP
            top = max(z_value + PIPETTE_TOP + 0.008, FIXED_GUIDE_Z0)
            m.geom_pos[gid] = base_pos
            m.geom_pos[gid, 2] = (bottom + top) / 2 - z_value
            m.geom_size[gid] = base_size
            m.geom_size[gid, 2] = max((top - bottom) / 2, 0.002)
            # ``play_protocol._bounds`` uses MuJoCo's compiled primitive AABB,
            # not geom_size. Keep that conservative box in step with the
            # follower so the moving clearance sweep sees the actual short or
            # long shoe at low/park/high Z.
            m.geom_aabb[gid, :3] = 0.0
            m.geom_aabb[gid, 3:] = m.geom_size[gid]
            m.geom_rbound[gid] = float(np.linalg.norm(m.geom_size[gid]))
        if t is not None:
            self._apply_modules(t)
        for (key, well), (gid, info, conical) in self.liquid.items():
            mix = state.wells.get((key, well), {})
            volume = sum(mix.values())
            if volume <= 0.05:
                m.geom_rgba[gid, 3] = 0.0
                continue
            pos, size = well_liquid_geometry(info, volume, conical=conical)
            m.geom_pos[gid] = pos
            m.geom_size[gid] = size
            m.geom_rgba[gid, :3] = self._rgb(mix)
            m.geom_rgba[gid, 3] = LIQUID_ALPHA
        for key, wells in self.rack.items():
            present = state.rack.get(key, set())
            for well, gid in wells.items():
                if well not in present:
                    m.geom_rgba[gid, 3] = 0.0
        for tool, geoms in self.tips.items():
            if not geoms:
                continue
            heights, table, reach = self.tip_table[tool]
            fall = state.falling.get(tool, 0.0)
            for k, (tip_id, liquid_id, base) in enumerate(geoms):
                mounted = state.mounted[tool][k]
                release = state.release_mm.get(tool, TRASH_FALL_M * 1000) * MM
                m.geom_pos[tip_id] = base - np.array([0.0, 0.0, fall * release])
                m.geom_rgba[tip_id, 3] = self.base_rgba[tip_id, 3] * (1.0 - fall) if mounted else 0.0
                mix = state.tip_liquid[tool][k]
                volume = sum(mix.values())
                if not mounted or volume <= 0.05 or fall > 0:
                    m.geom_rgba[liquid_id, 3] = 0.0
                    continue
                # An air gap at the outlet displaces liquid upward instead of
                # being rendered as extra liquid at the point of the tip.
                air = state.tip_front_air.get(tool, [0.] * len(geoms))[k]
                low = float(np.interp(air, table, heights))
                high = float(np.interp(air + volume, table, heights))
                h = high - low
                r = float(np.interp((low + high) / 2, heights, np.sqrt(np.maximum(np.gradient(table, heights), 1e-6) / np.pi)))
                m.geom_size[liquid_id, 0] = max(r * 0.92, 0.25) * MM
                m.geom_size[liquid_id, 1] = h / 2 * MM
                m.geom_pos[liquid_id, 2] = (-reach + low + h / 2 + 0.3) * MM
                m.geom_rgba[liquid_id, :3] = self._rgb(mix)
                m.geom_rgba[liquid_id, 3] = LIQUID_ALPHA
        mujoco.mj_forward(m, self.data)

    def _apply_modules(self, t: float) -> None:
        """Pin tops at platform + height (retracted tops hide in the body) and
        the lid lerped/slerped between its closed and open poses. Module-local
        poses are converted from module-local mm into MuJoCo metres."""

        m = self.model
        for entry in self.module_anim.values():
            if not entry["events"]:
                continue
            value = self._event_value(entry["events"], t)
            if entry["pins"] is not None:
                pins, length, platform = entry["pins"]
                top = platform + value - (0.6 if value <= 1e-9 else 0.0)
                for gid in pins:
                    m.geom_pos[gid, 2] = (top - length / 2) * MM
            if entry["lid"] is not None:
                skins = entry["lid"][0]
                center_mm, quat = thermocycler_v1_lid_pose(*entry["lid_pose"], -value * math.pi / 2)
                q = np.asarray(quat)
                rot = np.empty(9)
                mujoco.mju_quat2Mat(rot, q)
                # Include the lid's thickness in its hinge offset. The former
                # thin-panel radius formula moved a thick outer lid off-pivot.
                center = np.array(center_mm) * MM
                for gid, offset, ref_p, ref_q in skins:
                    m.geom_pos[gid, :3] = center + rot.reshape(3, 3) @ (offset + ref_p)
                    mujoco.mju_mulQuat(m.geom_quat[gid], q, ref_q)

    def at(self, t: float) -> tuple[dict, State]:
        q, state, _ = sample_plan(self.plan, t)
        self.apply(q, state, t)
        return q, state


# ---------------------------------------------------------------- checks


def tool_points(scene: Scene, tool: str, with_tip: bool) -> np.ndarray:
    """World positions of each nozzle's lowest point (tip end if mounted), meters."""

    mount = scene.mount_of[tool]
    reach = scene.tip_reach[tool] if with_tip else 0.0
    points = []
    for k in range(scene.channels[tool]):
        site = _id(scene.model, mujoco.mjtObj.mjOBJ_SITE, f"noz_{mount}_{k}")
        pos = scene.data.site_xpos[site].copy()
        pos[2] -= reach
        points.append(pos)
    return np.array(points)


def expected_position(plan: Plan, arrival, state: State) -> tuple[float, float, float]:
    """The critical point rebuilt from the labware definition and ``wellLocation``.

    The fixed trash is skipped: the engine rotates ``alternateDropLocation``
    through the bin, so the JSON position is the truth there.
    """

    run = plan.run
    cmd = run.commands[arrival.cmd]
    params = cmd["params"]
    if cmd["commandType"] == "moveToCoordinates":
        return tuple(float(params["coordinates"][axis]) for axis in "xyz")
    if arrival.target is None:
        p = (cmd.get("result") or {})["position"]
        return (float(p["x"]), float(p["y"]), float(p["z"]))
    key, name = arrival.target
    lw = run.by_key(key).labware
    well = lw.wells[name]
    o = state.origin[key]
    loc = params.get("wellLocation") or {"origin": "top", "offset": {"x": 0, "y": 0, "z": 0}}
    off = loc.get("offset") or {"x": 0, "y": 0, "z": 0}
    base = {"top": well.z + well.depth, "bottom": well.z, "center": well.z + well.depth / 2}.get(loc.get("origin", "top"), well.z + well.depth)
    if cmd["commandType"] == "dropTip" and loc.get("origin") == "default" and lw.is_tiprack:
        # The engine uses a model-specific fraction of the full tip length.
        # The release animation seats it the remaining way.
        pip = run.pipettes[params["pipetteId"]]
        base -= lw.tip_length * RETURN_TIP_SCALE[pip.name]
    return (o[0] + well.x + off["x"], o[1] + well.y + off["y"], o[2] + base + off["z"])


def check_targets(plan: Plan, scene: Scene) -> tuple[list, float, float]:
    """Critical points on ``result.position``, nozzles over the right wells."""

    model, data, run = scene.model, scene.data, plan.run
    corner = np.array(run.deck.corner)
    hits = []
    worst_json = worst_sim = 0.0
    for arrival in plan.arrivals:
        key = plan.keys[arrival.key]
        scene.apply(key.q, key.state, key.t)
        kind = run.commands[arrival.cmd]["commandType"]
        with_tip = any(key.state.mounted[arrival.tool])
        points = tool_points(scene, arrival.tool, with_tip)
        mounted = np.array(key.state.mounted[arrival.tool]) if with_tip else np.ones(len(points), bool)
        critical = points.mean(axis=0) if arrival.centered else points[0]
        sim_mm = critical / 1e-3 - corner
        json_mm = np.array(arrival.position_mm)
        definition = np.array(expected_position(plan, arrival, key.state))
        d_json = float(np.abs(definition - json_mm).max())
        if d_json > 0.1:
            raise RuntimeError(f"command {arrival.cmd + 1} {kind}: JSON position {json_mm} vs definition {definition}")
        error = float(np.linalg.norm(sim_mm - json_mm))
        if error > 0.5:
            raise RuntimeError(f"command {arrival.cmd + 1} {kind}: MuJoCo critical point at {sim_mm.round(2)}, JSON {json_mm}")
        worst_json, worst_sim = max(worst_json, d_json), max(worst_sim, error)

        under = []
        if arrival.target is not None:
            lw_key, name = arrival.target
            lw = run.by_key(lw_key).labware
            for k, point in enumerate(points):
                if not mounted[k] and kind != "pickUpTip":
                    continue
                channels = scene.channels[arrival.tool]
                if channels > 1 and not arrival.centered:
                    # Nozzle A sits on the addressed well; the rest span toward
                    # row H. Past H there is no well — the nozzle hangs off the
                    # labware, which is where the engine puts it too.
                    row = chr(ord(name[0]) + k)
                    want = f"{row}{name[1:]}" if row in NOZZLE_ROWS and lw.wells.get(f"{row}{name[1:]}") else None
                else:
                    want = name
                if want is None:
                    continue
                gid = _id(model, mujoco.mjtObj.mjOBJ_GEOM, f"{lw_key}_{want}")
                center = data.geom_xpos[gid]
                well = lw.wells[want]
                d = (point[:2] - center[:2]) / 1e-3
                if arrival.centered:
                    inside = abs(d[0]) <= well.size_x / 2 - 1.0 and abs(d[1]) <= well.size_y / 2 - 1.0
                    offset = float(np.hypot(*d))
                else:
                    offset = float(np.hypot(*d))
                    inside = offset <= 0.5
                if not inside:
                    raise RuntimeError(f"command {arrival.cmd + 1} {kind}: nozzle {k + 1} is {offset:.2f} mm off {lw_key} {want}")
                under.append({"nozzle": NOZZLE_ROWS[k], "well": f"{run.by_key(lw_key).name} {want}", "xy_offset_mm": round(offset, 3)})
        hits.append(
            {
                "cmd": arrival.cmd,
                "kind": kind,
                "tool": arrival.tool,
                "json_mm": tuple(round(v, 3) for v in json_mm),
                "definition_mm": tuple(round(v, 3) for v in definition),
                "sim_mm": tuple(round(float(v), 3) for v in sim_mm),
                "error_mm": round(error, 4),
                "wells": under,
                "t": round(key.t, 3),
            }
        )
    return hits, worst_json, worst_sim


def check_clearance(plan: Plan, scene: Scene) -> tuple[float, str, int]:
    """Sweep the path: the gantry and its tips against labware, trash and shell.

    The front face of the enclosure is open (the door panel is cut away), so
    only the sides, back and top of the shell are enforced.
    """

    scene.at(0.0)
    model, data, run = scene.model, scene.data, plan.run
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or "" for g in range(model.ngeom)]
    # Liquid columns are resized at apply time, which the compile-time bounding
    # radius used here cannot see; the tip capsule around them is checked instead.
    gantry = np.array([g for g, n in enumerate(names) if g in set(_subtree(model, "bridge")) and "_liquid" not in n and model.geom_group[g] != 4])
    tip_like = np.array([n.startswith(tuple(f"{t}_tip" for t in scene.tips)) or n.endswith("_needle") or "_needle_" in n for n in names])

    shell_id = _id(model, mujoco.mjtObj.mjOBJ_GEOM, "shell")
    shell_lo, shell_hi = _bounds(model, data, np.array([shell_id]))
    inner_lo = np.array([float(shell_lo[0, 0]) + 0.004, -np.inf, 0.0])
    inner_hi = np.array([float(shell_hi[0, 0]) - 0.004, float(shell_hi[0, 1]) - 0.004, float(shell_hi[0, 2]) - 0.004])

    lw_keys = {lw.key: lw for lw in run.labware.values()}
    obstacle, obstacle_key, well_of, rack_body = [], [], {}, {}
    for g, n in enumerate(names):
        key = n.split("_", 1)[0]
        if n.startswith("body_"):
            key = n[5:]
        if key in lw_keys and "_liquid_" not in n and not n.startswith(("beam", "carriage", "pipette_", "trash")):
            obstacle.append(g)
            obstacle_key.append(key)
            rest = n.split("_", 1)[1] if not n.startswith("body_") else ""
            lw = lw_keys[key].labware
            if rest in lw.wells:
                well_of[g] = (key, lw.wells[rest], lw.is_tiprack)
            if n.startswith("body_"):
                rack_body[g] = key
        elif n.startswith("trash_"):
            obstacle.append(g)
            obstacle_key.append("trash")
        elif n.startswith(("mod_", "viz_mod_")):
            # Include both original module proxies and added visible skins:
            # body, rim, pins, lid/heater, supports and chassis walls.
            # The pins ride between well rows, so a tip aimed at a well never
            # shares their footprint and no aimed-well exemption is needed.
            obstacle.append(g)
            obstacle_key.append("mod")
    obstacle = np.array(obstacle)
    obstacle_key = np.array(obstacle_key)
    is_well = np.array([g in well_of or g in rack_body for g in obstacle])
    # A tapered disposable tip's full-width socket is far above a plate rim.
    # A single AABB falsely reports that wide socket against adjacent wells
    # during native touch-tip motion. Clip its actual mesh to the obstacle's
    # vertical slab before testing those broad-phase candidates.
    tip_mesh_edges = {}
    for g in gantry[tip_like[gantry]]:
        if model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mesh = int(model.geom_dataid[g])
        if mesh not in tip_mesh_edges:
            start, count = int(model.mesh_faceadr[mesh]), int(model.mesh_facenum[mesh])
            faces = model.mesh_face[start:start + count]
            edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
            tip_mesh_edges[mesh] = np.unique(np.sort(edges, axis=1), axis=0)

    def tip_slab_bounds(g, z0, z1, vertices):
        mesh = int(model.geom_dataid[g])
        if mesh not in tip_mesh_edges:
            return None
        if g not in vertices:
            start, count = int(model.mesh_vertadr[mesh]), int(model.mesh_vertnum[mesh])
            vertices[g] = model.mesh_vert[start:start + count] @ data.geom_xmat[g].reshape(3, 3).T + data.geom_xpos[g]
        points = vertices[g]
        pieces = [points[(points[:, 2] >= z0) & (points[:, 2] <= z1)]]
        edges = tip_mesh_edges[mesh]
        a, b = points[edges[:, 0]], points[edges[:, 1]]
        for z in (z0, z1):
            cross = (np.minimum(a[:, 2], b[:, 2]) < z) & (np.maximum(a[:, 2], b[:, 2]) > z)
            aa, bb = a[cross], b[cross]
            pieces.append(aa + ((z - aa[:, 2]) / (bb[:, 2] - aa[:, 2]))[:, None] * (bb - aa))
        clipped = np.concatenate(pieces)
        return (clipped.min(axis=0), clipped.max(axis=0)) if len(clipped) else None

    times = sorted(set(np.round(np.arange(0.0, plan.duration, 0.08), 4)) | {round(k.t, 4) for k in plan.keys})
    worst, worst_geom, samples, slack = np.inf, "", 0, 5e-4
    for t in times:
        q, state = scene.at(float(t))
        samples += 1
        limits = model.jnt_range
        limited = model.jnt_limited.astype(bool)
        positions = data.qpos[model.jnt_qposadr]
        outside = limited & ((positions < limits[:, 0] - 1e-7) | (positions > limits[:, 1] + 1e-7))
        if outside.any():
            joint = int(np.flatnonzero(outside)[0])
            raise RuntimeError(f"{model.joint(joint).name} exceeds the model joint travel at t={t:.2f} s")
        visible = model.geom_rgba[:, 3] > 0
        moving = gantry[visible[gantry]]
        m_lo, m_hi = _bounds(model, data, moving)
        margin = np.minimum((m_lo - inner_lo).min(1), (inner_hi - m_hi).min(1))
        margin = np.where(np.isfinite(margin), margin, np.inf)
        if margin.min() < -1e-4:
            g = moving[int(np.argmin(margin))]
            raise RuntimeError(f"{names[g]} leaves the enclosure by {-margin.min() * 1000:.1f} mm at t={t:.2f} s")
        if margin.min() < worst:
            worst, worst_geom = float(margin.min()), names[moving[int(np.argmin(margin))]]

        obs_mask = visible[obstacle]
        obs = obstacle[obs_mask]
        o_lo, o_hi = _bounds(model, data, obs)
        o_xy = (o_lo + o_hi)[:, :2] / 2
        o_well = is_well[obs_mask]
        depth = np.min(np.minimum(m_hi[:, None], o_hi[None]) - np.maximum(m_lo[:, None], o_lo[None]), axis=2)
        hit = depth > slack
        if hit.any():
            vertices = {}
            for i in np.where(tip_like[moving])[0]:
                xy = data.geom_xpos[moving[i], :2]
                for j in np.where(hit[i] & o_well)[0]:
                    if obs[j] in rack_body:
                        key = rack_body[obs[j]]
                        o = state.origin[key]
                        local = xy / 1e-3 - np.array(run.deck.corner[:2]) - np.array(o[:2])
                        hole = any(np.hypot(local[0] - w.x, local[1] - w.y) < 1.0 for w in lw_keys[key].labware.wells.values())
                        if hole:
                            hit[i, j] = False
                        continue
                    key, well, rack = well_of[obs[j]]
                    d = (xy - o_xy[j]) / 1e-3
                    if rack:
                        aimed = np.hypot(*d) < 1.0
                    elif well.shape == "rectangular":
                        aimed = abs(d[0]) <= well.size_x / 2 and abs(d[1]) <= well.size_y / 2
                    else:
                        aimed = np.hypot(*d) <= well.radius + 1e-6
                    if aimed:
                        hit[i, j] = False
                for j in np.where(hit[i])[0]:
                    clipped = tip_slab_bounds(int(moving[i]), o_lo[j, 2], o_hi[j, 2], vertices)
                    if clipped is not None:
                        lo, hi = clipped
                        overlap = np.minimum(hi, o_hi[j]) - np.maximum(lo, o_lo[j])
                        if overlap.min() <= slack:
                            hit[i, j] = False
        if hit.any():
            i, j = np.argwhere(hit)[0]
            raise RuntimeError(f"{names[moving[i]]} runs into {names[obs[j]]} at t={t:.2f} s ({depth[i, j] * 1000:.1f} mm)")
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
    for (key, well), mix in sorted(final.wells.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        total = sum(mix.values())
        if total < 0.05:
            continue
        report.setdefault(run.by_key(key).name, {})[well] = {
            "uL": round(total, 2),
            "composition": {names.get(k, k): round(v / total, 4) for k, v in mix.items()},
        }
    return report


# ---------------------------------------------------------------- render


class Renderer:
    """The four-panel video frame and the web views, on the OT-2 scene."""

    def __init__(self, plan: Plan, scene: Scene) -> None:
        self.plan, self.scene = plan, scene
        self.close_default_orbit = (*CLOSE_DEFAULT_ORBIT[:2], .45) if any(m.model.startswith("thermocycler") for m in plan.run.modules.values()) else CLOSE_DEFAULT_ORBIT
        self.fonts = Fonts.load()
        self.main = mujoco.Renderer(scene.model, height=9 * 90, width=MAIN_W)
        self.close = mujoco.Renderer(scene.model, height=270, width=PANEL_W)
        # Sites are analytical anchors for target checks.  MuJoCo's default
        # renderer draws them as debug spheres, which makes a nozzle look as
        # if it ends in a floating bead.  Keep every site and coordinate in
        # the model; hide only this debug display group in beauty views.
        self.normal = mujoco.MjvOption()
        self.normal.sitegroup[:] = 0
        self.xray = mujoco.MjvOption()
        self.xray.sitegroup[:] = 0
        # Groups 2 (shell, beam, carriage) and 3 (collision boxes) go away so
        # the close camera sees the head and the deck; the pipette itself is
        # group 0 and stays.
        for group in (1, 2, 3):
            self.xray.geomgroup[group] = 0
        self.cam = mujoco.MjvCamera()
        self.cam.azimuth, self.cam.elevation, self.cam.distance = self.close_default_orbit
        self.focus: np.ndarray | None = None
        self.deck_cam = _id(scene.model, mujoco.mjtObj.mjOBJ_CAMERA, "deck")
        from sim.ot2_scene import deck_camera_pose

        _, look_at = deck_camera_pose(plan.run.deck)
        self.deck_look_at = np.array(look_at, dtype=float)
        self._deck_pos0 = scene.model.cam_pos[self.deck_cam].copy()
        self._deck_quat0 = scene.model.cam_quat[self.deck_cam].copy()
        self.track: np.ndarray | None = None
        self.track_fps = 30
        self.close_web = mujoco.Renderer(scene.model, height=CLOSE_WEB_H, width=CLOSE_WEB_W)
        self.web_cam = mujoco.MjvCamera()
        self.web_cam.azimuth, self.web_cam.elevation, self.web_cam.distance = self.close_default_orbit
        tools = [p.tool for p in plan.run.pipettes.values()]
        self.idle_tip = f"tip_{tools[0].split('_')[1]}" if tools else None

    def close_point(self, step, state: State) -> np.ndarray:
        if step and 0 <= step.cmd < len(self.plan.run.commands):
            command = self.plan.run.commands[step.cmd]
            module_id = command.get("params", {}).get("moduleId") or command.get("result", {}).get("moduleId")
            mod = self.plan.run.modules.get(module_id)
            if mod:
                body = self.scene.model.body(f"mod_{mod.slot}_{mod.model}").id
                dims = mod.definition['dimensions']
                height = 156. if mod.model.startswith("thermocycler") else dims['bareOverallHeight'] / 2
                return self.scene.data.xpos[body] + np.array([dims['xDimension']/2, dims['yDimension']/2, height]) * MM
        tool = step.tool if step and step.tool else None
        if tool is None:
            return self.focus if self.focus is not None else _site(self.scene, self.idle_tip) if self.idle_tip else self.deck_look_at.copy()
        points = tool_points(self.scene, tool, any(state.mounted[tool]))
        return points.mean(axis=0) + np.array([0.0, 0.0, 0.035])

    def _advance(self, t: float, smooth_focus: bool = True) -> tuple:
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
        frame = Image.new("RGB", (MAIN_W + PANEL_W, self.main.height), (250, 251, 252))
        frame.paste(main, (0, 0))
        caption(frame, self.plan, t, self.fonts)
        frame.paste(close, (MAIN_W, 0))
        from PIL import ImageDraw

        label = ImageDraw.Draw(frame, "RGBA")
        label.rounded_rectangle((MAIN_W + 8, 8, MAIN_W + 92, 30), 6, fill=(16, 18, 22, 190))
        label.text((MAIN_W + 16, 10), "跟随特写", font=self.fonts.small, fill=(255, 255, 255))
        frame.paste(draw_deck_map(self.plan, state, step, self.fonts), (MAIN_W, 270))
        frame.paste(draw_text_panel(self.plan, step, t, self.fonts, (PANEL_W, frame.height - 270 - 300)), (MAIN_W, 270 + 300))
        return frame

    def frame(self, t: float, smooth_focus: bool = True) -> Image.Image:
        self._set_main_pose(None)
        state, step = self._advance(t, smooth_focus)
        self.main.update_scene(self.scene.data, camera="deck", scene_option=self.normal)
        return self._compose(t, state, step, Image.fromarray(self.main.render()))

    def build_track(self, fps: int = 30) -> None:
        frames = int(math.ceil(self.plan.duration * fps)) + 1
        self.focus = None
        track = np.zeros((frames, 3))
        for i in range(frames):
            self._advance(min(i / fps, self.plan.duration))
            track[i] = self.focus
        self.track, self.track_fps = track, fps
        self.focus = None

    def web_main(self, t: float, orbit: tuple | None = None) -> Image.Image:
        self._set_main_pose(orbit)
        self.scene.at(t)
        self.main.update_scene(self.scene.data, camera="deck", scene_option=self.normal)
        return Image.fromarray(self.main.render())

    def web_close(self, t: float, orbit: tuple = CLOSE_DEFAULT_ORBIT) -> Image.Image:
        self.scene.at(t)
        self.web_cam.lookat[:] = self.track[self._track_index(t)]
        self.web_cam.azimuth, self.web_cam.elevation, self.web_cam.distance = orbit
        self.close_web.update_scene(self.scene.data, camera=self.web_cam, scene_option=self.xray)
        return Image.fromarray(self.close_web.render())

    def _track_index(self, t: float) -> int:
        index = int(round(t * self.track_fps))
        return min(max(index, 0), len(self.track) - 1)

    def _set_main_pose(self, orbit) -> None:
        model = self.scene.model
        if orbit is None:
            model.cam_pos[self.deck_cam] = self._deck_pos0
            model.cam_quat[self.deck_cam] = self._deck_quat0
            return
        pos, quat = orbit_pose(self.deck_look_at, *orbit)
        model.cam_pos[self.deck_cam] = pos
        model.cam_quat[self.deck_cam] = quat

    def default_orbit(self) -> dict:
        offset = self.deck_look_at - self._deck_pos0
        dist = float(np.linalg.norm(offset))
        fwd = offset / dist
        return {
            "azimuth": math.degrees(math.atan2(fwd[1], fwd[0])),
            "elevation": math.degrees(math.asin(fwd[2])),
            "distance": dist,
            "lookat": [float(v) for v in self.deck_look_at],
        }


def _site(scene: Scene, name: str) -> np.ndarray:
    return scene.data.site_xpos[_id(scene.model, mujoco.mjtObj.mjOBJ_SITE, name)].copy()


# ---------------------------------------------------------------- main


def write_trace(plan: Plan, hits: list, liquid: dict, path: Path, extra: dict) -> None:
    run = plan.run
    hit_by_cmd = {h["cmd"]: h for h in hits}
    commands = []
    for step in plan.steps:
        entry = {
            "index": step.cmd + 1,
            "commandType": step.kind,
            "caption": step.text,
            "video_s": [round(step.t0, 3), round(step.t1, 3)],
        }
        hit = hit_by_cmd.get(step.cmd)
        if hit:
            entry.update(
                tool=hit["tool"],
                json_position_mm=hit["json_mm"],
                definition_position_mm=hit["definition_mm"],
                mujoco_position_mm=hit["sim_mm"],
                error_mm=hit["error_mm"],
                nozzles=hit["wells"],
            )
        cmd = run.commands[step.cmd]
        if "volume" in cmd["params"]:
            entry["volume_uL"] = cmd["params"]["volume"]
        commands.append(entry)
    payload = {
        "protocol": str(run.path),
        "title": run.title,
        "robot": "OT-2",
        "labware": [
            {"key": lw.key, "name": lw.name, "loadName": lw.load_name, "slot": lw.slot}
            for lw in run.labware.values()
        ],
        "modules": [
            {"slot": mod.slot, "model": mod.model, "loadName": mod.model}
            for mod in sorted(run.modules.values(), key=lambda m: m.slot)
        ],
        "pipettes": [{"name": p.name, "mount": p.mount, "tool": p.tool, "tipLength_mm": p.tip.reach_mm if p.tip else None} for p in run.pipettes.values()],
        **extra,
        "warnings": plan.warnings,
        "final_liquid": liquid,
        "commands": commands,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate an OT-2 protocol from its opentrons analysis")
    parser.add_argument("protocol", type=Path, help="protocol .py (analyzed first) or .analysis.json")
    parser.add_argument("--view", action="store_true", help="open the MuJoCo window instead of rendering")
    parser.add_argument("--no-video", action="store_true", help="checks and stills only")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--frame", type=float, action="append", help="render only the frame at this time (s); repeatable")
    args = parser.parse_args()

    source = args.protocol.resolve()
    analysis = analyze(source) if source.suffix == ".py" else source
    name = analysis.name.replace(".analysis.json", "").replace(".json", "")
    deck = load_deck()
    try:
        run = load_analysis(analysis, deck)
        plan = make_plan(run)
    except ProtocolError as exc:
        raise SystemExit(f"cannot animate {analysis.name}: {exc}")
    folder = OUT_ROOT / name
    xml = write_spec_model(deck, scene_spec(plan), folder)
    model = mujoco.MjModel.from_xml_path(str(xml))
    data = mujoco.MjData(model)
    scene = Scene(plan, model, data)

    kinds: dict[str, int] = {}
    for cmd in run.commands:
        kinds[cmd["commandType"]] = kinds.get(cmd["commandType"], 0) + 1
    print(f"Protocol: {run.title} ({analysis.name}), {len(run.commands)} commands: " + ", ".join(f"{k}×{v}" for k, v in kinds.items()))
    for lw in run.labware.values():
        print(f"  {lw.slot}: {lw.name} [{lw.load_name}]")
    for mod in sorted(run.modules.values(), key=lambda m: m.slot):
        print(f"  {mod.slot}: {mod.model}")
    for pip in run.pipettes.values():
        print(f"  {pip.mount} mount: {pip.name}, tipLength {pip.tip.reach_mm if pip.tip else '-'} mm")

    hits, worst_json, worst_sim = check_targets(plan, scene)
    print(f"Targets: PASS ({len(hits)} positional commands; JSON vs labware definition worst {worst_json:.3f} mm)")
    print(f"Targets: PASS (MuJoCo critical point vs JSON position worst {worst_sim:.3f} mm; every nozzle over its well)")
    clearance, tightest, samples = check_clearance(plan, scene)
    print(f"Clearance: PASS ({samples} samples; no labware, trash or shell collisions; tightest enclosure gap {clearance * 1000:.1f} mm at {tightest})")
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
            raise SystemExit("On macOS, open the window with: mjpython -m sim.play_ot2_protocol <protocol> --view")
        view(plan, scene)
        return

    renderer = Renderer(plan, scene)
    if args.frame:
        for t in args.frame:
            path = folder / f"{name}_t{t:06.2f}.png"
            renderer.frame(t, smooth_focus=False).save(path)
            print(f"Frame: {path}")
        return
    stills = render_stills(plan, renderer, folder, name)
    for path in stills:
        print(f"Still: {path}")
    extra = {
        "checks": {
            "json_vs_definition_worst_mm": round(worst_json, 4),
            "mujoco_vs_json_worst_mm": round(worst_sim, 4),
            "clearance_samples": samples,
            "tightest_enclosure_gap_mm": round(clearance * 1000, 2),
        },
        "duration_s": round(plan.duration, 2),
    }
    if not args.no_video:
        video = folder / f"{name}.mp4"
        started = time.monotonic()
        frames = render_video(plan, renderer, video, args.fps)
        print(f"Video: {video} ({frames} frames, {time.monotonic() - started:.0f} s to render)")
        extra["video"] = video.name
    trace = folder / f"{name}_trace.json"
    write_trace(plan, hits, liquid, trace, extra)
    print(f"Trace: {trace}")


if __name__ == "__main__":
    main()

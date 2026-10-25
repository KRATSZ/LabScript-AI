"""Reference-based OT-2 Thermocycler GEN1 lid geometry.

This module is intentionally independent from :mod:`sim.ot2_scene`.  It gives
the scene/player a small, explicit hook for the physical GEN1 lid without
changing the authoritative labware origin, module body origin, or site
coordinates.  The source of the external envelope is the 2019 Opentrons
Thermocycler Module white paper (the local copy is
``exports/mujoco/ot2-photo-refine-20261025/references/thermocycler-2019.pdf``):

* closed envelope: 316 L x 172 W x 154 H mm;
* open envelope: 316 L x 172 W x 312 H mm.

The white paper does not provide a CAD mesh, hinge datum, heater dimensions, or
the exact cross-section of the GEN1 lid.  Those values are therefore marked as
estimates below.  This file must not be read as OEM CAD or a hardware
collision-certified model.  In particular, the 244.95 x 172 x 170.25 / 310.1
GEN2 dimensions must not be substituted for the GEN1 values here.

The main lid is a *hollow rounded frame* extruded through the documented
closed-height envelope.  It is deliberately not a filled 316 mm box: the rear
extension is represented by two narrow visual spine rails and the actual lid
panel ends at the estimated hinge.  A thin black outer skin covers only the
heater region on the outside of the frame, so the heater cannot show through
the lid when closed while the lower/opening side remains hollow.  Narrow white
side skins follow the photograph's outer edges.  The moving part keeps the
existing names
``<prefix>_lid``, ``viz_<prefix>_lid_heater`` and
``viz_<prefix>_lid_arm_{l,r}`` so an existing Scene hook can bind them without
changing protocol semantics.

All public dimensions and poses use the module-local millimetre frame used by
``ot2_scene``.  Geometry XML returned by :func:`thermocycler_v1_geoms` uses
metres, as required by the existing ``AssetBook`` helpers.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from sim.flex_shell import (
    MM,
    AssetBook,
    _f,
    _v,
    materials_xml,
    mesh_geom,
    rbox,
    rrect,
)


# ---------------------------------------------------------------------------
# Evidence and estimates


# These are documented in the local manufacturer white paper, p. 6 (the page
# headed "Specifications").  L is the long front-to-back axis in this
# module-local frame; W is the x axis.
V1_DOC_CLOSED_MM = (316.0, 172.0, 154.0)
V1_DOC_OPEN_MM = (316.0, 172.0, 312.0)
V1_TOTAL_LENGTH_MM = V1_DOC_CLOSED_MM[0]
V1_WIDTH_MM = V1_DOC_CLOSED_MM[1]
V1_CLOSED_HEIGHT_MM = V1_DOC_CLOSED_MM[2]
V1_OPEN_HEIGHT_MM = V1_DOC_OPEN_MM[2]

# The vendored OT-2 V1 definition is authoritative for the body frame.  The
# current scene's body proxy is 98 mm high; this is not the white-paper lid
# height and must not be replaced by the GEN2 dimensions.
V1_BODY_TOP_DEFAULT_MM = 98.0

# The following are engineering estimates derived from the body proxy and the
# product photograph (white paper p. 5).  The 2019 table publishes an external
# 316 mm length, while the vendored OT-2 V1 body proxy is 259.7 mm long.  We
# interpret the remaining ~56.3 mm as a rear exhaust/service/duct region.  It
# must not be silently turned into extra lid travel: the hinge is estimated
# inside the body, with a 20 mm rear margin.  A future measured hinge datum can
# replace these values without touching protocol coordinates.
V1_BODY_LENGTH_DEFAULT_MM = 259.7
V1_REAR_DUCT_LENGTH_EST_MM = V1_TOTAL_LENGTH_MM - V1_BODY_LENGTH_DEFAULT_MM
V1_HINGE_REAR_CLEARANCE_EST_MM = 20.0
# Pose-fit estimates for the current V1 body proxy.  They are selected so the
# rendered envelope agrees with the documented open/closed heights, but are not
# measured lid CAD and must be revisited against a full-scene/photo check.
V1_LID_LENGTH_EST_MM = 214.0
V1_LID_PACK_HEIGHT_EST_MM = 56.0
# The black lid frame is inset from the documented 172 mm outer width by the
# two narrow white side cheeks visible in the product photograph.
V1_WHITE_SIDE_CHEEK_MM = 8.0
V1_PANEL_SIDE_WALL_MM = 14.0
V1_PANEL_FRONT_RAIL_MM = 24.0
V1_PANEL_REAR_RAIL_MM = 40.0
V1_HEATER_RAISE_EST_MM = 8.0
V1_HEATER_WIDTH_EST_MM = 126.0
V1_HEATER_LENGTH_EST_MM = 86.0
V1_GASKET_OUTER_WIDTH_EST_MM = 140.0
V1_GASKET_OUTER_LENGTH_EST_MM = 104.0
# The external black back skin spans the frame cavity so the lower heater does
# not peek through an oblique closed view.  It is an upper/outer plate only;
# it does not replace the inner heater or fill the lid's bottom opening.
V1_OUTER_SKIN_WIDTH_EST_MM = V1_WIDTH_MM - 2.0 * V1_WHITE_SIDE_CHEEK_MM
V1_OUTER_SKIN_LENGTH_EST_MM = V1_LID_LENGTH_EST_MM - V1_PANEL_FRONT_RAIL_MM - V1_PANEL_REAR_RAIL_MM
V1_INNER_LINER_DEPTH_EST_MM = 32.0
V1_INNER_LINER_HEIGHT_EST_MM = 4.0

# The image/PDF gives no exact CAD cross-sections.  This short note is included
# in reports so estimates cannot accidentally be presented as measured facts.
EVIDENCE_NOTE = (
    "316x172x154 closed and 316x172x312 open are documented in the 2019 "
    "white paper; hinge, frame, heater, gasket, latch, outer skin, white side "
    "cheeks and spine dimensions "
    "are photo-based/derived estimates, not OEM CAD. The 259.7 mm body plus "
    "a narrow ~56.3 mm rear service/duct interpretation is not a measured V1 "
    "hinge datum."
)


@dataclass(frozen=True)
class V1LidLayout:
    """The module-local frame needed by the lid hook.

    ``body_top_mm`` comes from the module definition (normally 98.0 mm).  The
    rest of the moving-envelope values are estimates constrained by the two
    documented external dimensions.
    """

    body_x0_mm: float
    body_x1_mm: float
    body_top_mm: float
    plate_x0_mm: float
    plate_y0_mm: float
    plate_x1_mm: float
    plate_y1_mm: float
    plate_top_mm: float | None
    panel_center_x_mm: float
    hinge_y_mm: float
    panel_front_y_mm: float
    panel_rear_y_mm: float
    panel_length_mm: float
    pack_height_mm: float
    width_mm: float
    body_length_mm: float
    rear_duct_length_mm: float
    hinge_rear_clearance_mm: float
    total_length_mm: float
    closed_height_mm: float
    open_height_mm: float
    panel_front_to_plate_front_mm: float
    panel_front_body_margin_mm: float

    @property
    def closed_center_z_mm(self) -> float:
        return self.body_top_mm + self.pack_height_mm / 2.0

    @property
    def hinge_pivot(self) -> tuple[float, float, float]:
        """The estimated lower rear hinge datum in module-local mm."""

        return (self.panel_center_x_mm, self.hinge_y_mm, self.body_top_mm)


def _definition_of(definition_or_module: Mapping[str, Any] | Any | None) -> Mapping[str, Any]:
    """Accept a raw module definition or the existing ``ModuleRun`` object."""

    if definition_or_module is None:
        return {
            "model": "thermocyclerModuleV1",
            "labwareOffset": {"x": 0.0, "y": 82.56, "z": 97.8},
            "dimensions": {
                "bareOverallHeight": V1_BODY_TOP_DEFAULT_MM,
                "xDimension": V1_WIDTH_MM,
                "yDimension": V1_BODY_LENGTH_DEFAULT_MM,
                "labwareInterfaceXDimension": 128.0,
                "labwareInterfaceYDimension": 86.0,
                "lidHeight": 37.7,
            },
        }
    if isinstance(definition_or_module, Mapping):
        return definition_or_module
    definition = getattr(definition_or_module, "definition", None)
    if not isinstance(definition, Mapping):
        raise TypeError("expected a module definition dict or ModuleRun-like object")
    return definition


def _child_of(definition_or_module: Any, child: tuple | None) -> tuple | None:
    if child is not None:
        return tuple(child)
    candidate = getattr(definition_or_module, "child", None)
    return tuple(candidate) if candidate is not None else None


def _check_v1_definition(definition: Mapping[str, Any]) -> None:
    """Reject an accidental GEN2 call while allowing lightweight test dicts."""

    model = str(definition.get("model", ""))
    if model and model != "thermocyclerModuleV1":
        raise ValueError(
            f"thermocycler_v1 geometry requires thermocyclerModuleV1, got {model!r}; "
            "do not mix the GEN2 envelope into this hook"
        )


def _module_bounds(definition: Mapping[str, Any], child: tuple | None) -> tuple[float, float, float, float, float | None]:
    dims = definition.get("dimensions", {})
    off = definition.get("labwareOffset", {})
    if child is not None and len(child) >= 4:
        x0, y0, x1, y1 = (float(v) for v in child[:4])
        top = float(child[4]) if len(child) >= 5 and child[4] is not None else None
        return x0, y0, x1, y1, top
    x0 = float(off.get("x", 0.0))
    y0 = float(off.get("y", 82.56))
    x1 = x0 + float(dims.get("labwareInterfaceXDimension", 128.0))
    y1 = y0 + float(dims.get("labwareInterfaceYDimension", 86.0))
    return x0, y0, x1, y1, None


def thermocycler_v1_layout(
    definition_or_module: Mapping[str, Any] | Any | None = None,
    child: tuple | None = None,
) -> V1LidLayout:
    """Return the V1 frame/hinge layout without mutating module semantics.

    ``child`` is the existing ``(x0, y0, x1, y1, top_z)`` module-local tuple.
    The lid is centred on the documented 172 mm module body, not on the 128 mm
    plate opening; this is important because the plate is inset in the real
    thermocycler.  The plate is therefore expected to sit inside the lid
    window, not determine the lid's front edge.
    """

    d = _definition_of(definition_or_module)
    _check_v1_definition(d)
    dims = d.get("dimensions", {})
    x0, y0, x1, y1, top = _module_bounds(d, _child_of(definition_or_module, child))
    body_x0 = 0.0
    body_x1 = float(dims.get("xDimension", V1_WIDTH_MM))
    if body_x1 <= 0:
        body_x1 = V1_WIDTH_MM
    body_top = float(dims.get("bareOverallHeight", V1_BODY_TOP_DEFAULT_MM))

    body_length = float(dims.get("yDimension", V1_BODY_LENGTH_DEFAULT_MM))
    if body_length <= 0:
        body_length = V1_BODY_LENGTH_DEFAULT_MM
    # The lid hinge sits within the fixed housing.  The 316-259.7 difference
    # is reserved for the narrow rear service/duct spine, not for hinge travel.
    hinge_y = max(0.0, min(body_length, body_length - V1_HINGE_REAR_CLEARANCE_EST_MM))
    panel_length = V1_LID_LENGTH_EST_MM
    pack_height = V1_LID_PACK_HEIGHT_EST_MM
    panel_front = hinge_y - panel_length
    panel_rear = hinge_y
    cx = (body_x0 + body_x1) / 2.0
    return V1LidLayout(
        body_x0_mm=body_x0,
        body_x1_mm=body_x1,
        body_top_mm=body_top,
        plate_x0_mm=x0,
        plate_y0_mm=y0,
        plate_x1_mm=x1,
        plate_y1_mm=y1,
        plate_top_mm=top,
        panel_center_x_mm=cx,
        hinge_y_mm=hinge_y,
        panel_front_y_mm=panel_front,
        panel_rear_y_mm=panel_rear,
        panel_length_mm=panel_length,
        pack_height_mm=pack_height,
        width_mm=V1_WIDTH_MM,
        body_length_mm=body_length,
        rear_duct_length_mm=max(V1_TOTAL_LENGTH_MM - body_length, 0.0),
        hinge_rear_clearance_mm=body_length - hinge_y,
        total_length_mm=V1_TOTAL_LENGTH_MM,
        closed_height_mm=V1_CLOSED_HEIGHT_MM,
        open_height_mm=V1_OPEN_HEIGHT_MM,
        panel_front_to_plate_front_mm=panel_front - y0,
        panel_front_body_margin_mm=panel_front,
    )


def _quat_x(angle: float) -> tuple[float, float, float, float]:
    return (math.cos(angle / 2.0), math.sin(angle / 2.0), 0.0, 0.0)


def _rotate_x(vector: tuple[float, float, float], angle: float) -> tuple[float, float, float]:
    x, y, z = vector
    c, s = math.cos(angle), math.sin(angle)
    return (x, c * y - s * z, s * y + c * z)


def thermocycler_v1_lid_pose(
    definition_or_module: Mapping[str, Any] | Any | None,
    child: tuple | None,
    angle_rad: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float, float]]:
    """Return one moving-lid pose at ``angle_rad`` about the estimated hinge.

    The panel's lower/rear corner is the pivot.  At ``-pi/2`` the panel's
    front edge reaches z=312 mm, matching the documented open envelope.  The
    quaternion order is MuJoCo's ``w x y z``.
    """

    layout = thermocycler_v1_layout(definition_or_module, child)
    # Vector from panel centre to the lower/rear pivot at the closed pose.
    pivot_from_center = (0.0, layout.panel_length_mm / 2.0, -layout.pack_height_mm / 2.0)
    rotated = _rotate_x(pivot_from_center, angle_rad)
    px, py, pz = layout.hinge_pivot
    center = (px - rotated[0], py - rotated[1], pz - rotated[2])
    return center, _quat_x(angle_rad)


def thermocycler_v1_lid_poses(
    definition_or_module: Mapping[str, Any] | Any | None,
    child: tuple | None = None,
) -> tuple[tuple[tuple[float, float, float], tuple[float, float, float, float]], ...]:
    """Return ``(closed, open)`` poses for the existing Scene hook."""

    return (
        thermocycler_v1_lid_pose(definition_or_module, child, 0.0),
        thermocycler_v1_lid_pose(definition_or_module, child, -math.pi / 2.0),
    )


# Compatibility alias for a hook that wants the improved function but should
# not import the scene's old simplified implementation by accident.
thermocycler_lid_poses = thermocycler_v1_lid_poses


def thermocycler_v1_dynamic_names(prefix: str) -> tuple[str, ...]:
    """Names that should receive the same pose as ``<prefix>_lid``."""

    return (
        f"{prefix}_lid",
        f"viz_{prefix}_lid_outer_skin",
        f"viz_{prefix}_lid_heater",
        f"viz_{prefix}_lid_inner_liner",
        f"viz_{prefix}_lid_gasket",
        f"viz_{prefix}_lid_latch",
        f"viz_{prefix}_lid_latch_bar_l",
        f"viz_{prefix}_lid_latch_bar_r",
        f"viz_{prefix}_lid_side_l",
        f"viz_{prefix}_lid_side_r",
        f"viz_{prefix}_lid_arm_l",
        f"viz_{prefix}_lid_arm_r",
    )


def thermocycler_v1_part_offsets(
    definition_or_module: Mapping[str, Any] | Any | None,
    child: tuple | None,
    prefix: str,
) -> dict[str, tuple[float, float, float]]:
    """Return closed-pose local offsets for player-side pose propagation.

    The existing player can use this map to rotate heater/gasket/latch/arm
    skins around the same source frame instead of moving only the outer lid.
    Values are millimetres relative to the primary lid centre.
    """

    layout = thermocycler_v1_layout(definition_or_module, child)
    half_l = layout.panel_length_mm / 2.0
    half_p = layout.pack_height_mm / 2.0
    panel_center_y = layout.hinge_y_mm - layout.panel_length_mm / 2.0
    # Keep the inner heater/gasket centred on the loaded plate rather than on
    # the much longer lid cavity.  With the bundled V1 plate this is about
    # -7.14 mm from the lid centre.
    heater_y = (layout.plate_y0_mm + layout.plate_y1_mm) / 2.0 - panel_center_y
    heater_z = -half_p + V1_HEATER_RAISE_EST_MM
    # The outside skin is on the opposite face from the white heater.  It is
    # intentionally only the heater-sized rectangle, leaving the lower lid
    # opening/gasket a real opening instead of filling the whole panel.
    outer_skin_z = half_p - 1.5
    liner_y = heater_y - V1_HEATER_LENGTH_EST_MM / 2.0 - V1_INNER_LINER_DEPTH_EST_MM / 2.0
    latch_y = -half_l + 30.0
    latch_z = -half_p + 3.0
    hinge_y = half_l - 6.0
    arm_z = -half_p + 10.0
    x_arm = layout.width_mm / 2.0 - 13.0
    return {
        f"{prefix}_lid": (0.0, 0.0, 0.0),
        f"viz_{prefix}_lid_outer_skin": (0.0, heater_y, outer_skin_z),
        f"viz_{prefix}_lid_heater": (0.0, heater_y, heater_z),
        f"viz_{prefix}_lid_inner_liner": (0.0, liner_y, heater_z),
        f"viz_{prefix}_lid_gasket": (0.0, heater_y, -half_p + 2.0),
        f"viz_{prefix}_lid_latch": (0.0, latch_y, latch_z),
        f"viz_{prefix}_lid_latch_bar_l": (-30.0, latch_y + 2.0, latch_z + 2.5),
        f"viz_{prefix}_lid_latch_bar_r": (30.0, latch_y + 2.0, latch_z + 2.5),
        f"viz_{prefix}_lid_side_l": (-(layout.width_mm / 2.0 - 4.0), 0.0, 0.0),
        f"viz_{prefix}_lid_side_r": (layout.width_mm / 2.0 - 4.0, 0.0, 0.0),
        f"viz_{prefix}_lid_arm_l": (-x_arm, hinge_y, arm_z),
        f"viz_{prefix}_lid_arm_r": (x_arm, hinge_y, arm_z),
    }


def _closed_point(layout: V1LidLayout, offset: tuple[float, float, float]) -> tuple[float, float, float]:
    center = (layout.panel_center_x_mm, layout.hinge_y_mm - layout.panel_length_mm / 2.0, layout.closed_center_z_mm)
    return tuple(center[i] + offset[i] for i in range(3))


def _box_from_center(center_mm: tuple[float, float, float], size_mm: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    half = tuple(v / 2.0 for v in size_mm)
    return tuple(center_mm[i] - half[i] for i in range(3)), tuple(center_mm[i] + half[i] for i in range(3))


def thermocycler_v1_geoms(
    definition_or_module: Mapping[str, Any] | Any | None,
    book: AssetBook,
    prefix: str | None = None,
    child: tuple | None = None,
    *,
    include_static: bool = True,
) -> list[str]:
    """Create XML geoms for the V1 lid and its evidence-marked details.

    The returned strings are module-local geoms, matching the existing
    ``_module_spec_geoms`` convention.  ``include_static=False`` is useful
    when the caller already draws hinge blocks/rear supports.  In either mode,
    the authoritative body, labware, site and child block are untouched.
    """

    d = _definition_of(definition_or_module)
    actual_child = _child_of(definition_or_module, child)
    layout = thermocycler_v1_layout(d, actual_child)
    if prefix is None:
        prefix = str(getattr(definition_or_module, "prefix", "mod_tc_v1"))
    offsets = thermocycler_v1_part_offsets(d, actual_child, prefix)
    closed, _ = thermocycler_v1_lid_poses(d, actual_child)

    geoms: list[str] = []
    # Profiles are in the panel's local x/y plane and are swept through the
    # estimated closed pack height.  Same point counts let AssetBook stitch the
    # outer/inner loop into a real opening rather than a filled slab.
    frame_half_width_mm = layout.width_mm / 2.0 - V1_WHITE_SIDE_CHEEK_MM
    panel_outer = rrect(
        -frame_half_width_mm * MM,
        frame_half_width_mm * MM,
        -layout.panel_length_mm * MM / 2.0,
        layout.panel_length_mm * MM / 2.0,
        12.0 * MM,
        12.0 * MM,
        10,
    )
    panel_hole = rrect(
        -(frame_half_width_mm - V1_PANEL_SIDE_WALL_MM) * MM,
        (frame_half_width_mm - V1_PANEL_SIDE_WALL_MM) * MM,
        (-layout.panel_length_mm / 2.0 + V1_PANEL_FRONT_RAIL_MM) * MM,
        (layout.panel_length_mm / 2.0 - V1_PANEL_REAR_RAIL_MM) * MM,
        8.0 * MM,
        8.0 * MM,
        10,
    )
    lid_mesh = book.extrusion(
        f"{prefix}_v1_lid_frame",
        panel_outer,
        panel_hole,
        axis=2,
        lo=-layout.pack_height_mm * MM / 2.0,
        hi=layout.pack_height_mm * MM / 2.0,
    )
    geoms.append(mesh_geom(f"{prefix}_lid", lid_mesh, "matte_black", 0, tuple(v * MM for v in closed[0])))

    # Black outside skin: only the heater-sized region is covered.  Keeping this
    # as a separate dynamic part hides the white heater from a closed/top view
    # without turning the lower lid opening into a solid slab.
    skin_mesh = book.rbox_mesh((V1_OUTER_SKIN_WIDTH_EST_MM * MM, V1_OUTER_SKIN_LENGTH_EST_MM * MM, 3.0 * MM), 2.0 * MM)
    skin_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_outer_skin"])
    geoms.append(mesh_geom(f"viz_{prefix}_lid_outer_skin", skin_mesh, "matte_black", 0, tuple(v * MM for v in skin_pos_mm)))

    # Light heater face recessed above the lower frame edge.  The white paper
    # shows a light inner face but gives no heater plate dimensions; 126 x 86
    # x 3 mm is a plate-proportioned estimate, not an instrument specification.
    heater_mesh = book.rbox_mesh((V1_HEATER_WIDTH_EST_MM * MM, V1_HEATER_LENGTH_EST_MM * MM, 3.0 * MM), 2.0 * MM)
    heater_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_heater"])
    geoms.append(mesh_geom(f"viz_{prefix}_lid_heater", heater_mesh, "gantry_white", 0, tuple(v * MM for v in heater_pos_mm)))

    heater_y = offsets[f"viz_{prefix}_lid_heater"][1]
    gasket_outer_half_y = V1_GASKET_OUTER_LENGTH_EST_MM / 2.0
    gasket_hole_half_y = V1_HEATER_LENGTH_EST_MM / 2.0
    gasket_outer = rrect(
        -V1_GASKET_OUTER_WIDTH_EST_MM / 2.0 * MM,
        V1_GASKET_OUTER_WIDTH_EST_MM / 2.0 * MM,
        -gasket_outer_half_y * MM,
        gasket_outer_half_y * MM,
        8.0 * MM,
        8.0 * MM,
        8,
    )
    gasket_hole = rrect(
        -V1_HEATER_WIDTH_EST_MM / 2.0 * MM,
        V1_HEATER_WIDTH_EST_MM / 2.0 * MM,
        -gasket_hole_half_y * MM,
        gasket_hole_half_y * MM,
        6.0 * MM,
        6.0 * MM,
        8,
    )
    gasket_mesh = book.extrusion(
        f"{prefix}_v1_gasket",
        gasket_outer,
        gasket_hole,
        axis=2,
        lo=-1.0 * MM,
        hi=1.0 * MM,
    )
    gasket_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_gasket"])
    geoms.append(mesh_geom(f"viz_{prefix}_lid_gasket", gasket_mesh, "graphite", 0, tuple(v * MM for v in gasket_pos_mm)))

    # The frame cavity extends about 32 mm farther forward than the plate-sized
    # heater.  Add a black inner liner only in that front band.  The rear band
    # near the hinge stays empty: when upright it reads as the horizontal
    # through-opening below the heater rather than another filled panel.
    liner_mesh = book.rbox_mesh(
        (V1_HEATER_WIDTH_EST_MM * MM, V1_INNER_LINER_DEPTH_EST_MM * MM, V1_INNER_LINER_HEIGHT_EST_MM * MM),
        1.5 * MM,
    )
    liner_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_inner_liner"])
    geoms.append(mesh_geom(f"viz_{prefix}_lid_inner_liner", liner_mesh, "matte_black", 0, tuple(v * MM for v in liner_pos_mm)))

    # Front/inner latch housing and two small black latch bars.  Their exact
    # mechanism is not documented; these shapes are deliberately separate so a
    # later measured reference can replace them without changing the frame.
    latch_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_latch"])
    latch_lo, latch_hi = _box_from_center(latch_pos_mm, (112.0, 18.0, 8.0))
    geoms.append(rbox(book, f"viz_{prefix}_lid_latch", tuple(v * MM for v in latch_lo), tuple(v * MM for v in latch_hi), "graphite", 2.0 * MM, 0))
    for side in ("l", "r"):
        bar_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_latch_bar_{side}"])
        bar_lo, bar_hi = _box_from_center(bar_pos_mm, (22.0, 8.0, 5.0))
        geoms.append(rbox(book, f"viz_{prefix}_lid_latch_bar_{side}", tuple(v * MM for v in bar_lo), tuple(v * MM for v in bar_hi), "matte_black", 1.0 * MM, 0))

    # The photograph shows narrow white outer side cheeks beside the dark
    # frame.  They are intentionally narrower than the frame and lower than
    # the full pack height so the black outside skin remains the closed-view
    # surface; both cheeks rotate with the lid.
    for side in ("l", "r"):
        side_pos_mm = _closed_point(layout, offsets[f"viz_{prefix}_lid_side_{side}"])
        side_lo, side_hi = _box_from_center(side_pos_mm, (V1_WHITE_SIDE_CHEEK_MM, layout.panel_length_mm - 24.0, layout.pack_height_mm - 8.0))
        geoms.append(rbox(book, f"viz_{prefix}_lid_side_{side}", tuple(v * MM for v in side_lo), tuple(v * MM for v in side_hi), "gantry_white", 1.5 * MM, 0))

    for side, x_sign in (("l", -1.0), ("r", 1.0)):
        name = f"viz_{prefix}_lid_arm_{side}"
        arm_pos_mm = _closed_point(layout, offsets[name])
        arm_lo, arm_hi = _box_from_center(arm_pos_mm, (8.0, 18.0, 20.0))
        geoms.append(rbox(book, name, tuple(v * MM for v in arm_lo), tuple(v * MM for v in arm_hi), "graphite", 1.5 * MM, 0))

    if include_static:
        # The documented 316 mm length includes a rear exhaust/service region
        # beyond the 259.7 mm schema body proxy.  Two narrow rails carry that
        # extension without making a solid 316 mm box that swallows the deck;
        # the lid hinge itself stays at ``layout.hinge_y_mm`` inside the body.
        y0 = float(d.get("dimensions", {}).get("yDimension", V1_BODY_LENGTH_DEFAULT_MM))
        for side, x0 in (("l", 0.0), ("r", layout.width_mm - 12.0)):
            geoms.append(
                rbox(
                    book,
                    f"viz_{prefix}_v1_rear_spine_{side}",
                    (x0 * MM, y0 * MM, (layout.body_top_mm - 7.0) * MM),
                    ((x0 + 12.0) * MM, V1_TOTAL_LENGTH_MM * MM, (layout.body_top_mm + 7.0) * MM),
                    "matte_black",
                    2.0 * MM,
                    0,
                )
            )
        for side, x0 in (("l", 8.0), ("r", layout.width_mm - 20.0)):
            geoms.append(
                rbox(
                    book,
                    f"viz_{prefix}_v1_hinge_tower_{side}",
                    (x0 * MM, (layout.hinge_y_mm - 8.0) * MM, layout.body_top_mm * MM),
                    ((x0 + 12.0) * MM, (layout.hinge_y_mm + 8.0) * MM, (layout.body_top_mm + 20.0) * MM),
                    "graphite",
                    2.0 * MM,
                    0,
                )
            )
    return geoms


def thermocycler_v1_envelope(
    definition_or_module: Mapping[str, Any] | Any | None = None,
    child: tuple | None = None,
) -> dict[str, Any]:
    """Return documented envelope plus estimates and an explicit evidence note."""

    layout = thermocycler_v1_layout(definition_or_module, child)
    closed, opened = thermocycler_v1_lid_poses(definition_or_module, child)
    return {
        "documented_closed_mm": list(V1_DOC_CLOSED_MM),
        "documented_open_mm": list(V1_DOC_OPEN_MM),
        "pose_closed_center_mm": list(closed[0]),
        "pose_open_center_mm": list(opened[0]),
        "pose_open_quat_wxyz": list(opened[1]),
        "body_origin_unchanged": True,
        "module_body_top_mm": layout.body_top_mm,
        "estimated_panel_length_mm": layout.panel_length_mm,
        "estimated_lid_pack_height_mm": layout.pack_height_mm,
        "estimated_hinge_y_mm": layout.hinge_y_mm,
        "estimated_panel_front_y_mm": layout.panel_front_y_mm,
        "estimated_panel_rear_y_mm": layout.panel_rear_y_mm,
        "estimated_body_length_mm": layout.body_length_mm,
        "estimated_rear_service_duct_length_mm": layout.rear_duct_length_mm,
        "estimated_hinge_rear_clearance_mm": layout.hinge_rear_clearance_mm,
        "panel_front_to_plate_front_delta_mm": layout.panel_front_to_plate_front_mm,
        "panel_front_body_margin_mm": layout.panel_front_body_margin_mm,
        "estimated_heater_mm": [V1_HEATER_WIDTH_EST_MM, V1_HEATER_LENGTH_EST_MM, 3.0],
        "estimated_gasket_outer_mm": [V1_GASKET_OUTER_WIDTH_EST_MM, V1_GASKET_OUTER_LENGTH_EST_MM],
        "estimated_gasket_inner_mm": [V1_HEATER_WIDTH_EST_MM, V1_HEATER_LENGTH_EST_MM],
        "estimated_front_inner_liner_mm": [V1_HEATER_WIDTH_EST_MM, V1_INNER_LINER_DEPTH_EST_MM, V1_INNER_LINER_HEIGHT_EST_MM],
        "rear_inner_through_opening_preserved": True,
        "evidence": EVIDENCE_NOTE,
    }


def thermocycler_v1_planner_clearance(
    definition_or_module: Mapping[str, Any] | Any | None = None,
    child: tuple | None = None,
    margin_mm: float = 10.0,
) -> dict[str, Any]:
    """Return a safe planner hint without changing the global Z range.

    The planner should retract the pipette to at least ``open_top + margin``
    before opening/closing the lid and wait for that action to finish.  This is
    a local strategy, not permission to raise the robot's global Z limit or to
    shrink the V1 lid for clearance.
    """

    margin = max(float(margin_mm), 0.0)
    layout = thermocycler_v1_layout(definition_or_module, child)
    return {
        "open_lid_top_mm": layout.open_height_mm,
        "closed_lid_top_mm": layout.closed_height_mm,
        "recommended_retract_z_mm": layout.open_height_mm + margin,
        "margin_mm": margin,
        "strategy": "retract tool before lid action; perform lid motion; then descend",
        "global_z_range_unchanged": True,
        "clearance_is_conservative_estimate": True,
    }


def thermocycler_v1_contact_report(
    definition_or_module: Mapping[str, Any] | Any | None = None,
    child: tuple | None = None,
) -> dict[str, Any]:
    """Report known/estimated plate-to-lid space, without inventing contact CAD."""

    d = _definition_of(definition_or_module)
    layout = thermocycler_v1_layout(d, child)
    heater_bottom = layout.body_top_mm + V1_HEATER_RAISE_EST_MM - 1.5
    gasket_plane = layout.body_top_mm + 2.0
    block_proxy_top = float(d.get("labwareOffset", {}).get("z", 97.8)) - 10.7
    report: dict[str, Any] = {
        "known": {
            "plate_child_bounds_mm": [layout.plate_x0_mm, layout.plate_y0_mm, layout.plate_x1_mm, layout.plate_y1_mm, layout.plate_top_mm],
            "module_body_top_mm": layout.body_top_mm,
            "current_scene_block_proxy_top_mm": block_proxy_top,
            "lid_documented_closed_height_mm": layout.closed_height_mm,
            "lid_documented_open_height_mm": layout.open_height_mm,
        },
        "estimated": {
            "gasket_plane_mm": gasket_plane,
            "heater_panel_lower_face_mm": heater_bottom,
            "heater_clearance_over_child_top_mm": (
                None if layout.plate_top_mm is None else heater_bottom - layout.plate_top_mm
            ),
        },
        "warnings": [],
        "evidence": EVIDENCE_NOTE,
    }
    if layout.plate_top_mm is None:
        report["warnings"].append("No loaded child top was supplied; contact cannot be evaluated.")
    elif heater_bottom <= layout.plate_top_mm:
        report["warnings"].append(
            "Estimated heater lower face is at or below the child top; inspect the real plate/lid stack before claiming closed contact."
        )
    else:
        report["warnings"].append(
            "Positive value is only a photo-based estimated gap; lid compression, latch travel and plate skirt geometry are unmeasured."
        )
    return report


def validate_v1_geometry(
    definition_or_module: Mapping[str, Any] | Any | None = None,
    child: tuple | None = None,
) -> dict[str, Any]:
    """Run deterministic envelope/body/plate checks used by the render script."""

    layout = thermocycler_v1_layout(definition_or_module, child)
    closed, opened = thermocycler_v1_lid_poses(definition_or_module, child)
    errors: list[str] = []
    checks = {
        "width_is_documented": abs(layout.width_mm - V1_WIDTH_MM) < 1e-6,
        "closed_height_is_documented": abs(closed[0][2] + layout.pack_height_mm / 2 - V1_CLOSED_HEIGHT_MM) < 1e-6,
        "open_height_is_documented": abs(opened[0][2] + layout.panel_length_mm / 2 - V1_OPEN_HEIGHT_MM) < 1e-6,
        "hinge_stays_inside_body": 0.0 < layout.hinge_y_mm <= layout.body_length_mm,
        "plate_stays_inside_lid_window": layout.panel_front_y_mm <= layout.plate_y0_mm and layout.panel_rear_y_mm >= layout.plate_y1_mm,
        "panel_leaves_front_body_margin": layout.panel_front_body_margin_mm >= 0.0,
        "hollow_panel_has_positive_opening": layout.width_mm - 2 * V1_PANEL_SIDE_WALL_MM > 0 and layout.panel_length_mm - V1_PANEL_FRONT_RAIL_MM - V1_PANEL_REAR_RAIL_MM > 0,
        "rear_service_duct_fits_documented_length": layout.body_length_mm + layout.rear_duct_length_mm <= V1_TOTAL_LENGTH_MM + 1e-6,
    }
    for name, ok in checks.items():
        if not ok:
            errors.append(name)
    return {
        "ok": not errors,
        "checks": checks,
        "errors": errors,
        "envelope": thermocycler_v1_envelope(definition_or_module, child),
        "contact": thermocycler_v1_contact_report(definition_or_module, child),
        "evidence": EVIDENCE_NOTE,
    }


# ---------------------------------------------------------------------------
# Standalone validation/render harness


def _validation_xml(book: AssetBook, geoms: Iterable[str], child: tuple[float, ...]) -> str:
    """Small MuJoCo harness for closed/mid/open visual regression images."""

    x0, y0, x1, y1, top = (float(v) for v in child)
    plate_top = top if top is not None else 101.0
    plate_height = 14.0
    plate_bottom = plate_top - plate_height
    body_x = V1_WIDTH_MM / 2.0 * MM
    body_y = V1_BODY_LENGTH_DEFAULT_MM / 2.0 * MM
    body_z = V1_BODY_TOP_DEFAULT_MM / 2.0 * MM
    plate_c = ((x0 + x1) / 2 * MM, (y0 + y1) / 2 * MM, (plate_bottom + plate_top) / 2 * MM)
    plate_s = ((x1 - x0) / 2 * MM, (y1 - y0) / 2 * MM, plate_height / 2 * MM)
    return f"""<mujoco model=\"ot2_tc_v1_lid_validation\">
  <compiler angle=\"radian\" coordinate=\"local\" meshdir=\"assets\"/>
  <option timestep=\"0.01\" gravity=\"0 0 -9.81\"/>
  <visual>
    <global offwidth=\"960\" offheight=\"760\"/>
    <headlight ambient=\"0.55 0.55 0.55\" diffuse=\"0.65 0.65 0.65\" specular=\"0.25 0.25 0.25\"/>
  </visual>
  <asset>
    {materials_xml()}
    <material name="gantry_white" rgba="0.87 0.88 0.90 1" specular="0.35" shininess="0.35"/>
    {book.asset_xml()}
  </asset>
  <worldbody>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 -0.004\" size=\"1 1 0.01\" material=\"floor\" contype=\"0\" conaffinity=\"0\"/>
    <body name=\"tc_v1\" pos=\"0 0 0\">
      <geom name=\"body_proxy\" type=\"box\" pos=\"{_v(body_x, body_y, body_z)}\" size=\"{_v(V1_WIDTH_MM / 2 * MM, V1_BODY_LENGTH_DEFAULT_MM / 2 * MM, V1_BODY_TOP_DEFAULT_MM / 2 * MM)}\" material=\"graphite\" contype=\"0\" conaffinity=\"0\"/>
      <geom name=\"plate_proxy\" type=\"box\" pos=\"{_v(*plate_c)}\" size=\"{_v(*plate_s)}\" material=\"white\" contype=\"0\" conaffinity=\"0\"/>
      {''.join(geoms)}
    </body>
    <camera name=\"tc_camera\" pos=\"0.56 -0.52 0.38\"/>
  </worldbody>
</mujoco>"""


def render_v1_validation(output: Path) -> dict[str, Any]:
    """Write XML, deterministic checks, and three MuJoCo renders if available."""

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    assets = output / "assets"
    book = AssetBook(assets)
    definition = _definition_of(None)
    # The default child mirrors the bundled V1 interface in the module-local
    # frame.  It is only a visual harness; real protocol child coordinates are
    # supplied by the protocol loader at runtime.
    child = (22.125, 82.56, 149.875, 168.56, 101.0)
    geoms = thermocycler_v1_geoms(definition, book, prefix="mod_tc_v1", child=child, include_static=True)
    xml_path = output / "thermocycler_v1_validation.xml"
    xml_path.write_text(_validation_xml(book, geoms, child), encoding="utf-8")
    report: dict[str, Any] = {
        "source": "sim/ot2_thermocycler.py",
        "output": str(output),
        "xml": str(xml_path),
        "assets": sorted(p.name for p in assets.glob("*")),
        "geometry_names": list(thermocycler_v1_dynamic_names("mod_tc_v1")),
        "checks": validate_v1_geometry(definition, child),
        "renders": {},
        "limitations": [
            "Photo-based geometry; not OEM CAD or hardware collision certification.",
            "Standalone harness uses visual body/plate proxies and does not alter protocol site coordinates.",
        ],
    }

    try:
        import mujoco  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        report["render_error"] = f"MuJoCo/PIL unavailable: {exc}"
        (output / "tc_v1_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    try:
        model = mujoco.MjModel.from_xml_path(str(xml_path))
        anchor_id = model.geom("mod_tc_v1_lid").id
        names = thermocycler_v1_dynamic_names("mod_tc_v1")
        geom_ids = {name: model.geom(name).id for name in names}
        closed_center = np.array(thermocycler_v1_lid_pose(definition, child, 0.0)[0], dtype=float) * MM
        # MuJoCo may rotate/recentre a mesh at compile time.  Preserve that
        # source transform, as the production player does, and only animate
        # the requested lid pose around it.
        source_pos = {name: np.array(model.geom_pos[gid], dtype=float) for name, gid in geom_ids.items()}
        source_ref_pos: dict[str, np.ndarray] = {}
        source_ref_quat: dict[str, np.ndarray] = {}
        for name, gid in geom_ids.items():
            if model.geom_type[gid] == mujoco.mjtGeom.mjGEOM_MESH:
                mesh = int(model.geom_dataid[gid])
                source_ref_pos[name] = model.mesh_pos[mesh].copy()
                source_ref_quat[name] = model.mesh_quat[mesh].copy()
            else:
                source_ref_pos[name] = np.zeros(3, dtype=float)
                source_ref_quat[name] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
        target = np.array([0.086, 0.145, 0.145], dtype=float)
        camera = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(camera)
        camera.azimuth = 138.0
        camera.elevation = -22.0
        camera.distance = 0.58
        camera.lookat[:] = target
        renderer = mujoco.Renderer(model, height=760, width=960)
        layout = thermocycler_v1_layout(definition, child)
        states = (("closed", 0.0), ("mid", -math.pi / 4.0), ("open", -math.pi / 2.0))
        for state, angle in states:
            center_mm, quat = thermocycler_v1_lid_pose(definition, child, angle)
            center = np.array(center_mm, dtype=float) * MM
            rot = np.zeros(9, dtype=float)
            mujoco.mju_quat2Mat(rot, np.array(quat, dtype=float))
            rot = rot.reshape(3, 3)
            for name, gid in geom_ids.items():
                local_offset = source_pos[name] - source_ref_pos[name] - closed_center
                model.geom_pos[gid] = center + rot @ (local_offset + source_ref_pos[name])
                mujoco.mju_mulQuat(model.geom_quat[gid], np.array(quat, dtype=float), source_ref_quat[name])
            data = mujoco.MjData(model)
            mujoco.mj_forward(model, data)
            renderer.update_scene(data, camera)
            image = renderer.render()
            path = output / f"tc_v1_{state}.png"
            Image.fromarray(image).save(path)
            report["renders"][state] = {
                "path": str(path),
                "angle_rad": angle,
                "center_mm": list(center_mm),
                "top_envelope_mm": (
                    center_mm[2]
                    + abs(math.sin(angle)) * layout.panel_length_mm / 2.0
                    + abs(math.cos(angle)) * layout.pack_height_mm / 2.0
                ),
            }
        renderer.close()
        report["rendered"] = True
    except Exception as exc:  # pragma: no cover - renderer/display dependent
        report["rendered"] = False
        report["render_error"] = repr(exc)
    (output / "tc_v1_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _main() -> int:
    parser = argparse.ArgumentParser(description="Validate/render the reference-based OT-2 Thermocycler GEN1 lid")
    parser.add_argument("--validate", metavar="OUTPUT", type=Path, help="write XML, JSON, assets and closed/mid/open PNGs")
    args = parser.parse_args()
    if args.validate is None:
        print(json.dumps(validate_v1_geometry(), indent=2))
        return 0
    report = render_v1_validation(args.validate)
    print(json.dumps(report, indent=2))
    return 0 if report["checks"]["ok"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())

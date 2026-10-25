"""Visual shell for the OT-2 MuJoCo scene.

Only the look: enclosure, gantry framing, pipette bodies, trash bin. The
skeleton stays in ``ot2_scene.py`` (bridge ``y``, carriage ``x``, one ``z``
per mount; nozzle A is the head origin and the 8-channel row runs -y at
9 mm). Every geom is visual (the scene default is contype 0).

Where the numbers come from
---------------------------
The official Basic/Detailed STL stores its axes as ``(x width, y height,
z depth)``.  The local CAD manifest and ``blender/build_ot2_blend.py`` put the
assembly in the protocol frame with
``(x_parts, y_parts, z_parts) = (x_raw, z_raw, y_raw)`` and translation
``(231.30, 190.03, 72.00)`` mm.  The visible enclosure below therefore uses
the measured 624 x 568 x 662 mm envelope with the deck datum close to z=0;
the authoritative deck targets and slide-joint origins remain in their
existing protocol frame.  The moving gantry is an authored visual skeleton
anchored in that frame; the raw STL is static enclosure reference geometry,
not a replacement for the protocol-driven joints.

Public product appearance, not measurable in the STL (flat sheets): clear
acrylic side/top windows and front door, white frame, blue front status
light, interior LED strips (docs.opentrons.com OT-2 system description).
GEN1 styling follows the legacy white/black photos. GEN2 has a continuous
black/silver single-channel shell and a narrow upper tower over a wide
8-channel lower manifold. Current official pipette photos and original lab
installation photos establish those features; small moldings are estimated.

Geom groups: 0 pipettes and small deck-visible details, 2 shell, gantry
framing and glass (hidden by the follow close-up so the deck reads).
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from sim.flex_shell import (
    MM,
    AssetBook,
    _f,
    _font,
    _text_center,
    _v,
    arc,
    cyl,
    label,
    mesh_geom,
    rbox,
    rrect,
    write_lathe,
    write_extrusion,
)

# ---------------------------------------------------------------- envelope

# Robot-frame metres after the official raw-STL axis correction.  x is width,
# y is front-to-back depth, and z is height above the protocol deck datum.
X0, X1 = -0.2313, 0.3930
Y0, Y1 = -0.19003, 0.37797
Z0, Z1 = -0.0720, 0.5900
WALL = 0.026                    # front/side skin thickness (STL pillar width)
DOOR_X0, DOOR_X1 = -0.2023, 0.3637
DOOR_Z0, DOOR_Z1 = -0.0070, 0.5540
BASE_LO = Z0 + 0.018            # 18 mm above the measured base datum
SILL_Z = Z0 + 0.062             # parts front sill top, ~62 mm global
POST_Z = Z0 + 0.059             # retained descriptive datum for callers
WIN_Z0 = Z0 + 0.078             # side-window lower edge, ~78 mm global
WIN_Z1 = Z0 + 0.590             # side-window top, ~590 mm global

# Gantry, STL-measured. Bridge frame: x and z absolute, y = joint origin.
BEAM_X0, BEAM_X1 = -0.1936, 0.3553
BEAM_Z0, BEAM_Z1 = 0.4300, 0.5080
BEAM_HALF_Y = 0.0225
# The visible bridge sits on the rear side of the carriage.  The corrected
# frame puts the pipette bay at y=-26..8 mm; placing this beam at y=13..58 mm
# leaves a small, intentional visual gap in front of the gun while keeping
# the rear edge inside the 74 mm rear-inner limit at the new home-Y pose.
# This is a visual depth estimate only: the bridge joint origin/range and the
# authoritative head sites are unchanged.
BEAM_Y_REL = 0.0355
RAIL_X = (-0.1975, 0.3653)      # rail centres; top side rail band z .542..590
RAIL_Z = (0.542, 0.590)
PLATE_Z1 = RAIL_Z[0]            # side plates: beam top up to the rails
# Carriage frame: origin at the right nozzle, x/y relative, z absolute.
CARR_HALF_X = 0.058
CARR_Y = (0.014, 0.040)         # rear visual carriage plate; pipette bay ends at .008
CARR_Z = (0.488, 0.545)
CLAMP_Z = (0.451, 0.495)
MOUNT_Y = -0.009                # pipette bay centre in the carriage face
ZRAIL_X = (-0.0515, 0.0515)
# Mounts: left nozzle sits 34 mm left of the right one (kinematic anchor).
LEFT_DX = -0.034
PITCH = 0.009
NOZZLE_ROWS = tuple("ABCDEFGH")
# Pipette body: nozzle end z 0, mount flange meets the carriage bottom.
PIPETTE_Z = (0.042, 0.150)      # housing
PIPETTE_TOP = 0.186
PIPETTE_HALF_X = 0.017
PIPETTE_Y = (-0.026, 0.008)
MULTI_Y = (-0.073, 0.010)       # wide head spans the 63 mm nozzle row
# Visual-only lower end of the fixed rear guide.  This is an appearance
# estimate chosen from the accepted TC park envelope, not a measured OEM
# datum; a mounted head gets a dynamic follower up to this guide.
FIXED_GUIDE_Z0 = 0.324

# The official reference images establish the P300 GEN2 skin, but do not
# provide calibrated nozzle drawings for every supported OT-2 instrument.
# These are deliberately modest visual estimates for the exposed metal/dark
# shaft only; tip length, insertion depth, sites and the analytical origin
# remain owned by ``ot2_protocol``/``ot2_scene``.  Keeping the profiles
# capacity-specific prevents a P300's broad black nozzle from being silently
# reused for P10/P20/P50/P1000.
_NOZZLE_VISUAL = {
    "p10": (36.0, 1.10, 1.28),
    "p20": (36.0, 1.20, 1.40),
    "p50": (44.0, 1.30, 1.55),
    "p300": (46.0, 1.45, 1.75),
    "p1000": (49.0, 1.65, 1.95),
}


def materials_xml() -> str:
    return """
    <texture name="ot2_sky" type="skybox" builtin="gradient" rgb1="0.98 0.98 0.99" rgb2="0.78 0.81 0.86" width="512" height="512"/>
    <material name="shell_white" rgba="0.94 0.945 0.955 1" specular="0.3" shininess="0.3"/>
    <material name="shell_gray" rgba="0.74 0.76 0.78 1" specular="0.2" shininess="0.2"/>
    <material name="shell_wall" rgba="0.88 0.888 0.90 1" specular="0.15" shininess="0.25"/>
    <material name="frame_dark" rgba="0.105 0.12 0.14 1" specular="0.28" shininess="0.32"/>
    <material name="band_gray" rgba="0.62 0.64 0.665 1" specular="0.15" shininess="0.2"/>
    <material name="panel_edge" rgba="0.28 0.30 0.33 1" specular="0.22" shininess="0.28"/>
    <material name="aluminum_dark" rgba="0.36 0.38 0.41 1" specular="0.55" shininess="0.58"/>
    <material name="gantry_aluminum" rgba="0.55 0.58 0.62 1" specular="0.60" shininess="0.62"/>
    <material name="rail_black" rgba="0.055 0.060 0.066 1" specular="0.28" shininess="0.32"/>
    <material name="drive_belt" rgba="0.025 0.028 0.032 1" specular="0.12" shininess="0.14"/>
    <material name="glass" rgba="0.76 0.82 0.88 0.025" specular="0.03" shininess="0.7"/>
    <material name="rear_glass" rgba="0.72 0.77 0.83 0.34" specular="0.06" shininess="0.68"/>
    <material name="anodized" rgba="0.16 0.17 0.185 1" specular="0.5" shininess="0.6"/>
    <material name="graphite" rgba="0.17 0.18 0.195 1" specular="0.3" shininess="0.35"/>
    <material name="satin_black" rgba="0.078 0.082 0.09 1" specular="0.25" shininess="0.3"/>
    <material name="matte_black" rgba="0.065 0.07 0.075 1" specular="0.12" shininess="0.12"/>
    <material name="rubber" rgba="0.03 0.03 0.03 1" specular="0.02" shininess="0.05"/>
    <material name="steel" rgba="0.78 0.80 0.82 1" specular="0.55" shininess="0.55"/>
    <material name="chrome" rgba="0.86 0.88 0.90 1" specular="0.9" shininess="0.85"/>
    <material name="nozzle_steel" rgba="0.58 0.60 0.63 1" specular="0.9" shininess="0.85"/>
    <material name="gantry_white" rgba="0.87 0.88 0.90 1" specular="0.35" shininess="0.35"/>
    <material name="pipette_white" rgba="0.94 0.945 0.95 1" specular="0.4" shininess="0.4"/>
    <material name="pipette_gray" rgba="0.70 0.72 0.75 1" specular="0.25" shininess="0.25"/>
    <material name="pipette_black" rgba="0.045 0.050 0.058 1" specular="0.32" shininess="0.38"/>
    <material name="pipette_silver" rgba="0.62 0.65 0.69 1" specular="0.72" shininess="0.72"/>
    <material name="pipette_metal" rgba="0.76 0.79 0.82 1" specular="0.88" shininess="0.86"/>
    <material name="pipette_recess" rgba="0.10 0.11 0.13 1" specular="0.25" shininess="0.28"/>
    <material name="display_dark" rgba="0.06 0.065 0.07 1" specular="0.4" shininess="0.5"/>
    <material name="led_blue" rgba="0.06 0.40 1.0 1" emission="0.65" specular="0"/>
    <material name="led_white" rgba="1 1 1 1" emission="0.85"/>
    <material name="accent_blue" rgba="0.12 0.45 0.90 1" emission="0.15"/>
    <material name="deck_surface" rgba="0.48 0.52 0.57 1" specular="0.35" shininess="0.35"/>
    <material name="deck_slot" rgba="0.17 0.20 0.24 1" specular="0.18" shininess="0.22"/>
    <material name="deck_rim" rgba="0.64 0.68 0.72 1" specular="0.55" shininess="0.55"/>
    <material name="deck_locator" rgba="0.10 0.12 0.15 1" specular="0.2" shininess="0.25"/>
    <material name="rack_edge" rgba="0.32 0.35 0.40 1" specular="0.35" shininess="0.35"/>
    <material name="rack_socket" rgba="0.72 0.75 0.79 1" specular="0.45" shininess="0.4"/>
    <material name="well_rim" rgba="0.70 0.74 0.79 1" specular="0.42" shininess="0.45"/>
    <material name="bin_dark" rgba="0.19 0.205 0.225 1" specular="0.18" shininess="0.2"/>
    <material name="bin_inner" rgba="0.085 0.095 0.11 1" specular="0.08" shininess="0.12"/>
    <material name="bin_liner" rgba="0.23 0.25 0.28 1" specular="0.16" shininess="0.20"/>
    <material name="bin_rim" rgba="0.48 0.51 0.55 1" specular="0.55" shininess="0.55"/>
    """


# ---------------------------------------------------------------- textures


def _ot2_logo() -> Image.Image:
    img = Image.new("RGB", (1200, 180), (240, 241, 243))
    draw = ImageDraw.Draw(img)
    big = _font(118)
    draw.text((10, 22), "opentrons", font=big, fill=(38, 42, 50))
    width = draw.textlength("opentrons", font=big)
    draw.text((width + 34, 22), "OT-2", font=_font(118, bold=True), fill=(0, 108, 250))
    return img


def _pipette_face(volume: str, channels: str, dark: bool, gen2: bool = False) -> Image.Image:
    """Front of an OT-2 pipette: drop mark near the top, volume label mid-face.

    The face is tall and narrow (~30 x 100 mm), so the text sits at mid height
    where the deck camera sees it, not down by the nozzle.
    """

    w, h = 200, 900
    bg = (24, 25, 27) if dark else (226, 228, 232)
    fg = (226, 228, 232) if dark else (40, 44, 52)
    dim = (150, 156, 164) if dark else (110, 116, 124)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    cx, cy, r = w / 2, ((470 if channels == "8" else 265) if gen2 else 130), 42
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=dim, width=6)
    draw.ellipse((cx - 13, cy - 2, cx + 13, cy + 24), fill=dim)
    draw.polygon([(cx, cy - 24), (cx - 12, cy + 6), (cx + 12, cy + 6)], fill=dim)
    if gen2:
        # Manufacturer photos put the compact capacity badge near the foot
        # of the single's long face. The multi has its badge on the wide
        # lower housing, separately from the drop on the narrow upper tower.
        if channels == "1":
            draw.rectangle((12, 752, w - 12, 860), outline=(55, 58, 62), width=3)
            _text_center(draw, (cx, 805), f"{volume} GEN2", _font(25, bold=True), fg)
    else:
        _text_center(draw, (cx, h * 0.46), volume, _font(88, bold=True), fg)
        _text_center(draw, (cx, h * 0.57), f"{channels}-Channel", _font(44), dim)
    return img


def _gen2_badge(volume: str) -> Image.Image:
    img = Image.new("RGB", (300, 140), (30, 32, 35))
    draw = ImageDraw.Draw(img)
    draw.rectangle((2, 2, 297, 137), outline=(62, 65, 69), width=4)
    _text_center(draw, (150, 70), f"{volume} GEN2", _font(34, bold=True), (218, 220, 222))
    return img


def _drop_mark() -> Image.Image:
    """Drop/ring mark printed on the lower carriage cover.

    The mark is deliberately a separate texture from the OT-2 wordmark.  The
    official gantry photos show a simple drop on the tall light carriage
    cover, while the front header carries the full ``opentrons OT-2`` label.
    """

    img = Image.new("RGB", (240, 240), (222, 224, 230))
    draw = ImageDraw.Draw(img)
    cx = 120
    draw.arc((34, 34, 206, 206), 285, 255, fill=(74, 78, 84), width=20)
    draw.polygon([(cx, 64), (82, 126), (82, 150), (cx, 179), (158, 150), (158, 126)], fill=(40, 134, 175))
    draw.ellipse((82, 113, 158, 182), fill=(40, 134, 175))
    return img


def make_textures(book: AssetBook) -> None:
    book.texture("ot2_logo", _ot2_logo(), specular=0.25, shininess=0.3)
    book.texture("drop_mark", _drop_mark(), specular=0.30, shininess=0.35)
    # (volume, gen1 single, gen2 single, gen1 multi, gen2 multi)
    catalog = (
        ("P10", True, False, True, False),
        ("P20", False, True, False, True),
        ("P50", True, False, True, False),
        ("P300", True, True, True, True),
        ("P1000", True, True, False, False),
    )
    for volume, s1, s2, m1, m2 in catalog:
        if m2:
            book.texture(f"ot2_badge_{volume}_g2", _gen2_badge(volume), specular=0.20)
        for want, channels, dark, gen2, suffix in (
            (s1, "1", False, False, ""),
            # Official GEN2 instruments use the black/silver housing and a
            # dark face label; GEN1 remains the black or white legacy body.
            (s2, "1", True, True, "_g2"),
            (m1, "8", True, False, "_8"),
            (m2, "8", True, True, "_8g2"),
        ):
            if want:
                book.texture(
                    f"ot2_face_{volume}{suffix}",
                    _pipette_face(volume, channels, dark, gen2),
                    specular=0.3 if not dark else 0.25,
                    shininess=0.35 if not dark else 0.3,
                )


# ---------------------------------------------------------------- enclosure


def enclosure_xml(book: AssetBook) -> str:
    """Static shell in the robot frame: base, walls with windows, door, rails."""

    g: list[str] = []
    cx = (X0 + X1) / 2
    inner_x0, inner_x1 = X0 + WALL, X1 - WALL
    inner_y1 = Y1 - WALL

    # Feet and base band.  The feet start at the measured shell bottom
    # (Z0=-72 mm in the protocol frame), not at the deck datum.
    for i, (fx, fy) in enumerate(
        [(X0 + 0.025, Y0 + 0.033), (X1 - 0.025, Y0 + 0.033), (X0 + 0.025, Y1 - 0.033), (X1 - 0.025, Y1 - 0.033)]
    ):
        g.append(cyl(f"foot_{i}", (fx, fy, Z0), (fx, fy, Z0 + 0.024), 0.024, "rubber", 2))
        # A shallow metal foot plate makes the four support points read as
        # attached to the lower frame instead of four black cylinders.
        g.append(cyl(f"foot_{i}_pad", (fx, fy, Z0 + 0.001), (fx, fy, Z0 + 0.006), 0.027, "aluminum_dark", 2))
    # The band surrounds the deck; a solid slab here hides every short plate
    # below SILL_Z (the deck's working plane is z=0). Keep the open centre.
    band_sides = (
        ("front", (X0, Y0), (X1, Y0 + WALL)),
        ("back", (X0, Y1 - WALL), (X1, Y1)),
        ("left", (X0, Y0 + WALL), (X0 + WALL, Y1 - WALL)),
        ("right", (X1 - WALL, Y0 + WALL), (X1, Y1 - WALL)),
    )
    for name, lo, hi in band_sides:
        g.append(rbox(book, f"base_band_{name}", (*lo, BASE_LO), (*hi, SILL_Z), "shell_wall", 0.006, 2))
        g.append(rbox(book, f"base_trim_{name}", (*lo, SILL_Z - 0.012), (*hi, SILL_Z), "band_gray", 0.004, 2))
    # The lower enclosure is made from separate folded panels.  These dark
    # seams are shallow surface details, kept inside the measured envelope.
    g.extend(
        (
            rbox(book, "base_front_panel", (X0 + 0.050, Y0 - 0.001, BASE_LO), (X1 - 0.050, Y0 + 0.002, SILL_Z - 0.004), "band_gray", 0.003, 2),
            rbox(book, "base_front_seam", (cx - 0.002, Y0 - 0.002, BASE_LO), (cx + 0.002, Y0 + 0.003, SILL_Z - 0.004), "panel_edge", 0.001, 2),
            rbox(book, "base_front_lower_seam", (X0 + 0.050, Y0 - 0.002, Z0 + 0.024), (X1 - 0.050, Y0 + 0.003, Z0 + 0.027), "panel_edge", 0.001, 2),
        )
    )
    # Corner posts up to the door head height, framing the front.
    for name, lo, hi in (("l", X0, X0 + WALL), ("r", X1 - WALL, X1)):
        g.append(rbox(book, f"post_f_{name}", (lo, Y0, BASE_LO), (hi, Y0 + WALL, DOOR_Z1), "frame_dark", 0.006, 2))

    # Side walls: white frame with a tall window hole, then the glass.
    win_y = (Y0 + 0.052, Y1 - 0.052)
    win_z = (WIN_Z0, WIN_Z1)
    side = rrect(Y0, Y1, Z0, Z1, 0.008, 0.020)
    hole = rrect(win_y[0], win_y[1], win_z[0], win_z[1], 0.016, 0.016)
    for name, lo, hi in (("left", X0, X0 + WALL), ("right", X1 - WALL, X1)):
        g.append(mesh_geom(f"side_{name}", book.extrusion(f"side_{name}", side, hole, 0, lo, hi), "frame_dark", 2))
        g.append(
            f'<geom name="window_{name}" type="box" pos="{_v((lo + hi) / 2, (win_y[0] + win_y[1]) / 2, (win_z[0] + win_z[1]) / 2)}" '
            f'size="{_v((hi - lo) / 2 - 0.001, (win_y[1] - win_y[0]) / 2, (win_z[1] - win_z[0]) / 2)}" material="glass" group="2"/>'
        )
        # A lower panel break and a vertical return at the rear of the side
        # window give the sheet-metal frame the layered look of the product
        # photos without altering the window opening.
        g.append(rbox(book, f"side_{name}_lower_seam", (lo - 0.001, win_y[0], Z0 + 0.098), (hi + 0.001, win_y[1], Z0 + 0.103), "panel_edge", 0.001, 2))
        g.append(rbox(book, f"side_{name}_rear_return", (lo - 0.001, Y1 - 0.060, win_z[0]), (hi + 0.001, Y1 - 0.056, WIN_Z1), "band_gray", 0.002, 2))

    # Back wall: a real framed window rather than a solid gray slab.  The
    # inner glass keeps the rear of the machine readable in the default
    # camera, while the extrusion hole is what creates the actual opening in
    # the visible sheet-metal frame.
    back_outer = rrect(X0, X1, Z0, Z1, 0.008, 0.020)
    back_hole = rrect(X0 + 0.052, X1 - 0.052, WIN_Z0, WIN_Z1 - 0.012, 0.014, 0.014)
    g.append(mesh_geom("back_panel", book.extrusion("back_panel", back_outer, back_hole, 1, inner_y1, Y1), "shell_wall", 2))
    g.append(
        f'<geom name="back_glass" type="box" pos="{_v((X0 + X1) / 2, inner_y1 + 0.004, (WIN_Z0 + WIN_Z1 - 0.012) / 2)}" '
        f'size="{_v((X1 - X0) / 2 - 0.054, 0.004, (WIN_Z1 - 0.012 - WIN_Z0) / 2)}" material="rear_glass" group="2"/>'
    )
    # Thin dark returns make the opening edge visible from the front without
    # narrowing the physical shell bounds.
    g.extend(
        (
            rbox(book, "back_window_header", (X0 + 0.042, inner_y1 - 0.002, WIN_Z1 - 0.018), (X1 - 0.042, inner_y1 + 0.003, WIN_Z1 - 0.010), "frame_dark", 0.002, 2),
            rbox(book, "back_window_sill", (X0 + 0.042, inner_y1 - 0.002, Z0 + 0.100), (X1 - 0.042, inner_y1 + 0.003, Z0 + 0.108), "frame_dark", 0.002, 2),
        )
    )
    # Leave the clear rear opening unobstructed. The old decorative louvers
    # had reversed Y bounds and floated across this window; no verified rear
    # panel detail requires them.
    # No interior LED strip geoms: emissive bars above the side walls mirror
    # off the window panes at grazing angles and wash out the deck view.

    # Top: white frame ring with a clear panel.
    top_hole = rrect(X0 + 0.052, X1 - 0.052, Y0 + 0.052, Y1 - 0.052, 0.016, 0.016)
    g.append(mesh_geom("top_frame", book.extrusion("top_frame", rrect(X0, X1, Y0, Y1, 0.008, 0.020), top_hole, 2, Z1 - WALL, Z1), "shell_wall", 2))
    g.append(
        f'<geom name="top_glass" type="box" pos="{_v(cx, (Y0 + Y1) / 2, Z1 - WALL / 2)}" '
        f'size="{_v((X1 - X0) / 2 - 0.054, (Y1 - Y0) / 2 - 0.054, WALL / 2 - 0.001)}" material="glass" group="2"/>'
    )

    # Front: header band above the door, sill below it, clear door in between.
    g.append(rbox(book, "front_header", (X0, Y0, DOOR_Z1), (X1, Y0 + WALL, Z1), "shell_wall", 0.006, 2))
    g.append(rbox(book, "front_sill", (X0, Y0, SILL_Z), (X1, Y0 + WALL, SILL_Z + 0.020), "shell_gray", 0.004, 2))
    dz0, dz1 = DOOR_Z0 + 0.008, DOOR_Z1 - 0.008
    dx0, dx1 = DOOR_X0 + 0.008, DOOR_X1 - 0.008
    door_y = Y0 + WALL / 2
    hinge_z = (dz0 + dz1) / 2
    g.append(
        f'<geom name="door_glass" type="box" pos="{_v((dx0 + dx1) / 2, door_y, (hinge_z + dz1) / 2)}" '
        f'size="{_v((dx1 - dx0) / 2, 0.003, (dz1 - hinge_z) / 2)}" material="glass" group="2"/>'
    )
    g.append(
        f'<geom name="door_lower_glass" type="box" pos="{_v((dx0 + dx1) / 2, door_y, (dz0 + hinge_z) / 2)}" '
        f'size="{_v((dx1 - dx0) / 2, 0.003, (hinge_z - dz0) / 2 - 0.0007)}" material="glass" group="2"/>'
    )
    # Both manufacturer imagery and the HKUST/installation photographs show
    # a fixed upper window and a lower flap hinged at the middle seam. The
    # old bottom-mounted vertical barrels and full-height door frame were
    # incorrect. These leaves and horizontal axles show the closed pose;
    # this visual repair deliberately adds no unvalidated door articulation.
    g.append(rbox(book, "door_middle_join", (dx0, Y0 - 0.001, hinge_z - 0.0005), (dx1, Y0 + 0.001, hinge_z + 0.0005), "aluminum_dark", 0.0002, 2))
    for side, x in (("l", dx0 + 0.007), ("r", dx1 - 0.007)):
        for leaf, za, zb in (("upper", hinge_z + 0.003, hinge_z + 0.021), ("lower", hinge_z - 0.021, hinge_z - 0.003)):
            g.append(rbox(book, f"door_hinge_{side}_{leaf}", (x - 0.016, Y0 - 0.009, za), (x + 0.016, Y0 - 0.003, zb), "rail_black", 0.002, 2))
        g.append(cyl(f"door_hinge_{side}", (x - 0.017, Y0 - 0.010, hinge_z), (x + 0.017, Y0 - 0.010, hinge_z), 0.0045, "aluminum_dark", 2))
        for col in (-1, 1):
            for row in (-1, 1):
                sx, sz = x + col * 0.010, hinge_z + row * 0.013
                g.append(cyl(f"door_hinge_{side}_screw_{col}_{row}", (sx, Y0 - 0.010, sz), (sx, Y0 - 0.008, sz), 0.0021, "graphite", 2))
        g.append(rbox(book, f"door_catch_{side}", (x - 0.015, Y0 - 0.009, dz0 + 0.005), (x + 0.015, Y0 - 0.003, dz0 + 0.024), "rail_black", 0.002, 2))
    g.append(rbox(book, "front_header_seam", (X0 + 0.050, Y0 - 0.002, DOOR_Z1 - 0.004), (X1 - 0.050, Y0 + 0.003, DOOR_Z1 + 0.001), "panel_edge", 0.001, 2))
    # Small pull at the lower edge of the flap, as in the real closed door.
    g.append(rbox(book, "door_handle", (cx - 0.044, Y0 - 0.008, dz0 + 0.005), (cx + 0.044, Y0 + 0.002, dz0 + 0.014), "shell_white", 0.003, 2))
    g.append(rbox(book, "door_handle_grip", (cx - 0.037, Y0 - 0.009, dz0 + 0.006), (cx + 0.037, Y0 - 0.006, dz0 + 0.010), "band_gray", 0.001, 2))
    header_mid = (DOOR_Z1 + Z1) / 2
    for side, xx in (("l", X0 + 0.041), ("r", X1 - 0.041)):
        g.append(cyl(f"header_screw_{side}", (xx, Y0 - 0.002, header_mid), (xx, Y0 + 0.001, header_mid), 0.0035, "steel", 2))
        g.append(cyl(f"header_screw_{side}_socket", (xx, Y0 - 0.0025, header_mid), (xx, Y0 - 0.002, header_mid), 0.0015, "graphite", 2))
    # Put the decal ahead of the rounded header face, not within the mesh;
    # the previous 0.2 mm inset caused perspective-dependent clipped lettering.
    g.append(label(book, "logo", (cx - 0.105, Y0 - 0.002, header_mid), (0.26, 0.023), "ot2_logo", 2))
    # The product has a round status lamp on the upper-left pillar.
    lamp_x, lamp_z = X0 + WALL / 2, Z1 - 0.075
    g.append(cyl("status_led_bezel", (lamp_x, Y0 - 0.004, lamp_z), (lamp_x, Y0 + 0.003, lamp_z), 0.009, "steel", 2))
    g.append(cyl("status_led", (lamp_x, Y0 - 0.005, lamp_z), (lamp_x, Y0 - 0.004, lamp_z), 0.0065, "led_blue", 2))

    return "\n      ".join(g)


def rails_xml(book: AssetBook) -> str:
    """Static Y-rail assemblies on the two side walls.

    The library reference separates a lower stationary guide around
    z=.474--.488 m (after the -72 mm base datum) from the pale top side rail
    cover around z=.542--.590 m.  Keeping those as nested layers makes the
    bridge attachment legible without changing the bridge ``y`` joint.
    """

    g = []
    y0, y1 = Y0 + 0.052, Y1 - 0.040
    for name, x in (("left", RAIL_X[0]), ("right", RAIL_X[1])):
        # The dark stationary guide is the actual bearing datum; the bridge
        # trucks sit against this layer.  It is separate from the upper shell
        # rail so the latter does not read as a single oversized black bar.
        g.append(rbox(book, f"rail_{name}_stationary", (x - 0.018, y0 + 0.012, 0.474), (x + 0.018, y1 - 0.012, 0.488), "aluminum_dark", 0.003, 2))
        g.append(rbox(book, f"rail_{name}_stationary_bearing", (x - 0.010, y0 + 0.022, 0.478), (x + 0.010, y1 - 0.022, 0.484), "rail_black", 0.0015, 2))
        g.append(rbox(book, f"rail_{name}", (x - 0.027, y0, RAIL_Z[0] + 0.006), (x + 0.027, y1, RAIL_Z[1] - 0.004), "steel", 0.005, 2))
        g.append(rbox(book, f"rail_{name}_mount", (x - 0.023, y0 + 0.01, RAIL_Z[0] - 0.020), (x + 0.023, y1 - 0.01, RAIL_Z[0] + 0.008), "graphite", 0.004, 2))
        # Two nested guide surfaces and end bearing blocks make the long rail
        # legible as a moving axis.  They stay inside the existing rail AABB.
        g.append(rbox(book, f"rail_{name}_guide", (x - 0.012, y0 + 0.020, RAIL_Z[0] + 0.019), (x + 0.012, y1 - 0.020, RAIL_Z[0] + 0.026), "aluminum_dark", 0.002, 2))
        g.append(rbox(book, f"rail_{name}_belt", (x - 0.019, y0 + 0.024, RAIL_Z[0] + 0.012), (x + 0.019, y1 - 0.024, RAIL_Z[0] + 0.016), "drive_belt", 0.001, 2))
        for end, yy in (("front", y0 + 0.006), ("back", y1 - 0.018)):
            g.append(rbox(book, f"rail_{name}_end_{end}", (x - 0.030, yy, RAIL_Z[0] - 0.004), (x + 0.030, yy + 0.012, RAIL_Z[0] + 0.036), "rail_black", 0.003, 2))
    return "\n      ".join(g)


# ---------------------------------------------------------------- gantry


def bridge_geoms(book: AssetBook) -> str:
    """X beam plus the side plates and trucks that ride the Y rails.

    Bridge frame: x and z absolute in the robot frame, y relative to the joint
    origin (beam centred at ``BEAM_Y_REL``). The visible extrusion is a rear
    bridge: its front edge is deliberately behind the pipette bay, while the
    side trucks remain inside the same 13..58 mm depth band. The side plates
    clamp inside the enclosure: the whole bridge is in the moving clearance
    sweep, so nothing here may poke past the shell skins.
    """

    g = [
        # The production gantry is a light anodized extrusion with dark guide
        # surfaces set into its front face.  Keep the measured envelope and
        # joint frame; only the visible finish is changed here.
        rbox(book, "beam", (BEAM_X0, BEAM_Y_REL - BEAM_HALF_Y, BEAM_Z0), (BEAM_X1, BEAM_Y_REL + BEAM_HALF_Y, BEAM_Z1), "gantry_aluminum", 0.007, 2),
        rbox(book, "beam_groove", (BEAM_X0 + 0.030, BEAM_Y_REL - BEAM_HALF_Y - 0.001, BEAM_Z0 + 0.052), (BEAM_X1 - 0.030, BEAM_Y_REL - BEAM_HALF_Y + 0.004, BEAM_Z0 + 0.062), "satin_black", 0.001, 2),
        # Keep the upper seam inset from the rear extrusion edge; the former
        # 1 mm overhang was the last visual piece leaving the enclosure on the
        # P20 drop path.
        rbox(book, "beam_seam", (BEAM_X0 + 0.030, BEAM_Y_REL + BEAM_HALF_Y - 0.005, BEAM_Z1 - 0.020), (BEAM_X1 - 0.030, BEAM_Y_REL + BEAM_HALF_Y - 0.001, BEAM_Z1 - 0.014), "graphite", 0.0008, 2),
        rbox(book, "beam_front_rail", (BEAM_X0 + 0.022, BEAM_Y_REL - BEAM_HALF_Y - 0.002, BEAM_Z0 + 0.018), (BEAM_X1 - 0.022, BEAM_Y_REL - BEAM_HALF_Y + 0.003, BEAM_Z0 + 0.028), "rail_black", 0.0015, 2),
        rbox(book, "beam_top_cap", (BEAM_X0 + 0.018, BEAM_Y_REL - 0.022, BEAM_Z1 - 0.003), (BEAM_X1 - 0.018, BEAM_Y_REL + 0.022, BEAM_Z1 + 0.003), "shell_gray", 0.002, 2),
    ]
    for name, xa, xb in (
        ("left", max(RAIL_X[0] - 0.048, X0 + 0.008), RAIL_X[0] + 0.052),
        ("right", RAIL_X[1] - 0.052, min(RAIL_X[1] + 0.048, X1 - 0.010)),
    ):
        g.append(rbox(book, f"gantry_plate_{name}", (xa, BEAM_Y_REL - BEAM_HALF_Y + 0.006, BEAM_Z1 - 0.004), (xb, BEAM_Y_REL + BEAM_HALF_Y - 0.006, PLATE_Z1), "gantry_white", 0.005, 2))
        # The truck used to spread ±44 mm around the beam and crossed the
        # pipette bay. Keep a compact rear carriage instead; its estimated
        # 13.5..57.5 mm depth stays inside the corrected rear-inner datum even at
        # the P20 drop path's furthest sampled bridge position.
        g.append(rbox(book, f"gantry_truck_{name}", (xa + 0.008, BEAM_Y_REL - 0.022, PLATE_Z1 - 0.004), (xb - 0.008, BEAM_Y_REL + 0.022, PLATE_Z1 + 0.026), "matte_black", 0.005, 2))
        g.append(rbox(book, f"gantry_plate_{name}_trim", (xa + 0.004, BEAM_Y_REL - BEAM_HALF_Y + 0.006, BEAM_Z1 - 0.004), (xa + 0.008, BEAM_Y_REL + BEAM_HALF_Y - 0.006, PLATE_Z1 - 0.010), "graphite", 0.001, 2))
        for side, yy in (("front", BEAM_Y_REL - 0.022), ("back", BEAM_Y_REL + 0.012)):
            g.append(cyl(f"gantry_truck_{name}_roller_{side}", ((xa + xb) / 2, yy, PLATE_Z1 + 0.008), ((xa + xb) / 2, yy + 0.010, PLATE_Z1 + 0.008), 0.006, "chrome", 2))
        g.append(rbox(book, f"gantry_plate_{name}_drive", (xa + 0.016, BEAM_Y_REL - 0.020, PLATE_Z1 + 0.010), (xb - 0.016, BEAM_Y_REL - 0.014, PLATE_Z1 + 0.018), "drive_belt", 0.001, 2))
    return "\n        ".join(g)


def carriage_geoms(book: AssetBook) -> str:
    """X carriage: plate above the beam, clamp around it, two pipette mounts.

    Carriage frame: origin at the right nozzle (x = y = 0), z absolute.
    """

    cover_top = RAIL_Z[0] - 0.018
    # The official carriage is a long pale front cover, not a short tab just
    # above the X beam.  The lower end is kept behind the pipette and above
    # the deck; the fixed slide/ribbon stop at the upper guide datum while a
    # mounted head's runtime follower spans the moving Z stroke.
    cover_bottom = PIPETTE_TOP + 0.038
    ribbon_bottom = FIXED_GUIDE_Z0
    slide_bottom = FIXED_GUIDE_Z0
    # Put the pale cover just behind the pipette bay in the front-to-back
    # frame.  This preserves the official long cover silhouette while leaving
    # the black instrument face readable instead of hiding it at home Z.
    cover_y0, cover_y1 = MOUNT_Y + 0.023, MOUNT_Y + 0.043
    # Keep the fixed clamp in the rear half of the carriage.  The pipette
    # housing ends at y=.008 m; a 6 mm visual gap leaves the gun silhouette
    # readable at the full z stroke instead of letting the clamp read as a
    # plate pushed through its upper housing.
    clamp_y0, clamp_y1 = PIPETTE_Y[1] + 0.006, CARR_Y[1]
    g = [
        rbox(book, "carriage_plate", (-CARR_HALF_X, CARR_Y[0], CARR_Z[0]), (CARR_HALF_X, CARR_Y[1], CARR_Z[1]), "graphite", 0.005, 2),
        rbox(book, "carriage_cap", (-CARR_HALF_X + 0.006, CARR_Y[0] + 0.006, CARR_Z[1] - 0.010), (CARR_HALF_X - 0.006, CARR_Y[1] - 0.006, CARR_Z[1]), "satin_black", 0.003, 2),
        rbox(book, "carriage_clamp", (-CARR_HALF_X + 0.004, clamp_y0, CLAMP_Z[0]), (CARR_HALF_X - 0.004, clamp_y1, CLAMP_Z[1] - 0.013), "matte_black", 0.005, 2),
        # A narrow rear neck is the visible bridge from the lower clamp to the
        # carriage plate.  It is intentionally inset so it does not produce a
        # coplanar black rectangle over the plate's outer face.
        rbox(book, "carriage_clamp_neck", (-0.025, clamp_y0 + 0.006, CLAMP_Z[1] - 0.014), (0.025, clamp_y1 - 0.004, CARR_Z[0] + 0.003), "graphite", 0.0025, 2),
        rbox(book, "carriage_face", (-CARR_HALF_X + 0.004, CARR_Y[0] - 0.004, CARR_Z[0] + 0.008), (CARR_HALF_X - 0.004, CARR_Y[0] - 0.001, CARR_Z[1] - 0.012), "graphite", 0.0015, 2),
        rbox(book, "carriage_face_seam", (-CARR_HALF_X + 0.010, CARR_Y[0] - 0.005, CARR_Z[0] + 0.026), (CARR_HALF_X - 0.010, CARR_Y[0] - 0.002, CARR_Z[0] + 0.028), "matte_black", 0.0006, 2),
        # Official OT-2 photos show a tall pale carriage cover ahead of the
        # black mount plate, reaching toward the upper rail assembly.  It is a
        # moving visual part of the existing carriage body, with a dark lower
        # recess and a small drop mark.  The pipette bay remains in
        # front-to-back space y=-26..8 mm; the cover is placed just behind it
        # in the corrected depth frame so it cannot occlude the nozzle or
        # alter the anchors.
        rbox(book, "carriage_cover", (-0.046, cover_y0, cover_bottom), (0.046, cover_y1, cover_top), "gantry_white", 0.004, 2),
        rbox(book, "carriage_cover_face", (-0.036, cover_y0 - 0.003, cover_bottom + 0.012), (0.036, cover_y0 + 0.001, cover_top - 0.018), "gantry_white", 0.002, 2),
        rbox(book, "carriage_cover_lower", (-0.036, cover_y0 - 0.001, cover_bottom), (0.036, cover_y0 + 0.005, cover_bottom + 0.012), "aluminum_dark", 0.002, 2),
        rbox(book, "carriage_cover_recess", (-0.020, cover_y0 - 0.005, cover_bottom + 0.018), (0.020, cover_y0 - 0.001, cover_bottom + 0.028), "panel_edge", 0.001, 2),
        rbox(book, "carriage_cover_side_l", (-0.050, cover_y0 + 0.003, cover_bottom + 0.002), (-0.045, cover_y1 + 0.002, cover_top - 0.010), "aluminum_dark", 0.0015, 2),
        rbox(book, "carriage_cover_side_r", (0.045, cover_y0 + 0.003, cover_bottom + 0.002), (0.050, cover_y1 + 0.002, cover_top - 0.010), "aluminum_dark", 0.0015, 2),
        label(book, "carriage_cover_logo", (0.0, cover_y0 - 0.004, (cover_bottom + cover_top) / 2), (0.058, 0.064), "drop_mark", 2),
    ]
    for name, x in (("right", 0.0), ("left", LEFT_DX)):
        g.append(cyl(f"mount_{name}", (x, MOUNT_Y, CARR_Z[0] + 0.006), (x, MOUNT_Y, CARR_Z[1]), 0.0125, "steel", 2))
        g.append(cyl(f"mount_{name}_collar", (x, MOUNT_Y, CARR_Z[0] + 0.006), (x, MOUNT_Y, CARR_Z[0] + 0.020), 0.016, "graphite", 2))
        # The public installation procedure calls out two screws and a
        # ribbon connection at each mount.  These small brackets make the
        # moving pipette read as attached to the carriage instead of hanging
        # below an empty gap.  They are visual-only and live in the carriage
        # frame; the kinematic mount and target coordinates stay unchanged.
        g.append(rbox(book, f"mount_{name}_saddle", (x - 0.023, PIPETTE_Y[1] + 0.007, CLAMP_Z[0] - 0.003), (x + 0.023, CARR_Y[1] - 0.004, CLAMP_Z[0] + 0.011), "gantry_white", 0.003, 2))
        # The fixed slide is only the upper carriage guide.  The installed
        # head's runtime follower bridges its lower end without changing the
        # joint or its range; empty mounts therefore cannot read as dangling
        # forks below the park envelope.
        g.append(rbox(book, f"mount_{name}_slide", (x - 0.010, MOUNT_Y + 0.025, slide_bottom), (x + 0.010, MOUNT_Y + 0.041, CARR_Z[0] + 0.0115), "steel", 0.0025, 2))
        g.append(rbox(book, f"mount_{name}_backplate", (x - 0.020, MOUNT_Y + 0.026, CLAMP_Z[0] - 0.005), (x + 0.020, MOUNT_Y + 0.035, CARR_Z[0] + 0.012), "graphite", 0.002, 2))
        # The installation ribbon is a narrow, finite-thickness upper rear
        # strap.  Keep the stable geom name and leave the lower moving section
        # to the installed-head follower; the old z0 == z1 placeholder read
        # as a zero-thickness floating line in closeups.
        g.append(rbox(book, f"mount_{name}_ribbon", (x - 0.008, MOUNT_Y + 0.024, ribbon_bottom), (x + 0.008, MOUNT_Y + 0.032, CARR_Z[0] + 0.014), "drive_belt", 0.001, 2))
        for side in (-1, 1):
            g.append(cyl(f"mount_{name}_screw_{'l' if side < 0 else 'r'}", (x + side * 0.016, MOUNT_Y + 0.030, CLAMP_Z[0] + 0.002), (x + side * 0.016, MOUNT_Y + 0.035, CLAMP_Z[0] + 0.002), 0.0032, "chrome", 2))
    for name, x in (("l", ZRAIL_X[0]), ("r", ZRAIL_X[1])):
        g.append(rbox(book, f"z_rail_{name}", (x - 0.003, CARR_Y[0] - 0.002, BEAM_Z0 + 0.004), (x + 0.003, CARR_Y[0] + 0.003, CARR_Z[1] - 0.012), "chrome", 0.0012, 2))
    return "\n          ".join(g)


# ---------------------------------------------------------------- pipettes


def _volume_label(tool: str) -> str:
    name = tool.split("_")[0]
    return {"p10": "P10", "p20": "P20", "p50": "P50", "p300": "P300", "p1000": "P1000"}.get(name, name.upper())


def _is_gen2(tool: str) -> bool:
    return "gen2" in tool


def _nozzles(prefix: str, channels: int) -> list[str]:
    """Slim chrome cones, 4.4 mm across at the 9 mm row pitch.

    Radius matches the scene's 2.2 mm tip needles; fatter cones merge into a
    solid bar from front-quarter views and the row stops being countable.
    """
    g = []
    for k in range(channels):
        y = -PITCH * k
        g.append(
            f'<geom name="{prefix}_nozzle_{NOZZLE_ROWS[k]}" type="cylinder" '
            f'fromto="0 {_f(y)} 0 0 {_f(y)} 0.040" size="0.0022" material="nozzle_steel" group="0"/>'
        )
    return g


def _gen2_nozzle_mesh(book: AssetBook) -> str:
    """P300 GEN2 nozzle wall, authored in the head's nozzle frame.

    This is a visual estimate from the official GEN2 product photographs, not
    a measured or collision nozzle.  The profile is a section loop: the outer
    wall rises from a 1.8 mm mouth to a 3.15 mm shoulder at 14 mm, then a 3.4
    mm upper shoulder at 16 mm; the return path is the 0.6--1.0 mm bore.  The
    profile closes across the annular lower rim without returning to the
    axis, leaving the lower gas path open. Other capacities retain their
    existing nozzle shape until reference dimensions are established.
    """

    profile_mm = [
        (1.80, 0.0),
        (1.95, 1.2),
        (2.25, 4.5),
        (2.65, 8.5),
        (3.15, 14.0),
        (3.40, 15.0),
        (3.40, 16.0),
        (1.00, 16.0),
        (1.00, 14.0),
        (0.82, 7.0),
        (0.60, 1.2),
        (0.60, 0.0),
        (1.80, 0.0),
    ]
    profile = [(radius * MM, z * MM) for radius, z in profile_mm]
    return book._mesh("ot2_gen2_nozzle", lambda path: write_lathe(path, profile, seg=32))


def _visual_nozzle_mesh(book: AssetBook, tool: str) -> str:
    """Capacity-specific solid shaft for non-P300 or GEN1 visual nozzles.

    The analytical capsule in ``ot2_scene`` is a clearance proxy, not a
    product surface.  This lathe gives the rendered shaft a short tapered
    outlet, a shoulder and a narrower upper connection.  It intentionally
    stays a solid exterior skin: only the P300 GEN2 photo-backed profile is
    drawn as a hollow annulus.  Dimensions are appearance estimates in mm.
    """

    volume = tool.split("_", 1)[0]
    length, neck, shoulder = _NOZZLE_VISUAL.get(volume, (43.0, 1.35, 1.60))
    profile_mm = [
        (0.0, 0.0),
        (neck * 0.82, 0.0),
        (neck, 2.0),
        (shoulder, 8.0),
        (shoulder, max(10.0, length - 7.0)),
        (shoulder * 1.08, length - 2.0),
        (shoulder * 1.08, length),
        (0.0, length),
    ]
    profile = [(radius * MM, z * MM) for radius, z in profile_mm]
    key = f"ot2_visual_nozzle_{volume}_{round(length)}"
    return book._mesh(key, lambda path: write_lathe(path, profile, seg=28))


def pipette_single_body(book: AssetBook, tool: str, prefix: str | None = None) -> list[str]:
    """Single-channel pipette in the head frame: nozzle end z 0, body above.

    GEN2 uses a continuous black face, silver side shells and a lower badge;
    GEN1 retains the legacy service band and side ejector shaft. ``prefix`` names the geoms
    (the scene passes ``pipette_<mount>`` so both mounts can share a model).
    """

    name = prefix or tool
    volume = _volume_label(tool)
    face = f"ot2_face_{volume}{'_g2' if _is_gen2(tool) else ''}"
    z0, z1 = PIPETTE_Z
    gen2 = _is_gen2(tool)
    housing = "pipette_black" if gen2 else "pipette_white"
    housing_top = PIPETTE_TOP if gen2 else z1
    photo_nozzle = gen2 and tool.startswith("p300_")
    nozzle_mesh = _gen2_nozzle_mesh(book) if photo_nozzle else None
    visual_nozzle_mesh = None if photo_nozzle else _visual_nozzle_mesh(book, tool)
    g = [
        cyl(f"{name}_collar", (0.0, 0.0, 0.012 if gen2 else 0.022), (0.0, 0.0, z0 + 0.006), 0.0047 if gen2 else 0.0075, "pipette_black" if gen2 else "graphite", 0),
        rbox(book, f"{name}_housing", (-PIPETTE_HALF_X, PIPETTE_Y[0], z0), (PIPETTE_HALF_X, PIPETTE_Y[1], housing_top), housing, 0.005, 0),
        label(book, f"{name}_face", (0.0, PIPETTE_Y[0] - 0.0003, (z0 + housing_top) / 2), (PIPETTE_HALF_X * 2 - 0.004, housing_top - z0 - 0.006), face, 0),
        rbox(book, f"{name}_spine", (-0.011, PIPETTE_Y[0] + 0.004, z1), (0.011, PIPETTE_Y[1] - 0.004, PIPETTE_TOP), "pipette_black" if gen2 else "pipette_gray", 0.003, 0),
        rbox(book, f"{name}_cap", (-PIPETTE_HALF_X + 0.004, PIPETTE_Y[0] + 0.003, PIPETTE_TOP - 0.010), (PIPETTE_HALF_X - 0.004, PIPETTE_Y[1] - 0.003, PIPETTE_TOP), "graphite", 0.002, 0),
        # Moving flange and short connector overlap the fixed mount slide at
        # the working end of Z travel.  GEN2's product top is a narrow dark
        # cap/backplate; the earlier 42 mm silver block read as a hat over the
        # 34 mm housing.  Keep the mount pin overlap but confine the visible
        # cap to the upper body, while leaving GEN1's legacy shape intact.
        rbox(
            book,
            f"{name}_mount_flange",
            (-0.014 if gen2 else -0.021, PIPETTE_Y[0] + (0.006 if gen2 else 0.002), PIPETTE_TOP - (0.003 if gen2 else 0.006)),
            (0.014 if gen2 else 0.021, PIPETTE_Y[1] - (0.004 if gen2 else 0.002), PIPETTE_TOP + (0.006 if gen2 else 0.012)),
            "pipette_black" if gen2 else "gantry_white",
            0.0025 if gen2 else 0.003,
            0,
        ),
        cyl(f"{name}_mount_pin", (0.0, MOUNT_Y, PIPETTE_TOP + 0.006), (0.0, MOUNT_Y, PIPETTE_TOP + 0.034), 0.0055, "chrome", 0),
    ] + _nozzles(name, 1)
    if gen2:
        # Current GEN2 photos show an uninterrupted long face, thin silver
        # side panels and a black lower nozzle. There is no large exposed
        # silver ejector cage on this configuration. Preserve the head/site
        # frame; the small lower skin covers the unchanged analytical needle.
        g.extend(
            (
                rbox(book, f"{name}_silver_side_l", (-PIPETTE_HALF_X - 0.0005, PIPETTE_Y[0] + 0.003, z0 + 0.009), (-PIPETTE_HALF_X + 0.003, PIPETTE_Y[1] - 0.003, housing_top - 0.005), "pipette_silver", 0.0015, 0),
                rbox(book, f"{name}_silver_side_r", (PIPETTE_HALF_X - 0.003, PIPETTE_Y[0] + 0.003, z0 + 0.009), (PIPETTE_HALF_X + 0.0005, PIPETTE_Y[1] - 0.003, housing_top - 0.005), "pipette_silver", 0.0015, 0),
                rbox(book, f"{name}_heel_seam", (-PIPETTE_HALF_X + 0.002, PIPETTE_Y[0] - 0.0005, z0 + 0.008), (PIPETTE_HALF_X - 0.002, PIPETTE_Y[0] + 0.001, z0 + 0.009), "pipette_recess", 0.0003, 0),
                # Keep the original black shaft name.  P300 GEN2 uses the
                # photo-backed open annulus below; other GEN2 capacities use
                # their own narrow, capacity-specific exterior shaft.
                (cyl(f"{name}_needle_skin", (0.0, 0.0, 0.012), (0.0, 0.0, 0.016), 0.0023, "pipette_black", 0)
                 if photo_nozzle else mesh_geom(f"{name}_needle_skin", visual_nozzle_mesh, "pipette_black", 0)),
            )
        )
    else:
        g.extend(
            (
                mesh_geom(f"{name}_needle_skin", visual_nozzle_mesh, "nozzle_steel", 0),
                rbox(book, f"{name}_band", (-PIPETTE_HALF_X, PIPETTE_Y[0] - 0.0008, z0 + 0.048), (PIPETTE_HALF_X, PIPETTE_Y[1] + 0.0008, z0 + 0.056), "pipette_gray", 0.002, 0),
            )
        )
        g.append(cyl(f"{name}_ejector", (PIPETTE_HALF_X - 0.004, PIPETTE_Y[1] - 0.006, z0 + 0.012), (PIPETTE_HALF_X - 0.004, PIPETTE_Y[1] - 0.006, z1 - 0.020), 0.003, "satin_black", 0))
    # One metal collar per channel gives the disposable tip a visible seat.
    # This collar is part of the nozzle/tip assembly.  Keeping ``needle`` in
    # its name makes the existing aimed-well exemption treat it like the
    # adjacent needle capsule during clearance sweeps.
    if photo_nozzle:
        # The stable collar name now carries the shared open nozzle mesh;
        # there is no coplanar cylinder under it.
        g.append(mesh_geom(f"{name}_needle_collar", nozzle_mesh, "pipette_black", 0))
    elif gen2:
        g.append(cyl(f"{name}_needle_collar", (0.0, 0.0, 0.007), (0.0, 0.0, 0.016), 0.0034, "pipette_black", 0))
    else:
        g.append(cyl(f"{name}_needle_collar", (0.0, 0.0, 0.004), (0.0, 0.0, 0.014), 0.0034, "nozzle_steel", 0))
    return g


def pipette_multi_body(book: AssetBook, tool: str, prefix: str | None = None) -> list[str]:
    """8-channel pipette: wide black head spanning the nozzle row (-y at 9 mm)."""

    name = prefix or tool
    volume = _volume_label(tool)
    face = f"ot2_face_{volume}_8{'g2' if _is_gen2(tool) else ''}"
    z0, z1 = PIPETTE_Z
    if _is_gen2(tool):
        # Official GEN2 front/side photos: narrow upper instrument tower,
        # broad lower manifold and short individual nozzle ends. Do not
        # stretch the 8-channel width through the entire upper housing.
        # The official multi-channel image has a shorter lower manifold and a
        # taller narrow tower.  The former .108 split made the lower black
        # block dominate the instrument; this visual-only split preserves the
        # 9 mm row and all nozzle/site origins.
        split, bottom = 0.090, 0.010
        photo_nozzle = tool.startswith("p300_")
        nozzle_mesh = _gen2_nozzle_mesh(book) if photo_nozzle else None
        visual_nozzle_mesh = None if photo_nozzle else _visual_nozzle_mesh(book, tool)
        g = [
            rbox(book, f"{name}_housing", (-PIPETTE_HALF_X, MULTI_Y[0], bottom), (PIPETTE_HALF_X, MULTI_Y[1], split), "pipette_black", 0.005, 0),
            rbox(book, f"{name}_tower", (-PIPETTE_HALF_X + 0.002, PIPETTE_Y[0], split - 0.003), (PIPETTE_HALF_X - 0.002, PIPETTE_Y[1], PIPETTE_TOP), "pipette_black", 0.002, 0),
            label(book, f"{name}_face", (0.0, PIPETTE_Y[0] - 0.0004, (split + PIPETTE_TOP) / 2), (0.027, PIPETTE_TOP - split - 0.004), face, 0),
            label(book, f"{name}_badge", (0.0, MULTI_Y[0] - 0.0005, 0.070), (0.024, 0.014), f"ot2_badge_{volume}_g2", 0),
            rbox(book, f"{name}_cap", (-PIPETTE_HALF_X + 0.003, PIPETTE_Y[0] + 0.002, PIPETTE_TOP - 0.004), (PIPETTE_HALF_X - 0.003, PIPETTE_Y[1] + 0.002, PIPETTE_TOP), "graphite", 0.001, 0),
            # Match the single GEN2 cap: a narrow black mounting top, not a
            # wide silver slab over the tower.
            rbox(book, f"{name}_mount_flange", (-0.014, PIPETTE_Y[0] + 0.006, PIPETTE_TOP - 0.003), (0.014, PIPETTE_Y[1] - 0.004, PIPETTE_TOP + 0.006), "pipette_black", 0.0025, 0),
            cyl(f"{name}_mount_pin", (0.0, MOUNT_Y, PIPETTE_TOP + 0.006), (0.0, MOUNT_Y, PIPETTE_TOP + 0.034), 0.0055, "chrome", 0),
            rbox(book, f"{name}_heel_seam", (-PIPETTE_HALF_X + 0.001, MULTI_Y[0] - 0.0005, bottom + 0.012), (PIPETTE_HALF_X - 0.001, MULTI_Y[0] + 0.001, bottom + 0.013), "pipette_recess", 0.0003, 0),
            # Two restrained front seams give the broad lower manifold the
            # stepped, moulded break visible in the GEN2 reference photo.
            rbox(book, f"{name}_lower_join_seam", (-0.015, MULTI_Y[0] - 0.0005, split - 0.005), (0.015, MULTI_Y[0] + 0.001, split - 0.002), "pipette_recess", 0.0004, 0),
            rbox(book, f"{name}_lower_heel_seam", (-0.014, MULTI_Y[0] - 0.0005, bottom + 0.018), (0.014, MULTI_Y[0] + 0.001, bottom + 0.021), "pipette_recess", 0.0004, 0),
        ] + _nozzles(name, 8)
        for side, xa, xb in (("l", -PIPETTE_HALF_X - 0.0003, -PIPETTE_HALF_X + 0.003), ("r", PIPETTE_HALF_X - 0.003, PIPETTE_HALF_X + 0.0003)):
            g.append(rbox(book, f"{name}_silver_side_{side}", (xa, PIPETTE_Y[0] + 0.003, split + 0.003), (xb, PIPETTE_Y[1] - 0.002, PIPETTE_TOP - 0.003), "pipette_silver", 0.001, 0))
        for k, row in enumerate(NOZZLE_ROWS):
            yy = -PITCH * k
            # The upper black shaft remains a short 12--16 mm connection;
            # the lower seat is the shared open lathe, translated by the
            # unchanged 9 mm channel pitch.
            if photo_nozzle:
                g.append(cyl(f"{name}_needle_{row}_skin", (0.0, yy, 0.012), (0.0, yy, 0.016), 0.0023, "pipette_black", 0))
                g.append(mesh_geom(f"{name}_needle_{row}_seat", nozzle_mesh, "pipette_black", 0, pos=(0.0, yy, 0.0)))
            else:
                g.append(mesh_geom(f"{name}_needle_{row}_skin", visual_nozzle_mesh, "pipette_black", 0, pos=(0.0, yy, 0.0)))
                g.append(cyl(f"{name}_needle_{row}_seat", (0.0, yy, 0.006), (0.0, yy, bottom + 0.004), 0.0034, "pipette_black", 0))
        return g
    g = [
        rbox(book, f"{name}_nose", (-PIPETTE_HALF_X, MULTI_Y[0] + 0.010, 0.034), (PIPETTE_HALF_X, 0.004, z0 + 0.010), "matte_black", 0.003, 0),
        rbox(book, f"{name}_housing", (-PIPETTE_HALF_X, MULTI_Y[0], z0), (PIPETTE_HALF_X, MULTI_Y[1], z1), "satin_black", 0.004, 0),
        label(book, f"{name}_face", (0.0, MULTI_Y[0] - 0.0003, z0 + 0.058), (PIPETTE_HALF_X * 2 - 0.004, 0.096), face, 0),
        rbox(book, f"{name}_spine", (-0.011, MULTI_Y[0] + 0.006, z1), (0.011, MULTI_Y[1] - 0.004, PIPETTE_TOP), "satin_black", 0.003, 0),
        rbox(book, f"{name}_cap", (-PIPETTE_HALF_X + 0.004, MULTI_Y[0] + 0.003, PIPETTE_TOP - 0.010), (PIPETTE_HALF_X - 0.004, MULTI_Y[1] - 0.003, PIPETTE_TOP), "graphite", 0.002, 0),
        rbox(book, f"{name}_mount_flange", (-0.021, MULTI_Y[0] + 0.002, PIPETTE_TOP - 0.006), (0.021, MULTI_Y[1] - 0.002, PIPETTE_TOP + 0.012), "gantry_white", 0.003, 0),
        cyl(f"{name}_mount_pin", (0.0, MOUNT_Y, PIPETTE_TOP + 0.006), (0.0, MOUNT_Y, PIPETTE_TOP + 0.034), 0.0055, "chrome", 0),
    ] + _nozzles(name, 8)
    visual_nozzle_mesh = _visual_nozzle_mesh(book, tool)
    for k, row in enumerate(NOZZLE_ROWS):
        yy = -PITCH * k
        g.append(mesh_geom(f"{name}_needle_{row}_skin", visual_nozzle_mesh, "nozzle_steel", 0, pos=(0.0, yy, 0.0)))
        g.append(cyl(f"{name}_needle_{row}_seat", (0.0, yy, 0.004), (0.0, yy, 0.014), 0.0034, "nozzle_steel", 0))
    return g


def pipette_body(book: AssetBook, tool: str, prefix: str | None = None, include_nozzles: bool = True) -> list[str]:
    """Look geoms for any ``OT2_PIPETTES`` name, in the head frame.

    ``include_nozzles=False`` when the scene mounts its own needle geoms (the
    ones the clearance check exempts at aimed wells) so the rows do not
    z-fight with these cones.
    """

    body = pipette_multi_body if "multi" in tool else pipette_single_body
    g = body(book, tool, prefix)
    if not include_nozzles:
        rows = 8 if "multi" in tool else 1
        cone = {geom.split('name="', 1)[1].split('"', 1)[0] for geom in _nozzles(prefix or tool, rows)}
        return [geom for geom in g if geom.split('name="', 1)[1].split('"', 1)[0] not in cone]
    return g


# ---------------------------------------------------------------- scene wiring


def hit_boxes() -> dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]]:
    """Gantry collision boxes in the spec joint frames: (center, half-extents).

    The beam box lives in the bridge frame (x/z absolute, y relative to the
    nozzle joint origin, hence ``BEAM_Y_REL``); the carriage box in the
    carriage frame (right nozzle xy, z absolute). Both cover the full look
    sweep so ``check_clearance`` sees the gantry as one obstacle.
    """

    return {
        "beam": (
            ((BEAM_X0 + BEAM_X1) / 2, BEAM_Y_REL, (BEAM_Z0 + BEAM_Z1) / 2),
            ((BEAM_X1 - BEAM_X0) / 2, BEAM_HALF_Y, (BEAM_Z1 - BEAM_Z0) / 2),
        ),
        "carriage": (
            (0.0, (CARR_Y[0] + CARR_Y[1]) / 2, (CARR_Z[0] + CARR_Z[1]) / 2),
            (CARR_HALF_X, (CARR_Y[1] - CARR_Y[0]) / 2, (CARR_Z[1] - CARR_Z[0]) / 2),
        ),
    }


# Effective clearance envelope in the corrected parts/protocol frame. These
# are the measured visual shell extents, not the old wrong-axis STL AABB. The
# group-3 proxy keeps the stable geom name and collision semantics; it does
# not move any deck target or slide joint. The parent planner owns the home-y
# correction needed for this now-correct rear datum.
BOUND_LO = (X0, Y0, Z0)
BOUND_HI = (X1, Y1, Z1)


def shell_bound() -> str:
    """Invisible group-3 box named ``shell``: the clearance envelope.

    ``check_clearance`` derives the enclosure's inner box from the AABB of the
    geom named ``shell`` (sides, back and top; the front door cut stays open).
    The proxy follows the corrected official parts envelope and intentionally
    rejects the former wrong-axis back/top overrun.
    """

    c = tuple((lo + hi) / 2 for lo, hi in zip(BOUND_LO, BOUND_HI))
    h = tuple((hi - lo) / 2 for lo, hi in zip(BOUND_LO, BOUND_HI))
    return f'<geom name="shell" type="box" pos="{_v(*c)}" size="{_v(*h)}" rgba="0 0 0 0" group="3"/>'


def visual_xml(offwidth: int = 1920, offheight: int = 1200) -> str:
    """Flex-style visual block: dim headlight, soft shadows, light haze."""

    return f"""<visual>
      <global azimuth="128" elevation="-22" offwidth="{offwidth}" offheight="{offheight}"/>
      <quality shadowsize="8192" offsamples="8"/>
      <headlight ambient="0.34 0.34 0.36" diffuse="0.22 0.22 0.22" specular="0.06 0.06 0.06"/>
      <map znear="0.01" zfar="20" haze="0.08"/>
      <rgba haze="0.96 0.965 0.975 1"/>
    </visual>"""


# ---------------------------------------------------------------- trash


def trash_xml(book: AssetBook, origin: tuple[float, float, float], size: tuple[float, float, float]) -> str:
    """Open-top bin with a recessed floor and a four-piece hollow lip.

    ``trash_inner`` and ``trash_rim`` are retained as stable visual names for
    callers that already know this helper.  They now represent the recessed
    floor and front lip member respectively; neither is a full-volume cap.
    """

    x0, y0, z0 = origin
    sx, sy, sz = size
    t = 0.004
    g = [
        rbox(book, "trash_floor", (x0 + t, y0 + t, z0), (x0 + sx - t, y0 + sy - t, z0 + t), "bin_dark", 0.002, 2),
        rbox(book, "trash_wall_front", (x0, y0, z0), (x0 + sx, y0 + t, z0 + sz), "bin_dark", 0.002, 2),
        rbox(book, "trash_wall_back", (x0, y0 + sy - t, z0), (x0 + sx, y0 + sy, z0 + sz), "bin_dark", 0.002, 2),
        rbox(book, "trash_wall_left", (x0, y0 + t, z0), (x0 + t, y0 + sy - t, z0 + sz), "bin_dark", 0.002, 2),
        rbox(book, "trash_wall_right", (x0 + sx - t, y0 + t, z0), (x0 + sx, y0 + sy - t, z0 + sz), "bin_dark", 0.002, 2),
        # Recessed inner floor: the mouth remains open from the rim down to
        # this shallow floor instead of being filled by a tall solid block.
        rbox(book, "trash_inner", (x0 + t + 0.002, y0 + t + 0.002, z0 + 0.010), (x0 + sx - t - 0.002, y0 + sy - t - 0.002, z0 + 0.014), "bin_inner", 0.001, 2),
        # Thin inner liner on all four walls; the open center has no top face.
        rbox(book, "trash_liner_front", (x0 + t + 0.006, y0 + t + 0.006, z0 + 0.012), (x0 + sx - t - 0.006, y0 + t + 0.008, z0 + sz - 0.010), "bin_liner", 0.001, 2),
        rbox(book, "trash_liner_back", (x0 + t + 0.006, y0 + sy - t - 0.008, z0 + 0.012), (x0 + sx - t - 0.006, y0 + sy - t - 0.006, z0 + sz - 0.010), "bin_liner", 0.001, 2),
        rbox(book, "trash_liner_left", (x0 + t + 0.006, y0 + t + 0.008, z0 + 0.012), (x0 + t + 0.008, y0 + sy - t - 0.008, z0 + sz - 0.010), "bin_liner", 0.001, 2),
        rbox(book, "trash_liner_right", (x0 + sx - t - 0.008, y0 + t + 0.008, z0 + 0.012), (x0 + sx - t - 0.006, y0 + sy - t - 0.008, z0 + sz - 0.010), "bin_liner", 0.001, 2),
        # Four independent lip members leave the opening visibly hollow.
        # ``trash_rim`` remains the front member for backwards name stability.
        rbox(book, "trash_rim", (x0 - 0.004, y0 - 0.004, z0 + sz - 0.006), (x0 + sx + 0.004, y0 + t + 0.004, z0 + sz + 0.004), "bin_rim", 0.003, 2),
        rbox(book, "trash_rim_back", (x0 - 0.004, y0 + sy - t - 0.004, z0 + sz - 0.006), (x0 + sx + 0.004, y0 + sy + 0.004, z0 + sz + 0.004), "bin_rim", 0.003, 2),
        rbox(book, "trash_rim_left", (x0 - 0.004, y0 + t, z0 + sz - 0.006), (x0 + t + 0.004, y0 + sy - t, z0 + sz + 0.004), "bin_rim", 0.003, 2),
        rbox(book, "trash_rim_right", (x0 + sx - t - 0.004, y0 + t, z0 + sz - 0.006), (x0 + sx + 0.004, y0 + sy - t, z0 + sz + 0.004), "bin_rim", 0.003, 2),
    ]
    return "\n      ".join(g)


# ---------------------------------------------------------------- lighting


def scene_lighting() -> str:
    """Three-point directional rig tuned for the front deck camera.

    The key sits almost centered above the front so neither side window pane
    catches it at a grazing angle toward a front viewer (Fresnel glare wash);
    steep direction keeps the deck brightly lit through the door opening.
    """
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
    return f"""<light name="key" pos="{cx + 0.15:.3f} {cy - 1.45:.3f} 2.05" dir="-0.05 0.50 -0.86" directional="true" diffuse="0.62 0.62 0.59" specular="0.24 0.24 0.22" castshadow="true"/>
<light name="fill" pos="{cx - 1.1:.3f} {cy - 1.0:.3f} 1.15" dir="0.42 0.55 -0.72" directional="true" diffuse="0.40 0.42 0.45" specular="0.06 0.06 0.07" castshadow="false"/>
<light name="deck_fill" pos="{cx:.3f} {cy - 0.15:.3f} 1.55" dir="0.02 0.12 -0.99" directional="true" diffuse="0.28 0.30 0.32" specular="0.08 0.08 0.09" castshadow="false"/>
<light name="rim" pos="{cx:.3f} {cy + 1.5:.3f} 1.7" dir="0 -0.45 -0.88" directional="true" diffuse="0.12 0.12 0.14" specular="0.07 0.07 0.08" castshadow="false"/>"""

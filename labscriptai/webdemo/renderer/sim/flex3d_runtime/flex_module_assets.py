"""Load the shared Flex module mesh pack. Millimetres convert once here.

``FLEX3D_MODULE_ASSETS`` can point at a manifest or its directory. Otherwise
the runtime resolves ``cad/flex/modules/manifest.json`` below ``FLEX3D_ROOT``
(with the source repo's nested ``detailed`` layout as a compatibility
fallback). Absent packs keep the portable primitive fallback; malformed packs
fail loudly.
"""
import json
import math
import os
from pathlib import Path


def manifest_path():
    value = os.environ.get('FLEX3D_MODULE_ASSETS')
    if value:
        path = Path(value).expanduser()
    else:
        root_override = os.environ.get('FLEX3D_ROOT')
        root = Path(root_override).expanduser().resolve() if root_override else Path(__file__).resolve().parents[2]
        # The checkout keeps the detailed module pack at cad/flex/modules.
        # Accept the source repo's nested ``detailed`` layout too so this
        # namespace can be copied into LabScript-AI without asset rewrites.
        path = root / 'cad/flex/modules/manifest.json'
        if not path.is_file():
            path = root / 'cad/flex/modules/detailed/manifest.json'
    return path / 'manifest.json' if path.is_dir() else path


def load_pack():
    path = manifest_path()
    if not path.is_file():
        if os.environ.get('FLEX3D_MODULE_ASSETS'):
            raise FileNotFoundError(path)
        return None
    pack = json.loads(path.read_text())
    if pack.get('schema') != 'virtual-lab.flex-modules/1' or pack.get('units') != 'mm':
        raise ValueError(f'Unsupported Flex asset pack: {path}')
    return path.resolve().parent, pack['modules']


def module_xml(deck, mod, book, robot_m):
    loaded = load_pack()
    if not loaded or mod.model not in loaded[1]:
        return None
    folder, modules = loaded
    asset = modules[mod.model]
    # Keep the official addressable area; never move the protocol's labware to fit art.
    origin = robot_m(deck, tuple(mod.area_mm[i] - asset['interface_origin_mm'][i] for i in range(3)))
    groups = []
    for name, group in asset['groups'].items():
        if group.get('optional'):
            continue
        geoms = []
        for part in asset['parts']:
            if part['group'] != name:
                continue
            source = (folder / part['file']).resolve()
            if not source.is_relative_to(folder):
                raise ValueError('Mesh outside asset pack')
            mesh_name = f"detail_{mod.model}_{part['name']}"
            def write_mesh(path, source=source):
                # OBJ remains in a part-local frame; scale vertices from mm to m.
                lines = []
                for line in source.read_text().splitlines():
                    if line.startswith('v '):
                        line = 'v ' + ' '.join(f'{float(v)*.001:.9f}' for v in line.split()[1:])
                    lines.append(line)
                path.write_text('\n'.join(lines)+'\n')
            book._mesh(mesh_name, write_mesh)
            color = part['rgba']
            if mod.model == 'temperatureModuleV2' and part['name'].endswith('_cyan'):
                # The authored studio pose shows 04; the player has no measured
                # temperature telemetry. Leave those display segments unlit.
                color = [.055, .07, .08, 1]
            rgba = ' '.join(map(str, color))
            geoms.append(f'<geom name="{mod.key}_visual_{part["name"]}" type="mesh" mesh="{mesh_name}" rgba="{rgba}" group="0" mass="0"/>')
        if mod.model == 'thermocyclerModuleV2' and name == 'lid':
            # A rotating lid remains an obstacle when open. Its box follows
            # the same body as the visual cover, instead of disappearing.
            geoms.append(f'<geom name="{mod.key}_lid" type="box" pos="0 -.1 .0257" size=".082 .098 .0257" group="5" rgba=".5 .5 .5 1" mass="0"/>')
        xyz = ' '.join(f'{v*.001:.9f}' for v in group['origin_mm'])
        groups.append(f'<body name="{mod.key}_detail_{name}" pos="{xyz}">{"".join(geoms)}</body>')
    return f'<body name="{mod.key}_detail" pos="{" ".join(map(str,origin))}">{"".join(groups)}</body>'


class ModuleMotion:
    """Real body transforms, also exported by the existing Three.js frame writer."""
    def __init__(self, model, run):
        import mujoco
        self.model = model
        self.parts = []
        loaded = load_pack()
        for mod in run.modules.values():
            if not loaded or mod.model not in loaded[1]:
                continue
            for joint in loaded[1][mod.model]['joints']:
                bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, f'{mod.key}_detail_{joint["name"]}')
                if bid >= 0:
                    self.parts.append((mod, joint, bid, model.body_pos[bid].copy()))

    def apply(self, state):
        for mod, joint, bid, home in self.parts:
            if joint['type'] == 'hinge':
                closed = getattr(state, 'module_lid', {}).get(mod.key, float(mod.key in state.lid_closed))
                angle = math.radians(joint['open'] * (1-closed))
                axis = joint['axis']; s = math.sin(angle/2)
                self.model.body_quat[bid] = [math.cos(angle/2), *(s*v for v in axis)]
            elif joint['type'] == 'slide':
                closed = getattr(state, 'module_latch', {}).get(mod.key, 1.)
                self.model.body_pos[bid] = home + [v*joint['open']*.001*(1-closed) for v in joint['axis']]
            elif joint['type'] == 'removable':
                closed = getattr(state, 'module_lid', {}).get(mod.key, 1.)
                # The reader lid is removable, not hinged. Its gripper trajectory
                # is not present in older analyses: show an explicit parked pose.
                self.model.body_pos[bid] = home + [0, -.13*(1-closed), 0]

"""Permanent Flex protocol/runtime regressions.

These tests deliberately start with an inline Python protocol and run the
installed Opentrons analyzer before handing its JSON to the isolated Flex
runtime.  They are semantic/runtime tests, not a copy of the reference
repository's fixtures: the only files created are temporary protocol and
analysis files, plus a temporary MuJoCo model for the rendering assertion.

Run with the product QA environment (Python 3.11, Opentrons 8.8.2,
MuJoCo 3.17):

    PYTHONPATH=. /path/to/qa-venv/bin/python -m unittest discover \
        -s tests -p 'test_flex_protocol_regression.py' -v
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sim.flex3d_runtime.flex_protocol import ProtocolError, load_analysis, plan, scene_spec
from sim.flex3d_runtime.flex_scene import load_deck, load_model, write_model


ROOT = Path(__file__).resolve().parents[1]


def _fresh_protocol() -> str:
    """A small Flex protocol used by tests that mutate analysis commands."""

    return '''from opentrons import protocol_api, types
requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def run(p):
    trash = p.load_trash_bin("A3")
    rack = p.load_labware("opentrons_flex_96_tiprack_50ul", "D1")
    reservoir = p.load_labware("nest_12_reservoir_15ml", "B3")
    plate = p.load_labware("nest_96_wellplate_200ul_flat", "C3")
    water = p.define_liquid(name="Water", description="Water", display_color="#55aaff")
    reservoir["A1"].load_liquid(water, 1000)
    pip = p.load_instrument("flex_1channel_50", "left", tip_racks=[rack])
    pip.pick_up_tip()
    pip.aspirate(10, reservoir["A1"])
    pip.air_gap(5)
    pip.move_to(types.Location(types.Point(100, 100, 100), None))
    p.delay(seconds=2)
    p.home()
    pip.drop_tip(trash)
'''


def _air_order_protocol() -> str:
    return '''from opentrons import protocol_api
requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def run(p):
    trash = p.load_trash_bin("A3")
    rack = p.load_labware("opentrons_flex_96_tiprack_50ul", "D1")
    reservoir = p.load_labware("nest_12_reservoir_15ml", "B3")
    plate = p.load_labware("nest_96_wellplate_200ul_flat", "C3")
    water = p.define_liquid(name="Water", description="Water", display_color="#55aaff")
    reservoir["A1"].load_liquid(water, 30)
    pip = p.load_instrument("flex_1channel_50", "left", tip_racks=[rack])
    pip.pick_up_tip()
    pip.aspirate(10, reservoir["A1"])
    pip.air_gap(5)
    pip.dispense(5, plate["A1"])
    pip.dispense(10, plate["A1"])
    pip.drop_tip(trash)
'''


def _multichannel_chute_protocol() -> str:
    return '''from opentrons import protocol_api
requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def run(p):
    chute = p.load_waste_chute()
    rack = p.load_labware("opentrons_flex_96_tiprack_50ul", "A3")
    reservoir = p.load_labware("nest_12_reservoir_15ml", "B3")
    plate = p.load_labware("nest_96_wellplate_200ul_flat", "C3")
    water = p.define_liquid(name="Water", description="Water", display_color="#55aaff")
    reservoir["A1"].load_liquid(water, 2000)
    pip = p.load_instrument("flex_8channel_50", "left", tip_racks=[rack])
    pip.pick_up_tip()
    pip.aspirate(10, reservoir["A1"])
    pip.dispense(10, plate["A1"])
    pip.drop_tip(chute)
'''


def _module_and_gripper_protocol() -> str:
    return '''from opentrons import protocol_api
requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def run(p):
    tc = p.load_module("thermocyclerModuleV2", "B1")
    tc.open_lid()
    tc.close_lid()
    tc.set_block_temperature(60, hold_time_seconds=3)
    tc.deactivate_block()
    plate = p.load_labware("nest_96_wellplate_200ul_flat", "D2")
    p.move_labware(plate, "C3", use_gripper=True)
'''


class FlexProtocolRegressionTests(unittest.TestCase):
    """Run against the installed official CLI and the product Flex runtime."""

    @classmethod
    def setUpClass(cls) -> None:
        # The repository's default interpreter does not necessarily carry the
        # robot SDK.  The product QA command supplies both dependencies; skip
        # cleanly when a developer invokes unittest with another interpreter.
        missing = [name for name in ("opentrons", "mujoco") if importlib.util.find_spec(name) is None]
        if missing:
            raise unittest.SkipTest(f"Flex QA dependencies unavailable: {', '.join(missing)}")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="flex-protocol-regression-")
        self.work = Path(self.temp.name)
        self.deck = load_deck()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def analyze(self, source: str, label: str = "protocol"):
        """Analyze source with the current official CLI and load its JSON."""

        source_path = self.work / f"{label}.py"
        output_path = self.work / f"{label}.analysis.json"
        source_path.write_text(source, encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "opentrons.cli",
                "analyze",
                "--check",
                "--json-output",
                str(output_path),
                str(source_path),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"official Flex analysis failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
        )
        self.assertTrue(output_path.is_file(), completed.stderr)
        raw = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertFalse(raw.get("errors"), raw.get("errors"))
        return load_analysis(output_path, self.deck), raw

    def test_air_gap_coordinates_exact_wait_and_explicit_waste(self):
        run, raw = self.analyze(_fresh_protocol(), "air-gap")
        planned = plan(run)
        kinds = [command["commandType"] for command in raw["commands"]]
        self.assertIn("airGapInPlace", kinds)
        self.assertIn("moveToCoordinates", kinds)
        self.assertIn("waitForDuration", kinds)
        wait = next(step for step in planned.steps if step.kind == "waitForDuration")
        self.assertEqual(wait.t1 - wait.t0, 2.0)

        air_key = next(key for key in planned.keys if key.phase == "aspirate air")
        tool = "pipette_1000_left"
        self.assertEqual(air_key.state.tip_air[tool][0], 5.0)
        self.assertEqual(air_key.state.tip_front_air[tool][0], 5.0)
        self.assertAlmostEqual(sum(air_key.state.tip_liquid[tool][0].values()), 10.0)
        final = planned.keys[-1].state
        self.assertAlmostEqual(sum(final.waste["trash:movableTrashA3"].values()), 10.0)

        # Verify that the renderer uses the front-air offset rather than
        # drawing the colored slug at the tip outlet as if air were liquid.
        import mujoco
        from sim.flex3d_runtime.play_protocol import Scene, check_targets, check_clearance

        folder = self.work / "air-model"
        model = load_model(write_model(self.deck, scene_spec(planned), folder))
        scene = Scene(planned, model, mujoco.MjData(model))
        check_targets(planned, scene)
        check_clearance(planned, scene)
        liquid_geom = scene.tips[tool][0][1]
        scene.apply(air_key.q, air_key.state)
        air_z = float(model.geom_pos[liquid_geom, 2])
        no_air = copy.deepcopy(air_key.state)
        no_air.tip_front_air[tool][0] = 0.0
        scene.apply(air_key.q, no_air)
        no_air_z = float(model.geom_pos[liquid_geom, 2])
        self.assertGreater(air_z, no_air_z)

    def test_air_gap_is_lifo_and_does_not_become_destination_liquid(self):
        run, _ = self.analyze(_air_order_protocol(), "air-order")
        planned = plan(run)
        reservoir = next(item for item in run.labware.values() if item.slot == "B3")
        plate = next(item for item in run.labware.values() if item.slot == "C3")
        state = planned.keys[-1].state
        self.assertAlmostEqual(sum(state.wells[(reservoir.key, "A1")].values()), 20.0)
        self.assertAlmostEqual(sum(state.wells[(plate.key, "A1")].values()), 10.0)
        self.assertEqual(state.tip_liquid["pipette_1000_left"][0], {})
        self.assertNotIn("outside_wells", state.waste)

    def test_manual_pause_is_disclosed(self):
        run, _ = self.analyze(_fresh_protocol().replace("p.delay(seconds=2)", "p.pause('Check the plate')\n    p.delay(seconds=2)"), "manual-pause")
        self.assertTrue(any("manual resume" in warning for warning in plan(run).warnings))

    def test_partial_nozzle_layout_is_explicitly_rejected(self):
        source = '''from opentrons import protocol_api
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def run(p):
    rack = p.load_labware("opentrons_flex_96_tiprack_50ul", "D1")
    pip = p.load_instrument("flex_8channel_50", "left", tip_racks=[rack])
    pip.configure_nozzle_layout(style=protocol_api.SINGLE, start="A1", tip_racks=[rack])
'''
        run, raw = self.analyze(source, "partial-nozzle")
        self.assertIn("configureNozzleLayout", [command["commandType"] for command in raw["commands"]])
        with self.assertRaisesRegex(ProtocolError, "partial nozzle layout"):
            plan(run)

    def test_known_underflow_and_destination_capacity_are_hard_errors(self):
        underflow = '''from opentrons import protocol_api
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def run(p):
    rack = p.load_labware("opentrons_flex_96_tiprack_50ul", "D1")
    reservoir = p.load_labware("nest_12_reservoir_15ml", "B3")
    liquid = p.define_liquid(name="Water", description="Water", display_color="#55aaff")
    reservoir["A1"].load_liquid(liquid, 5)
    pip = p.load_instrument("flex_1channel_50", "left", tip_racks=[rack])
    pip.pick_up_tip()
    pip.aspirate(10, reservoir["A1"])
'''
        run, _ = self.analyze(underflow, "underflow")
        with self.assertRaisesRegex(ProtocolError, "cannot aspirate"):
            plan(run)

        capacity = '''from opentrons import protocol_api
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def run(p):
    rack = p.load_labware("opentrons_flex_96_tiprack_50ul", "D1")
    reservoir = p.load_labware("nest_12_reservoir_15ml", "B3")
    plate = p.load_labware("nest_96_wellplate_200ul_flat", "C3")
    liquid = p.define_liquid(name="Water", description="Water", display_color="#55aaff")
    reservoir["A1"].load_liquid(liquid, 20)
    plate["A1"].load_liquid(liquid, 195)
    pip = p.load_instrument("flex_1channel_50", "left", tip_racks=[rack])
    pip.pick_up_tip()
    pip.aspirate(10, reservoir["A1"])
    pip.dispense(10, plate["A1"])
'''
        run, _ = self.analyze(capacity, "capacity")
        with self.assertRaisesRegex(ProtocolError, "capacity .* exceeded"):
            plan(run)

    def test_home_axes_and_unknown_motion_or_liquid_actions_are_rejected(self):
        run, _ = self.analyze(_fresh_protocol(), "home-axes")
        home = next(command for command in run.commands if command["commandType"] == "home")
        home["params"] = {"axes": ["leftZ", "extensionZ", "extensionJaw"]}
        planned = plan(run)
        self.assertTrue(any(key.phase == "axis home" for key in planned.keys))

        run, _ = self.analyze(_fresh_protocol(), "bad-axis")
        home = next(command for command in run.commands if command["commandType"] == "home")
        home["params"] = {"axes": ["not-a-flex-axis"]}
        with self.assertRaisesRegex(ProtocolError, "unsupported Flex home axes"):
            plan(run)

        for kind in ("futureMove", "futureAspirate"):
            run, _ = self.analyze(_fresh_protocol(), f"unsupported-{kind}")
            run.commands.append({"commandType": kind, "params": {}, "result": {}})
            with self.subTest(kind=kind), self.assertRaisesRegex(ProtocolError, "unsupported Flex replay action"):
                plan(run)

    def test_multichannel_waste_chute_and_tip_drop_baseline(self):
        run, _ = self.analyze(_multichannel_chute_protocol(), "multichannel-chute")
        planned = plan(run)
        self.assertTrue(run.chutes)
        self.assertIsNotNone(run.chute)
        plate = next(item for item in run.labware.values() if item.slot == "C3")
        state = planned.keys[-1].state
        self.assertEqual(
            [sum(state.wells[(plate.key, f"{row}1")].values()) for row in "ABCDEFGH"],
            [10.0] * 8,
        )
        self.assertEqual(state.tip_liquid["pipette_8"][0], {})
        self.assertTrue(any(key.phase == "eject" for key in planned.keys))

    def test_module_hold_is_exact_and_gripper_moves_labware(self):
        run, raw = self.analyze(_module_and_gripper_protocol(), "module-gripper")
        kinds = [command["commandType"] for command in raw["commands"]]
        self.assertIn("thermocycler/setTargetBlockTemperature", kinds)
        self.assertIn("thermocycler/waitForBlockTemperature", kinds)
        planned = plan(run)
        hold_index = next(
            index for index, key in enumerate(planned.keys)
            if key.phase == "thermocycler/holdBlock"
        )
        self.assertEqual(
            planned.keys[hold_index].t - planned.keys[hold_index - 1].t,
            3.0,
        )
        self.assertTrue(any(step.kind == "moveLabware" for step in planned.steps))
        self.assertTrue(any(key.phase == "grip" for key in planned.keys))
        plate = next(item for item in run.labware.values() if item.load_name == "nest_96_wellplate_200ul_flat")
        self.assertEqual(planned.keys[-1].state.parent[plate.key], ("slot", "C3"))
        self.assertIsNone(planned.keys[-1].state.held)

        # A new action in a known module family must not silently become a
        # generic visual beat.
        bad = copy.deepcopy(run)
        module_id = next(iter(bad.modules))
        bad.commands.append({"commandType": "thermocycler/futureAction", "params": {"moduleId": module_id}, "result": {}})
        with self.assertRaisesRegex(ProtocolError, "unsupported Flex module action"):
            plan(bad)


if __name__ == "__main__":
    unittest.main()

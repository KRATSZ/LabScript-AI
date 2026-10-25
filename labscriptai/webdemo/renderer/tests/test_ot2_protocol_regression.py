"""Long-lived OT-2 protocol regression tests.

The fixtures are small, independently authored protocol intents.  Every test
starts by running the real Opentrons 8.8.2 analyzer in a temporary directory,
then feeds that JSON to the renderer's real OT-2 loader and planner.  The
default suite is semantic and fast; MuJoCo XML/target/clearance checks are
opt-in with ``OT2_GEOMETRY=1`` because they generate a considerably larger
temporary model.
"""

from __future__ import annotations

import copy
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RENDERER_ROOT = Path(__file__).resolve().parents[1]
if str(RENDERER_ROOT) not in sys.path:
    sys.path.insert(0, str(RENDERER_ROOT))

from sim.flex_protocol import ProtocolError  # noqa: E402
from sim.ot2_protocol import (  # noqa: E402
    RETURN_TIP_SCALE,
    load_analysis,
    plan as make_plan,
    sample,
)
from sim.ot2_scene import load_deck  # noqa: E402


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
PROTOCOL_ROOT = FIXTURE_ROOT / "protocols"
EDGE_ROOT = FIXTURE_ROOT / "edge-protocols"
EXPECTATIONS_PATH = FIXTURE_ROOT / "expectations.json"
EDGE_EXPECTATIONS_PATH = FIXTURE_ROOT / "edge_expectations.json"
RETURN_EXPECTATIONS_PATH = FIXTURE_ROOT / "return_tip_expectations.json"
OPENTRONS_PYTHON = Path(os.environ.get("OPENTRONS_PYTHON", sys.executable))

_ANALYSIS_TEMP: tempfile.TemporaryDirectory[str] | None = None
_RAW: dict[str, dict] = {}
_ANALYSIS_PATHS: dict[str, Path] = {}
_PLANS: dict[str, object] = {}
_PLAN_ERRORS: dict[str, str] = {}
_ORACLE: dict = {}
_EDGE_ORACLE: dict = {}
_RETURN_ORACLE: dict = {}


def _fixture_paths() -> list[Path]:
    return sorted(PROTOCOL_ROOT.glob("*.py")) + sorted(EDGE_ROOT.glob("*.py"))


def _analysis_json(protocol: Path, destination: Path) -> dict:
    """Run the official analyzer and reject a false-positive exit code."""

    command = [
        str(OPENTRONS_PYTHON),
        "-m",
        "opentrons.cli",
        "analyze",
        "--check",
        "--json-output",
        str(destination),
        str(protocol),
    ]
    result = subprocess.run(
        command,
        cwd=str(RENDERER_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, PYTHONPATH=str(RENDERER_ROOT)),
    )
    if result.returncode != 0 or not destination.exists():
        raise AssertionError(
            "official Opentrons analyze failed for "
            f"{protocol.name} (exit {result.returncode})\n"
            f"stdout:\n{result.stdout[-4000:]}\nstderr:\n{result.stderr[-4000:]}"
        )
    raw = json.loads(destination.read_text())
    if raw.get("result") != "ok" or raw.get("errors"):
        raise AssertionError(
            f"official analyzer returned errors for {protocol.name}: "
            f"{raw.get('errors')!r}"
        )
    return raw


def _load_fixture_suite() -> None:
    global _ANALYSIS_TEMP, _ORACLE, _EDGE_ORACLE, _RETURN_ORACLE
    _ANALYSIS_TEMP = tempfile.TemporaryDirectory(prefix="labscriptai-ot2-analysis-")
    _ORACLE = json.loads(EXPECTATIONS_PATH.read_text())
    _EDGE_ORACLE = json.loads(EDGE_EXPECTATIONS_PATH.read_text())
    _RETURN_ORACLE = json.loads(RETURN_EXPECTATIONS_PATH.read_text())

    expected = set(_ORACLE["protocols"]) | set(_EDGE_ORACLE)
    actual = {path.name for path in _fixture_paths()}
    if actual != expected:
        raise AssertionError(f"fixture manifest differs from oracle: missing={expected - actual}, extra={actual - expected}")

    deck = load_deck()
    for protocol in _fixture_paths():
        analysis_path = Path(_ANALYSIS_TEMP.name) / f"{protocol.parent.name}-{protocol.stem}.json"
        raw = _analysis_json(protocol, analysis_path)
        _RAW[protocol.name] = raw
        _ANALYSIS_PATHS[protocol.name] = analysis_path
        try:
            _PLANS[protocol.name] = make_plan(load_analysis(analysis_path, deck))
        except ProtocolError as exc:
            if not _EDGE_ORACLE.get(protocol.name, {}).get("expected_plan_error"):
                raise
            _PLAN_ERRORS[protocol.name] = str(exc)


def setUpModule() -> None:
    _load_fixture_suite()


def tearDownModule() -> None:
    if _ANALYSIS_TEMP is not None:
        _ANALYSIS_TEMP.cleanup()


def _freeze(value):
    """Stable comparison representation for nested planner state."""

    if isinstance(value, dict):
        return tuple(sorted((str(k), _freeze(v)) for k, v in value.items()))
    if isinstance(value, (set, frozenset)):
        return tuple(sorted(_freeze(v) for v in value))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, float):
        return round(value, 8)
    return value


def _state_signature(state) -> tuple:
    return (
        _freeze(state.wells),
        _freeze(state.rack),
        _freeze(state.mounted),
        _freeze(state.tip_liquid),
        _freeze(getattr(state, "tip_air", {})),
        _freeze(getattr(state, "tip_front_air", {})),
        _freeze(getattr(state, "release_mm", {})),
        _freeze(getattr(state, "waste", {})),
    )


def _volume(mix: dict[str, float] | None) -> float:
    return sum((mix or {}).values())


def _well_for(plan_, expected: dict) -> tuple[str, str]:
    slot = str(expected["slot"])
    load_name = expected["load_name"]
    for labware in plan_.run.labware.values():
        if labware.slot == slot and labware.load_name == load_name:
            return labware.key, expected["well"]
    raise AssertionError(f"fixture labware not found: slot {slot}, {load_name}")


def _expected_volume(record: dict) -> float:
    return float(record.get("volume", record.get("volume_each")))


def _initial_liquid_totals(raw: dict) -> dict[str, float]:
    totals: dict[str, float] = {}
    for command in raw["commands"]:
        if command["commandType"] != "loadLiquid":
            continue
        liquid = command["params"]["liquidId"]
        totals[liquid] = totals.get(liquid, 0.0) + sum(command["params"]["volumeByWell"].values())
    return totals


def _final_liquid_totals(plan_) -> dict[str, float]:
    state = plan_.keys[-1].state
    totals: dict[str, float] = {}
    for mix in state.wells.values():
        for liquid, volume in mix.items():
            totals[liquid] = totals.get(liquid, 0.0) + volume
    for tool_mixes in state.tip_liquid.values():
        for mix in tool_mixes:
            for liquid, volume in mix.items():
                totals[liquid] = totals.get(liquid, 0.0) + volume
    for mix in getattr(state, "waste", {}).values():
        for liquid, volume in mix.items():
            totals[liquid] = totals.get(liquid, 0.0) + volume
    return totals


def _plan_for(name: str):
    return _PLANS[name]


class OT2SemanticRegressionTests(unittest.TestCase):
    """Checks that can run without compiling the MuJoCo geometry."""

    def test_fixture_manifest_and_official_analyzer(self) -> None:
        self.assertEqual(set(_RAW), {path.name for path in _fixture_paths()})
        for name, raw in _RAW.items():
            self.assertEqual(raw.get("robotType"), "OT-2 Standard", name)
            self.assertEqual(raw.get("result"), "ok", name)
            self.assertFalse(raw.get("errors"), name)

    def test_final_volumes_match_independent_oracle_and_conserve_liquid(self) -> None:
        for name, expected in _ORACLE["protocols"].items():
            plan_ = _plan_for(name)
            final = plan_.keys[-1].state
            for record in expected["final_volumes_ul"]:
                wells = record.get("wells") or [record["well"]]
                for well in wells:
                    one = dict(record, well=well)
                    key, well_name = _well_for(plan_, one)
                    actual = _volume(final.wells.get((key, well_name)))
                    self.assertAlmostEqual(
                        actual,
                        _expected_volume(record),
                        places=5,
                        msg=f"{name}: {record['load_name']} {well}",
                    )
            initial = _initial_liquid_totals(_RAW[name])
            final_totals = _final_liquid_totals(plan_)
            self.assertEqual(set(initial), set(final_totals), name)
            for liquid, volume in initial.items():
                self.assertAlmostEqual(volume, final_totals[liquid], places=5, msg=f"{name}: {liquid}")

    def test_explicit_waits_are_preserved(self) -> None:
        for name, expected in _ORACLE["protocols"].items():
            wanted = [float(item["seconds"]) for item in expected.get("explicit_waits", [])]
            actual = [
                float(command["params"]["seconds"])
                for command in _RAW[name]["commands"]
                if command["commandType"] == "waitForDuration"
            ]
            # The thermocycler API represents an explicit hold as
            # setTargetBlockTemperature(..., hold_time_seconds=...), followed
            # by waitForBlockTemperature; it is not a waitForDuration command.
            if name == "thermocycler.py":
                actual.extend(
                    float(command["params"]["holdTimeSeconds"])
                    for command in _RAW[name]["commands"]
                    if command["commandType"] == "thermocycler/setTargetBlockTemperature"
                )
            self.assertEqual(actual, wanted, name)

        edge = _EDGE_ORACLE["no_tip_motion.py"]
        waits = [
            float(command["params"]["seconds"])
            for command in _RAW["no_tip_motion.py"]["commands"]
            if command["commandType"] == "waitForDuration"
        ]
        self.assertEqual(waits, edge["explicit_wait_seconds"])

    def test_air_gap_is_not_counted_as_liquid(self) -> None:
        name = "single_p20.py"
        expected = _ORACLE["protocols"][name]["air_liquid"]
        raw = _RAW[name]
        aspirates = [c for c in raw["commands"] if c["commandType"] == "aspirate"]
        self.assertEqual([c["params"]["volume"] for c in aspirates], [10, 2])
        self.assertNotIn("airGap", [c["commandType"] for c in raw["commands"]])
        self.assertNotIn("aspirateInPlace", [c["commandType"] for c in raw["commands"]])

        plan_ = _plan_for(name)
        air_keys = [key for key in plan_.keys if key.phase == "aspirate air"]
        self.assertEqual(len(air_keys), 1)
        air_state = air_keys[0].state
        tool = next(iter(plan_.run.pipettes.values())).tool
        self.assertAlmostEqual(sum(air_state.tip_liquid[tool][0].values()), expected["liquid_ul"])
        self.assertAlmostEqual(air_state.tip_air[tool][0], expected["air_gap_ul"])

        destination = next(
            record for record in _ORACLE["protocols"][name]["final_volumes_ul"] if record["slot"] == "2"
        )
        key, well = _well_for(plan_, destination)
        self.assertAlmostEqual(_volume(plan_.keys[-1].state.wells[(key, well)]), expected["liquid_ul"])
        self.assertEqual(expected["dispense_command_ul"], 12)

    def test_return_tip_restores_three_rack_categories(self) -> None:
        for name, expected in _RETURN_ORACLE["cases"].items():
            plan_ = _plan_for(name)
            pipette = next(iter(plan_.run.pipettes.values()))
            self.assertEqual(pipette.name, expected["pipette"], name)
            self.assertAlmostEqual(RETURN_TIP_SCALE[pipette.name], expected["scale"], places=8, msg=name)

            rack = expected["rack"]
            initial_rack = plan_.keys[0].state.rack[rack]
            final_rack = plan_.keys[-1].state.rack[rack]
            self.assertEqual(final_rack, initial_rack, name)
            return_keys = [key for key in plan_.keys if key.phase == "return tip"]
            self.assertEqual(len(return_keys), 1, name)
            self.assertGreater(return_keys[0].state.release_mm[pipette.tool], 0.0, name)
            self.assertTrue(
                any(where.startswith("returned_tip:") for where in return_keys[0].state.waste),
                name,
            )

    def test_module_only_and_no_tip_motion(self) -> None:
        module_run = _plan_for("module_only.py").run
        self.assertEqual(len(module_run.pipettes), _EDGE_ORACLE["module_only.py"]["pipettes"])
        self.assertEqual(len(_plan_for("module_only.py").arrivals), 0)

        no_tip_plan = _plan_for("no_tip_motion.py")
        self.assertEqual(len(no_tip_plan.run.pipettes), 1)
        kinds = [command["commandType"] for command in _RAW["no_tip_motion.py"]["commands"]]
        self.assertNotIn("pickUpTip", kinds)
        self.assertNotIn("dropTip", kinds)
        self.assertNotIn("pickUpTip", [step.kind for step in no_tip_plan.steps])
        self.assertNotIn("dropTip", [step.kind for step in no_tip_plan.steps])

    def test_api_224_air_gap_retain_and_absolute_coordinate_dispense(self) -> None:
        expected = _EDGE_ORACLE["air_gap_224.py"]
        plan_ = _plan_for("air_gap_224.py")
        raw = _RAW["air_gap_224.py"]
        api_version = raw.get("config", {}).get("apiVersion")
        self.assertEqual(".".join(str(value) for value in api_version), expected["api_level"])
        self.assertIn("airGapInPlace", [command["commandType"] for command in raw["commands"]])
        pipette_tool = next(iter(plan_.run.pipettes.values())).tool
        air_states = [
            key.state
            for key in plan_.keys
            if abs(key.state.tip_air[pipette_tool][0] - expected["air_gap_ul"]) < 1e-6
        ]
        self.assertTrue(air_states)
        self.assertAlmostEqual(sum(air_states[-1].tip_liquid[pipette_tool][0].values()), 10.0)

        source_key, source_well = _well_for(plan_, expected["source"])
        destination_key, destination_well = _well_for(plan_, expected["destination"])
        final = plan_.keys[-1].state
        self.assertAlmostEqual(_volume(final.wells[(source_key, source_well)]), expected["source"]["volume"])
        self.assertAlmostEqual(_volume(final.wells[(destination_key, destination_well)]), expected["destination"]["volume"])
        returned = final.waste.get("returned_tip:lw1/A1", {})
        self.assertAlmostEqual(_volume(returned), expected["return_tip_remaining_liquid_ul"])

        absolute = _plan_for("absolute_move.py")
        absolute_expected = _EDGE_ORACLE["absolute_move.py"]
        absolute_raw = _RAW["absolute_move.py"]
        move = next(command for command in absolute_raw["commands"] if command["commandType"] == "moveToCoordinates")
        self.assertEqual(
            [move["params"]["coordinates"][axis] for axis in ("x", "y", "z")],
            absolute_expected["absolute_coordinates_mm"],
        )
        self.assertIn("moveToCoordinates", [command["commandType"] for command in absolute_raw["commands"]])
        absolute_source_key, absolute_source_well = _well_for(absolute, absolute_expected["source"])
        self.assertAlmostEqual(
            _volume(absolute.keys[-1].state.wells[(absolute_source_key, absolute_source_well)]),
            absolute_expected["source"]["volume"],
        )
        self.assertAlmostEqual(
            _volume(absolute.keys[-1].state.waste.get("outside_wells", {})),
            absolute_expected["outside_wells_ul"],
        )

    def test_unsupported_manual_move_is_rejected(self) -> None:
        raw = _RAW["manual_move.py"]
        self.assertIn(_EDGE_ORACLE["manual_move.py"]["unsupported_command"], [command["commandType"] for command in raw["commands"]])
        self.assertIn("manual_move.py", _PLAN_ERRORS)
        self.assertRegex(_PLAN_ERRORS["manual_move.py"], "moveLabware")

    def test_review_mixed_rack_air(self) -> None:
        for name in ("mixed_rack_air.py", "mixed_rack_air_reachable.py"):
            with self.subTest(protocol=name):
                self._check_mixed_rack_air(name)

    def _check_mixed_rack_air(self, mixed_name) -> None:
        mixed = _plan_for(mixed_name)
        mixed_expected = _EDGE_ORACLE[mixed_name]
        mixed_api = _RAW[mixed_name]["config"]["apiVersion"]
        self.assertEqual(".".join(str(value) for value in mixed_api), mixed_expected["api_level"])
        source_key, source_well = _well_for(mixed, mixed_expected["source"])
        destination_key, destination_well = _well_for(mixed, mixed_expected["destination"])
        final = mixed.keys[-1].state
        self.assertAlmostEqual(_volume(final.wells[(source_key, source_well)]), mixed_expected["source"]["volume"])
        self.assertAlmostEqual(_volume(final.wells[(destination_key, destination_well)]), mixed_expected["destination"]["volume"])
        tool = next(iter(mixed.run.pipettes.values())).tool
        self.assertTrue(any(abs(air - mixed_expected["air_gap_ul"]) < 1e-6 for key in mixed.keys for air in key.state.tip_air[tool]))
        self.assertAlmostEqual(
            _volume(final.waste.get("returned_tip:lw1/A1", {})),
            mixed_expected["return_tip_remaining_liquid_ul"],
        )

    def test_review_plunger_home(self) -> None:
        plunger_name = "plunger_home.py"
        plunger = _plan_for(plunger_name)
        plunger_expected = _EDGE_ORACLE[plunger_name]
        plunger_home = next(command for command in _RAW[plunger_name]["commands"] if command["commandType"] == "home" and command["params"].get("axes"))
        self.assertEqual(plunger_home["params"]["axes"], plunger_expected["home_axes"])
        self.assertEqual(
            [command["params"]["seconds"] for command in _RAW[plunger_name]["commands"] if command["commandType"] == "waitForDuration"],
            [plunger_expected["wait_seconds"]],
        )
        command_index = next(index for index, command in enumerate(_RAW[plunger_name]["commands"])
                             if command["commandType"] == "home" and command["params"].get("axes"))
        keys = [(index, key) for index, key in enumerate(plunger.keys) if key.cmd == command_index]
        self.assertTrue(keys)
        before = plunger.keys[keys[0][0] - 1].q
        self.assertTrue(all(key.q == before for _, key in keys))

    def test_review_reset_tips(self) -> None:
        reset_name = "reset_tips.py"
        reset = _plan_for(reset_name)
        reset_expected = _EDGE_ORACLE[reset_name]
        reset_raw = _RAW[reset_name]
        self.assertEqual(
            sum(command["commandType"] == "pickUpTip" for command in reset_raw["commands"]),
            reset_expected["tip_pickups"],
        )
        self.assertEqual(
            sum(command["commandType"] in {"dropTip", "dropTipInPlace"} for command in reset_raw["commands"]),
            reset_expected["tip_drops"],
        )
        set_tip = next(command for command in reset_raw["commands"] if command["commandType"] == "setTipState")
        self.assertEqual(set_tip["params"]["tipWellState"], reset_expected["reset_tip_state"])
        self.assertTrue(any("manual resume" in warning for warning in reset.warnings))
        command_index = next(index for index, command in enumerate(reset_raw["commands"]) if command["commandType"] == "setTipState")
        restored = [key for key in reset.keys if key.cmd == command_index][-1].state
        rack_key = next(iter(restored.rack))
        self.assertEqual(len(restored.rack[rack_key]), 96)
        plate_key, plate_well = _well_for(reset, reset_expected["destination"])
        self.assertAlmostEqual(_volume(reset.keys[-1].state.wells[(plate_key, plate_well)]), 10.0)

    def test_api_224_thermocycler_fixture_matches_hold_oracle(self) -> None:
        name = "thermal_224.py"
        raw = _RAW[name]
        expected = _EDGE_ORACLE[name]
        self.assertEqual(".".join(str(value) for value in raw["config"]["apiVersion"]), expected["api_level"])
        block = next(command for command in raw["commands"] if command["commandType"] == "thermocycler/setTargetBlockTemperature")
        self.assertEqual(block["params"]["celsius"], expected["block_temperature_c"])
        self.assertEqual(block["params"]["holdTimeSeconds"], expected["hold_seconds"][0])
        plan_ = _plan_for(name)
        hold_key = next(key for key in plan_.keys if key.phase == "thermocycler/holdBlock")
        index = plan_.keys.index(hold_key)
        self.assertAlmostEqual(hold_key.t - plan_.keys[index - 1].t, expected["hold_seconds"][0])

    def test_thermocycler_block_hold_and_profile(self) -> None:
        module_name = "module_only.py"
        module_raw = _RAW[module_name]
        block = next(command for command in module_raw["commands"] if command["commandType"] == "thermocycler/setTargetBlockTemperature")
        self.assertEqual(block["params"]["celsius"], _EDGE_ORACLE[module_name]["block_temperature_c"])
        self.assertEqual(block["params"]["holdTimeSeconds"], _EDGE_ORACLE[module_name]["hold_seconds"][0])
        hold_keys = [key for key in _plan_for(module_name).keys if key.phase == "thermocycler/holdBlock"]
        self.assertEqual(len(hold_keys), 1)
        hold_index = _plan_for(module_name).keys.index(hold_keys[0])
        previous_key = _plan_for(module_name).keys[hold_index - 1]
        self.assertAlmostEqual(hold_keys[0].t - previous_key.t, 2.0)

        profile_name = "thermal_profile.py"
        profile_cmd = next(command for command in _RAW[profile_name]["commands"] if command["commandType"] == "thermocycler/runProfile")
        profile = profile_cmd["params"]["profile"]
        expected = _EDGE_ORACLE[profile_name]
        self.assertEqual([step["celsius"] for step in profile], expected["profile_celsius"])
        self.assertEqual([step["holdSeconds"] for step in profile], expected["profile_hold_seconds"])
        plan_ = _plan_for(profile_name)
        hold_keys = [key for key in plan_.keys if key.phase.startswith("thermocycler/holdProfile/")]
        self.assertEqual(len(hold_keys), len(expected["profile_hold_seconds"]))
        durations = []
        for key in hold_keys:
            index = plan_.keys.index(key)
            durations.append(round(key.t - plan_.keys[index - 1].t, 8))
        self.assertEqual(durations, expected["profile_hold_seconds"])

    def test_sample_seek_order_is_deterministic(self) -> None:
        names = ["single_p20.py", "eight_p300.py", "p1000_single_gen2_return.py", "thermal_profile.py"]
        for name in names:
            plan_ = _plan_for(name)
            times = [0.0, plan_.duration * 0.37, plan_.duration * 0.83, plan_.duration]
            for t in times:
                q_a, state_a, index_a = sample(plan_, t)
                for other_t in reversed(times):
                    sample(plan_, other_t)
                q_b, state_b, index_b = sample(plan_, t)
                self.assertEqual(index_a, index_b, name)
                self.assertEqual(_freeze(q_a), _freeze(q_b), name)
                self.assertEqual(_state_signature(state_a), _state_signature(state_b), name)

    def test_invalid_inventory_capacity_and_slot_are_rejected(self) -> None:
        base = copy.deepcopy(_RAW["single_p20.py"])
        source = next(command for command in base["commands"] if command["commandType"] == "loadLiquid")
        source["params"]["volumeByWell"]["A1"] = 5
        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-invalid-") as td:
            path = Path(td) / "underflow.json"
            path.write_text(json.dumps(base))
            with self.assertRaises(ProtocolError):
                make_plan(load_analysis(path, load_deck()))

        too_large_tip = copy.deepcopy(_RAW["single_p20.py"])
        first_aspirate = next(command for command in too_large_tip["commands"] if command["commandType"] == "aspirate")
        first_aspirate["params"]["volume"] = 21
        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-invalid-") as td:
            path = Path(td) / "tip-capacity.json"
            path.write_text(json.dumps(too_large_tip))
            with self.assertRaises(ProtocolError):
                make_plan(load_analysis(path, load_deck()))

        destination_over_capacity = copy.deepcopy(_RAW["single_p20.py"])
        loads = [command for command in destination_over_capacity["commands"] if command["commandType"] == "loadLiquid"]
        destination = next(command for command in destination_over_capacity["commands"] if command["commandType"] == "loadLabware" and command["params"]["location"].get("slotName") == "2")
        extra = copy.deepcopy(loads[0])
        extra["params"]["labwareId"] = destination["result"]["labwareId"]
        extra["params"]["volumeByWell"] = {"A1": 195}
        destination_over_capacity["commands"].insert(destination_over_capacity["commands"].index(loads[0]) + 1, extra)
        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-invalid-") as td:
            path = Path(td) / "destination-capacity.json"
            path.write_text(json.dumps(destination_over_capacity))
            with self.assertRaises(ProtocolError):
                make_plan(load_analysis(path, load_deck()))

        bad_slot = copy.deepcopy(_RAW["single_p20.py"])
        bad_load = next(command for command in bad_slot["commands"] if command["commandType"] == "loadLabware")
        bad_load["params"]["location"]["slotName"] = "99"
        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-invalid-") as td:
            path = Path(td) / "bad-slot.json"
            path.write_text(json.dumps(bad_slot))
            with self.assertRaises(ProtocolError):
                load_analysis(path, load_deck())

        unknown_command = copy.deepcopy(_RAW["single_p20.py"])
        unknown_command["commands"].insert(1, {"commandType": "notARealOT2Command", "params": {}, "result": {}})
        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-invalid-") as td:
            path = Path(td) / "unknown-command.json"
            path.write_text(json.dumps(unknown_command))
            with self.assertRaises(ProtocolError):
                make_plan(load_analysis(path, load_deck()))


class OT2GeometryRegressionTests(unittest.TestCase):
    """Optional MuJoCo checks; enabled explicitly with ``OT2_GEOMETRY=1``."""

    def setUp(self) -> None:
        if os.environ.get("OT2_GEOMETRY", "").lower() not in {"1", "true", "yes"}:
            self.skipTest("set OT2_GEOMETRY=1 for temporary XML, target and clearance checks")
        try:
            import mujoco  # noqa: F401
        except ImportError as exc:
            self.skipTest(f"MuJoCo is not installed: {exc}")

    @staticmethod
    def _scene(name: str, folder: Path):
        import mujoco

        from sim.ot2_protocol import scene_spec
        from sim.ot2_scene import write_spec_model
        from sim.play_ot2_protocol import Scene

        protocol_folder = folder / Path(name).stem
        protocol_folder.mkdir()
        xml = write_spec_model(load_deck(), scene_spec(_plan_for(name)), protocol_folder)
        model = mujoco.MjModel.from_xml_path(str(xml))
        data = mujoco.MjData(model)
        return Scene(_plan_for(name), model, data)

    def test_targets_and_clearance_for_all_fixtures(self) -> None:
        from sim.play_ot2_protocol import check_clearance, check_targets

        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-geometry-") as td:
            folder = Path(td)
            for name in _RAW:
                if _EDGE_ORACLE.get(name, {}).get("expected_plan_error"):
                    continue  # The semantic suite asserts the explicit rejection.
                with self.subTest(protocol=name):
                    scene = self._scene(name, folder)
                    check_targets(_plan_for(name), scene)
                    expected_error = _EDGE_ORACLE.get(name, {}).get("expected_clearance_error")
                    if expected_error:
                        with self.assertRaisesRegex(RuntimeError, expected_error):
                            check_clearance(_plan_for(name), scene)
                    else:
                        check_clearance(_plan_for(name), scene)

    def test_bad_json_position_is_rejected_by_target_check(self) -> None:
        import mujoco

        from sim.ot2_protocol import scene_spec
        from sim.ot2_scene import write_spec_model
        from sim.play_ot2_protocol import Scene, check_targets

        raw = copy.deepcopy(_RAW["single_p20.py"])
        positional = next(command for command in raw["commands"] if "position" in (command.get("result") or {}))
        positional["result"]["position"]["z"] += 5.0
        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-position-") as td:
            path = Path(td) / "bad-position.json"
            path.write_text(json.dumps(raw))
            plan_ = make_plan(load_analysis(path, load_deck()))
            xml = write_spec_model(load_deck(), scene_spec(plan_), Path(td) / "model")
            model = mujoco.MjModel.from_xml_path(str(xml))
            with self.assertRaises(RuntimeError):
                check_targets(plan_, Scene(plan_, model, mujoco.MjData(model)))

    def test_mujoco_seek_order_is_stable(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory(prefix="labscriptai-ot2-seek-") as td:
            for name in ("single_p20.py", "eight_p300.py", "p1000_single_gen2_return.py"):
                with self.subTest(protocol=name):
                    scene = self._scene(name, Path(td))
                    plan_ = _plan_for(name)
                    times = [0.0, plan_.duration * 0.31, plan_.duration * 0.79, plan_.duration]
                    for t in times:
                        q_a, _ = scene.at(t)
                        qpos_a = scene.data.qpos.copy()
                        for other_t in reversed(times):
                            scene.at(other_t)
                        q_b, _ = scene.at(t)
                        self.assertTrue(np.allclose(qpos_a, scene.data.qpos, atol=1e-9), name)
                        self.assertEqual(_freeze(q_a), _freeze(q_b), name)

    def test_thermocycler_lid_keeps_its_hinge_and_all_skins(self) -> None:
        import mujoco
        import numpy as np
        from sim.ot2_thermocycler import thermocycler_v1_dynamic_names, thermocycler_v1_layout

        with tempfile.TemporaryDirectory(prefix="labscriptai-tc-hinge-") as td:
            scene = self._scene("thermocycler.py", Path(td))
            plan_ = _plan_for("thermocycler.py")
            mod = next(iter(plan_.run.modules.values()))
            prefix = f"mod_{mod.slot}_{mod.model}"
            gid = scene.model.geom(f"{prefix}_lid").id
            mid = int(scene.model.geom_dataid[gid])
            layout = thermocycler_v1_layout(mod.definition, mod.child)
            pivot = np.array(layout.hinge_pivot) * .001
            closed_center = np.array([layout.panel_center_x_mm, layout.hinge_y_mm - layout.panel_length_mm / 2, layout.closed_center_z_mm]) * .001
            local_pivot = pivot - closed_center
            # Use the action window: its displayed step may also contain the
            # preceding tool retraction and XY move out of the lid's sweep.
            event = scene.module_anim[mod.id]["events"][0]
            for time in np.linspace(event[0], event[1], 31):
                scene.at(float(time))
                rotation = np.empty(9)
                mujoco.mju_quat2Mat(rotation, scene.model.geom_quat[gid])
                ref_rot = np.empty(9)
                mujoco.mju_quat2Mat(ref_rot, scene.model.mesh_quat[mid])
                source_rot = rotation.reshape(3, 3) @ ref_rot.reshape(3, 3).T
                source_center = scene.model.geom_pos[gid] - source_rot @ scene.model.mesh_pos[mid]
                np.testing.assert_allclose(source_center + source_rot @ local_pivot, pivot, atol=1e-8)
                for name in thermocycler_v1_dynamic_names(prefix):
                    skin = scene.model.geom(name).id
                    self.assertGreater(scene.model.geom_rgba[skin, 3], 0)
                    skin_mesh = int(scene.model.geom_dataid[skin])
                    skin_rot, skin_ref = np.empty(9), np.empty(9)
                    mujoco.mju_quat2Mat(skin_rot, scene.model.geom_quat[skin])
                    mujoco.mju_quat2Mat(skin_ref, scene.model.mesh_quat[skin_mesh])
                    np.testing.assert_allclose(skin_rot.reshape(3, 3) @ skin_ref.reshape(3, 3).T, source_rot, atol=1e-8)
            scene.at(event[1])
            start, count = int(scene.model.mesh_vertadr[mid]), int(scene.model.mesh_vertnum[mid])
            world = scene.model.mesh_vert[start:start + count] @ scene.data.geom_xmat[gid].reshape(3, 3).T + scene.data.geom_xpos[gid]
            body = int(scene.model.geom_bodyid[gid])
            self.assertAlmostEqual(float(world[:, 2].max() - scene.data.xpos[body, 2]) * 1000, 312, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

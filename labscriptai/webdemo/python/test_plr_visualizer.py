from __future__ import annotations

import unittest

from labscriptai.planir.schema import PLAN_SCHEMA_ID, load_plan
from plr_visualizer import _robot_kind, build_liquid_handler

DEMO = {
    "schema": PLAN_SCHEMA_ID,
    "plan_id": "demo-transfer",
    "backend": "serializing",
    "resources": [
        {"id": "tips", "type": "tiprack", "slot": "1"},
        {"id": "plate", "type": "plate", "slot": "2", "max_volume_ul": 200},
    ],
    "initial_volumes_ul": {"plate:A1": 100, "plate:B1": 0},
    "steps": [
        {"step_id": "1", "primitive_type": "PICK_TIPS", "tip_rack": "tips", "tip_positions": ["A1"], "dependencies": []},
        {"step_id": "2", "primitive_type": "ASPIRATE", "source": "plate:A1", "volume_ul": 50, "dependencies": ["1"]},
        {"step_id": "3", "primitive_type": "DISPENSE", "destination": "plate:B1", "volume_ul": 50, "dependencies": ["2"]},
        {"step_id": "4", "primitive_type": "DROP_TIPS", "to_waste": True, "dependencies": ["3"]},
    ],
}


class PlrVisualizerTests(unittest.TestCase):
    def test_robot_kind_maps_display_names(self) -> None:
        self.assertEqual(_robot_kind("Hamilton"), "star")
        self.assertEqual(_robot_kind("Vantage"), "vantage")
        self.assertEqual(_robot_kind("Tecan"), "fluent")
        self.assertEqual(_robot_kind("Tecan Fluent"), "fluent")

    def test_plate_a1_is_the_back_left_well(self) -> None:
        from pylabrobot.resources import Cor_96_wellplate_360ul_Fb

        plate = Cor_96_wellplate_360ul_Fb("plate")
        a1 = plate["A1"][0]
        h1 = plate["H1"][0]
        a12 = plate["A12"][0]
        self.assertGreater(a1.location.y, h1.location.y)
        self.assertLess(a1.location.x, a12.location.x)

    def test_starlet_and_evo_decks(self) -> None:
        plan = load_plan(DEMO)
        star = build_liquid_handler(plan, "Hamilton")
        self.assertEqual(star["kind"], "star")
        self.assertIn("STARLet", star["deck_name"])
        self.assertIn("tips", star["placed"])
        vantage = build_liquid_handler(plan, "Vantage")
        self.assertEqual(vantage["kind"], "vantage")
        self.assertIn("Vantage", vantage["deck_name"])
        fluent = build_liquid_handler(plan, "Tecan")
        self.assertEqual(fluent["kind"], "fluent")
        self.assertIn("Fluent", fluent["deck_name"])
        self.assertNotIn("EVO 200", fluent["deck_name"])
        self.assertEqual(fluent["note"], "")

    def test_fluent_places_reservoir_as_tecan_labware(self) -> None:
        payload = {
            **DEMO,
            "resources": [
                *DEMO["resources"],
                {"id": "reservoir", "type": "reservoir", "slot": "3"},
            ],
        }
        fluent = build_liquid_handler(load_plan(payload), "Tecan Fluent")
        self.assertIn("reservoir", fluent["placed"])
        self.assertLessEqual(max(fluent["rails"].values()), 69)


if __name__ == "__main__":
    unittest.main()

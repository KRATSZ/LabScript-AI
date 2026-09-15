from __future__ import annotations

import unittest

from pylabrobot_backend import (
    normalize_robot_model,
    plan_volume_error,
    robot_model_from_yaml,
)


class PylabrobotBackendTests(unittest.TestCase):
    def test_tecan_display_name_is_not_hamilton(self) -> None:
        self.assertEqual(normalize_robot_model("Tecan Freedom EVO"), "tecan_evo")
        self.assertEqual(normalize_robot_model("Tecan Fluent"), "tecan_fluent")
        self.assertEqual(normalize_robot_model("Hamilton STAR"), "hamilton_star")
        self.assertEqual(normalize_robot_model("Hamilton Vantage"), "hamilton_vantage")
        self.assertEqual(
            robot_model_from_yaml("robot_model: Tecan Freedom EVO\nresources: {}"),
            "tecan_evo",
        )
        self.assertNotEqual(
            robot_model_from_yaml("robot_model: Tecan Freedom EVO"),
            "hamilton_star",
        )

    def test_volume_gate_rejects_5000_keeps_20(self) -> None:
        small = {
            "steps": [
                {"primitive_type": "ASPIRATE", "volume_ul": 20},
                {"primitive_type": "DISPENSE", "volume_ul": 20},
            ]
        }
        huge = {
            "steps": [
                {"primitive_type": "ASPIRATE", "volume_ul": 5000},
                {"primitive_type": "DISPENSE", "volume_ul": 5000},
            ]
        }
        self.assertIsNone(plan_volume_error(small, "Tecan Fluent"))
        err = plan_volume_error(huge, "Tecan Freedom EVO")
        self.assertIsNotNone(err)
        self.assertIn("5000", err or "")
        self.assertIn("1000", err or "")


if __name__ == "__main__":
    unittest.main()

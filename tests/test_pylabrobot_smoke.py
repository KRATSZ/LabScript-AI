from __future__ import annotations

import unittest

from test_labflow_ir import minimal_transfer_ir

from labscriptai.ir.pylabrobot_smoke import (
    run_pylabrobot_opentrons_simulator_smoke,
    run_pylabrobot_serializing_smoke,
)


class PyLabRobotSmokeTests(unittest.TestCase):
    def test_labflow_ir_runs_through_real_pylabrobot_serializing_backend(self) -> None:
        try:
            import pylabrobot  # noqa: F401
        except ImportError:
            self.skipTest("PyLabRobot is not installed; run with `uv run --with pylabrobot ...`")

        result = run_pylabrobot_serializing_smoke(minimal_transfer_ir())

        self.assertTrue(result["ok"])
        self.assertEqual(result["pylabrobot_command_count"], 4)
        self.assertEqual(
            result["pylabrobot_commands"],
            ["pick_up_tips", "aspirate", "dispense", "drop_tips"],
        )

    def test_labflow_ir_maps_to_multiple_real_pylabrobot_platform_resources(self) -> None:
        try:
            import pylabrobot  # noqa: F401
        except ImportError:
            self.skipTest("PyLabRobot is not installed; run with `uv run --with pylabrobot ...`")

        results = {
            platform: run_pylabrobot_serializing_smoke(minimal_transfer_ir(), platform=platform)
            for platform in ("opentrons", "hamilton", "tecan")
        }

        for result in results.values():
            self.assertTrue(result["ok"])
            self.assertEqual(
                result["pylabrobot_commands"],
                ["pick_up_tips", "aspirate", "dispense", "drop_tips"],
            )
        self.assertEqual(results["opentrons"]["resource_classes"]["tips"], "TipRack")
        self.assertEqual(results["hamilton"]["resource_classes"]["tips"], "TipRack")
        self.assertEqual(results["tecan"]["resource_classes"]["tips"], "TecanTipRack")
        self.assertEqual(results["tecan"]["resource_classes"]["plate"], "TecanPlate")

    def test_labflow_ir_runs_through_real_pylabrobot_opentrons_simulator(self) -> None:
        try:
            import pylabrobot  # noqa: F401
        except ImportError:
            self.skipTest("PyLabRobot is not installed; run with `uv run --with pylabrobot ...`")

        result = run_pylabrobot_opentrons_simulator_smoke(minimal_transfer_ir())

        self.assertTrue(result["ok"])
        self.assertEqual(result["backend"], "opentrons_ot2_simulator")
        self.assertEqual(result["simulated_action_count"], 4)
        self.assertEqual(
            result["simulated_actions"],
            ["pick_up_tip", "aspirate", "dispense", "drop_tip"],
        )
        self.assertFalse(result["left_pipette_has_tip"])
        self.assertIn("1: tips", result["deck_summary"])
        self.assertIn("2: plate", result["deck_summary"])


if __name__ == "__main__":
    unittest.main()

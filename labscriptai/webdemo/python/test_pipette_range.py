import unittest
from unittest.mock import patch
from pipette_range import evaluate_pipette_ranges
from eval_logicpass import apply_pipette_range_gate
from eval_plan import attach_pipette_range_gate


def analyze(name="p1000_single_flex", volume=2, configure=None):
    commands = []
    if configure is not None:
        commands.append({"commandType": "configureForVolume", "params": {"pipetteId": "p", "volume": configure}})
    commands.append({"commandType": "aspirate", "params": {"pipetteId": "p", "volume": volume}})
    return {"pipettes": [{"id": "p", "pipetteName": name}], "commands": commands}


class RangeTests(unittest.TestCase):
    def test_flex_default_min_and_max(self):
        for v, outcome in [(2, "fail"), (5, "pass"), (1000, "pass"), (1001, "fail"), (-1, "fail"), (0, "pass")]:
            with self.subTest(v=v):
                self.assertEqual(evaluate_pipette_ranges(analyze(volume=v))["outcome"], outcome)

    def test_aliases_ot2_and_volume_modes(self):
        cases = [("flex_1channel_1000", 2, None, "fail"), ("p300_single_gen2", 2, None, "fail"),
                 ("p300_single_gen2", 20, None, "pass"), ("flex_1channel_50", 2, None, "fail"),
                 ("flex_1channel_50", 2, 2, "pass"), ("p50_single_flex", 40, 2, "fail"),
                 ("p50_single_flex", 40, 40, "pass")]
        for name, volume, mode, outcome in cases:
            with self.subTest(name=name, volume=volume, mode=mode):
                self.assertEqual(evaluate_pipette_ranges(analyze(name, volume, mode))["outcome"], outcome)

    def test_missing_unknown_and_unused_hardware(self):
        for name in ["made_up", ""]:
            self.assertEqual(evaluate_pipette_ranges(analyze(name))["outcome"], "unevaluable")
        a = analyze(volume=50)
        a["pipettes"].append({"id": "unused", "pipetteName": "unknown"})
        self.assertEqual(evaluate_pipette_ranges(a)["outcome"], "pass")
        a["pipettes"] = []
        self.assertEqual(evaluate_pipette_ranges(a)["outcome"], "unevaluable")

    def test_unavailable_official_data_never_passes(self):
        with patch("pipette_range.official_ranges", side_effect=ImportError):
            self.assertEqual(evaluate_pipette_ranges(analyze(volume=50))["outcome"], "unevaluable")

    def test_mode_changes_apply_in_command_order(self):
        a = analyze("p50_single_flex", 2, 2)
        a["commands"] += [{"commandType": "configureForVolume", "params": {"pipetteId": "p", "volume": 40}},
                          {"commandType": "dispense", "params": {"pipetteId": "p", "volume": 2}}]
        result = evaluate_pipette_ranges(a)
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["issues"][0]["step_index"], 3)

    def test_overlay_invalidates_false_green_and_preserves_old_failure(self):
        for old in ["pass", "fail", "unevaluable"]:
            p = {"outcome": old, "logic_pass": old == "pass", "final_pass_v2": old == "pass", "issues": []}
            out = apply_pipette_range_gate(p, analyze())
            self.assertEqual(out["outcome"], "fail")
            self.assertFalse(out["final_pass_v2"])
            self.assertTrue(out["issues"])

    def test_plan_fallback_cannot_bypass_range_or_guess_between_pipettes(self):
        green = {"logicpass": {"outcome": "pass", "logic_pass": True, "final_pass_v2": True}, "fab": {"lit": True}}
        plan = {"steps": [{"primitive_type": "ASPIRATE", "volume_ul": 2}]}
        for hardware, expected in [({"leftPipette": "flex_1channel_1000"}, "fail"), ({}, "unevaluable"),
                                   ({"leftPipette": "flex_1channel_1000", "rightPipette": "flex_1channel_50"}, "unevaluable")]:
            out = attach_pipette_range_gate(green, plan, {"robot": "Flex", "hardware": hardware})
            self.assertEqual(out["logicpass"]["outcome"], expected)
            self.assertFalse(out["fab"]["lit"])


if __name__ == "__main__":
    unittest.main()

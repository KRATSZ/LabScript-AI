import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "opentrons-protocol-verify" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from preflight_static import analyze_protocol_text  # noqa: E402


class PreflightStaticTests(unittest.TestCase):
    def test_rejects_invalid_flex_pipette(self) -> None:
        src = (
            'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n'
            'p = load_instrument("flex_1channel_200"'
        )
        r = analyze_protocol_text(src)
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["code"], "invalid_flex_pipette_name")

    def test_warns_liquid_class_low_api(self) -> None:
        src = (
            'requirements = {"robotType": "Flex", "apiLevel": "2.20"}\n'
            'protocol.get_liquid_class(name="water")\n'
        )
        r = analyze_protocol_text(src)
        self.assertTrue(r["ok"])
        self.assertTrue(any(w["code"] == "liquid_class_api_level" for w in r["warnings"]))

    def test_display_name_too_long_is_error(self) -> None:
        long_name = "x" * 31
        src = f'''
requirements = {{"robotType": "Flex", "apiLevel": "2.24"}}
def add_parameters(parameters):
    parameters.add_int(
        display_name="{long_name}",
        variable_name="n",
        default=1,
        minimum=1,
        maximum=96,
    )
'''
        r = analyze_protocol_text(src)
        self.assertFalse(r["ok"])
        self.assertTrue(any(e["code"] == "display_name_too_long" for e in r["errors"]))

    def test_display_name_positional_too_long_is_error(self) -> None:
        long_name = "x" * 31
        src = f'''
requirements = {{"robotType": "Flex", "apiLevel": "2.24"}}
def add_parameters(parameters):
    parameters.add_int(
        "{long_name}",
        "n",
        1,
        1,
        96,
    )
'''
        r = analyze_protocol_text(src)
        self.assertFalse(r["ok"])
        self.assertTrue(any(e["code"] == "display_name_too_long" for e in r["errors"]))

    def test_default_flow_rate_attribute_is_error(self) -> None:
        src = """
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def run(protocol):
    pipette.default_flow_rate.aspirate = 50
"""
        r = analyze_protocol_text(src)
        self.assertFalse(r["ok"])
        self.assertTrue(
            any(e["code"] == "nonexistent_default_flow_rate" for e in r["errors"])
        )

    def test_mixed_positional_keyword_add_int_warns(self) -> None:
        src = """
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def add_parameters(parameters):
    parameters.add_int("Samples", variable_name="sample_count", default=8, minimum=1, maximum=96)
"""
        r = analyze_protocol_text(src)
        self.assertTrue(r["ok"])
        self.assertTrue(
            any(w["code"] == "mixed_positional_keyword_params" for w in r["warnings"])
        )

    def test_transfer_mismatched_literal_lists_warns(self) -> None:
        src = """
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def run(protocol):
    pipette.transfer(10, [plate["A1"], plate["A2"]], [plate["B1"]])
"""
        r = analyze_protocol_text(src)
        self.assertTrue(r["ok"])
        self.assertTrue(
            any(w["code"] == "transfer_length_mismatch_risk" for w in r["warnings"])
        )


if __name__ == "__main__":
    unittest.main()

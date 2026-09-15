from __future__ import annotations

import unittest

from code_service import _extract_python, analyze_protocol_code, simulate_protocol_code

TINY = """
from opentrons import protocol_api
metadata = {"apiLevel": "2.15", "protocolName": "t"}
def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", 1)
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", 2)
    p = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])
    p.pick_up_tip()
    p.aspirate(20, plate["A1"])
    p.dispense(20, plate["B1"])
    p.drop_tip()
"""


class CodeServiceTests(unittest.TestCase):
    def test_extract_python_strips_fence(self) -> None:
        self.assertEqual(_extract_python("```python\ndef run(p):\n    pass\n```"), "def run(p):\n    pass")

    def test_simulate_and_analyze_tiny_ot2(self) -> None:
        sim = simulate_protocol_code(TINY)
        self.assertTrue(sim["success"], sim)
        analyzed = analyze_protocol_code(TINY)
        cmds = analyzed.get("commands") or []
        self.assertGreater(len(cmds), 0)
        self.assertTrue(any(c.get("commandType") for c in cmds if isinstance(c, dict)))
        self.assertEqual(analyzed.get("errors") or [], [])


if __name__ == "__main__":
    unittest.main()

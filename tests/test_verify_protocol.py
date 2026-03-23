from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opentrons_lab_agent.verify_protocol import build_bootstrap_code


class VerifyProtocolTests(unittest.TestCase):
    def test_bootstrap_code_injects_version_module(self) -> None:
        bootstrap = build_bootstrap_code("opentrons.cli")
        self.assertIn('types.ModuleType("opentrons._version")', bootstrap)
        self.assertIn('mod.version = "0.0.0-dev"', bootstrap)
        self.assertIn('runpy.run_module("opentrons.cli", run_name="__main__")', bootstrap)


if __name__ == "__main__":
    unittest.main()

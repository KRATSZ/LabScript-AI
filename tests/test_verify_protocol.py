from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opentrons_lab_agent.verify_protocol import build_bootstrap_code, resolve_workspace_paths


class VerifyProtocolTests(unittest.TestCase):
    def test_bootstrap_code_injects_version_module_for_source_layout(self) -> None:
        bootstrap = build_bootstrap_code("opentrons.cli", True)
        self.assertIn('types.ModuleType("opentrons._version")', bootstrap)
        self.assertIn('mod.version = "0.0.0-dev"', bootstrap)
        self.assertIn('runpy.run_module("opentrons.cli", run_name="__main__")', bootstrap)

    def test_bootstrap_code_skips_version_module_without_source_layout(self) -> None:
        bootstrap = build_bootstrap_code("opentrons.cli", False)
        self.assertNotIn('types.ModuleType("opentrons._version")', bootstrap)
        self.assertIn('runpy.run_module("opentrons.cli", run_name="__main__")', bootstrap)

    def test_resolve_workspace_paths_defaults_to_installed_runtime_mode(self) -> None:
        paths = resolve_workspace_paths()
        self.assertIsNone(paths.workspace_root)
        self.assertIsNone(paths.api_root)
        self.assertIsNone(paths.shared_data_root)
        self.assertFalse(paths.source_layout_ready)


if __name__ == "__main__":
    unittest.main()

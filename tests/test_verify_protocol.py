from __future__ import annotations

import contextlib
import io
from pathlib import Path
import runpy
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "opentrons-protocol-verify" / "scripts" / "verify_protocol.py"

# Load module via runpy to avoid spec_from_file_location issues with @dataclass
_mod_dict = runpy.run_path(str(SCRIPT_PATH))
MODULE = types.SimpleNamespace(**{k: v for k, v in _mod_dict.items() if not k.startswith("_")})

build_bootstrap_code = MODULE.build_bootstrap_code
resolve_workspace_paths = MODULE.resolve_workspace_paths


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

    def test_handle_doctor_returns_nonzero_when_runtime_probes_fail(self) -> None:
        original_probe_module = _mod_dict["probe_module"]

        def fake_probe_module(python_executable, paths, module_name):
            return {
                "ok": False,
                "python": python_executable,
                "module": module_name,
                "error_type": "ModuleNotFoundError",
                "error": "No module named 'opentrons'",
            }

        _mod_dict["probe_module"] = fake_probe_module
        try:
            output = io.StringIO()
            args = types.SimpleNamespace(
                workspace_root=None,
                api_root=None,
                shared_data_root=None,
                python="/usr/bin/python3",
            )
            with contextlib.redirect_stdout(output):
                exit_code = MODULE.handle_doctor(args)

            self.assertEqual(exit_code, 1)
            self.assertIn('"ok": false', output.getvalue())
        finally:
            _mod_dict["probe_module"] = original_probe_module


if __name__ == "__main__":
    unittest.main()

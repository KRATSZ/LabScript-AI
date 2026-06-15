from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path
import runpy
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "opentrons-protocol-verify" / "scripts" / "verify_protocol.py"

# Load module via runpy to avoid spec_from_file_location issues with @dataclass
_mod_dict = runpy.run_path(str(SCRIPT_PATH))
MODULE = types.SimpleNamespace(**{k: v for k, v in _mod_dict.items() if not k.startswith("_")})

build_bootstrap_code = MODULE.build_bootstrap_code
resolve_workspace_paths = MODULE.resolve_workspace_paths
resolve_simulation_cwd = MODULE.resolve_simulation_cwd


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
        globals_dict = MODULE.handle_doctor.__globals__
        original_probe_module = globals_dict["probe_module"]

        def fake_probe_module(python_executable, paths, module_name):
            return {
                "ok": False,
                "python": python_executable,
                "module": module_name,
                "error_type": "ModuleNotFoundError",
                "error": "No module named 'opentrons'",
            }

        globals_dict["probe_module"] = fake_probe_module
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
            globals_dict["probe_module"] = original_probe_module

    def test_resolve_simulation_cwd_uses_protocol_parent_for_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "pkg"
            package_dir.mkdir()
            protocol = package_dir / "protocol.py"
            protocol.write_text("# stub\n", encoding="utf-8")
            self.assertEqual(resolve_simulation_cwd(protocol), package_dir.resolve())

    def test_resolve_simulation_cwd_uses_bundle_dir_for_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp) / "bundle"
            bundle_dir.mkdir()
            self.assertEqual(resolve_simulation_cwd(bundle_dir), bundle_dir.resolve())

    def test_run_module_passes_cwd_to_subprocess(self) -> None:
        paths = resolve_workspace_paths()
        subprocess_module = MODULE.run_module.__globals__["subprocess"]
        with mock.patch.object(subprocess_module, "run") as run_mock:
            run_mock.return_value = types.SimpleNamespace(returncode=0)
            package_dir = ROOT / "tmp_sim_cwd_pkg"
            exit_code = MODULE.run_module(
                sys.executable,
                paths,
                "opentrons.simulate",
                ["protocol.py"],
                cwd=package_dir,
            )
        self.assertEqual(exit_code, 0)
        run_mock.assert_called_once()
        self.assertEqual(run_mock.call_args.kwargs["cwd"], str(package_dir))

    def test_simulate_side_effect_file_written_to_package_dir(self) -> None:
        probe = MODULE.probe_module(
            sys.executable,
            resolve_workspace_paths(),
            "opentrons.simulate",
        )
        if not probe.get("ok"):
            self.skipTest("opentrons.simulate not available")

        side_effect_name = "sim_cwd_side_effect.txt"
        repo_marker = ROOT / side_effect_name
        if repo_marker.exists():
            repo_marker.unlink()

        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "pkg"
            package_dir.mkdir()
            protocol = package_dir / "protocol.py"
            protocol.write_text(
                'metadata = {"apiLevel": "2.15"}\n\n'
                f'def run(protocol):\n'
                f'    open("{side_effect_name}", "w", encoding="utf-8").write("ok")\n',
                encoding="utf-8",
            )
            args = types.SimpleNamespace(
                workspace_root=None,
                api_root=None,
                shared_data_root=None,
                python=None,
                protocol=str(protocol),
                extra_args=[],
            )
            try:
                exit_code = MODULE.handle_simulate(args)
                self.assertEqual(exit_code, 0, "simulate should succeed for minimal protocol")
                self.assertTrue((package_dir / side_effect_name).is_file())
                self.assertFalse(repo_marker.exists())
            finally:
                if repo_marker.exists():
                    repo_marker.unlink()
                package_marker = package_dir / side_effect_name
                if package_marker.exists():
                    package_marker.unlink()


if __name__ == "__main__":
    unittest.main()

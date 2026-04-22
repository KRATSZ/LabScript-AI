from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "opentrons-protocol-library" / "scripts" / "search_protocols.py"
SPEC = spec_from_file_location("search_protocols", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProtocolLibraryScriptTests(unittest.TestCase):
    def test_resolve_library_path_prefers_explicit_path(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            explicit = tmp / "explicit"
            bundled = tmp / "repo" / "reference-protocols" / "Protocols-develop"
            sibling = tmp / "Protocols-develop"
            explicit.mkdir(parents=True)
            bundled.mkdir(parents=True)
            sibling.mkdir(parents=True)

            resolved = MODULE.resolve_library_path(
                explicit,
                environ={"OPENTRONS_PROTOCOL_LIBRARY_PATH": str(sibling)},
                repo_root=tmp / "repo",
            )

        self.assertEqual(resolved, explicit.resolve())

    def test_resolve_library_path_prefers_env_before_bundled(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            repo_root = tmp / "repo"
            bundled = repo_root / "reference-protocols" / "Protocols-develop"
            env_path = tmp / "env-library"
            bundled.mkdir(parents=True)
            env_path.mkdir(parents=True)

            resolved = MODULE.resolve_library_path(
                None,
                environ={"OPENTRONS_PROTOCOL_LIBRARY_PATH": str(env_path)},
                repo_root=repo_root,
            )

        self.assertEqual(resolved, env_path.resolve())

    def test_resolve_library_path_prefers_bundled_before_sibling(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            repo_root = tmp / "repo"
            bundled = repo_root / "reference-protocols" / "Protocols-develop"
            sibling = tmp / "Protocols-develop"
            bundled.mkdir(parents=True)
            sibling.mkdir(parents=True)

            resolved = MODULE.resolve_library_path(None, environ={}, repo_root=repo_root)

        self.assertEqual(resolved, bundled.resolve())

    def test_resolve_library_path_falls_back_to_sibling(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            repo_root = tmp / "repo"
            sibling = tmp / "Protocols-develop"
            repo_root.mkdir(parents=True)
            sibling.mkdir(parents=True)

            resolved = MODULE.resolve_library_path(None, environ={}, repo_root=repo_root)

        self.assertEqual(resolved, sibling.resolve())

    def test_search_protocols_matches_source_code_content(self) -> None:
        library_path = ROOT / "reference-protocols" / "Protocols-develop"

        results = MODULE.search_protocols(library_path, ["p20_mount"], limit=20)

        self.assertTrue(any(result["name"] == "00222e" for result in results))

    def test_show_protocol_returns_paths_and_metadata(self) -> None:
        library_path = ROOT / "reference-protocols" / "Protocols-develop"

        result = MODULE.show_protocol(library_path, "00222e")

        self.assertEqual(result["slug"], "00222e")
        self.assertIn("serially diluted stock solution", result["summary"])
        self.assertTrue(result["readme_path"].endswith("00222e/README.md"))
        self.assertTrue(any(path.endswith(".py") for path in result["python_paths"]))
        self.assertIn("OT-2", result["robot_types"])
        self.assertEqual(result["python_files"][0]["apiLevel"], "2.11")

    def test_snippet_protocol_returns_keyword_hits(self) -> None:
        library_path = ROOT / "reference-protocols" / "Protocols-develop"

        result = MODULE.snippet_protocol(library_path, "00222e", ["serial", "plasma"], limit=3)

        self.assertEqual(result["slug"], "00222e")
        self.assertGreater(result["snippet_count"], 0)
        self.assertTrue(
            any(
                snippet["path"].endswith("README.md") or snippet["path"].endswith(".py")
                for snippet in result["snippets"]
            )
        )

    def test_cookbook_missing_returns_clear_message(self) -> None:
        library_path = ROOT / "reference-protocols" / "Protocols-develop"

        result = MODULE.get_cookbook_sections(library_path)

        self.assertFalse(result["available"])
        self.assertIn("Cookbook.md is not present", result["message"])


if __name__ == "__main__":
    unittest.main()

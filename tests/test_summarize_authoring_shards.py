import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.summarize_authoring_shards import main


class SummarizeAuthoringShardsTest(unittest.TestCase):
    def test_handles_null_simulation_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            task_dir = root / "shard01" / "T001"
            task_dir.mkdir(parents=True)
            (task_dir / "record.json").write_text(
                json.dumps(
                    {
                        "task_id": "T001",
                        "validation": {"package_complete": True, "ok": False},
                        "simulation": None,
                        "first_simulation": None,
                        "provider_error_count": 0,
                        "total_tokens": 3,
                    }
                ),
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()):
                self.assertEqual(main(["summarize_authoring_shards.py", str(root)]), 0)
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["task_count"], 1)
            self.assertEqual(summary["simulation_pass_count"], 0)
            self.assertEqual(summary["first_pass_simulation_pass_count"], 0)
            self.assertEqual(summary["package_complete_count"], 1)

    def test_preserves_simulation_repair_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            task_dir = root / "shard01" / "T056"
            task_dir.mkdir(parents=True)
            (task_dir / "record.json").write_text(
                json.dumps(
                    {
                        "task_id": "T056",
                        "validation": {"package_complete": True, "ok": True},
                        "simulation": {"ok": True},
                        "first_simulation": {"ok": False},
                        "provider_error_count": 0,
                        "generation_attempts": 1,
                        "attempts": 3,
                        "total_tokens": 150,
                        "authoring_total_tokens": 100,
                        "repair_input_tokens": 40,
                        "repair_output_tokens": 10,
                        "repair_total_tokens": 50,
                        "simulation_repair_attempts": 2,
                        "repair_success": True,
                        "repair_patch_backend": "rewrite",
                        "simulator_calls": 3,
                    }
                ),
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()):
                self.assertEqual(main(["summarize_authoring_shards.py", str(root)]), 0)
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["simulation_repair_attempts"], 2)
            self.assertEqual(summary["repair_success_count"], 1)
            self.assertEqual(summary["max_repair_attempts_observed"], 2)
            self.assertEqual(summary["repair_attempts_per_task"], {"T056": 2})
            self.assertEqual(summary["repair_total_tokens"], 50)
            self.assertEqual(summary["simulator_calls"], 3)
            self.assertEqual(summary["repair_patch_backend"], "rewrite")


if __name__ == "__main__":
    unittest.main()

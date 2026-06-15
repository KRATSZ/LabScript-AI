import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()

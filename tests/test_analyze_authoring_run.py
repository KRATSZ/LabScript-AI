from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.analyze_authoring_run import analyze_run


class AnalyzeAuthoringRunTests(unittest.TestCase):
    def test_analyze_run_handles_null_simulation_for_provider_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks_path = root / "tasks.yaml"
            tasks_path.write_text(
                "tasks:\n"
                "  - id: T900\n"
                "    source: test\n"
                "    difficulty: Medium\n"
                "    holdout: false\n"
                "    output_contract: protocol.py only\n"
                "    prompt: |\n"
                "      Transfer 50 uL from A1 to B1.\n",
                encoding="utf-8",
            )
            summary_path = root / "summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "task_id": "T900",
                                "difficulty": "Medium",
                                "package_dir": str(root / "missing-package"),
                                "provider_error_count": 1,
                                "simulation": None,
                                "validation": None,
                                "first_simulation": None,
                                "error": "codex_returncode_1",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = analyze_run(summary_path, tasks_path, root / "analysis")

        self.assertEqual(result["task_count"], 1)
        self.assertEqual(result["simulation_pass_count"], 0)
        self.assertEqual(result["validator_ok_count"], 0)
        self.assertEqual(result["task_pass_count"], 0)
        self.assertEqual(result["per_task"][0]["failure_mode"], "provider_error")


if __name__ == "__main__":
    unittest.main()

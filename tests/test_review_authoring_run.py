from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.review_authoring_run import (
    build_review_prompt,
    normalize_review,
    review_run,
)
from labscriptai.benchmark.tasks import AuthoringTask
from test_package_validator import write_valid_package


class ReviewAuthoringRunTests(unittest.TestCase):
    def test_build_review_prompt_excludes_trace(self) -> None:
        task = AuthoringTask(
            task_id="T900",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt="Transfer 50 uL from A1 to B1.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "trace.jsonl").write_text('{"secret":"trace"}\n', encoding="utf-8")

            prompt = build_review_prompt(task, package_dir, {"validation": {"ok": True}})

        self.assertIn("Transfer 50 uL", prompt)
        self.assertIn("protocol.py", prompt)
        self.assertNotIn("trace.jsonl", prompt)
        self.assertNotIn("secret", prompt)

    def test_normalize_review_clamps_scores(self) -> None:
        result = normalize_review(
            {
                "task_alignment_score": 6,
                "biological_reasonableness_score": 4,
                "liquid_handling_quality_score": 3,
                "safety_control_score": 2,
                "code_quality_score": 0,
                "major_issues": ["missing control"],
                "notes": "reviewed",
            },
            task_id="T900",
            package_dir="/tmp/package",
        )

        self.assertEqual(result.scores["task_alignment_score"], 5.0)
        self.assertEqual(result.scores["code_quality_score"], 1.0)
        self.assertAlmostEqual(result.mean_score or 0.0, 3.0)

    def test_review_run_writes_summary_with_mock_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            tasks_path = root / "tasks.yaml"
            tasks_path.write_text(
                "tasks:\n"
                "  - id: T056\n"
                "    source: test\n"
                "    difficulty: Easy\n"
                "    holdout: true\n"
                "    output_contract: execution_package\n"
                "    prompt: |\n"
                "      Transfer 50 uL.\n",
                encoding="utf-8",
            )
            summary_path = root / "summary.json"
            summary_path.write_text(
                json.dumps({"records": [{"task_id": "T056", "package_dir": str(package_dir)}]}),
                encoding="utf-8",
            )

            def reviewer(task: AuthoringTask, package_dir: Path, record: dict[str, object]) -> dict[str, object]:
                return {
                    "task_alignment_score": 4,
                    "biological_reasonableness_score": 4,
                    "liquid_handling_quality_score": 3,
                    "safety_control_score": 5,
                    "code_quality_score": 4,
                    "major_issues": [],
                    "notes": "mostly correct",
                }

            result = review_run(summary_path, tasks_path, root / "reviews", reviewer=reviewer)

        self.assertEqual(result["review_count"], 1)
        self.assertEqual(result["review_ok_count"], 1)
        self.assertAlmostEqual(result["mean_scores"]["expert_score_mean"], 4.0)


if __name__ == "__main__":
    unittest.main()

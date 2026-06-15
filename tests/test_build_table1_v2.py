from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_table1_v2 import TableRow, build_table


class BuildTable1V2Tests(unittest.TestCase):
    def test_build_table_uses_summary_analysis_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            (root / "analysis").mkdir(parents=True)
            (root / "expert_review").mkdir()
            (root / "summary.json").write_text(
                json.dumps(
                    {
                        "task_count": 2,
                        "simulation_pass_count": 1,
                        "total_tokens": 100,
                        "tool_calls": 3,
                    }
                ),
                encoding="utf-8",
            )
            (root / "analysis" / "attribution-summary.json").write_text(
                json.dumps({"task_count": 2, "task_pass_count": 1}),
                encoding="utf-8",
            )
            (root / "expert_review" / "review-summary.json").write_text(
                json.dumps({"mean_scores": {"expert_score_mean": 4.25}}),
                encoding="utf-8",
            )

            table = build_table((TableRow("Tiny", "Native agent", "Agent", root),))

        self.assertIn(
            "| Tiny | Native agent | Agent | 2 | 0/2 | 1/2 | 1/2 | 0/2 | 4.25/5 | NA | 100 | 50 | 0 | 0 | 3 | complete |",
            table,
        )

    def test_build_table_adds_three_reviewer_panel_mean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            (root / "analysis").mkdir(parents=True)
            (root / "expert_review").mkdir()
            (root / "summary.json").write_text(
                json.dumps(
                    {
                        "task_count": 2,
                        "simulation_pass_count": 1,
                        "total_tokens": 100,
                        "tool_calls": 3,
                    }
                ),
                encoding="utf-8",
            )
            (root / "analysis" / "attribution-summary.json").write_text(
                json.dumps({"task_count": 2, "task_pass_count": 1}),
                encoding="utf-8",
            )
            (root / "expert_review" / "review-summary.json").write_text(
                json.dumps({"mean_scores": {"expert_score_mean": 4.25}}),
                encoding="utf-8",
            )
            for dirname, score in (
                ("expert_review_panel_deepseek", 4.0),
                ("expert_review_panel_gpt", 3.0),
                ("expert_review_panel_gemini", 5.0),
            ):
                review_dir = root / dirname
                review_dir.mkdir()
                review_dir.joinpath("review-summary.json").write_text(
                    json.dumps(
                        {
                            "review_count": 30,
                            "review_ok_count": 30,
                            "reviewer": {"model": dirname},
                            "per_task": [
                                {
                                    "task_id": f"T{index:03d}",
                                    "ok": True,
                                    "expert_score_mean": score,
                                }
                                for index in range(1, 31)
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

            table = build_table((TableRow("Tiny", "Native agent", "Agent", root, panel_expected=True),))

        self.assertIn("Expert panel (3-LLM mean)", table)
        self.assertIn(
            "| Tiny | Native agent | Agent | 2 | 0/2 | 1/2 | 1/2 | 0/2 | 4.25/5 | 4.00/5 | 100 | 50 | 0 | 0 | 3 | complete |",
            table,
        )


if __name__ == "__main__":
    unittest.main()

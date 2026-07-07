from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
            "| Tiny | Native agent | Agent | Native agent | 2 | 0/2 | 1/2 | 4.25/5 | 50 | NA | 0 | 0 | complete |",
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

        self.assertIn(
            "| Tiny | Native agent | Agent | Native agent | 2 | 0/2 | 1/2 | 4.00/5 | 50 | NA | 0 | 0 | complete |",
            table,
        )

    def test_panel_complete_without_legacy_expert_review_is_not_expert_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            (root / "analysis").mkdir(parents=True)
            (root / "summary.json").write_text(
                json.dumps(
                    {
                        "task_count": 2,
                        "simulation_pass_count": 1,
                        "total_tokens": 100,
                        "tool_calls": 0,
                    }
                ),
                encoding="utf-8",
            )
            (root / "analysis" / "attribution-summary.json").write_text(
                json.dumps({"task_count": 2, "task_pass_count": 1}),
                encoding="utf-8",
            )
            for dirname, score in (
                ("expert_review_panel_deepseek", 3.0),
                ("expert_review_panel_gpt", 3.0),
                ("expert_review_panel_gemini", 3.0),
            ):
                review_dir = root / dirname
                review_dir.mkdir()
                review_dir.joinpath("review-summary.json").write_text(
                    json.dumps(
                        {
                            "review_count": 30,
                            "review_ok_count": 30,
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

            table = build_table((TableRow("Tiny", "Literature", "Inagaki", root, panel_expected=True),))

        self.assertIn(
            "| Tiny | Literature | Inagaki | Literature | 2 | 0/2 | 1/2 | 3.00/5 | 50 | NA | 0 | 0 | complete |",
            table,
        )
        self.assertNotIn("expert_missing", table)

    def test_api_fail_rate_excludes_row_from_main_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            (root / "analysis").mkdir(parents=True)
            (root / "summary.json").write_text(
                json.dumps(
                    {
                        "task_count": 10,
                        "provider_error_count": 1,
                        "records": [
                            {"task_id": "T001", "error": "quota"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "analysis" / "attribution-summary.json").write_text(
                json.dumps({"task_count": 10, "task_pass_count": 0}),
                encoding="utf-8",
            )

            table = build_table((TableRow("Tiny", "Native agent", "Agent", root),))

        self.assertNotIn("| Tiny | Native agent | Agent | Native agent | 10 |", table)
        self.assertIn("| Tiny | Native agent | Agent | 10 | provider_error_count=1/10; final_api_fail=1/10 |", table)


if __name__ == "__main__":
    unittest.main()

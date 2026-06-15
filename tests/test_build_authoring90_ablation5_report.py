from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_authoring90_ablation5_report import ROWS, _to_markdown, build_report


class BuildAuthoring90Ablation5ReportTests(unittest.TestCase):
    def test_build_report_includes_expert_column_and_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model_dir = root / "flash"
            for index, row in enumerate(ROWS, start=1):
                row_dir = model_dir / row
                (row_dir / "analysis").mkdir(parents=True)
                (row_dir / "expert_review").mkdir()
                (row_dir / "expert_review_panel_gpt").mkdir()
                (row_dir / "expert_review_panel_gemini").mkdir()
                records = [
                    {
                        "task_id": f"T{task:03d}",
                        "repair_total_tokens": index,
                        "repair_patch_count": 1,
                    }
                    for task in range(1, 91)
                ]
                (row_dir / "summary.json").write_text(
                    json.dumps(
                        {
                            "task_count": 90,
                            "records": records,
                            "simulation_pass_count": 80 + index,
                            "provider_error_count": 0,
                            "total_tokens": 9000 * index,
                        }
                    ),
                    encoding="utf-8",
                )
                (row_dir / "analysis" / "attribution-summary.json").write_text(
                    json.dumps(
                        {
                            "task_count": 90,
                            "task_pass_count": 50 + index,
                            "simulation_pass_count": 80 + index,
                            "semantic_ok_count": 60 + index,
                            "validator_ok_count": 80 + index,
                        }
                    ),
                    encoding="utf-8",
                )
                (row_dir / "expert_review" / "review-summary.json").write_text(
                    json.dumps(
                        {
                            "review_ok_count": 90,
                            "mean_scores": {"expert_score_mean": 3.5 + index / 10},
                        }
                    ),
                    encoding="utf-8",
                )
                (row_dir / "expert_review_panel_gpt" / "review-summary.json").write_text(
                    json.dumps(
                        {
                            "review_ok_count": 30,
                            "mean_scores": {"expert_score_mean": 3.4 + index / 10},
                        }
                    ),
                    encoding="utf-8",
                )
                (row_dir / "expert_review_panel_gemini" / "review-summary.json").write_text(
                    json.dumps(
                        {
                            "review_ok_count": 30,
                            "mean_scores": {"expert_score_mean": 3.3 + index / 10},
                        }
                    ),
                    encoding="utf-8",
                )

            report = build_report(root)
            markdown = _to_markdown(report)

        first_row = report["models"]["flash"]["rows"][0]
        self.assertEqual(first_row["expert_mean"], 3.6)
        self.assertAlmostEqual(first_row["expert_panel_gpt_mean"], 3.5)
        self.assertAlmostEqual(first_row["expert_panel_gemini_mean"], 3.4)
        self.assertEqual(first_row["review_ok_count"], 90)
        self.assertTrue(report["acceptance"]["flash"]["llm_direct"]["review_ok_count_is_90"])
        self.assertTrue(report["acceptance"]["flash"]["llm_direct"]["panel_gpt_ok_count_is_30"])
        self.assertIn("| row | task_pass/90 | Expert | Expert GPT (30) | Expert Gemini (30) |", markdown)
        self.assertIn("| llm_direct | 51/90 | 3.60/5 | 3.50/5 | 3.40/5 | 81/90 |", markdown)
        self.assertIn("Task Pass means all four deterministic gates pass", markdown)


if __name__ == "__main__":
    unittest.main()

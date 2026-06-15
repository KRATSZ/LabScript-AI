from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.review_authoring_run import _filter_records, review_run
from labscriptai.benchmark.tasks import (
    REVIEW_PANEL_COUNTS,
    AuthoringTask,
    load_authoring_tasks,
    select_review_panel_task_ids,
)


class ReviewPanelTests(unittest.TestCase):
    def test_select_review_panel_task_ids_counts(self) -> None:
        tasks = load_authoring_tasks(Path("benchmarks/authoring/tasks.yaml"))
        panel_ids = select_review_panel_task_ids(tasks)
        self.assertEqual(len(panel_ids), sum(REVIEW_PANEL_COUNTS.values()))
        by_difficulty: dict[str, int] = {}
        task_map = {task.task_id: task for task in tasks}
        for task_id in panel_ids:
            by_difficulty[task_map[task_id].difficulty] = (
                by_difficulty.get(task_map[task_id].difficulty, 0) + 1
            )
        self.assertEqual(by_difficulty, REVIEW_PANEL_COUNTS)

    def test_filter_records_by_task_ids_preserves_order(self) -> None:
        records = [
            {"task_id": "T003"},
            {"task_id": "T001"},
            {"task_id": "T002"},
        ]
        filtered = _filter_records(records, task_ids=("T001", "T003"))
        self.assertEqual([row["task_id"] for row in filtered], ["T001", "T003"])

    def test_review_run_respects_task_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            (package_dir / "protocol.py").write_text("def run(protocol): pass\n", encoding="utf-8")
            (package_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "0.4",
                        "task_id": "T056",
                        "system_id": "labscriptai",
                        "model_id": "test",
                        "scaffold_id": "test",
                    }
                ),
                encoding="utf-8",
            )
            (package_dir / "setup_card.html").write_text("<p>setup</p>", encoding="utf-8")
            tasks_path = root / "tasks.yaml"
            tasks_path.write_text(
                "tasks:\n"
                "  - id: T056\n"
                "    source: test\n"
                "    difficulty: Easy\n"
                "    holdout: true\n"
                "    output_contract: protocol.py only\n"
                "    prompt: |\n"
                "      Transfer 50 uL.\n"
                "  - id: T057\n"
                "    source: test\n"
                "    difficulty: Easy\n"
                "    holdout: true\n"
                "    output_contract: protocol.py only\n"
                "    prompt: |\n"
                "      Transfer 25 uL.\n",
                encoding="utf-8",
            )
            summary_path = root / "summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {"task_id": "T057", "package_dir": str(package_dir)},
                            {"task_id": "T056", "package_dir": str(package_dir)},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def reviewer(task: AuthoringTask, package_dir: Path, record: dict[str, object]) -> dict[str, object]:
                return {
                    "task_alignment_score": 4,
                    "biological_reasonableness_score": 4,
                    "liquid_handling_quality_score": 4,
                    "safety_control_score": 4,
                    "code_quality_score": 4,
                    "major_issues": [],
                    "notes": task.task_id,
                }

            result = review_run(
                summary_path,
                tasks_path,
                root / "reviews",
                reviewer=reviewer,
                task_ids=("T056",),
            )

        self.assertEqual(result["review_count"], 1)
        self.assertEqual(result["per_task"][0]["task_id"], "T056")


if __name__ == "__main__":
    unittest.main()

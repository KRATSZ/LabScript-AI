from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.benchmark.tasks import load_authoring_tasks


TASKS = ROOT / "benchmarks" / "authoring" / "tasks.yaml"

ALLOWED_DIFFICULTIES = frozenset({"Easy", "Medium", "Hard", "Expert"})


class TaxonomyLabelTests(unittest.TestCase):
    def test_v02_difficulty_labels_are_valid(self) -> None:
        for task in load_authoring_tasks(TASKS):
            self.assertIn(
                task.difficulty,
                ALLOWED_DIFFICULTIES,
                f"{task.task_id} has invalid difficulty {task.difficulty!r}",
            )

    def test_named_taxonomy_corrections_are_locked(self) -> None:
        tasks = {task.task_id: task for task in load_authoring_tasks(TASKS)}

        self.assertEqual(tasks["T013"].difficulty, "Easy")
        self.assertEqual(tasks["T036"].difficulty, "Medium")
        self.assertEqual(tasks["T045"].difficulty, "Medium")
        self.assertEqual(tasks["T050"].difficulty, "Hard")
        self.assertEqual(tasks["T051"].difficulty, "Hard")
        for task_id in ("T086", "T087", "T088", "T089", "T090"):
            self.assertEqual(tasks[task_id].difficulty, "Medium")


if __name__ == "__main__":
    unittest.main()

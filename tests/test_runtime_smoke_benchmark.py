from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.tasks import (
    load_authoring_tasks,
    select_stratified_tasks,
)
from labscriptai.runtime.smoke_benchmark import (
    _offline_factory,
    run_runtime_smoke,
)


ROOT = Path(__file__).resolve().parents[1]


class RuntimeSmokeBenchmarkTests(unittest.TestCase):
    def test_load_authoring_tasks_reads_frozen_manifest(self) -> None:
        tasks = load_authoring_tasks(ROOT / "benchmarks" / "authoring" / "tasks.yaml")

        self.assertEqual(len(tasks), 90)
        self.assertEqual(tasks[0].task_id, "T001")
        self.assertTrue(tasks[0].holdout)
        self.assertIn("Basic liquid handling", tasks[0].prompt)

    def test_select_stratified_tasks_prefers_new_holdout_tasks(self) -> None:
        tasks = load_authoring_tasks(ROOT / "benchmarks" / "authoring" / "tasks.yaml")
        selected = select_stratified_tasks(tasks, per_level=1)

        self.assertEqual([task.difficulty for task in selected], ["Easy", "Medium", "Hard"])
        self.assertEqual([task.task_id for task in selected], ["T056", "T058", "T070"])

    def test_runtime_smoke_writes_summary_and_traces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "smoke"
            summary = run_runtime_smoke(
                tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                output_dir=output_dir,
                candidate_provider_factory=_offline_factory,
                model_id="offline-test",
            )

            summary_path = output_dir / "summary.json"
            saved = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["task_count"], 3)
        self.assertEqual(summary["completed_count"], 3)
        self.assertEqual(saved["records"][0]["decision_actions"], ["simulate_protocol"])


if __name__ == "__main__":
    unittest.main()

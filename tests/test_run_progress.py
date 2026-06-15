from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.run_progress import (
    completed_task_ids,
    is_task_record_complete,
    pending_task_ids,
)


class RunProgressTests(unittest.TestCase):
    def test_success_record_is_complete_before_retry_limit(self) -> None:
        record = {
            "task_id": "T001",
            "generation_attempts": 1,
            "validation": {"ok": True},
        }

        self.assertTrue(is_task_record_complete(record, retry_attempts=2))

    def test_interim_provider_failure_is_not_complete(self) -> None:
        record = {
            "task_id": "T001",
            "generation_attempts": 1,
            "error": "HTTPError: 502",
        }

        self.assertFalse(is_task_record_complete(record, retry_attempts=2))

    def test_final_failure_after_last_retry_is_complete(self) -> None:
        record = {
            "task_id": "T001",
            "generation_attempts": 2,
            "error": "HTTPError: 502",
        }

        self.assertTrue(is_task_record_complete(record, retry_attempts=2))

    def test_pending_task_ids_skip_only_truly_completed_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / "T001").mkdir()
            (out_dir / "T001" / "record.json").write_text(
                json.dumps({"task_id": "T001", "generation_attempts": 1, "validation": {"ok": True}}),
                encoding="utf-8",
            )
            (out_dir / "T002").mkdir()
            (out_dir / "T002" / "record.json").write_text(
                json.dumps({"task_id": "T002", "generation_attempts": 1, "error": "HTTPError: 502"}),
                encoding="utf-8",
            )
            (out_dir / "T003").mkdir()
            (out_dir / "T003" / "record.json").write_text("{broken", encoding="utf-8")

            completed = completed_task_ids(
                out_dir,
                ("T001", "T002", "T003", "T004"),
                retry_attempts=2,
            )
            pending = pending_task_ids(
                out_dir,
                ("T001", "T002", "T003", "T004"),
                retry_attempts=2,
            )

        self.assertEqual(completed, ["T001"])
        self.assertEqual(pending, ["T002", "T003", "T004"])


if __name__ == "__main__":
    unittest.main()

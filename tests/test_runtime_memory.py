from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.runtime.memory import append_memory_note, remember_shadow_record, search_memory


class RuntimeMemoryTests(unittest.TestCase):
    def test_append_and_search_markdown_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_dir = Path(tmp)
            path = append_memory_note(
                memory_dir,
                title="Missing tip recovery",
                body="Retry pick up tip with the next candidate well after MCP parse_error.",
                tags=("runtime", "missing_tip"),
            )

            hits = search_memory(memory_dir, "missing_tip next candidate", limit=3)

        self.assertTrue(path.name.endswith("missing-tip-recovery.md"))
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].title, "Missing tip recovery")
        self.assertGreaterEqual(hits[0].score, 2)

    def test_remember_shadow_record_writes_searchable_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory_dir = Path(tmp)
            remember_shadow_record(
                memory_dir,
                {
                    "case_id": "case-run-1",
                    "run_id": "run-1",
                    "error_category": "missing_tip",
                    "expected_policy": "retry_next_tip",
                    "action_type": "execute_recovery_branch",
                    "gatekeeper_status": "approved",
                    "passed": True,
                    "reasons": ["action approved"],
                },
            )

            hits = search_memory(memory_dir, "missing_tip approved")

        self.assertEqual(len(hits), 1)
        self.assertIn("missing_tip", hits[0].title)


if __name__ == "__main__":
    unittest.main()

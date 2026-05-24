from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.tasks import load_authoring_tasks


class TaskLoaderTests(unittest.TestCase):
    def test_prompt_block_preserves_blank_lines(self) -> None:
        manifest = """tasks:
  - id: TTEST001
    source: test
    difficulty: Easy
    holdout: true
    output_contract: execution_package
    prompt: |
      First line.

      Source workflow: REAL_SOURCE.

      Workflow:
      1. Do the thing.
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.yaml"
            path.write_text(manifest, encoding="utf-8")
            task = load_authoring_tasks(path)[0]

        self.assertIn("Source workflow: REAL_SOURCE.", task.prompt)
        self.assertIn("\n\nWorkflow:\n", task.prompt)


if __name__ == "__main__":
    unittest.main()

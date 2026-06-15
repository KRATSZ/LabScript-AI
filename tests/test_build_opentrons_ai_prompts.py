from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.authoring_pilot import PY_ONLY_AUTHORING_SYSTEM_PROMPT, _prompt_hash
from labscriptai.benchmark.tasks import load_authoring_tasks

from scripts.build_opentrons_ai_prompts import build_full_prompt, build_prompt_record, write_outputs


class BuildOpentronsAiPromptsTests(unittest.TestCase):
    def test_full_prompt_uses_py_only_prefix_and_task_body(self) -> None:
        tasks_path = Path("benchmarks/authoring/tasks.yaml")
        task = load_authoring_tasks(tasks_path)[0]
        full = build_full_prompt(task)

        self.assertTrue(full.startswith(PY_ONLY_AUTHORING_SYSTEM_PROMPT.strip()))
        self.assertIn(f"Task (difficulty: {task.difficulty}):", full)
        self.assertIn(task.prompt.strip(), full)

    def test_prompt_hash_matches_task_prompt_only(self) -> None:
        task = load_authoring_tasks(Path("benchmarks/authoring/tasks.yaml"))[0]
        record = build_prompt_record(task)
        self.assertEqual(record["prompt_hash"], _prompt_hash(task.prompt))

    def test_write_outputs_creates_jsonl_and_doc(self) -> None:
        task = load_authoring_tasks(Path("benchmarks/authoring/tasks.yaml"))[0]
        record = build_prompt_record(task)
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            tasks_path = Path("benchmarks/authoring/tasks.yaml")
            doc_path, jsonl_path = write_outputs([record], out_dir=out_dir, tasks_path=tasks_path)

            self.assertTrue(doc_path.is_file())
            self.assertTrue(jsonl_path.is_file())
            self.assertTrue((out_dir / "prompt_manifest.json").is_file())

            loaded = json.loads(jsonl_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(loaded["task_id"], task.task_id)
            self.assertEqual(loaded["full_prompt"], record["full_prompt"])


if __name__ == "__main__":
    unittest.main()

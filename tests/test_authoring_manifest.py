from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.benchmark.tasks import load_authoring_tasks

TASKS = ROOT / "benchmarks" / "authoring" / "tasks.yaml"
HOLDOUT = ROOT / "benchmarks" / "authoring" / "holdout_manifest.json"


class AuthoringManifestTests(unittest.TestCase):
    def test_tasks_manifest_freezes_90_ids(self) -> None:
        text = TASKS.read_text(encoding="utf-8")
        task_ids = re.findall(r"^  - id: (T\d{3})$", text, flags=re.MULTILINE)

        self.assertEqual(len(task_ids), 90)
        self.assertEqual(task_ids[0], "T001")
        self.assertEqual(task_ids[-1], "T090")
        self.assertEqual(len(set(task_ids)), 90)

    def test_holdout_manifest_matches_required_distribution(self) -> None:
        manifest = json.loads(HOLDOUT.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_version"], "0.2")
        self.assertEqual(manifest["total_tasks"], 90)
        self.assertEqual(manifest["holdout_count"], 30)
        self.assertGreaterEqual(manifest["new_holdout_count"], 18)
        self.assertEqual(len(manifest["holdout_task_ids"]), 30)
        self.assertEqual(len(set(manifest["holdout_task_ids"])), 30)

    def test_manifest_records_upstream_and_new_task_specs(self) -> None:
        text = TASKS.read_text(encoding="utf-8")

        self.assertIn('schema_version: "0.3"', text)
        self.assertIn("adapter_default: opentrons", text)
        self.assertIn("repo: labauto/Inagaki_2023_GPT4OT2", text)
        self.assertEqual(len(re.findall(r"^    upstream_id: inagaki_2023$", text, flags=re.MULTILINE)), 55)
        self.assertEqual(len(re.findall(r"^    spec:$", text, flags=re.MULTILINE)), 35)
        self.assertEqual(len(re.findall(r"^    output_contract: execution_package$", text, flags=re.MULTILINE)), 90)
        self.assertNotIn("seven_file_protocol_package", text)

    def test_task_loader_exposes_specs_and_handoffs(self) -> None:
        tasks = {task.task_id: task for task in load_authoring_tasks(TASKS)}

        self.assertEqual(tasks["T056"].spec.default_samples, 96)
        self.assertIn("unsafe tip reuse rejected", tasks["T056"].spec.expected_risk_flags)
        self.assertEqual(tasks["T039"].off_platform_handoff, ("plate_reader",))
        self.assertEqual(tasks["T013"].difficulty, "Easy")
        self.assertEqual(tasks["T045"].difficulty, "Medium")


if __name__ == "__main__":
    unittest.main()

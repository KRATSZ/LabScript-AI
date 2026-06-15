from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.tasks import load_authoring_tasks

from scripts.collect_opentrons_ai_responses import (
    extract_protocol_from_text,
    write_collection_outputs,
)
from scripts.ingest_opentrons_ai_run import ingest_task


TASKS_PATH = Path("benchmarks/authoring/tasks.yaml")


class OpentronsAiRunTests(unittest.TestCase):
    def test_extract_protocol_from_markdown_fence(self) -> None:
        response = """Here is the protocol:

```python
from opentrons import protocol_api

metadata = {"apiLevel": "2.14"}

def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "1")
    protocol.comment(str(plate))
```
"""

        extracted = extract_protocol_from_text(response)

        self.assertEqual(extracted.status, "ok")
        self.assertEqual(extracted.method, "markdown_fence")
        self.assertIn("def run(", extracted.protocol_text)

    def test_refusal_is_not_extracted_as_protocol(self) -> None:
        extracted = extract_protocol_from_text(
            "I cannot help write this protocol because it is unsupported by policy."
        )

        self.assertEqual(extracted.status, "refused")
        self.assertEqual(extracted.protocol_text, "")

    def test_ingest_no_protocol_counts_denominator_without_provider_error(self) -> None:
        task = load_authoring_tasks(TASKS_PATH)[0]
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_collection_outputs(
                out_dir=out_dir,
                record={
                    "task_id": task.task_id,
                    "difficulty": task.difficulty,
                    "holdout": task.holdout,
                    "prompt_hash": "sha256:test",
                    "full_prompt": task.prompt,
                },
                response_text="I cannot provide a protocol for this task.",
            )

            record = ingest_task(
                task=task,
                output_dir=out_dir,
                tasks_path=TASKS_PATH,
                simulate=False,
                opentrons_python=None,
                workspace_root=None,
                simulation_timeout_sec=1,
            )

        self.assertEqual(record["failure_mode"], "unsupported")
        self.assertEqual(record["provider_error_count"], 0)
        self.assertFalse(record["validation"]["ok"])

    def test_ingest_rederives_sidecars_after_protocol_repair(self) -> None:
        task = load_authoring_tasks(TASKS_PATH)[0]
        response = """```python
from opentrons import protocol_api

metadata = {"apiLevel": "2.15"}

def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "1")
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "2")
    pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])
    pipette.pick_up_tip()
    pipette.drop_tip()
```
"""
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_collection_outputs(
                out_dir=out_dir,
                record={
                    "task_id": task.task_id,
                    "difficulty": task.difficulty,
                    "holdout": task.holdout,
                    "prompt_hash": "sha256:test",
                    "full_prompt": task.prompt,
                },
                response_text=response,
            )

            record = ingest_task(
                task=task,
                output_dir=out_dir,
                tasks_path=TASKS_PATH,
                simulate=False,
                opentrons_python=None,
                workspace_root=None,
                simulation_timeout_sec=1,
            )

        issue_codes = {issue["code"] for issue in record["validation"]["issues"]}
        self.assertIn("guarded pick_up_tip with tiprack reset", record["repairs"])
        self.assertNotIn("hash_mismatch", issue_codes)


if __name__ == "__main__":
    unittest.main()

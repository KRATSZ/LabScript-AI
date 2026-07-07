from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from labscriptai.benchmark.tasks import AuthoringTask
from labscriptai.benchmark.validators.models import PackageValidationResult
from native_agent_baseline_common import NativeAgentSpec, TokenUsage, run_task
from scripts.run_claude_authoring_baseline import SPEC, _claude_command


class RepairText(str):
    def __new__(cls, value: str) -> "RepairText":
        obj = str.__new__(cls, value)
        obj.usage = {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
        return obj


def _passing_validation(package_dir: Path, *, simulation_pass: bool, **_kwargs: object) -> PackageValidationResult:
    return PackageValidationResult(
        package_dir=str(package_dir),
        package_complete=True,
        simulation_pass=simulation_pass,
        deck_consistency_score=1.0,
        volume_feasibility_score=1.0,
        tip_budget_score=1.0,
        contamination_safety_score=1.0,
        risk_flag_recall=1.0,
        handoff_declared_score=1.0,
    )


class RunClaudeAuthoringBaselineTests(unittest.TestCase):
    def test_claude_command_uses_explicit_opus_model_and_prompt_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            prompt_path = work_dir / "prompt.txt"

            cmd = _claude_command(work_dir, prompt_path, "hello")
            prompt_text = prompt_path.read_text(encoding="utf-8")

        self.assertEqual(cmd[:4], ["claude", "-p", "--model", "claude-opus-4-8"])
        self.assertEqual(cmd[-1], "prompt.txt")
        self.assertEqual(prompt_text, "hello")

    def test_spec_uses_prompt_file_instead_of_stdin(self) -> None:
        self.assertFalse(SPEC.prompt_stdin)

    def test_native_run_task_records_rewrite_simulation_repair_fields(self) -> None:
        task = AuthoringTask(
            task_id="T999",
            source="unit",
            difficulty="Easy",
            holdout=False,
            output_contract="protocol.py",
            prompt="Write a small protocol.",
        )
        spec = NativeAgentSpec(
            system_id="unit_agent",
            model_id="unit-model",
            scaffold_id="unit-scaffold",
            log_prefix="unit",
            executable="unit-agent",
            default_scratch_root=Path("/tmp/unit-agent"),
            default_derive_scaffold_id="unit-derived",
            command_builder=lambda work_dir, prompt_path, prompt: ["unit-agent", prompt_path.name],
            display_command=("unit-agent", "prompt.txt"),
            disabled_features=(),
            token_parser=lambda _text: TokenUsage(
                input_tokens=2,
                output_tokens=3,
                total_tokens=5,
            ),
        )

        def fake_agent_run(cmd, **kwargs):
            work_dir = Path(kwargs["cwd"])
            package_dir = work_dir / "package"
            package_dir.mkdir()
            (package_dir / "protocol.py").write_text(
                'metadata = {"apiLevel": "2.15"}\n'
                "def run(protocol):\n"
                "    protocol.comment('original')\n",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        repair_calls = {"count": 0}

        def repairer(task_arg, protocol_py, simulation_result):
            repair_calls["count"] += 1
            self.assertEqual(task_arg.task_id, "T999")
            self.assertIn("original", protocol_py)
            self.assertFalse(simulation_result["ok"])
            return RepairText(protocol_py.replace("original", "repaired"))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "out"
            scratch_root = root / "scratch"
            with (
                mock.patch("native_agent_baseline_common.subprocess.run", side_effect=fake_agent_run),
                mock.patch("native_agent_baseline_common.validate_package", side_effect=_passing_validation),
                mock.patch(
                    "native_agent_baseline_common.simulate_protocol_file",
                    side_effect=[
                        {"ok": False, "returncode": 1, "stdout": "", "stderr": "bad protocol"},
                        {"ok": True, "returncode": 0, "stdout": "ok", "stderr": ""},
                    ],
                ),
                mock.patch("native_agent_baseline_common._derive_sidecars", return_value={"derived": True}),
                mock.patch(
                    "native_agent_baseline_common._derive_sidecars_for_model",
                    return_value={"derived": "after_repair"},
                ),
                mock.patch(
                    "native_agent_baseline_common.build_rewrite_protocol_repairer",
                    return_value=repairer,
                ),
            ):
                record = run_task(
                    task=task,
                    output_dir=output_dir,
                    scratch_root=scratch_root,
                    timeout_sec=30,
                    simulate=True,
                    opentrons_python=None,
                    workspace_root=None,
                    simulation_timeout_sec=5,
                    prompt_mode="minimal",
                    metadata_repair=False,
                    protocol_only=True,
                    derive_scaffold_id="unit-derived",
                    simulation_repair_attempts=3,
                    repair_api_prefix="LLM_ONLY",
                    repair_model="unit-repair-model",
                    repair_max_tokens=12000,
                    spec=spec,
                )
            saved = json.loads((output_dir / "T999" / "record.json").read_text(encoding="utf-8"))

        self.assertEqual(repair_calls["count"], 1)
        self.assertEqual(record["simulation_repair_attempts"], 1)
        self.assertEqual(saved["simulation_repair_attempts"], 1)
        self.assertEqual(saved["simulator_calls"], 2)
        self.assertEqual(saved["attempts"], 2)
        self.assertEqual(saved["repair_input_tokens"], 7)
        self.assertEqual(saved["repair_output_tokens"], 3)
        self.assertEqual(saved["repair_total_tokens"], 10)
        self.assertEqual(saved["total_tokens"], 15)
        self.assertEqual(saved["repair_model"], "unit-repair-model")
        self.assertTrue(saved["simulation"]["ok"])
        self.assertFalse(saved["first_simulation"]["ok"])
        self.assertFalse(saved["score"]["first_pass_success"])


if __name__ == "__main__":
    unittest.main()

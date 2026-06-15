from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.authoring.agent import AuthoringAgent
from labscriptai.authoring.task_state import AuthoringTaskState
from labscriptai.authoring.tools.registry import AuthoringToolRegistry
from labscriptai.benchmark.tasks import AuthoringTask
from tests.test_package_validator import write_valid_package


class ScriptedAuthoringClient:
    def __init__(self, responses):
        self.responses = iter(responses)

    def complete(self, messages, tools):
        del messages, tools
        return next(self.responses)


class AuthoringAgentTests(unittest.TestCase):
    def test_react_loop_executes_tools_and_records_counts(self) -> None:
        task = AuthoringTask(
            task_id="T999",
            source="test",
            difficulty="Easy",
            holdout=False,
            output_contract="execution_package",
            prompt="Create a simple package.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = root / "seed"
            seed.mkdir()
            write_valid_package(seed)
            responses = [
                {
                    "tool_calls": [
                        {
                            "name": "load_skill",
                            "arguments": {"name": "common_errors"},
                        },
                        *[
                            {
                                "name": "write_file",
                                "arguments": {
                                    "path": path.name,
                                    "content": path.read_text(encoding="utf-8"),
                                },
                            }
                            for path in seed.iterdir()
                        ],
                        {
                            "name": "validate_package",
                            "arguments": {"simulation_pass": True},
                        },
                    ]
                },
                {"final": {"package_ready": True}},
            ]
            agent = AuthoringAgent(client=ScriptedAuthoringClient(responses), max_steps=4)

            result = agent.run(
                task=task,
                package_dir=root / "package",
                trace_path=root / "trace.jsonl",
            )
            stats = json.loads((root / "package" / "authoring_stats.json").read_text(encoding="utf-8"))
            patch_log = (root / "package" / "authoring_patch_log.jsonl").read_text(encoding="utf-8")
            protocol_exists = (result.package_dir / "protocol.py").exists()
            packaged_agent = AuthoringAgent(
                client=ScriptedAuthoringClient(
                    [
                        responses[0],
                        {"final": {"package_ready": True}},
                    ]
                ),
                max_steps=4,
            )
            files = packaged_agent.run_to_files(task=task, work_dir=root / "packaged")

        self.assertTrue(result.completed)
        self.assertGreaterEqual(result.tool_calls, 5)
        self.assertEqual(result.skill_loads, 1)
        self.assertEqual(stats["tool_calls"], result.tool_calls)
        self.assertTrue(protocol_exists)
        self.assertIn('"tool": "write_file"', patch_log)
        self.assertIn('"tool": "validate_package"', patch_log)
        self.assertIn("trace.jsonl", files)
        self.assertIn('"event_type": "tool_call"', files["trace.jsonl"])

    def test_authoring_tools_support_json_set_and_append_md_patch_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "manifest.json").write_text(
                json.dumps({"schema_version": "0.1", "task_id": "T001"}),
                encoding="utf-8",
            )
            registry = AuthoringToolRegistry(
                package_dir=package_dir,
                state=AuthoringTaskState(run_id="authoring-test", task_id="T001"),
            )

            json_result = registry.call(
                "json_set",
                {
                    "path": "manifest.json",
                    "pointer": "/metadata/operator",
                    "value": "LabscriptAI",
                    "reason": "add package owner",
                },
            )
            md_result = registry.call(
                "append_md",
                {
                    "path": "runbook.md",
                    "text": "## Setup\n\nLoad the plate before starting.",
                    "reason": "add setup note",
                },
            )

            manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
            runbook = (package_dir / "runbook.md").read_text(encoding="utf-8")
            log_entries = [
                json.loads(line)
                for line in (package_dir / "authoring_patch_log.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertTrue(json_result.ok)
        self.assertTrue(md_result.ok)
        self.assertEqual(manifest["metadata"]["operator"], "LabscriptAI")
        self.assertIn("Load the plate", runbook)
        self.assertEqual([entry["schema_version"] for entry in log_entries], ["0.1", "0.1"])
        self.assertEqual([entry["tool"] for entry in log_entries], ["json_set", "append_md"])
        self.assertEqual(log_entries[0]["target_path"], "manifest.json")

    def test_authoring_tool_registry_can_disable_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = AuthoringToolRegistry(
                package_dir=Path(tmp),
                state=AuthoringTaskState(run_id="authoring-test", task_id="T001"),
                skill_mode="off",
            )

            tools = {tool["name"] for tool in registry.list_tool_specs()}
            result = registry.call("load_skill", {"name": "tip_management"})

        self.assertNotIn("load_skill", tools)
        self.assertFalse(result.ok)
        self.assertEqual(result.content["error"], "unknown tool: load_skill")

    def test_authoring_tool_registry_light_mode_limits_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = AuthoringToolRegistry(
                package_dir=Path(tmp),
                state=AuthoringTaskState(run_id="authoring-test", task_id="T001"),
                skill_mode="light",
            )

            blocked = registry.call("load_skill", {"name": "tip_management"})
            allowed = registry.call("load_skill", {"name": "common_errors"})

        self.assertFalse(blocked.ok)
        self.assertIn("skill disabled in light mode", blocked.content["error"])
        self.assertTrue(allowed.ok)

    def test_authoring_tool_profiles_expose_scaffold_ablation_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edit_registry = AuthoringToolRegistry(
                package_dir=root / "edit",
                state=AuthoringTaskState(run_id="authoring-edit", task_id="T001"),
                skill_mode="off",
                tool_profile="edit",
            )
            simulate_registry = AuthoringToolRegistry(
                package_dir=root / "simulate",
                state=AuthoringTaskState(run_id="authoring-simulate", task_id="T001"),
                skill_mode="off",
                tool_profile="simulate",
            )
            kb_registry = AuthoringToolRegistry(
                package_dir=root / "kb",
                state=AuthoringTaskState(run_id="authoring-kb", task_id="T001"),
                skill_mode="light",
                tool_profile="kb",
            )

            edit_tools = {tool["name"] for tool in edit_registry.list_tool_specs()}
            simulate_tools = {tool["name"] for tool in simulate_registry.list_tool_specs()}
            kb_tools = {tool["name"] for tool in kb_registry.list_tool_specs()}

        self.assertIn("write_file", edit_tools)
        self.assertNotIn("run_simulate", edit_tools)
        self.assertNotIn("load_skill", edit_tools)
        self.assertIn("run_simulate", simulate_tools)
        self.assertNotIn("load_skill", simulate_tools)
        self.assertIn("run_simulate", kb_tools)
        self.assertIn("load_skill", kb_tools)
        self.assertNotIn("search_protocol_library", kb_tools)

    def test_protocol_only_run_to_files_derives_sidecars(self) -> None:
        task = AuthoringTask(
            task_id="T998",
            source="test",
            difficulty="Easy",
            holdout=False,
            output_contract="protocol.py only",
            prompt="Create a simple protocol.",
        )
        responses = [
            {
                "tool_calls": [
                    {
                        "name": "write_file",
                        "arguments": {
                            "path": "protocol.py",
                            "content": (
                                'metadata = {"apiLevel": "2.15"}\n'
                                "def run(protocol):\n"
                                "    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')\n"
                                "    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '2')\n"
                                "    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips])\n"
                                "    pipette.pick_up_tip()\n"
                                "    pipette.drop_tip()\n"
                            ),
                        },
                    }
                ]
            },
            {"final": {"package_ready": True}},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            files = AuthoringAgent(
                client=ScriptedAuthoringClient(responses),
                max_steps=4,
                protocol_only=True,
            ).run_to_files(task=task, work_dir=Path(tmp) / "protocol-only")

        self.assertIn("protocol.py", files)
        self.assertIn("manifest.json", files)
        self.assertIn("setup_card.html", files)
        manifest = json.loads(files["manifest.json"])
        self.assertEqual(manifest["derive"]["source"], "protocol.py")


if __name__ == "__main__":
    unittest.main()

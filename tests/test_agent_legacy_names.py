from __future__ import annotations

from labscriptai.agent.tools import ToolCall


def test_legacy_name_mapping() -> None:
    cases = {
        "read_file": "read",
        "write_file": "write",
        "str_replace": "str_replace",
        "json_set": "json_set",
        "append_md": "append_md",
    }
    for legacy_name, op in cases.items():
        call = ToolCall.from_model(
            {
                "name": legacy_name,
                "arguments": {"path": "protocol.py"},
            }
        )
        assert call.name == "package.read_write"
        assert call.arguments["op"] == op
        assert call.arguments["path"] == "protocol.py"


def test_safe_run_tool_name_mapping() -> None:
    cases = {
        "robot_inspect": "robot.inspect",
        "error_parse": "error.parse",
        "recovery_suggest": "recovery.suggest",
        "run_control": "run.control",
        "package_read_write": "package.read_write",
        "package_validate": "package.validate",
        "package_simulate": "package.simulate",
        "skill_search_load": "skill.search_load",
        "memory_read_write": "memory.read_write",
        "protocol_search": "protocol.search",
    }
    for model_name, internal_name in cases.items():
        call = ToolCall.from_model({"name": model_name, "arguments": {"reason": "test"}})
        assert call.name == internal_name
        assert call.arguments["reason"] == "test"

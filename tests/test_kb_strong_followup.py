from __future__ import annotations

import pytest

from labscriptai.authoring import kb_context
from labscriptai.authoring.diff_edit import DiffEditError, apply_search_replace_diff
from labscriptai.agent.facade import UnifiedAuthoringFacade
from labscriptai.benchmark.tasks import AuthoringTask, TaskSpec


def test_diff_edit_replaces_exact_search_block() -> None:
    result = apply_search_replace_diff(
        "alpha\nold()\nomega\n",
        "------- SEARCH\nold()\n=======\nnew()\n+++++++ REPLACE\n",
    )

    assert result.content == "alpha\nnew()\nomega\n"
    assert result.applied_count == 1
    assert result.rejected_count == 0


def test_diff_edit_matches_line_trimmed_search_block() -> None:
    result = apply_search_replace_diff(
        "def run(protocol):\n    pipette.aspirate(300, source)\n",
        (
            "------- SEARCH\n"
            "pipette.aspirate(300, source)\n"
            "=======\n"
            "pipette.aspirate(250, source)\n"
            "+++++++ REPLACE\n"
        ),
    )

    assert result.content == "def run(protocol):\n    pipette.aspirate(250, source)\n"


def test_diff_edit_matches_by_block_anchors() -> None:
    result = apply_search_replace_diff(
        "start()\nkeep_original_middle()\nend()\n",
        (
            "------- SEARCH\n"
            "start()\n"
            "model_guessed_middle()\n"
            "end()\n"
            "=======\n"
            "start()\n"
            "fixed_middle()\n"
            "end()\n"
            "+++++++ REPLACE\n"
        ),
    )

    assert result.content == "start()\nfixed_middle()\nend()\n"


def test_diff_edit_rejects_missing_search_block() -> None:
    with pytest.raises(DiffEditError, match="did not match"):
        apply_search_replace_diff(
            "alpha\n",
            "------- SEARCH\nmissing\n=======\nnew\n+++++++ REPLACE\n",
        )


def test_diff_edit_rejects_overlapping_blocks() -> None:
    with pytest.raises(DiffEditError, match="overlap"):
        apply_search_replace_diff(
            "old()\n",
            (
                "------- SEARCH\n"
                "old()\n"
                "=======\n"
                "new_a()\n"
                "+++++++ REPLACE\n"
                "------- SEARCH\n"
                "old()\n"
                "=======\n"
                "new_b()\n"
                "+++++++ REPLACE\n"
            ),
        )


def test_diff_edit_rejects_malformed_block() -> None:
    with pytest.raises(DiffEditError, match="unterminated"):
        apply_search_replace_diff(
            "old()\n",
            "------- SEARCH\nold()\n=======\nnew()\n",
        )


def test_diff_edit_applies_multiple_non_overlapping_blocks() -> None:
    result = apply_search_replace_diff(
        "old_a()\nkeep()\nold_b()\n",
        (
            "------- SEARCH\n"
            "old_a()\n"
            "=======\n"
            "new_a()\n"
            "+++++++ REPLACE\n"
            "------- SEARCH\n"
            "old_b()\n"
            "=======\n"
            "new_b()\n"
            "+++++++ REPLACE\n"
        ),
    )

    assert result.content == "new_a()\nkeep()\nnew_b()\n"
    assert result.applied_count == 2


def test_compact_kb_context_limits_hits_and_omits_long_protocol_description(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    failure_patterns = tmp_path / "failure_patterns.json"
    failure_patterns.write_text(
        """
[
  {
    "task_type": "serial_dilution",
    "common_failure": "Overlong failure text that should be trimmed but retained.",
    "fix": "Use a source well, transfer stepwise, and mix after each dilution.",
    "preferred_labware": "should not be included in compact mode",
    "preferred_pipette": "should not be included in compact mode"
  },
  {
    "task_type": "serial_dilution",
    "common_failure": "second hit",
    "fix": "second fix"
  }
]
""",
        encoding="utf-8",
    )

    def fake_search(task_types, repo_root, *, max_items, compact):
        assert max_items == 1
        assert compact is True
        return [
            {
                "task_type": task_types[0],
                "title": "Reference",
                "path": "protocols/reference.py",
                "why_relevant": "Closest reference found for serial_dilution.",
            }
        ]

    monkeypatch.setattr(kb_context, "_search_protocols", fake_search)
    task = AuthoringTask(
        task_id="T067",
        source="test",
        difficulty="Medium",
        holdout=True,
        output_contract="package",
        prompt="Create a serial dilution protocol.",
    )

    context = kb_context.build_kb_context(
        task,
        failure_patterns_path=failure_patterns,
        repo_root=tmp_path,
        context_mode="compact",
    )
    payload = context.to_prompt_payload()

    assert context.context_mode == "compact"
    assert context.to_stats()["protocol_hits"] == 1
    assert context.to_stats()["memory_hits"] == 1
    assert context.to_stats()["kb_context_tokens_estimate"] <= 250
    assert "summary" not in payload["protocol_reference_summaries"][0]
    assert "description" not in payload["protocol_reference_summaries"][0]
    assert "preferred_labware" not in payload["failure_patterns"][0]


def test_compact_v2_uses_obligations_without_protocol_search(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    def fail_search(*args, **kwargs):
        raise AssertionError("compact_v2 must not search protocol references at startup")

    monkeypatch.setattr(kb_context, "_search_protocols", fail_search)
    task = AuthoringTask(
        task_id="T083",
        source="test",
        difficulty="Hard",
        holdout=True,
        output_contract="package",
        prompt="Transfer into 24 wells with positive control at A1 and negative control at H12. Confirm module state.",
        legacy_type="module_state_pause",
        spec=TaskSpec(
            default_samples=24,
            controls={"positive": ["A1"], "negative": ["H12"]},
        ),
    )

    context = kb_context.build_kb_context(task, repo_root=tmp_path, context_mode="compact_v2")
    payload = context.to_prompt_payload()

    assert payload["context_mode"] == "compact_v2"
    assert payload["legacy_type"] == "module_state_pause"
    assert payload["task_types"] == ["module_usage"]
    assert payload["task_obligations"]["default_samples"] == 24
    assert "skill_summaries" not in payload
    assert "protocol_reference_summaries" not in payload
    assert context.to_stats()["protocol_hits"] == 0
    assert context.to_stats()["kb_context_tokens_estimate"] <= 350


def test_unified_no_kb_gets_contract_without_kb_context() -> None:
    task = AuthoringTask(
        task_id="T001",
        source="test",
        difficulty="Easy",
        holdout=True,
        output_contract="package",
        prompt="Transfer 10 uL.",
    )
    facade = UnifiedAuthoringFacade(
        client=object(),
        tool_profile="simulate",
        skill_mode="off",
        kb_context_mode="none",
    )
    messages = facade._initial_messages(task)
    payload = __import__("json").loads(messages[1]["content"])

    assert "semantic_output_contract" in payload
    assert "kb_strong_context" not in payload

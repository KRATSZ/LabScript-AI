# -*- coding: utf-8 -*-
"""Unit tests for the pure-Python Opentrons code generation loop."""

import asyncio

import pytest

from backend.code_runner import run_code_generation_python_stream
from backend.llm_client import _extract_message_content
from backend.opentrons_utils import is_non_fatal_warning

SEPARATOR = "\n---CONFIG_SEPARATOR---\n"

VALID_OT2 = """from opentrons import protocol_api

metadata = {'apiLevel': '2.19'}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])
    p300.pick_up_tip()
    p300.aspirate(50, reservoir['A1'])
    p300.dispense(50, plate['A1'])
    p300.drop_tip()
"""

INVALID_OT2 = """from opentrons import protocol_api

metadata = {'apiLevel': '2.19'}

def run(protocol: protocol_api.ProtocolContext):
    protocol.load_labware('not_a_real_labware', '1')
"""

RAISE_ONLY = """from opentrons import protocol_api

metadata = {'apiLevel': '2.19'}

def run(protocol: protocol_api.ProtocolContext):
    raise RuntimeError("impossible labware and volume")
"""

RAISE_AFTER_LOAD = """from opentrons import protocol_api

metadata = {'apiLevel': '2.19'}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_20ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    p20 = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=[tiprack])
    raise RuntimeError("P20 cannot aspirate 300 uL")
"""

VALID_FLEX = """from opentrons import protocol_api

requirements = {'robotType': 'Flex', 'apiLevel': '2.21'}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'D1')
    pipette = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])
    pipette.pick_up_tip()
    pipette.aspirate(50, plate['A1'])
    pipette.dispense(50, plate['A2'])
    pipette.drop_tip()
"""

TOOL_INPUT = (
    "1. Transfer 50 uL from reservoir A1 to plate A1.\n"
    + SEPARATOR
    + "Robot Model: OT-2\nAPI Version: 2.19\nLeft Pipette: p300_single_gen2\n"
    "Deck Layout:\n  1: opentrons_96_tiprack_300ul\n"
    "  2: corning_96_wellplate_360ul_flat\n"
    "  3: nest_12_reservoir_15ml"
)


def _ok_sim(_code, return_structured=True):
    return {
        "success": True,
        "has_warnings": False,
        "error_details": "",
        "warning_details": "",
        "raw_output": "--- Simulation STDOUT ---\nok\n--- Simulation STDERR ---\n",
        "final_status": "成功",
    }


def _fail_sim(_code, return_structured=True):
    return {
        "success": False,
        "has_warnings": False,
        "error_details": "LabwareLoadError: cannot find a definition for labware not_a_real_labware",
        "warning_details": "",
        "raw_output": "Traceback (most recent call last):\nLabwareLoadError: cannot find a definition for labware not_a_real_labware",
        "final_status": "失败",
    }


def _warn_sim(_code, return_structured=True):
    return {
        "success": True,
        "has_warnings": True,
        "error_details": "",
        "warning_details": "Belt calibration not found; using default pipette calibration",
        "raw_output": "--- Simulation STDOUT ---\nok\n--- Simulation STDERR ---\nBelt calibration not found",
        "final_status": "成功，但有警告",
    }


async def _collect(agen):
    return [event async for event in agen]


def _types(events):
    return [e["event_type"] for e in events]


def _nodes(events):
    return [e.get("node_name") for e in events if e["event_type"] == "node_complete"]


@pytest.mark.asyncio
async def test_success_event_sequence():
    async def fake_complete(_prompt: str) -> str:
        return VALID_OT2

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=3,
            complete_fn=fake_complete,
            simulate_fn=_ok_sim,
        )
    )
    assert _types(events) == [
        "start",
        "initialization",
        "node_complete",
        "node_complete",
        "attempt_result",
        "final_result",
    ]
    assert _nodes(events) == ["generator", "simulator"]
    assert events[2]["has_code"] is True
    assert events[3]["simulation_success"] is True
    assert events[4]["status"] == "SUCCESS"
    assert events[5]["status"] == "success"
    assert events[5]["generated_code"].strip() == VALID_OT2.strip()
    assert events[5]["total_attempts"] == 1
    assert "stream_complete" not in _types(events)


@pytest.mark.asyncio
async def test_simulation_failure_retries_via_feedback():
    codes = [INVALID_OT2, VALID_OT2]
    sims = [_fail_sim, _ok_sim]

    async def fake_complete(_prompt: str) -> str:
        return codes.pop(0)

    def fake_sim(code, return_structured=True):
        return sims.pop(0)(code, return_structured=return_structured)

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=3,
            complete_fn=fake_complete,
            simulate_fn=fake_sim,
        )
    )
    assert _nodes(events) == ["generator", "simulator", "feedback_preparer", "generator", "simulator"]
    feedback = next(e for e in events if e.get("node_name") == "feedback_preparer")
    assert feedback["has_feedback"] is True
    assert "Labware" in feedback["error_analysis"] or feedback["error_analysis"]
    assert events[-2]["event_type"] == "attempt_result"
    assert events[-2]["status"] == "SUCCESS"
    assert events[-1]["status"] == "success"
    assert events[-1]["total_attempts"] == 2


@pytest.mark.asyncio
async def test_heartbeat_while_complete_is_slow():
    async def slow_complete(_prompt: str) -> str:
        await asyncio.sleep(0.45)
        return VALID_OT2

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=1,
            complete_fn=slow_complete,
            simulate_fn=_ok_sim,
            heartbeat_interval=0.15,
        )
    )
    thinking = [e for e in events if e["event_type"] == "thinking"]
    assert len(thinking) >= 2
    assert all(e["message"] == "Model is reasoning..." for e in thinking)
    assert _types(events)[:2] == ["start", "initialization"]
    assert "thinking" in _types(events)
    assert events[-1]["status"] == "success"


@pytest.mark.asyncio
async def test_aclose_cancels_slow_complete_without_orphan():
    started = asyncio.Event()
    cancelled = False

    async def slow_complete(_prompt: str) -> str:
        nonlocal cancelled
        started.set()
        try:
            await asyncio.sleep(30)
            return VALID_OT2
        except asyncio.CancelledError:
            cancelled = True
            raise

    agen = run_code_generation_python_stream(
        TOOL_INPUT,
        max_iterations=1,
        complete_fn=slow_complete,
        simulate_fn=_ok_sim,
        heartbeat_interval=0.2,
    )

    async def pump():
        async for _event in agen:
            pass

    task = asyncio.create_task(pump())
    await asyncio.wait_for(started.wait(), timeout=2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(0.05)
    leftover = [
        t
        for t in asyncio.all_tasks()
        if not t.done() and t is not asyncio.current_task()
    ]
    assert cancelled is True
    assert leftover == []


@pytest.mark.asyncio
async def test_exhausted_retries_emit_final_failed():
    async def fake_complete(_prompt: str) -> str:
        return INVALID_OT2

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=2,
            complete_fn=fake_complete,
            simulate_fn=_fail_sim,
        )
    )
    attempt = next(e for e in events if e["event_type"] == "attempt_result")
    assert attempt["status"] == "FINAL_FAILED"
    final = events[-1]
    assert final["event_type"] == "final_result"
    assert final["status"] == "failure"
    assert "协议生成失败报告" in final["error_report"]
    assert final["total_attempts"] == 2


@pytest.mark.asyncio
async def test_empty_complete_stops_after_two_attempts():
    calls = {"n": 0}

    async def fake_complete(_prompt: str) -> str:
        calls["n"] += 1
        return ""

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=9,
            complete_fn=fake_complete,
            simulate_fn=_ok_sim,
        )
    )
    assert calls["n"] == 2
    attempt = next(e for e in events if e["event_type"] == "attempt_result")
    assert attempt["status"] == "FINAL_FAILED"
    assert "可执行协议代码" in attempt["error_details"]
    final = events[-1]
    assert final["event_type"] == "final_result"
    assert final["status"] == "failure"
    assert "可执行协议代码" in final["error_details"]
    assert final["total_attempts"] == 2


@pytest.mark.asyncio
async def test_first_empty_then_valid_code_succeeds():
    codes = ["", VALID_OT2]

    async def fake_complete(_prompt: str) -> str:
        return codes.pop(0)

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=9,
            complete_fn=fake_complete,
            simulate_fn=_ok_sim,
        )
    )
    assert _nodes(events) == [
        "generator",
        "simulator",
        "feedback_preparer",
        "generator",
        "simulator",
    ]
    assert events[-2]["status"] == "SUCCESS"
    assert events[-1]["status"] == "success"
    assert events[-1]["generated_code"].strip() == VALID_OT2.strip()
    assert events[-1]["total_attempts"] == 2


@pytest.mark.asyncio
async def test_raise_only_not_success_even_if_simulate_ok():
    async def fake_complete(_prompt: str) -> str:
        return RAISE_ONLY

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=1,
            complete_fn=fake_complete,
            simulate_fn=_ok_sim,
        )
    )
    attempt = next(e for e in events if e["event_type"] == "attempt_result")
    assert attempt["status"] == "FINAL_FAILED"
    assert "可执行协议" in attempt["error_details"]
    assert events[-1]["status"] == "failure"
    assert not any(
        e.get("status") in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}
        for e in events
        if e["event_type"] == "attempt_result"
    )

    codes = [RAISE_ONLY, VALID_OT2]

    async def fake_complete_retry(_prompt: str) -> str:
        return codes.pop(0)

    retry_events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=3,
            complete_fn=fake_complete_retry,
            simulate_fn=_ok_sim,
        )
    )
    assert "feedback_preparer" in _nodes(retry_events)
    first_sim = next(e for e in retry_events if e.get("node_name") == "simulator")
    assert first_sim["simulation_success"] is False
    assert "可执行协议" in first_sim["error_details"]
    assert retry_events[-2]["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_empty_sop_or_hardware_errors_without_llm():
    async def boom(_prompt: str) -> str:
        raise AssertionError("complete should not be called")

    empty_sop = await _collect(
        run_code_generation_python_stream(
            SEPARATOR + "Robot Model: OT-2\nAPI Version: 2.19",
            max_iterations=3,
            complete_fn=boom,
            simulate_fn=_ok_sim,
        )
    )
    assert empty_sop[-1]["event_type"] == "error"
    assert "SOP" in empty_sop[-1]["message"]
    assert "initialization" not in _types(empty_sop)

    empty_hw = await _collect(
        run_code_generation_python_stream(
            "1. Transfer 50 uL." + SEPARATOR,
            max_iterations=3,
            complete_fn=boom,
            simulate_fn=_ok_sim,
        )
    )
    assert empty_hw[-1]["event_type"] == "error"
    assert "hardware_context" in empty_hw[-1]["message"]
    assert "initialization" not in _types(empty_hw)


@pytest.mark.asyncio
async def test_valid_flex_with_calibration_warnings_still_succeeds():
    async def fake_complete(_prompt: str) -> str:
        return VALID_FLEX

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=3,
            complete_fn=fake_complete,
            simulate_fn=_warn_sim,
        )
    )
    assert events[-2]["event_type"] == "attempt_result"
    assert events[-2]["status"] == "SUCCESS_WITH_WARNINGS"
    assert events[-1]["status"] == "success"
    assert events[-1]["has_warnings"] is True
    assert "calibration" in events[-2]["warning_details"].lower()


def test_extract_message_content_joins_text_parts():
    data = {
        "choices": [
            {
                "message": {
                    "reasoning_content": "should be ignored",
                    "content": [
                        {"type": "text", "text": "def run("},
                        {"type": "reasoning", "text": "hidden"},
                        {"type": "text", "text": "protocol):\n    pass"},
                    ],
                }
            }
        ]
    }
    assert _extract_message_content(data) == "def run(protocol):\n    pass"
    assert _extract_message_content({"choices": [{"message": {"content": ""}}]}) == ""


@pytest.mark.asyncio
async def test_load_then_raise_not_success_even_if_simulate_ok():
    async def fake_complete(_prompt: str) -> str:
        return RAISE_AFTER_LOAD

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=1,
            complete_fn=fake_complete,
            simulate_fn=_ok_sim,
        )
    )
    attempt = next(e for e in events if e["event_type"] == "attempt_result")
    assert attempt["status"] == "FINAL_FAILED"
    assert events[-1]["status"] == "failure"
    assert not any(
        e.get("status") in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}
        for e in events
        if e["event_type"] == "attempt_result"
    )


@pytest.mark.asyncio
async def test_simulate_warning_that_is_really_runtimeerror_is_failure():
    def fake_success_with_runtimeerror(_code, return_structured=True):
        stderr = (
            "/Users/test/.opentrons/robot_settings.json not found. Loading defaults\n"
            "Deck calibration not found.\n"
            "RuntimeError: P20 cannot aspirate 300 uL\n"
        )
        return {
            "success": True,
            "has_warnings": True,
            "error_details": "",
            "warning_details": stderr,
            "raw_output": "--- Simulation STDOUT ---\n\n--- Simulation STDERR ---\n" + stderr,
            "final_status": "成功，但有警告",
        }

    async def fake_complete(_prompt: str) -> str:
        return VALID_OT2

    events = await _collect(
        run_code_generation_python_stream(
            TOOL_INPUT,
            max_iterations=1,
            complete_fn=fake_complete,
            simulate_fn=fake_success_with_runtimeerror,
        )
    )
    assert events[-1]["status"] == "failure"
    assert "RuntimeError" in events[-1]["error_details"]


def test_runtimeerror_plus_calibration_is_fatal():
    stderr = (
        "/Users/test/.opentrons/robot_settings.json not found. Loading defaults\n"
        "Deck calibration not found.\n"
        "RuntimeError: P20 cannot aspirate 300 uL\n"
    )
    assert is_non_fatal_warning(stderr) is False
    assert is_non_fatal_warning(
        "/Users/test/.opentrons/robot_settings.json not found. Loading defaults\n"
        "Deck calibration not found.\n"
    ) is True

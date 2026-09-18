# -*- coding: utf-8 -*-
"""Regression tests for Opentrons trash handling and warning propagation."""

from backend.langchain_agent import should_continue
from backend.opentrons_utils import get_error_recommendations, is_non_fatal_warning


def test_runtimeerror_with_calibration_noise_is_fatal():
    stderr = (
        "/Users/test/.opentrons/robot_settings.json not found. Loading defaults\n"
        "Deck calibration not found.\n"
        "RuntimeError: P20 cannot aspirate 300 uL\n"
    )
    assert is_non_fatal_warning(stderr) is False


def test_no_trash_defined_error_is_fatal():
    stderr = (
        "/Users/test/.opentrons/robot_settings.json not found. Loading defaults\n"
        "Belt calibration not found.\n"
        "NoTrashDefinedError [line 45]: Error 4000 GENERAL_ERROR "
        "(NoTrashDefinedError): No trash container has been defined in this protocol."
    )

    assert is_non_fatal_warning(stderr) is False
    assert any("protocol.load_trash_bin" in item for item in get_error_recommendations(stderr))


def test_warning_details_are_reported_on_success_with_warnings():
    events = []
    state = {
        "simulation_result": {
            "success": True,
            "has_warnings": True,
            "warning_details": "Belt calibration not found.",
            "error_details": "",
        },
        "attempts": 1,
        "max_attempts": 3,
        "iteration_reporter": events.append,
    }

    assert should_continue(state) == "end"
    assert events[-1]["status"] == "SUCCESS_WITH_WARNINGS"
    assert events[-1]["warning_details"] == "Belt calibration not found."

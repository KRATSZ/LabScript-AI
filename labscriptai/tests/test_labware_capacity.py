"""Unit tests for labware max-volume inference."""

from __future__ import annotations

import pytest

from labscriptai.benchmark.logicpass.labware_capacity import (
    infer_max_volume_ul_from_labware_name,
    infer_max_volume_ul_from_labware_record,
    labware_max_ul_from_analyze_labware,
)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("nest_96_wellplate_200ul_flat", 200.0),
        ("corning_96_wellplate_360ul_flat", 360.0),
        ("nest_12_reservoir_15ml", 15000.0),
        ("opentrons/nest_96_wellplate_200ul_flat/2", 200.0),
        ("garbage_labware_no_hint", None),
        ("", None),
        (None, None),
    ],
)
def test_infer_max_volume_ul_from_labware_name(name: str | None, expected: float | None) -> None:
    assert infer_max_volume_ul_from_labware_name(name) == expected


def test_infer_max_volume_ul_from_labware_record_prefers_load_name() -> None:
    record = {
        "id": "plate",
        "loadName": "nest_96_wellplate_200ul_flat",
        "displayName": "corning_96_wellplate_360ul_flat",
    }
    assert infer_max_volume_ul_from_labware_record(record) == 200.0


def test_labware_max_ul_from_analyze_labware() -> None:
    labware = (
        {"id": "plate", "loadName": "nest_96_wellplate_200ul_flat"},
        {"id": "res", "definitionUri": "opentrons/nest_12_reservoir_15ml/1"},
        {"id": "unknown"},
    )
    assert labware_max_ul_from_analyze_labware(labware) == {
        "plate": 200.0,
        "res": 15000.0,
    }

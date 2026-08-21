"""Scenario presets distilled from real Flex runs on Silabrobot001 (10.31.17.153).

Error payloads mirror captured robot responses (errorType/errorCode/detail/notes).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _tip_error(well: str = "A1") -> dict[str, Any]:
    return {
        "errorType": "tipPhysicallyMissing",
        "errorCode": "3003",
        "detail": "No Tip Detected",
        "isDefined": True,
        "errorInfo": {},
        "wrappedErrors": [
            {
                "errorType": "PickUpTipTipNotAttachedError",
                "errorCode": "3005",
                "detail": "Error 3005 UNEXPECTED_TIP_REMOVAL (PickUpTipTipNotAttachedError)",
                "isDefined": False,
                "errorInfo": {},
                "wrappedErrors": [],
            }
        ],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "longMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "source": "execution",
            }
        ],
        "recovery_policy": "WAIT_FOR_RECOVERY",
    }


def _liquid_not_found_error() -> dict[str, Any]:
    return {
        "errorType": "liquidNotFound",
        "errorCode": "2017",
        "detail": "Liquid Not Found",
        "isDefined": True,
        "errorInfo": {},
        "wrappedErrors": [
            {
                "errorType": "PipetteLiquidNotFoundError",
                "errorCode": "2017",
                "detail": "Liquid not found during probe.",
                "isDefined": False,
                "errorInfo": {"P_L": "19.749", "Z_L": "158.728"},
                "wrappedErrors": [],
            }
        ],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "longMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "source": "execution",
            }
        ],
        "recovery_policy": "WAIT_FOR_RECOVERY",
    }


def _tip_not_attached_fail_run() -> dict[str, Any]:
    return {
        "errorType": "TipNotAttachedError",
        "errorCode": "3005",
        "detail": "Pipette should have a tip attached, but does not.",
        "isDefined": False,
        "errorInfo": {},
        "wrappedErrors": [],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with FAIL_RUN.",
                "longMessage": "Handling this command failure with FAIL_RUN.",
                "source": "execution",
            }
        ],
        "recovery_policy": "FAIL_RUN",
    }


def _tip_clog_error() -> dict[str, Any]:
    """Mirrors Flex overpressure / tip clog failures from decision-bench 05/06."""
    return {
        "errorType": "PipetteOverpressureError",
        "errorCode": "3006",
        "detail": "Pipette overpressure detected — possible tip clog.",
        "isDefined": True,
        "errorInfo": {},
        "wrappedErrors": [
            {
                "errorType": "OverpressureError",
                "errorCode": "3006",
                "detail": "Pressure outside limits during aspirate/dispense (clog).",
                "isDefined": False,
                "errorInfo": {},
                "wrappedErrors": [],
            }
        ],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "longMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "source": "execution",
            }
        ],
        "recovery_policy": "WAIT_FOR_RECOVERY",
    }


def _default_deck() -> dict[str, Any]:
    return {
        "cutoutFixtures": [
            {"cutoutFixtureId": "singleCenterSlot", "cutoutId": "cutoutA2"},
            {"cutoutFixtureId": "singleCenterSlot", "cutoutId": "cutoutB2"},
            {"cutoutFixtureId": "singleCenterSlot", "cutoutId": "cutoutC2"},
            {"cutoutFixtureId": "singleCenterSlot", "cutoutId": "cutoutD2"},
            {"cutoutFixtureId": "trashBinAdapter", "cutoutId": "cutoutA3"},
            {"cutoutFixtureId": "singleRightSlot", "cutoutId": "cutoutB3"},
            {"cutoutFixtureId": "singleRightSlot", "cutoutId": "cutoutC3"},
            {"cutoutFixtureId": "singleRightSlot", "cutoutId": "cutoutD3"},
            {"cutoutFixtureId": "singleLeftSlot", "cutoutId": "cutoutA1"},
            {"cutoutFixtureId": "singleLeftSlot", "cutoutId": "cutoutB1"},
            {"cutoutFixtureId": "singleLeftSlot", "cutoutId": "cutoutC1"},
            {"cutoutFixtureId": "singleLeftSlot", "cutoutId": "cutoutD1"},
        ],
        "lastModifiedAt": "2026-06-08T09:24:47.960814Z",
    }


def _base_world(**overrides: Any) -> dict[str, Any]:
    world = {
        "door_status": "closed",
        "estop_status": "disengaged",
        "tip_wells_present": {
            # B2 tiprack — column-major A1,B1,C1,... used by local protocols
            "A1": True,
            "B1": True,
            "C1": True,
            "D1": True,
            "E1": True,
            "A2": True,
            "B2": True,
            "C2": True,
        },
        "liquid_present": {
            "C2.A1": True,  # Assay Buffer primary
            "C2.A2": True,  # Assay Buffer reserve
            "C2.A3": True,  # Wash
            "C2.A4": True,  # Additive
            "D2.A1": False,
            "D2.A2": False,
            "D2.A3": False,
            "D2.H12": False,
        },
        "liquid_heights_mm": {
            "C2.A1": 18.5,
            "C2.A2": 16.11,
            "C2.A3": 17.0,
            "C2.A4": 15.0,
            "D2.A1": 4.8,
        },
        "left_tip_attached": False,
        "modules": [],
        "deck": _default_deck(),
        # Protocol script executed on play. Steps may set fail=True to inject errors.
        "script": [
            {"commandType": "home"},
            {
                "commandType": "loadLabware",
                "params": {
                    "location": {"slotName": "B2"},
                    "loadName": "opentrons_flex_96_tiprack_1000ul",
                    "namespace": "opentrons",
                    "version": 1,
                },
            },
            {
                "commandType": "loadLabware",
                "params": {
                    "location": {"slotName": "C2"},
                    "loadName": "nest_12_reservoir_15ml",
                    "namespace": "opentrons",
                    "version": 1,
                },
            },
            {
                "commandType": "loadLabware",
                "params": {
                    "location": {"slotName": "D2"},
                    "loadName": "nest_96_wellplate_200ul_flat",
                    "namespace": "opentrons",
                    "version": 1,
                },
            },
            {
                "commandType": "loadPipette",
                "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
            },
            {"commandType": "comment", "params": {"message": "Assay Buffer primary C2.A1"}},
            {"commandType": "pickUpTip", "params": {"wellName": "A1", "slotName": "B2"}},
            {
                "commandType": "liquidProbe",
                "params": {"wellName": "A1", "slotName": "C2"},
            },
            {
                "commandType": "aspirate",
                "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
            },
            {
                "commandType": "dispense",
                "params": {"wellName": "A1", "slotName": "D2", "volume": 100},
            },
            {"commandType": "dropTip", "params": {"slotName": "A3"}},
        ],
    }
    world.update(overrides)
    return world


SCENARIOS: dict[str, dict[str, Any]] = {
    "healthy": {
        "id": "healthy",
        "description": "Happy path — all tips present, liquids present, run succeeds.",
        "world": _base_world(),
    },
    # From local/log 02_triple_transfer_chain / run d3d1cdd9
    "tip_missing_budget_block": {
        "id": "tip_missing_budget_block",
        "description": (
            "First pickUpTip A1 fails tipPhysicallyMissing; only B1/C1 remain "
            "(3 pickups needed → tip budget insufficient → escalate)."
        ),
        "world": _base_world(
            tip_wells_present={
                "A1": False,
                "B1": True,
                "C1": True,
            },
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {"commandType": "comment", "params": {"message": "Step1 Assay Buffer"}},
                {
                    "commandType": "pickUpTip",
                    "params": {"wellName": "A1", "slotName": "B2"},
                    "inject_error": _tip_error("A1"),
                },
                # Remaining script is not reached until recovery + resume.
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 100},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
                {"commandType": "comment", "params": {"message": "Step2 Wash"}},
                {"commandType": "pickUpTip", "params": {"wellName": "B1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A3", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A3", "slotName": "C2", "volume": 150},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "H12", "slotName": "D2", "volume": 150},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
                {"commandType": "comment", "params": {"message": "Step3 Additive"}},
                {"commandType": "pickUpTip", "params": {"wellName": "C1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A4", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A4", "slotName": "C2", "volume": 50},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 50},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
            ],
        ),
        "meta": {
            "tip_pickups_needed": 3,
            "expected_error_leaf": "TIP_PHYSICALLY_MISSING",
            "expected_gate": "tip_budget_insufficient",
        },
    },
    # From 01_dual_well / 09_hold — tip missing but enough spares to recover
    "tip_missing_recoverable": {
        "id": "tip_missing_recoverable",
        "description": "A1 tip missing; B1+ available → tip recovery should succeed.",
        "world": _base_world(
            tip_wells_present={
                "A1": False,
                "B1": True,
                "C1": True,
                "D1": True,
                "E1": True,
                "A2": True,
                "B2": True,
                "C2": True,
            },
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {
                    "commandType": "pickUpTip",
                    "params": {"wellName": "A1", "slotName": "B2"},
                    "inject_error": _tip_error("A1"),
                },
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A2", "slotName": "D2", "volume": 100},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
            ],
        ),
        "meta": {
            "expected_error_leaf": "TIP_PHYSICALLY_MISSING",
            "expected_gate": "tip_budget_sufficient",
        },
    },
    # From 03_primary_reserve_buffer / run e977f6fa
    "liquid_not_found_with_reserve": {
        "id": "liquid_not_found_with_reserve",
        "description": (
            "pickUpTip ok; liquidProbe C2.A1 liquidNotFound; tip stays attached; "
            "C2.A2 reserve available for substitute_liquid_source_with_attached_tip."
        ),
        "world": _base_world(
            liquid_present={
                "C2.A1": False,
                "C2.A2": True,
                "C2.A3": True,
                "C2.A4": True,
                "D2.A1": False,
                "D2.A2": False,
                "D2.A3": False,
            },
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {
                    "commandType": "comment",
                    "params": {"message": "Assay Buffer primary C2.A1 -> samples A1-A3"},
                },
                {
                    "commandType": "comment",
                    "params": {"message": "Reserve same-identity stock available at C2.A2"},
                },
                {"commandType": "pickUpTip", "params": {"wellName": "A1", "slotName": "B2"}},
                {
                    "commandType": "liquidProbe",
                    "params": {"wellName": "A1", "slotName": "C2"},
                    "inject_error": _liquid_not_found_error(),
                },
                # Remaining primary transfers not reached until substitution/resume.
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 100},
                },
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A2", "slotName": "D2", "volume": 100},
                },
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A3", "slotName": "D2", "volume": 100},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
            ],
        ),
        "meta": {
            "expected_error_leaf": "INSUFFICIENT_VOLUME",
            "expected_recovery": "substitute_liquid_source_with_attached_tip",
            "same_liquid_reserve": "C2.A2",
        },
    },
    # From 04_high_volume / 08_sample_confirm — no auto substitute
    "liquid_not_found_no_reserve": {
        "id": "liquid_not_found_no_reserve",
        "description": "liquidNotFound on C2.A1 with no usable reserve → manual_only.",
        "world": _base_world(
            liquid_present={
                "C2.A1": False,
                "C2.A2": False,
                "C2.A3": False,
                "C2.A4": False,
                "D2.A1": False,
            },
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {"commandType": "pickUpTip", "params": {"wellName": "A1", "slotName": "B2"}},
                {
                    "commandType": "liquidProbe",
                    "params": {"wellName": "A1", "slotName": "C2"},
                    "inject_error": _liquid_not_found_error(),
                },
            ],
        ),
        "meta": {
            "expected_error_leaf": "INSUFFICIENT_VOLUME",
            "expected_gate": "manual_only",
        },
    },
    # From run 8ffb3139 — TipNotAttachedError FAIL_RUN
    "tip_not_attached_fail_run": {
        "id": "tip_not_attached_fail_run",
        "description": "liquidProbe without tip → TipNotAttachedError FAIL_RUN → failed.",
        "world": _base_world(
            left_tip_attached=False,
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                # Skip pickUpTip intentionally; probe fails hard.
                {
                    "commandType": "liquidProbe",
                    "params": {"wellName": "A1", "slotName": "C2"},
                    "inject_error": _tip_not_attached_fail_run(),
                    "force_no_tip": True,
                },
            ],
        ),
        "meta": {"expected_status": "failed"},
    },
    "door_open": {
        "id": "door_open",
        "description": "Door open blocker — play should be blocked / status reports door_open.",
        "world": _base_world(door_status="open"),
    },
    "estop_engaged": {
        "id": "estop_engaged",
        "description": "E-stop engaged blocker.",
        "world": _base_world(estop_status="physicallyEngaged"),
    },
    # tip recovery race from 09_hold_tolerant — tip actually attached after "missing"
    "tip_false_missing_already_attached": {
        "id": "tip_false_missing_already_attached",
        "description": (
            "pickUpTip reports tipPhysicallyMissing but left tip becomes attached "
            "(UnexpectedTipAttachError on retry) — recovery should still resume."
        ),
        "world": _base_world(
            tip_wells_present={"A1": False, "B1": True, "C1": True, "D1": True},
            # After failed A1 pickup, tip is actually on pipette (sensor glitch).
            attach_tip_on_failed_pickup=True,
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {
                    "commandType": "pickUpTip",
                    "params": {"wellName": "A1", "slotName": "B2"},
                    "inject_error": _tip_error("A1"),
                },
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 100},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
            ],
        ),
        "meta": {"expected_error_leaf": "TIP_PHYSICALLY_MISSING"},
    },
    # decision-bench 04 — reserve present but too short for remaining volume
    "liquid_reserve_volume_short": {
        "id": "liquid_reserve_volume_short",
        "description": (
            "C2.A1 liquidNotFound; C2.A2 present but height implies usable volume "
            "far below required transfer (STOP — do not substitute short reserve)."
        ),
        "world": _base_world(
            liquid_present={
                "C2.A1": False,
                "C2.A2": True,
                "C2.A3": True,
                "C2.A4": True,
                "D2.A1": False,
                "D2.A2": False,
                "D2.A3": False,
            },
            liquid_heights_mm={
                "C2.A1": 0.0,
                # ~220 µL usable after dead volume on nest_12 → insufficient for 3×200µL
                "C2.A2": 2.0,
            },
            script=_base_world()["script"],
        ),
        "meta": {
            "expected_error_leaf": "INSUFFICIENT_VOLUME",
            "expected_decision": "STOP",
            "reserve_volume_short": True,
        },
    },
    # decision-bench 05 — clog on waste path (non-precious redo)
    "tip_clog_on_waste_dispense": {
        "id": "tip_clog_on_waste_dispense",
        "description": "Overpressure/clog while discarding wash to D2.H12 (FIX: change tip, redo waste).",
        "world": _base_world(
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {"commandType": "pickUpTip", "params": {"wellName": "A1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 50},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 50},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
                {"commandType": "pickUpTip", "params": {"wellName": "B1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A3", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A3", "slotName": "C2", "volume": 200},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "H12", "slotName": "D2", "volume": 200},
                    "inject_error": _tip_clog_error(),
                },
            ],
        ),
        "meta": {"expected_error_leaf": "TIP_CLOG", "expected_decision": "FIX"},
    },
    # decision-bench 06 — clog mid precious aliquot
    "tip_clog_on_precious_aliquot": {
        "id": "tip_clog_on_precious_aliquot",
        "description": "Overpressure on 2nd precious aliquot (STOP — do not blind top-up).",
        "world": _base_world(
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {"commandType": "pickUpTip", "params": {"wellName": "A1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 100},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 100},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
                {"commandType": "pickUpTip", "params": {"wellName": "B1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A4", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A4", "slotName": "C2", "volume": 50},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 50},
                },
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A4", "slotName": "C2", "volume": 50},
                    "inject_error": _tip_clog_error(),
                },
            ],
        ),
        "meta": {"expected_error_leaf": "TIP_CLOG", "expected_decision": "STOP"},
    },
    # decision-bench 09/10 — pause after Phase 1 tip cycle
    "pause_after_phase1": {
        "id": "pause_after_phase1",
        "description": "Pause after Phase 1 completes (first dropTip); used for time-window checks.",
        "world": _base_world(),
        "meta": {"expected_decision": "FIX_or_STOP_by_elapsed"},
    },
    # decision-bench 08 — pause after sample probe with tip still attached
    "pause_after_sample_probe": {
        "id": "pause_after_sample_probe",
        "description": (
            "After LPD on sample D2.A1, pause with tip attached (sample contact). "
            "STOP if agent tries common-stock re-entry with that tip."
        ),
        "world": _base_world(
            liquid_present={
                "C2.A1": True,
                "D2.A1": True,
            },
            script=[
                {"commandType": "home"},
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "B2"},
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "C2"},
                        "loadName": "nest_12_reservoir_15ml",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadLabware",
                    "params": {
                        "location": {"slotName": "D2"},
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "namespace": "opentrons",
                        "version": 1,
                    },
                },
                {
                    "commandType": "loadPipette",
                    "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
                },
                {"commandType": "pickUpTip", "params": {"wellName": "A1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "C2"}},
                {
                    "commandType": "aspirate",
                    "params": {"wellName": "A1", "slotName": "C2", "volume": 60},
                },
                {
                    "commandType": "dispense",
                    "params": {"wellName": "A1", "slotName": "D2", "volume": 60},
                },
                {"commandType": "dropTip", "params": {"slotName": "A3"}},
                {"commandType": "pickUpTip", "params": {"wellName": "B1", "slotName": "B2"}},
                {"commandType": "liquidProbe", "params": {"wellName": "A1", "slotName": "D2"}},
                # Hold here — dropTip intentionally omitted so tip stays sample-wet.
                {"commandType": "comment", "params": {"message": "HOLD: tip on sample, do not enter stock"}},
            ],
            pause_after_script=True,
        ),
        "meta": {"expected_decision": "STOP", "contamination": "sample_tip_vs_stock"},
    },
}


def list_scenarios() -> list[dict[str, str]]:
    return [
        {"id": s["id"], "description": s["description"]}
        for s in SCENARIOS.values()
    ]


def get_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise KeyError(f"Unknown scenario '{scenario_id}'. Known: {known}")
    return deepcopy(SCENARIOS[scenario_id])

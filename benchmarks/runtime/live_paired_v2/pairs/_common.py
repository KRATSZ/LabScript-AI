"""Shared helpers for live_paired_v2 case authors."""

from __future__ import annotations

from typing import Any

TIP_ORDER = tuple(f"{row}{column}" for column in range(1, 13) for row in "ABCDEFGH")
API_LEVEL = "2.24"


def tip_protocol(case_id: str, tip_names: tuple[str, ...], *, purpose: str) -> str:
    dest_names = TIP_ORDER[: len(tip_names)]
    source_volume = max(2200, 2000 + 20 * len(tip_names))
    return f'''from opentrons import protocol_api

metadata = {{
    "protocolName": "Live Flex paired v2 {case_id}",
    "author": "LabscriptAI runtime benchmark",
    "description": "{purpose}",
}}

requirements = {{"robotType": "Flex", "apiLevel": "{API_LEVEL}"}}


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    water = protocol.define_liquid(
        name="water_control",
        description="Non-biological live recovery control liquid",
        display_color="#3B82F6",
    )
    reservoir["A1"].load_liquid(liquid=water, volume={source_volume})
    tip_names = {list(tip_names)!r}
    destination_names = {list(dest_names)!r}

    for tip_name, destination_name in zip(tip_names, destination_names):
        pipette.pick_up_tip(tiprack[tip_name])
        pipette.aspirate(20, reservoir["A1"])
        pipette.dispense(20, plate[destination_name])
        pipette.drop_tip(trash)
'''


def liquid_backup_protocol(
    case_id: str,
    *,
    liquid_id: str,
    backup_volume_ul: int,
    aspirate_ul: int,
    purpose: str,
) -> str:
    """Empty primary A1 + annotated same-liquid backup in A2 (ADV09-style volume contrast)."""
    return f'''from opentrons import protocol_api

metadata = {{
    "protocolName": "Live Flex paired v2 {case_id}",
    "author": "LabscriptAI runtime benchmark",
    "description": "{purpose}",
}}

requirements = {{"robotType": "Flex", "apiLevel": "{API_LEVEL}"}}


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    liquid = protocol.define_liquid(
        name="{liquid_id}",
        description="Control liquid identity for annotated backup discrimination (water/dye only)",
        display_color="#10B981",
    )
    # Primary A1 starts empty; A2 holds the annotated same-liquid_id backup.
    reservoir["A2"].load_liquid(liquid=liquid, volume={backup_volume_ul})
    protocol.comment(
        "A1 must start empty for liquidNotFound; A2 is annotated same-liquid backup "
        "({backup_volume_ul} uL {liquid_id})"
    )

    pipette.pick_up_tip(tiprack["A1"])
    pipette.require_liquid_presence(reservoir["A1"])
    pipette.aspirate({aspirate_ul}, reservoir["A1"])
    pipette.dispense({aspirate_ul}, plate["A1"])
    pipette.drop_tip(trash)
'''


def design_notes_base(
    case_id: str,
    *,
    family: str,
    expected_policy: str,
    tip_reason: str,
    limitations: list[str],
) -> dict[str, Any]:
    return {
        "question_id": case_id,
        "experiment_type": "live_runtime_recovery_pair_v2",
        "family": family,
        "robot": "Flex",
        "deck_layout": {
            "description": (
                "A3 trash; B3 source reservoir; C2 200 uL tips; C3 destination plate. "
                "Only the case-specific missing tips or backup volumes differ."
            ),
            "slots_used": ["A3", "B3", "C2", "C3"],
        },
        "pipette_choice": {
            "name": "flex_1channel_1000",
            "reason": (
                "Single-channel pressure sensing supports tip/liquid faults while covering "
                "20-100 uL control transfers."
            ),
        },
        "tip_strategy": {
            "policy": "fresh_tip_per_control_transfer",
            "reason": tip_reason,
        },
        "key_decisions": [
            {
                "decision": "Use non-biological control liquid for physical validation",
                "rationale": "Benchmark tests runtime policy and evidence capture, not chemistry.",
            },
            {
                "decision": "Keep model-visible context separate from oracle labels",
                "rationale": "Prevents gold / local_trap / correct_action leakage.",
            },
            {
                "decision": "Inject tip budget / backup volume via agent_context",
                "rationale": "These fields are not native Flex telemetry; they are eval context.",
            },
            {
                "decision": expected_policy,
                "rationale": "Pass/fail follows Assisted vs Autonomous and global correctness.",
            },
        ],
        "known_limitations": limitations,
    }


def empty_pair_stub(pair_id: str, title: str) -> dict[str, Any]:
    """Placeholder export for teammates (not included in the built manifest)."""
    return {
        "implemented": False,
        "pair_id": pair_id,
        "title": title,
        "status": "stub",
        "cases": {},
    }

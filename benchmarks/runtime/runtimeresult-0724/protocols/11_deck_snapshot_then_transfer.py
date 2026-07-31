"""Flex protocol — Deck snapshot then transfer (reconcile-visible hold).

Deck (same family as automation/new/protocol_b2_tip_c2_water_to_c1.py):
  B2  opentrons_flex_96_tiprack_1000ul
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat   ← required final seat
  A3  trash bin

Fault injection (operator): initially seat the sample plate in the WRONG slot
(C1) while leaving D2 empty, so reconcile_state / deck checks can report a
diff. After the agent requests correction, move the plate to D2, recheck, then
continue the transfer to succeeded.
"""
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def finish_tip(pipette, trash, dry_run_on: bool) -> None:
    if dry_run_on:
        pipette.return_tip()
    else:
        pipette.drop_tip(trash)


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    parameters.add_bool(
        display_name="Dry run: return tips",
        variable_name="dry_run_on",
        default=False,
    )
    parameters.add_bool(
        display_name="Use liquid probe",
        variable_name="use_liquid_probe",
        default=True,
    )


metadata = {
    "protocolName": "Deck snapshot then transfer",
    "author": "LabscriptAI OT",
    "description": (
        "Document deck, pause for reconcile/operator seat correction on D2, "
        "then transfer buffer into sample A1."
    ),
}


def run(protocol: protocol_api.ProtocolContext) -> None:

    trash = protocol.load_trash_bin("A3")
    tip_rack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D2")

    dry_run_on = protocol.params.dry_run_on
    use_liquid_probe = protocol.params.use_liquid_probe

    pipette = protocol.load_instrument(
        "flex_1channel_1000",
        "left",
        tip_racks=[tip_rack],
        liquid_presence_detection=use_liquid_probe,
    )
    water = protocol.get_liquid_class(name="water")
    glycerol = protocol.get_liquid_class(name="glycerol_50")
    if dry_run_on:
        protocol.comment("DRY RUN: no liquids loaded; tips return to rack.")

    buf = reservoir["A1"]
    sample = plate["A1"]

    protocol.comment("Document deck before transfer")
    try:
        protocol.capture_image(filename="decision_bench_11_pretransfer")
    except Exception:
        protocol.comment("capture_image unavailable in this runtime; continue after visual check")

    # Hold for agent reconcile / operator correction. Expected final seat: D2.
    # Injected mismatch: plate physically on C1 (empty D2) until operator moves it.
    protocol.pause(
        "SAFE HOLD: reconcile deck vs expected D2 plate. "
        "If the sample plate is on C1 (or D2 empty/wrong), ask operator to move "
        "it to D2, recheck, then resume. Do not motor-nudge the plate."
    )

    protocol.comment("Transfer Assay Buffer -> D2.A1")
    pipette.pick_up_tip()
    if use_liquid_probe:
        pipette.require_liquid_presence(buf)
    pipette.transfer_with_liquid_class(
        liquid_class=water, volume=100, source=buf, dest=sample,
        new_tip="never", trash_location=trash,
    )
    finish_tip(pipette, trash, dry_run_on)

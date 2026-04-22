"""Template: PCR setup — master mix + sample into a 96-well PCR plate.

Includes a no-template control row pattern (commented). Uses single-channel for flexibility;
switch to multi-channel if your map is column-aligned.
"""

from opentrons import protocol_api

metadata = {
    "protocolName": "Flex — PCR setup template",
    "author": "Replace",
    "description": "Master mix distribution and sample addition — set wells from intent review.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    parameters.add_float(
        display_name="Master mix (µL)",
        variable_name="mm_volume_ul",
        default=15.0,
        minimum=2.0,
        maximum=50.0,
    )
    parameters.add_float(
        display_name="Sample (µL)",
        variable_name="sample_volume_ul",
        default=5.0,
        minimum=1.0,
        maximum=20.0,
    )


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_50ul", "D3")

    mm_res = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    sample_plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "C2")
    pcr_plate = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "C3")

    pipette = protocol.load_instrument(
        "flex_1channel_50",
        "left",
        tip_racks=[tiprack],
    )

    mm_vol = protocol.params.mm_volume_ul
    sample_vol = protocol.params.sample_volume_ul

    # Example: reactions in first row A1–H1 — replace with target_wells from intent review.
    reaction_wells = [f"A{i}" for i in range(1, 9)]

    # TIP BUDGET: For large plate setups (>48 reactions), use new_tip="once" within
    # each reagent step to stay within a single 96-tip rack.
    # Step 1 (master mix): 1 tip per well — same source, so distribute with one tip per well.
    # Step 2 (sample): 1 tip per well — cross-contamination requires fresh tip each well.
    # Total tips = 2 × N reactions. For N=96: 192 tips → need 2 tip racks or new_tip="once"
    # for master mix (1 tip for all MM) → 97 tips (fits in 1 rack if N≤48, else add rack).

    # Master mix — use transfer with new_tip="always" (same reagent, no cross-contamination
    # between destinations, but fresh tip prevents carryover). For tight tip budgets, switch
    # to new_tip="once" (one tip for entire MM distribution).
    pipette.transfer(
        mm_vol,
        mm_res["A1"],
        [pcr_plate[w] for w in reaction_wells],
        new_tip="always",
        trash_location=trash,
    )

    # Sample addition — always new_tip (different biological samples).
    # Mix after each sample addition.
    for dest_well in reaction_wells:
        d = pcr_plate[dest_well]
        s = sample_plate[dest_well]
        pipette.pick_up_tip()
        pipette.aspirate(sample_vol, s)
        pipette.dispense(sample_vol, d)
        pipette.mix(repetitions=5, volume=min(20, mm_vol + sample_vol - 1), location=d)
        pipette.drop_tip(trash)

    # NTC: e.g. add MM to H12 but skip sample — model explicitly in your study design.

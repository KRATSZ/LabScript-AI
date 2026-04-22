"""Template: serial dilution along row A (A1 = stock / high concentration, A2+ = dilution chain).

`A1` holds the source material (e.g. stock). `A2` is primed with diluent buffer (2× transfer
volume) so the first xfer from A1→A2 lands in buffer, not an empty well. Subsequent steps
move along the row: A2→A3, A3→A4, …

Adjust diluent volume, transfer volume, and number of steps to match your SOP.
"""

from opentrons import protocol_api

metadata = {
    "protocolName": "Flex — serial dilution (row) template",
    "author": "Replace",
    "description": "Row A: A1 stock, A2 primed, serial transfer along A — parameterize counts.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    parameters.add_int(
        display_name="Number of dilution steps",
        variable_name="dilution_steps",
        default=7,
        minimum=1,
        maximum=11,
    )
    parameters.add_float(
        display_name="Step transfer volume (µL)",
        variable_name="transfer_volume_ul",
        default=50.0,
        minimum=5.0,
        maximum=50.0,
    )


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_50ul", "D3")

    diluent = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "C3")

    pipette = protocol.load_instrument(
        "flex_1channel_50",
        "left",
        tip_racks=[tiprack],
    )

    steps = protocol.params.dilution_steps
    xfer = protocol.params.transfer_volume_ul

    row = "A"
    wells = [f"{row}{i}" for i in range(1, 2 + steps)]

    # Prime A2 (not A1): A1 stays stock-only; buffer headroom for first serial step.
    prime_vol = min(pipette.max_volume, xfer * 2)
    pipette.pick_up_tip()
    pipette.aspirate(prime_vol, diluent["A1"])
    pipette.dispense(prime_vol, plate[wells[1]])
    pipette.drop_tip(trash)

    for i in range(steps):
        src = plate[wells[i]]
        dst = plate[wells[i + 1]]
        pipette.pick_up_tip()
        pipette.aspirate(xfer, src)
        pipette.dispense(xfer, dst)
        pipette.mix(repetitions=8, volume=min(40, xfer * 0.8), location=dst)
        pipette.drop_tip(trash)

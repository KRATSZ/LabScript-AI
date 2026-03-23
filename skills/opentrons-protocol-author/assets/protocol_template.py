from opentrons import protocol_api

metadata = {
    "protocolName": "Replace me",
    "author": "Replace me",
    "description": "Replace me",
}

# Set robotType to "OT-2" or "Flex". Adjust apiLevel for the features you need.
requirements = {"robotType": "OT-2", "apiLevel": "2.16"}


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    """Add runtime parameters here when the protocol needs per-run inputs."""
    return None


def run(protocol: protocol_api.ProtocolContext) -> None:
    """Replace the example setup below with the real workflow."""
    tip_rack = protocol.load_labware("opentrons_96_tiprack_300ul", 1)
    source = protocol.load_labware("nest_12_reservoir_15ml", 2)
    destination = protocol.load_labware("nest_96_wellplate_200ul_flat", 3)
    pipette = protocol.load_instrument("p300_single_gen2", "left", [tip_rack])

    pipette.pick_up_tip()
    pipette.aspirate(50, source["A1"])
    pipette.dispense(50, destination["A1"])
    pipette.drop_tip()

    # Optional camera usage on supported runtimes:
    # protocol.capture_image(filename="after-first-dispense")


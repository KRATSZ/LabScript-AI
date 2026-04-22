from opentrons import protocol_api

metadata = {
    "protocolName": "Flex template — replace me",
    "author": "Replace me",
    "description": "Replace me",
}

# Flex: use flex_* pipette names, load_trash_bin, and Flex tip racks.
# Default apiLevel 2.24+ (liquid-class compatible). Raise toward MAX_SUPPORTED_VERSION if needed.
requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    """Add runtime parameters when the protocol needs per-run inputs.

    Every display_name must be <= 30 characters (Opentrons hard limit).
    """
    # Example — uncomment and tune; keep display_name short:
    # parameters.add_int(
    #     display_name="Sample count",
    #     variable_name="sample_count",
    #     default=8,
    #     minimum=1,
    #     maximum=96,
    # )
    return None


def run(protocol: protocol_api.ProtocolContext) -> None:
    """Adjust slots and labware to match the physical deck before running."""

    trash = protocol.load_trash_bin("A3")
    tip_rack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")

    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tip_rack])

    pipette.pick_up_tip()
    pipette.aspirate(50, reservoir["A1"])
    pipette.dispense(50, plate["A1"])
    pipette.drop_tip(trash)

    # protocol.capture_image(filename="after-first-dispense")

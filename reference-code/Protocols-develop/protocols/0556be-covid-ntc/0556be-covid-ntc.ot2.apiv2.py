metadata = {
    'protocolName': 'COVID NTC Protocol - NFW',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [p1000_mount, component_1_volume, asp_height] = get_values(  # noqa: F821
        "p1000_mount", "component_1_volume", "asp_height")

    asp_height = float(asp_height)

    # Load Labware
    tuberack = ctx.load_labware(
        'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 10)['A1']
    dest_tubes = ctx.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap', 11)
    tiprack_1000ul = ctx.load_labware('opentrons_96_filtertiprack_1000ul', 1)

    # Load Instruments
    p1000 = ctx.load_instrument('p1000_single_gen2', 'right',
                                tip_racks=[tiprack_1000ul])

    # Transfer Component 1 to Destination Tubes
    p1000.transfer(float(component_1_volume), tuberack.bottom(asp_height),
                   dest_tubes.wells())

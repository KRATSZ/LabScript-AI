metadata = {
    'protocolName': 'Covid Sample Prep with Custom 96 Tube Rack',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, p300_mount] = get_values(  # noqa: F821
        "num_samp", "p300_mount")

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a column number 1-12")

    # labware
    tuberack = ctx.load_labware('opentrons_96_tuberack_96x5ml_custom', '1')
    plate = ctx.load_labware('biorad_96_wellplate_50ul', '11')
    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', '10')]

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2',
                               p300_mount, tip_racks=tiprack)

    # protocol
    for sample, well in zip(tuberack.wells(), plate.wells()[:num_samp]):
        p300.pick_up_tip()
        p300.aspirate(50, sample)
        p300.dispense(50, well)
        p300.blow_out()
        p300.drop_tip()

metadata = {
    'protocolName': 'Reformatting with Custom Tube Rack',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samp, volume, p300_mount] = get_values(  # noqa: F821
        "num_samp", "volume", "p300_mount")

    if not 1 <= num_samp <= 86:
        raise Exception("Enter a sample number between 1-86")

    # labware

    tuberacks = [ctx.load_labware('custom_24_tuberack', slot)
                 for slot in [1, 2, 3, 4]]
    plate = ctx.load_labware('nest_96_wellplate_2ml_deep', 6)
    tips = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
            for slot in [8]]

    # pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=tips)

    # mapping
    source_wells = [tube for rack in tuberacks
                    for row in rack.rows() for tube in row][:num_samp]
    dest_wells = [well for row in plate.rows() for well in row][10:]

    # protocol
    ctx.comment('\n---------------ADDING SAMPLE TO PLATE----------------\n\n')
    for s, d in zip(source_wells, dest_wells):
        p300.pick_up_tip()
        p300.aspirate(volume, s)
        p300.dispense(volume, d)
        p300.drop_tip()
        ctx.comment('\n')

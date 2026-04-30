metadata = {
    'protocolName': 'Custom Tube to Tube transfer',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [num_samp, delay, asp_height_recipient,
     disp_height_dest, p1000_mount] = get_values(  # noqa: F821
            "num_samp", "delay", "asp_height_recipient",
            "disp_height_dest", "p1000_mount")

    if not 1 <= num_samp <= 24:
        raise Exception("Enter a sample number between 1-24")

    # load labware
    source_tube_rack = ctx.load_labware("6x4_0.6inch_t6", '1',
                                        label='Source Tube Rack')
    dest_tube_rack = ctx.load_labware("6x5_half_inch_t1_t3", '2',
                                      label='Dest Tube Rack')
    tiprack1000 = ctx.load_labware('opentrons_96_tiprack_1000ul', '3')

    # load instrument
    p1000 = ctx.load_instrument('p1000_single_gen2',
                                p1000_mount, tip_racks=[tiprack1000])

    dest_tubes = [tube for row in dest_tube_rack.rows() for tube in row[:4]]

    for s, d in zip(source_tube_rack.wells()[:num_samp], dest_tubes):
        p1000.pick_up_tip()
        p1000.aspirate(500, s.bottom(asp_height_recipient))
        ctx.delay(seconds=delay)
        p1000.dispense(500, d.bottom(disp_height_dest))
        p1000.drop_tip()
        ctx.comment('\n')

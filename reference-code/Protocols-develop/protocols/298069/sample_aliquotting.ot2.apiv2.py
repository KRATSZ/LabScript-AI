import math

# metadata
metadata = {
    'protocolName': 'Sample Aliquoting',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    # parameters
    [p1000_mount] = get_values(  # noqa: F821
        'p1000_mount')

    # labware
    rack15 = ctx.load_labware(
        'opentrons_15_tuberack_falcon_15ml_conical', '1', '15ml tuberack')
    rack2 = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '2',
        '2ml tuberack')
    tiprack1000 = ctx.load_labware(
        'opentrons_96_tiprack_1000ul', '4', '1000ul tiprack')

    # pipettes
    p1000 = ctx.load_instrument(
        'p1000_single_gen2', p1000_mount, tip_racks=[tiprack1000])

    # setup
    srcs = {
        rack15.columns()[0][0]: 60,
        rack15.columns()[0][1]: 60
    }
    dest_sets = [
        [well for row in rack2.rows()[i*2:i*2+2] for well in row]
        for i in range(2)
    ]

    def h_track(src, dv):
        dh = (dv/(math.pi*(src.diameter/2)**2))*1.05
        h = srcs[src]
        srcs[src] = h - dh if h - dh >= 10 else 10
        return src.bottom(srcs[src])

    # perform transfers
    for s, dest_set in zip(srcs, dest_sets):
        p1000.pick_up_tip()
        for i in range(4):
            p1000.distribute(
                300,
                h_track(s, 900),
                [d.top() for d in dest_set[i*3:i*3+3]],
                disposal_vol=0,
                new_tip='never'
            )
            if i < 3:
                p1000.blow_out(s.top())
        p1000.drop_tip()

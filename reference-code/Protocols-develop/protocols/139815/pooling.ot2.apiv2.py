# metadata
metadata = {
    'protocolName': 'Pooling and Consolidation',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    p10_mount, p300_mount = get_values(  # noqa: F821
        'p10_mount', 'p300_mount')

    # load labware
    plate = ctx.load_labware(
        'eppendorftwin.tec96_96_aluminumblock_200ul',
        '1',
        '96-well plate in insert'
    )
    strips = ctx.load_labware(
        'usascientific8strip_96_aluminumblock_300ul', '2', 'strips in insert')
    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '3',
        '1.5ml tuberack'
    )
    tiprack10 = [ctx.load_labware(
        'opentrons_96_filtertiprack_10ul', '4', '10ul tiprack')]
    tiprack300 = [ctx.load_labware(
        'opentrons_96_filtertiprack_200ul', '5', '300ul tiprack')]

    # pipettes
    m10 = ctx.load_instrument(
        'p10_multi', mount=p10_mount, tip_racks=tiprack10)
    p300 = ctx.load_instrument(
        'p300_single', mount=p300_mount, tip_racks=tiprack300)

    # reagents
    strip = strips.columns()[0]
    pool = tuberack.wells()[0]

    # consolidate plate contents to 1 strip
    for well in plate.rows()[0]:
        m10.pick_up_tip()
        m10.aspirate(2, well.top())
        m10.aspirate(2, well.bottom(2))
        m10.dispense(4, strip[0].bottom(2))
        m10.blow_out(strip[0].bottom(5))
        m10.drop_tip()

    ctx.pause('Spin down the strip and return to the OT-2 for pooling.')

    p300.consolidate(
        24, [well.bottom(1) for well in strip], pool.bottom(5), blow_out=True)

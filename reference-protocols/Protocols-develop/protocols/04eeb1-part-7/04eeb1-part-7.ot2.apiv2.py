from opentrons import types

metadata = {
    'protocolName': 'Illumina COVIDSeq Test: Pool and Clean Up Libraries',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [m300_mount, m20_mount] = get_values(  # noqa: F821
        "m300_mount", "m20_mount")

    # Labware
    tips200ul = [ctx.load_labware('opentrons_96_filtertiprack_200ul', 4)]
    tips20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul', 7)
    pcr_strip = ctx.load_labware(
                'opentrons_96_aluminumblock_generic_pcr_strip_200ul', 8)
    tuberack = ctx.load_labware(
                'opentrons_24_aluminumblock_nest_1.5ml_snapcap', 5)
    mag_mod = ctx.load_module('magnetic module gen2', 3)
    plate_1 = mag_mod.load_labware('biorad_96_wellplate_200ul_pcr')

    # Pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips200ul)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=[tips20ul])

    # Wells
    plate_1_wells = plate_1.rows()[0]
    tube = tuberack['A1']
    pcr_tube_col = pcr_strip['A1']
    pcr_tube_col_wells = pcr_strip.columns()[0]

    # Helper Functions
    def remove_supernatant(pip, vol, src, dest, side):
        pip.aspirate(5, src.top())
        pip.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        pip.dispense(vol, dest)
        pip.dispense(5, dest)

    num_channels_per_pickup = 1  # (only pickup tips on front-most channel)
    tips_ordered = [tip for rack in tips200ul for row in rack.rows(
            )[len(
             rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]
            for tip in row]

    tip_count = 0

    def pick_up(pip):
        nonlocal tip_count
        pip.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # Protocol Steps

    # Engage Mag Mod
    mag_mod.engage()
    ctx.delay(minutes=3, msg='''Waiting 3 minutes for beads to pellet.''')

    for col in plate_1_wells:
        m20.pick_up_tip()
        remove_supernatant(m20, 5, col, pcr_tube_col, -1)
        m20.drop_tip()

    ctx.pause('Vortex and Centrifuge PCR Strip. Then click Resume.')

    for well in pcr_tube_col_wells:
        pick_up(m300)
        m300.aspirate(55, well)
        m300.dispense(55, tube)
        m300.drop_tip()

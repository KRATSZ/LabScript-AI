import math

metadata = {
    'protocolName': 'Sample Plating Protocol',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.9'
}


def run(ctx):

    [num_samples, sample_vol, asp_height, p300_mount,
     tip_type] = get_values(  # noqa: F821
        'num_samples', 'sample_vol', 'asp_height', 'p300_mount', 'tip_type')

    # define source/dest wells
    if num_samples > 96:
        raise Exception('The number of samples should be 1-96.')

    # load labware
    num_racks = math.ceil(num_samples/15)
    source_tuberacks = [
        ctx.load_labware('avantik_15_tuberack_3000ul', slot,
                         'sample tuberack ' + str(i + 1))
        for i, slot in enumerate(
            ['1', '4', '5', '6', '7', '8', '9'][:num_racks])]
    dest_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '2', 'deepwell plate')
    tiprack300 = [ctx.load_labware(tip_type, '3')]

    # load pipette
    p300 = ctx.load_instrument(
        'p300_single_gen2', p300_mount, tip_racks=tiprack300)

    # define source/dest wells
    if num_samples > 96:
        raise Exception('The number of samples should be 1-96.')

    sources = [tube for rack in source_tuberacks
               for tube in rack.wells()][:num_samples]
    dests = dest_plate.wells()[:num_samples]

    # calculate air gap allowable
    tip_max_vol = tiprack300[0].wells()[0].max_volume
    if tip_max_vol - sample_vol < 20:
        if tip_max_vol - sample_vol > 0:
            air_gap = tip_max_vol - sample_vol
        else:
            air_gap = 0  # no air gap if multiple transfers
    else:
        air_gap = 20
    for source, dest in zip(sources, dests):
        p300.pick_up_tip()
        p300.transfer(sample_vol, source.bottom(asp_height),
                      dest, air_gap=air_gap, new_tip='never')
        p300.air_gap(20)  # ensure no dripping on way to trash
        p300.drop_tip()

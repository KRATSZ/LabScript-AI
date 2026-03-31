from opentrons.types import Point

# metadata
metadata = {
    'protocolName': 'Pooling from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [input_csv, p20_mount, p300_mount, source_type,
     using_tempdeck, dest_type] = get_values(  # noqa: F821
        'input_csv', 'p20_mount', 'p300_mount',
        'source_type', 'using_tempdeck', 'dest_type')

    # labware
    tempdeck = ctx.load_module('temperature module gen2', '1')
    if using_tempdeck:
        tempdeck.set_temperature(4)
    source_plate = tempdeck.load_labware(source_type, 'source plate')
    pooling_tube = ctx.load_labware(dest_type, '2', 'pooling tube').wells()[0]
    tiprack20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot, '20ul tiprack')
        for slot in ['3']
    ]
    tiprack300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '300ul tiprack')
        for slot in ['6']
    ]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tiprack300)

    # parse
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]]

    # perform pooling
    for line in data:
        s, vol_s = line[:2]

        if not vol_s:
            vol_s = 0
        else:
            vol_s = float(vol_s)

        source = source_plate.wells_by_name()[s]

        # transfer sample
        pip = p300 if vol_s > 20 else p20
        if vol_s != 0:
            pip.pick_up_tip()
            pip.transfer(vol_s, source.bottom(3), pooling_tube.bottom(2),
                         new_tip='never')
            pip.blow_out(pooling_tube.bottom(2))
            pip.move_to(pooling_tube.bottom().move(Point(
                x=pooling_tube.diameter/4, z=2)))
            pip.drop_tip()

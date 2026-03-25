from opentrons import types

# metadata
metadata = {
    'protocolName': 'Normalization from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [input_csv, p20_type, p20_mount, p300_type, p300_mount, source_type,
     using_tempdeck, dest_type, reservoir_type] = get_values(  # noqa: F821
        'input_csv', 'p20_type', 'p20_mount', 'p300_type', 'p300_mount',
        'source_type', 'using_tempdeck', 'dest_type', 'reservoir_type')

    # labware
    tempdeck = ctx.load_module('temperature module gen2', '1')
    if using_tempdeck:
        tempdeck.set_temperature(4)
    source_plate = tempdeck.load_labware(source_type, 'source plate')
    destination_plate = ctx.load_labware(dest_type, '2', 'destination plate')
    water = ctx.load_labware(
        reservoir_type, '5',
        'reservoir for water (position A1)').wells()[0].bottom(1)
    tiprack20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot, '20ul tiprack')
        for slot in ['3']
    ]
    tiprack300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '300ul tiprack')
        for slot in ['6']
    ]

    # pipettes
    p20 = ctx.load_instrument(p20_type, p20_mount, tip_racks=tiprack20)
    p300 = ctx.load_instrument(p300_type, p300_mount, tip_racks=tiprack300)

    # parse
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]]

    # perform normalization
    for line in data:
        s, d, vol_s, vol_w = line[:4]

        if not vol_w:
            vol_w = 0
        else:
            vol_w = float(vol_w)

        d = destination_plate.wells_by_name()[d]
        center_AI = d.center()
        right_AI = center_AI.move(types.Point(x=2.67, y=0, z=0))

        # pre-transfer diluent
        if vol_w > 20:
            pip = p300
            pip.flow_rate.blow_out = 75
            pip.flow_rate.aspirate = 75
        else:
            pip = p20
            pip.flow_rate.blow_out = 5
            pip.flow_rate.aspirate = 5
        if not pip.has_tip:
            pip.pick_up_tip()

        pip.transfer(vol_w, water, d.bottom(4), new_tip='never')
        pip.blow_out(d.top(-2))
        pip.move_to(right_AI)

    for pip in [p20, p300]:
        if pip.has_tip:
            pip.drop_tip()

    # perform normalization
    for line in data:
        s, d, vol_s, vol_w = line[:4]
        if not vol_s:
            vol_s = 0
        else:
            vol_s = float(vol_s)

        s = source_plate.wells_by_name()[s]
        d = destination_plate.wells_by_name()[d]
        center_AI = d.center()
        right_AI = center_AI.move(types.Point(x=2.67, y=0, z=0))

        # transfer sample
        if vol_s > 20:
            pip = p300
            pip.flow_rate.blow_out = 75
            pip.flow_rate.aspirate = 75
        else:
            pip = p20
            pip.flow_rate.blow_out = 5
            pip.flow_rate.aspirate = 5
        if vol_s != 0:
            pip.pick_up_tip()
            pip.transfer(vol_s, s, d, new_tip='never')
            pip.blow_out(d.top(-2))
            pip.move_to(right_AI)
            pip.drop_tip()

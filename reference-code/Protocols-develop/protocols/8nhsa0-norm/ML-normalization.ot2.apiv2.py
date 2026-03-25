# metadata
metadata = {
    'protocolName': 'Normalization from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.4'
}


def run(ctx):

    [input_csv, p10_type, p10_mount, p300_type,
     p300_mount, source_type, dest_type] = get_values(  # noqa: F821
        'input_csv', 'p10_type', 'p10_mount', 'p300_type', 'p300_mount',
        'source_type', 'dest_type')

    # labware
    source_plate = ctx.load_labware(source_type, '1', 'source plate')
    destination_plate = ctx.load_labware(dest_type, '2', 'destination plate')
    tiprack10 = [
        ctx.load_labware('opentrons_96_tiprack_10ul', slot, '10ul tiprack')
        for slot in ['3', '6']
    ]
    water = ctx.load_labware(
        'nest_1_reservoir_195ml', '5',
        'reservoir for water (channel 1)').wells()[0].bottom(5)
    tiprack300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '300ul tiprack')
        for slot in ['8', '9']
    ]

    # pipettes
    p10 = ctx.load_instrument('p10_single', p10_mount, tip_racks=tiprack10)
    p300 = ctx.load_instrument('p300_single', p300_mount, tip_racks=tiprack300)

    # parse
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]]

    # perform normalization
    for s, d, vol_s, vol_w in data:
        vol_s = float(vol_s)
        vol_w = float(vol_w)
        s = source_plate.wells_by_name()[s]
        d = destination_plate.wells_by_name()[d]

        pip = p300 if vol_s + vol_w >= 20 else p10
        pip.pick_up_tip()
        if vol_w > 0:
            pip.aspirate(vol_w, water)
        if vol_s > 0:
            pip.aspirate(vol_s, s)
        pip.dispense(pip.current_volume, d)
        pip.blow_out(d.top(-2))
        pip.drop_tip()

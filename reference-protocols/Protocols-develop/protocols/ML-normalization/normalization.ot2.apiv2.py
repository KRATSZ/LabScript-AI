from opentrons import protocol_api

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

    if using_tempdeck:
        tempdeck = ctx.load_module('temperature module gen2', '1')
        tempdeck.set_temperature(4)
        source_plate = tempdeck.load_labware(source_type, 'source plate')

    else:
        source_plate = ctx.load_labware(source_type, 1, 'source plate')

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

    # Helper Functions
    def pick_up(pip):
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

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

        # pre-transfer diluent
        pip = p300 if vol_w > 20 else p20
        if not pip.has_tip:
            pick_up(pip)

        pip.transfer(vol_w, water, d.bottom(2), new_tip='never')
        pip.blow_out(d.top(-2))

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

        # transfer sample
        pip = p300 if vol_s > 20 else p20
        if vol_s != 0:
            pick_up(pip)
            pip.transfer(vol_s, s.bottom(3), d, new_tip='never')
            pip.blow_out(d.top(-2))
            pip.drop_tip()

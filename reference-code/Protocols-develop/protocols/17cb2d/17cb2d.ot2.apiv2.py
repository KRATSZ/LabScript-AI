from opentrons import types

metadata = {
    'protocolName': 'Plate Filling Master Mix in AB 384 Well Plate',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [piptype, pipmnt, num_plates, p384, mm_vol] = get_values(  # noqa: F821
        'piptype', 'pipmnt', 'num_plates', 'p384', 'mm_vol')

    # load labware and pipettes
    pip_name, tip_name = piptype.split()
    tips = protocol.load_labware(tip_name, '10')
    pip = protocol.load_instrument(pip_name, pipmnt, tip_racks=[tips])
    res = protocol.load_labware('nest_12_reservoir_15ml', '11')
    mm1 = [res['A1']]*5+[res['A2']]*4
    mm2 = [res['A11']]*5+[res['A12']]*4
    num_plates += 1
    plates = [
        protocol.load_labware(p384, s) for s in range(1, num_plates)]

    if pip_name == 'p20_multi_gen2':
        max_vol = mm_vol * 2
    else:
        max_vol = (300//mm_vol) * mm_vol

    # distribute mastermix 1
    protocol.comment('Distributing master mix 1...')
    pip.pick_up_tip()
    for plate, mm in zip(plates, mm1):
        wells = plate.rows()[0]
        # disp_vol = 12
        vol_ctr = 0
        for well in wells:
            if vol_ctr < 1:
                pip.aspirate(max_vol, mm)
                vol_ctr = max_vol
                protocol.max_speeds['X'] = 25
                pip.move_to(mm.top().move(types.Point(x=3.5, y=0, z=-4)))
                pip.move_to(mm.top().move(types.Point(x=-3.5, y=0, z=-2)))
                protocol.max_speeds['X'] = None
            # pip.dispense(disp_vol, well)
            pip.dispense(mm_vol, well)
            vol_ctr -= mm_vol
            # pip.blow_out(well)
            # pip.aspirate(2, well.top())
    pip.drop_tip()

    # distribute mastermix 2
    protocol.comment('Distributing master mix 2...')
    pip.pick_up_tip()
    for plate, mm in zip(plates, mm2):
        wells = plate.rows()[1]
        # disp_vol = 12
        vol_ctr = 0
        for well in wells:
            if vol_ctr < 1:
                pip.aspirate(max_vol, mm)
                vol_ctr = max_vol
                protocol.max_speeds['X'] = 25
                pip.move_to(mm.top().move(types.Point(x=3.5, y=0, z=-4)))
                pip.move_to(mm.top().move(types.Point(x=-3.5, y=0, z=-2)))
                protocol.max_speeds['X'] = None
            # pip.dispense(disp_vol, well)
            pip.dispense(mm_vol, well)
            vol_ctr -= mm_vol
            # pip.blow_out(well)
            # pip.aspirate(2, well.top())
    pip.drop_tip()

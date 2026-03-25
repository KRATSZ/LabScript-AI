from opentrons import types

metadata = {
    'protocolName': 'Plate Filling QE in NEST Plate',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [piptype, pipmnt, num_plates] = get_values(  # noqa: F821
        'piptype', 'pipmnt', 'num_plates')

    # load labware and pipettes
    pip_name, tip_name = piptype.split()
    tips = protocol.load_labware(tip_name, '10')
    pip = protocol.load_instrument(pip_name, pipmnt, tip_racks=[tips])
    res = protocol.load_labware('nest_12_reservoir_15ml', '11')
    mm1 = [res['A1']]*5+[res['A2']]*4
    num_plates += 1
    plates = [
        protocol.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt',
            s) for s in range(1, num_plates)]

    # max_vol = 15 if pip_name == 'p20_multi_gen2' else 180

    # distribute 10ul of QE
    pip.pick_up_tip()
    for plate, mm, r in zip(plates, mm1, range(1, 10)):
        wells = plate.rows()[0]
        disp_vol = 12
        protocol.comment(f'Distributing 10ul to plate {r}...')
        for well in wells:
            pip.aspirate(10, mm)
            protocol.max_speeds['X'] = 25
            pip.move_to(mm.top().move(types.Point(x=3.5, y=0, z=-4)))
            pip.move_to(mm.top().move(types.Point(x=-3.5, y=0, z=-2)))
            protocol.max_speeds['X'] = None
            pip.dispense(disp_vol, well)
            pip.blow_out(well)
            pip.aspirate(2, well.top())
    pip.drop_tip()

    protocol.comment('Protocol complete.')

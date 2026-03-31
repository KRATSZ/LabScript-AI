import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Drug Release Time Point Testing',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


# Start protocol
def run(ctx):

    [vol_transfer, quadrant, mount_p1000, tiprack_start,
     tipwell_start] = get_values(  # noqa:F821
        'vol_transfer', 'quadrant', 'mount_p1000', 'tiprack_start',
        'tipwell_start')

    # labware
    plate24 = ctx.load_labware('corning_24_wellplate_3.4ml_flat', '1',
                               'source plate')
    plates96 = [
        ctx.load_labware('corning_96_wellplate_360ul_flat', slot,
                         f'destination plate {i+1}')
        for i, slot in enumerate(['2', '3'])]
    reservoir = ctx.load_labware('agilent_1_reservoir_290ml', '4')
    tipracks1000 = [
        ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot)
        for slot in ['5', '6', '8', '9']]

    # pipette
    p1000 = ctx.load_instrument(
        'p1000_single_gen2',
        mount_p1000,
        tip_racks=tipracks1000)

    # setup locations
    sources = plate24.wells()
    all_columns = [col for plate in plates96 for col in plate.columns()]
    quadrants = [
        [well
         for col in all_columns[plate_ind*12+j*6:plate_ind*12+(j+1)*6]
         for well in col[i*4:(i+1)*4]]
        for plate_ind in range(2)
        for i in range(2)
        for j in range(2)
    ]
    quadrant_keys = ['1A1', '1A7', '1E1', '1E7', '1A1', '1A7', '1E1', '1E7']
    quadrant_map = {
        key: quadrant
        for key, quadrant in zip(quadrant_keys, quadrants)
    }
    buffer = reservoir.wells()[0]

    # select quadrant
    dest_quadrant = quadrant_map[quadrant]

    # select starting tip
    p1000.starting_tip = ctx.loaded_labwares[
        int(tiprack_start)].wells_by_name()[tipwell_start]

    # void all other tips in the tipracks
    all_tips = [tip for rack in p1000.tip_racks for tip in rack.wells()]
    for tip in all_tips[:all_tips.index(p1000.starting_tip)]:
        tip.has_tip = False

    def pick_up(pip=p1000):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def slow_withdraw(well, pip=p1000):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # transfer from 24-wel to 96-well quadrant
    for s, d in zip(sources, dest_quadrant):
        pick_up()
        p1000.flow_rate.aspirate = 50
        p1000.aspirate(vol_transfer, s.bottom(4))
        p1000.flow_rate.aspirate = 274.7
        p1000.touch_tip(s)
        p1000.dispense(vol_transfer, d)
        p1000.blow_out(d.bottom(1))
        slow_withdraw(d)
        p1000.drop_tip()

    num_dests_per_asp = int(
        p1000.tip_racks[0].wells()[0].max_volume/vol_transfer)
    num_asps = math.ceil(len(sources)/num_dests_per_asp)
    buffer_distribution_sets = [
        sources[i*num_dests_per_asp:(i+1)*num_dests_per_asp]
        if i < num_asps - 1
        else sources[i*num_dests_per_asp:]
        for i in range(num_asps)]

    pick_up()
    for b_d_set in buffer_distribution_sets:
        p1000.aspirate(vol_transfer*len(b_d_set), buffer)
        slow_withdraw(buffer)
        for i, d in enumerate(b_d_set):
            p1000.dispense(vol_transfer, d.top(-1))
            if i == len(b_d_set) - 1:
                p1000.blow_out(d.top(-1))
    p1000.return_tip()

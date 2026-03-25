import math

metadata = {
    'protocolName': 'Drug Dosing',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_cell_lines, tip_start_col,
     num_rep_plates] = get_values(  # noqa: F821
        'num_cell_lines', 'tip_start_col', 'num_rep_plates')

    # labware
    rep_plates = [
        ctx.load_labware(
            'thermofisher_96_wellplate_300ul', slot, f'rep {slot}')
        for slot in range(1, 1+num_rep_plates)]
    source_plate = ctx.load_labware('thermoscientificnunc_96_wellplate_2000ul',
                                    '4', 'DRUG + YOYO-MEDIA')
    tipracks300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '10')]

    # pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'right', tip_racks=tipracks300)
    m300.starting_tip = tipracks300[0].columns()[tip_start_col-1][0]

    # variables
    vol_dose = 100.0
    vol_air_gap = 0
    cell_lines = [
        source_plate.rows()[0][i*2] for i in range(num_cell_lines)]
    rep_destination_sets = [
            [plate.rows()[0][1+i*3:1+(i+1)*3] for plate in rep_plates]
            for i in range(num_cell_lines)]
    rep_destination_sets_flat = []
    for rep_set in rep_destination_sets:
        flat_set = []
        for inner_set in rep_set:
            for well in inner_set:
                flat_set.append(well)
        rep_destination_sets_flat.append(flat_set)

    def slow_withdraw(pip, well):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # perform transfers
    num_dests_per_asp = int(
        m300.tip_racks[0].wells()[0].max_volume/(vol_dose+vol_air_gap))
    for source, dest_set in zip(cell_lines, rep_destination_sets_flat):
        num_asp = math.ceil(len(dest_set)/num_dests_per_asp)
        dest_sets_per_asp = [
            dest_set[i*num_dests_per_asp:(i+1)*num_dests_per_asp]
            if i < num_asp - 1
            else dest_set[i*num_dests_per_asp:]
            for i in range(num_asp)]
        m300.pick_up_tip()
        for d_set in dest_sets_per_asp:
            m300.mix(3, 300, source.bottom(1))  # premix
            for _ in range(len(d_set)):
                if vol_air_gap:
                    m300.aspirate(vol_air_gap, source.top())
                m300.aspirate(vol_dose, source.bottom(1))
            for i, d in enumerate(d_set):
                m300.dispense(vol_dose+vol_air_gap, d.bottom(7.6))
                if i == len(d_set) - 1:
                    m300.blow_out(d.bottom(7.6))
        m300.drop_tip()

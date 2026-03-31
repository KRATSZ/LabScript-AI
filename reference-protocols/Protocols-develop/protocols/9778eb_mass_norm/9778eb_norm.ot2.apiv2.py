"""OPEN TRONS."""
import math

metadata = {
    'protocolName': 'Normalization with CSV',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.12'
}


def run(ctx):
    """PROTOCOL."""
    [vol_water, src_plate, dst_plate,
     p20_mount, file_input] = get_values(  # noqa: F821
        'vol_water', 'src_plate', 'dst_plate', 'p20_mount', 'file_input')

    if p20_mount == 'right':
        p300_mount = 'left'
    else:
        p300_mount = 'right'
    source_plate = ctx.load_labware(src_plate, '1')
    dest_plate = ctx.load_labware(dst_plate, '2')
    reagent_tubes = ctx.load_labware('opentrons_6_tuberack_'
                                     'falcon_50ml_conical', '4')

    # parse
    csv_1 = file_input.split('\\n')
    csv_2 = [val.split(',') for val in csv_1]
    header_removed = csv_2[1:]
    flat_list = [item for sublist in header_removed for item in sublist]
    well_list = flat_list[::5]
    sample_mass = [eval(i) for i in flat_list[1::5]]
    sample_vol = [eval(i) for i in flat_list[2::5]]
    final_mass = [eval(i) for i in flat_list[3::5]]
    final_vol = [eval(i) for i in flat_list[4::5]]
    start_conc = []
    final_conc = []
    bad_wells = []
    print(well_list)

    for mass, vol in zip(sample_mass, sample_vol):
        start_conc.append(mass/vol)

    for mass, vol in zip(final_mass, final_vol):
        final_conc.append(mass/vol)

    transfer_vol = []
    nfw_vol = []
    for final, start, vol in zip(final_conc, start_conc, final_vol):
        transfer_vol.append(vol*round(final/start, 1))
    for s_vol, f_vol in zip(transfer_vol, final_vol):
        nfw_vol.append(f_vol-s_vol)
    lists = [well_list, sample_mass, sample_vol, final_mass, final_vol,
             start_conc, final_conc, transfer_vol, nfw_vol]
    # clean up bad wells from lists
    for i, (start, final) in enumerate(zip(start_conc, final_conc)):
        if start < final:
            bad_wells.append(well_list[i])
            for list in lists:
                del list[i]

    # Reagents and Well Lists

    nfw_source = reagent_tubes.wells()[0]

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in ['3', '6'][:math.ceil(len(well_list)/48)]]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['5', '7'][:math.ceil(len(well_list)/48)]]
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips300)

    # liquid height tracking
    v_naught_dil = vol_water*1000
    radius = reagent_tubes.wells()[0].diameter/2
    h_naught_water = 0.85*v_naught_dil/(math.pi*radius**2)
    h = h_naught_water

    def adjust_height(vol):
        nonlocal h
        dh = vol/(math.pi*radius**2)
        h -= dh
        if h < 12:
            h = 1

    # do NFW addition first to save tips, mix after sample addition
    ctx.comment('\n\n~~~~~~~~~~~~~~ADDING NFW TO WELLS~~~~~~~~~~~~~~~\n')
    p20.pick_up_tip()
    p300.pick_up_tip()
    for nfw, d in zip(nfw_vol, well_list):
        if nfw >= 20:
            pip = p300
        else:
            pip = p20
        pip.transfer(nfw, nfw_source.bottom(h), dest_plate[d],
                     new_tip='never')
        adjust_height(nfw)
    p20.drop_tip()
    p300.drop_tip()

    ctx.comment('\n\n~~~~~~~~~~~~~TRANSFERRING SAMPLE VOLUMES~~~~~~~~~~~~~~\n')
    for t_vol, well in zip(transfer_vol, well_list):
        if t_vol >= 20:
            pip = p300
        else:
            pip = p20
        pip.pick_up_tip()
        pip.transfer(t_vol, source_plate.wells_by_name()[well],
                     dest_plate.wells_by_name()[well], new_tip='never')
        pip.mix(4, f_vol/2, dest_plate.wells_by_name()[well])
        pip.drop_tip()

    # bad_list = [well.display_name.split(' ')[0] for well in bad_wells]
    # print(lists)

    if len(bad_wells) > 0:
        bad_msg = '\n\n'.join(bad_wells)
        ctx.comment(f'The following sample wells failed: \n\n{bad_msg}')

    for c in ctx.commands():
        print(c)

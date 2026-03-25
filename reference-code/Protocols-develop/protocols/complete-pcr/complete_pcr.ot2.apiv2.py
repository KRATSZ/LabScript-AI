import math

# metadata
metadata = {
    'protocolName': 'Complete PCR Workflow with Thermocycler',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [number_of_samples, dna_volume, mastermix_volume,
     master_mix_csv, tuberack_type, single_channel_type, single_channel_mount,
     pipette_2_type, pipette_2_mount, lid_temp, init_temp, init_time, d_temp,
     d_time, a_temp, a_time, e_temp, e_time, no_cycles, fe_temp, fe_time,
     final_temp] = get_values(  # noqa: F821
        'number_of_samples', 'dna_volume', 'mastermix_volume',
        'master_mix_csv', 'tuberack_type', 'single_channel_type',
        'single_channel_mount', 'pipette_2_type', 'pipette_2_mount',
        'lid_temp', 'init_temp', 'init_time', 'd_temp', 'd_time', 'a_temp',
        'a_time', 'e_temp', 'e_time', 'no_cycles', 'fe_temp', 'fe_time',
        'final_temp')

    range1 = single_channel_type.split('_')[0][1:]
    tipracks1 = [
        ctx.load_labware('opentrons_96_tiprack_' + range1 + 'ul', slot)
        for slot in ['2', '3']
    ]
    p1 = ctx.load_instrument(
        single_channel_type, single_channel_mount, tip_racks=tipracks1)

    using_multi = True if pipette_2_type.split('_')[1] == 'multi' else False
    if using_multi:
        mm_plate = ctx.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt', '4',
            'plate for mastermix distribution')
    if pipette_2_type and pipette_2_mount:
        range2 = pipette_2_type.split('_')[0][1:]
        tipracks2 = [
            ctx.load_labware('opentrons_96_tiprack_' + range2 + 'ul', slot)
            for slot in ['6', '9']
        ]
        p2 = ctx.load_instrument(
            pipette_2_type, pipette_2_mount, tip_racks=tipracks2)

    # labware setup
    tc = ctx.load_module('thermocycler')
    tc_plate = tc.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'thermocycler plate')
    if tc.lid_position != 'open':
        tc.open_lid()
    tc.set_lid_temperature(lid_temp)
    if 'cooled' in tuberack_type:
        tempdeck = ctx.load_module('tempdeck', '1')
        tuberack = tempdeck.load_labware(
            tuberack_type, 'rack for mastermix reagents'
        )
    else:
        tuberack = ctx.load_labware(
            tuberack_type, '1', 'rack for mastermix reagents')
    dna_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '5', 'DNA plate')

    # reagent setup
    mm_tube = tuberack.wells()[0]
    num_cols = math.ceil(number_of_samples/8)

    pip_counts = {p1: 0, p2: 0}
    p1_max = len(tipracks1)*96
    p2_max = len(tipracks2)*12 if using_multi else len(tipracks2)*96
    pip_maxs = {p1: p1_max, p2: p2_max}

    def pick_up(pip):
        if pip_counts[pip] == pip_maxs[pip]:
            ctx.pause('Replace empty tipracks before resuming.')
            pip.reset_tipracks()
            pip_counts[pip] = 0
        pip.pick_up_tip()
        pip_counts[pip] += 1

    # determine which pipette has the smaller volume range
    if using_multi:
        pip_s, pip_l = p1, p1
    else:
        if int(range1) <= int(range2):
            pip_s, pip_l = p1, p2
        else:
            pip_s, pip_l = p2, p1

    # destination
    mastermix_dest = tuberack.wells()[0]

    info_list = [
        [cell.strip() for cell in line.split(',')]
        for line in master_mix_csv.splitlines()[1:] if line
    ]

    """ create mastermix """
    for line in info_list[1:]:
        source = tuberack.wells(line[1].upper())
        vol = float(line[2])
        pip = pip_s if vol <= pip_s.max_volume else pip_l
        pick_up(pip)
        pip.transfer(vol, source, mastermix_dest, new_tip='never')
        pip.drop_tip()

    """ distribute mastermix and transfer sample """
    if tc.lid_position != 'open':
        tc.open_lid()
    if using_multi:
        mm_source = mm_plate.rows()[0][0]
        mm_dests = tc_plate.rows()[0][:num_cols]
        vol_per_well = mastermix_volume*num_cols*1.05
        pick_up(p1)
        for well in mm_plate.columns()[0]:
            p1.transfer(vol_per_well, mm_tube, well, new_tip='never')
            p1.blow_out(well.top(-2))
        p1.drop_tip()
        pip_mm = p2

    else:
        mm_source = mm_tube
        mm_dests = tc_plate.wells()[:number_of_samples]
        pip_mm = pip_s if mastermix_volume <= pip_s.max_volume else pip_l

    for d in mm_dests:
        pick_up(pip_mm)
        pip_mm.transfer(mastermix_volume, mm_source, d, new_tip='never')
        pip_mm.drop_tip()

    # transfer DNA to corresponding well
    if using_multi:
        dna_sources = dna_plate.rows()[0][:num_cols]
        dna_dests = tc_plate.rows()[0][:num_cols]
        pip_dna = p2
    else:
        dna_sources = dna_plate.wells()[:number_of_samples]
        dna_dests = tc_plate.wells()[:number_of_samples]
        pip_dna = pip_s if dna_volume <= pip_s.max_volume else pip_l

    for s, d in zip(dna_sources, dna_dests):
        pick_up(pip_dna)
        pip_dna.transfer(
            dna_volume, s, d, mix_after=(5, 0.8*mastermix_volume + dna_volume),
            new_tip='never')
        pip_dna.drop_tip()

    """ run PCR profile on thermocycler """

    # Close lid
    if tc.lid_position != 'closed':
        tc.close_lid()

    # lid temperature set
    tc.set_lid_temperature(lid_temp)

    # initialization
    well_vol = mastermix_volume + dna_volume
    tc.set_block_temperature(
        init_temp, hold_time_seconds=init_time, block_max_volume=well_vol)

    # run profile
    profile = [
        {'temperature': d_temp, 'hold_time_seconds': d_time},
        {'temperature': a_temp, 'hold_time_seconds': a_temp},
        {'temperature': e_temp, 'hold_time_seconds': e_time}
    ]

    tc.execute_profile(
        steps=profile, repetitions=no_cycles, block_max_volume=well_vol)

    # final elongation
    tc.set_block_temperature(
        fe_temp, hold_time_seconds=fe_time, block_max_volume=well_vol)

    # final hold
    tc.deactivate_lid()
    tc.set_block_temperature(final_temp)

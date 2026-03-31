import math
from opentrons import protocol_api
from opentrons.types import Point

metadata = {
    'apiLevel': '2.14',
    'protocolName': 'Custom Dilution and PCR',
    'author': 'Nick Diehl <ndiehl@opentrons.com>'
}

DO_THERMOCYCLER = True


def run(ctx):

    [num_samples, cp_list, type_molecule,
     type_sample_rack] = get_values(  # noqa: F821
        'num_samples', 'cp_list', 'type_molecule', 'type_sample_rack')

    # [num_samples, cp_list, type_molecule] = [24, cp_list_ex, 'pDNA']

    # parse
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in cp_list.splitlines()
        if line and line.split(',')[0].strip()]

    num_cols = math.ceil((num_samples)/8)
    try:
        tc = ctx.load_module('thermocyclerModuleV2')
    except:  # noqa
        tc = ctx.load_module('thermocycler')
    tc.open_lid()
    tc_plate = tc.load_labware('biorad_96_wellplate_200ul_pcr')
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['3']]
    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['6', '9']]
    dil_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr',
                                 '5', 'dilution plate')
    res = ctx.load_labware('nest_12_reservoir_15ml', '2')
    tuberack = ctx.load_labware(type_sample_rack, '4')
    mm_plate = ctx.load_labware('biorad_96_aluminumblock_250ul', '1',
                                'mastermix plate')

    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tipracks300)
    p20 = ctx.load_instrument(
        'p20_single_gen2', 'right', tip_racks=tipracks20)

    samples = tuberack.wells()[:num_samples]
    rxn_mix_1 = res.wells()[0]
    rxn_mix_2 = res.wells()[1]
    diluent = res.wells()[2:6]
    mm = res.wells()[5]

    if type_molecule == '401':
        vol_rxn_mix_2 = 50.0
    elif type_molecule == 'pDNA':
        vol_rxn_mix_2 = 90.0

    # define liquids
    try:
        rxn_mix_1_liq = ctx.define_liquid(
            name='DNAse',
            description='DNAse',
            display_color='#00FF00',
        )
        rxn_mix_2_liq = ctx.define_liquid(
            name='PK',
            description='PK',
            display_color='#0000FF',
        )
        diluent_liq = ctx.define_liquid(
            name='dilution buffer',
            description='dilution buffer',
            display_color='#FF0000',
        )
        mastermix_liq = ctx.define_liquid(
            name='mastermix',
            description='mastermix',
            display_color='#FBFF00',
        )
        sample_liq = ctx.define_liquid(
            name='sample',
            description='sample, NTC, and DAC',
            display_color='#F300FF',
        )

        # load liquids
        [s.load_liquid(sample_liq, volume=200/num_samples) for s in samples]
        if not type_molecule == 'pDNA':
            rxn_mix_1.load_liquid(rxn_mix_1_liq, volume=30*num_cols*8*1.1+2000)
        if not type_molecule == '101':
            rxn_mix_2.load_liquid(
                rxn_mix_2_liq, volume=vol_rxn_mix_2*num_cols*8*1.1+2000)
        mm.load_liquid(mastermix_liq, volume=16.5*len(data)*4*1.1+2000)
        [d.load_liquid(diluent_liq, volume=1200)
         for d in diluent[:math.ceil(num_cols*4/3)]]

    except:  # noqa
        pass

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause('Replace the tips')
            pip.reset_tipracks()
            pip.pick_up_tip()

    vol_max_dil = 10500
    vol_current = 0
    dil_tracker = iter(diluent)
    dil_current = next(dil_tracker)

    def track_dilution(vol):
        nonlocal vol_current
        nonlocal dil_current
        vol_actual = vol*8  # multi-channel pipette
        if vol_actual + vol_current > vol_max_dil:
            vol_current = 0
            dil_current = next(dil_tracker)
        vol_current += vol_actual
        return dil_current

    def wick(pip, well, side=1):
        if well.diameter:
            radius = well.diameter/2
        else:
            radius = well.width/2
        pip.move_to(well.bottom().move(Point(x=side*radius*0.7, z=3)))

    def slow_withdraw(pip, well, delay=2.0):
        pip.default_speed /= 16
        ctx.delay(seconds=delay)
        pip.move_to(well.top())
        pip.default_speed *= 16

    rxn_mix_1_dests = [tc_plate.rows()[0][i*4+1] for i in range(num_cols)]
    if not type_molecule == 'pDNA':
        # first dilution
        first_dil_dests_m = [tc_plate.rows()[0][i*4] for i in range(num_cols)]
        pick_up(m300)
        vol_dil = 180
        for d in first_dil_dests_m:
            source = track_dilution(vol_dil)
            m300.aspirate(vol_dil, source)
            slow_withdraw(m300, source)
            m300.dispense(vol_dil, d.bottom(5))
            slow_withdraw(m300, d)
        m300.drop_tip()

        pick_up(m300)
        for d in rxn_mix_1_dests:
            m300.aspirate(30, rxn_mix_1)
            slow_withdraw(m300, rxn_mix_1)
            m300.dispense(30, d.bottom(2))
            slow_withdraw(m300, d)
        m300.drop_tip()

        # transfer sample
        first_dil_cols = [tc_plate.columns()[i*4] for i in range(num_cols)]
        first_dil_dests_s = [
            well for col in first_dil_cols for well in col][:num_samples]
        for i, (s, d) in enumerate(zip(samples, first_dil_dests_s)):
            pick_up(p20)
            p20.aspirate(20, s.bottom(0.5))
            slow_withdraw(p20, s)
            p20.dispense(20, d.bottom(d.depth/2))
            # p20.mix(5, 20, d.bottom(d.depth/2))
            slow_withdraw(p20, d)
            if i % 8 == 0:  # row A
                p20.move_to(d.top(2))
                p20.move_to(d.top().move(Point(y=-5, z=2)))
            p20.drop_tip()

        # add to mix
        for s, d in zip(first_dil_dests_m, rxn_mix_1_dests):
            pick_up(m300)
            m300.mix(5, 100, s.bottom(s.depth/2))
            m300.aspirate(20, s.bottom(5))
            slow_withdraw(m300, s)
            m300.dispense(20, d.bottom(2))
            m300.mix(5, 20, d.bottom(2))
            slow_withdraw(m300, d)
            m300.drop_tip()

        tc.close_lid()
        if DO_THERMOCYCLER:
            tc.set_lid_temperature(105)
            tc.set_block_temperature(37, hold_time_minutes=30)
        tc.open_lid()

    else:
        # rxn mix 2
        for d in rxn_mix_1_dests:

            pick_up(m300)
            m300.aspirate(vol_rxn_mix_2, rxn_mix_2)
            slow_withdraw(m300, rxn_mix_2)
            m300.dispense(vol_rxn_mix_2, d.bottom(2))
            # m300.mix(5, 20, d.bottom(d.depth/2))
            slow_withdraw(m300, d)
            m300.drop_tip()
        rxn_mix_1_columns = [
            tc_plate.columns()[tc_plate.rows()[0].index(col)]
            for col in rxn_mix_1_dests]
        rxn_mix_1_s = [
            well for col in rxn_mix_1_columns for well in col][:num_samples]
        for s, d in zip(samples, rxn_mix_1_s):
            pick_up(p20)
            p20.aspirate(10, s.bottom(0.5))
            slow_withdraw(p20, s)
            p20.dispense(10, d.top(-5))
            p20.mix(5, 20, d.bottom(d.depth/2))
            slow_withdraw(p20, d)
            p20.drop_tip()

    if not type_molecule == '101':
        if type_molecule == '401':  # rxn mix 2
            for d in rxn_mix_1_dests:
                pick_up(m300)
                m300.aspirate(50, rxn_mix_2)
                slow_withdraw(m300, rxn_mix_2)
                m300.dispense(50, d.bottom(2))
                m300.mix(5, 20, d.bottom(2), rate=0.5)
                slow_withdraw(m300, d)
                m300.drop_tip()

        tc.close_lid()
        if DO_THERMOCYCLER:
            tc.set_block_temperature(55, hold_time_minutes=30)
            tc.set_block_temperature(95, hold_time_minutes=15)
            tc.set_block_temperature(4)
        tc.open_lid()
        tc.deactivate_lid()

    dil_sets_tc = [
        tc_plate.rows()[0][i*4+2:i*4+4] for i in range(num_cols)
    ]
    dil_sets_dil = [
        dil_plate.rows()[0][i*4:i*4+4] for i in range(num_cols)
    ]
    dil_sets_all = []
    for set_t, set_d in zip(dil_sets_tc, dil_sets_dil):
        dil_set = set_t + set_d
        dil_sets_all.append(dil_set)

    # add diluent to all
    pick_up(m300)
    vol_dil = 180
    for d_set in dil_sets_all:
        for d in d_set:
            source = track_dilution(vol_dil)
            m300.aspirate(vol_dil, source)
            slow_withdraw(m300, source)
            m300.dispense(vol_dil, d.bottom(5))
            slow_withdraw(m300, d)

    def mix_high_low(reps, vol, well, h_low, h_high):
        for _ in range(reps):
            m300.aspirate(vol, well.bottom(h_low))
            m300.dispense(vol, well.bottom(h_high))

    # perform dilutions
    for i, dil_set in enumerate(dil_sets_all):
        sources = [rxn_mix_1_dests[i]] + dil_set[:len(dil_sets_all[0])-1]
        dests = dil_set
        for s, d in zip(sources, dests):
            if not m300.has_tip:
                pick_up(m300)
            m300.mix(1, 20, s.bottom(5))
            m300.aspirate(20, s.bottom(5))
            slow_withdraw(m300, s)
            m300.dispense(20, d.bottom(d.depth/2))
            mix_high_low(8, 50, d, d.depth/2-2, d.depth/2+3)
            m300.mix(8, 50, d.bottom(d.depth/2))
            slow_withdraw(m300, d)
            m300.drop_tip()

    # mm
    mm_dest_sets = [
        mm_plate.rows()[i % 8][(i//8)*4:(i//8 + 1)*4]
        for i in range(len(data))]
    pick_up(p20)
    for d_set in mm_dest_sets:
        for d in d_set:
            p20.aspirate(2, mm.top())  # pre-airgap
            p20.aspirate(16.5, mm)
            slow_withdraw(p20, mm)
            p20.dispense(p20.current_volume, d.bottom(1))
            slow_withdraw(p20, d)
    p20.drop_tip()

    # # add diluted positive control
    # pc_mm_dest_set = mm_dest_sets.pop(2)
    # pick_up(p20)
    # for d in pc_mm_dest_set:
    #     if not p20.has_tip:
    #         pick_up(p20)
    #     p20.aspirate(2, pc.bottom(0.5))  # pre-airgap
    #     p20.aspirate(5.5, pc.bottom(0.5))
    #     slow_withdraw(p20, pc)
    #     p20.dispense(5.5, d.bottom(2))
    #     slow_withdraw(p20, d)
    #     p20.drop_tip()

    # cherrypick
    cp_lw_map = {
        'T': tc_plate,
        'D': dil_plate
    }
    cp_sources = [
        cp_lw_map[line[1][0]].wells_by_name()[line[0]]
        for line in data]
    for s, d_set in zip(cp_sources, mm_dest_sets):
        for d in d_set:
            pick_up(p20)
            p20.aspirate(2, s.bottom(5))  # pre-airgap
            p20.aspirate(5.5, s.bottom(5))
            slow_withdraw(p20, s)
            p20.dispense(5.5, d.bottom(2))
            slow_withdraw(p20, d)
            p20.drop_tip()

    # fill remaining columns if necessary
    num_mm_dest_sets = len(data)  # including PC
    if num_mm_dest_sets % 8 == 0:
        remaining_rows = 0
    else:
        remaining_rows = 8 - num_mm_dest_sets % 8
    mm_dest_sets_blank = [
        mm_plate.rows()[i % 8][(i//8)*4:(i//8 + 1)*4]
        for i in range(num_mm_dest_sets, num_mm_dest_sets+remaining_rows)]
    vol_blank = 22.0
    tip_ref_vol = p20.tip_racks[0].wells()[0].max_volume - 2.0  # vol preairgap
    num_trans = math.ceil(vol_blank/tip_ref_vol)
    vol_per_trans = round(vol_blank/num_trans, 2)
    pick_up(p20)
    for dest_set in mm_dest_sets_blank:
        for d in dest_set:
            for _ in range(num_trans):
                source = track_dilution(vol_per_trans)
                p20.aspirate(2, source.top())  # pre-airgap
                p20.aspirate(vol_per_trans, source)
                slow_withdraw(p20, source)
                p20.dispense(p20.current_volume, d.bottom(2))
                slow_withdraw(p20, d)
    p20.drop_tip()

    tc.deactivate_block()

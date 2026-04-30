import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'ELISA',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        'num_samples')

    # labware
    num_plates_needed = math.ceil((num_samples - 8)/20)

    sample_plate = ctx.load_labware('thermo_96_wellplate_400ul', '5',
                                    'sample plate')
    elisa_plates = [
        ctx.load_labware(
            'thermo_96_wellplate_400ul', slot, f'test plate {i+1}')
        for i, slot in enumerate(['1', '2', '3'][:num_plates_needed])]
    res12 = ctx.load_labware('starlab_12_reservoir_22000ul', '6')
    res1 = ctx.load_labware('starlab_1_reservoir_240000ul', '7')
    waste = ctx.load_labware(
        'starlab_1_reservoir_240000ul', '9').wells()[0].top()
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in range(1, 12) if slot not in ctx.loaded_labwares]

    # pipettes
    p300 = ctx.load_instrument(
        'p300_single_gen2', 'left', tip_racks=tipracks300)
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'right', tip_racks=tipracks300)

    vol_sample = 50.0
    vol_wash = 300.0
    vol_a6029 = 50.0
    vol_tmb = 100.0
    vol_stop = 100.0

    pbst = res1.wells()[:1]
    a6029 = res12.rows()[0][:1]
    tmb = res12.rows()[0][1:3]
    stop = res12.rows()[0][3:5]

    try:
        pbst_liq = ctx.define_liquid(
            name='Beads', description='ampure beads', display_color='#B925FF')
        a6029_liq = ctx.define_liquid(
            name='A6029', description='A6029',
            display_color='#FFD600')
        tmb_liq = ctx.define_liquid(
            name='TMB', description='TMB',
            display_color='#9DFFD8')
        stop_liq = ctx.define_liquid(
            name='Stop Buffer', description='Stop Buffer',
            display_color='#FF9900')

        [well.load_liquid(
            liquid=pbst_liq, volume=vol_wash*4*96*3)
         for well in pbst]
        [well.load_liquid(
            liquid=a6029_liq, volume=vol_a6029*96*3+2000)
         for well in a6029]
        [well.load_liquid(
            liquid=tmb_liq, volume=(vol_tmb*96*3)/2+2000)
         for well in tmb]
        [well.load_liquid(
            liquid=stop_liq, volume=(vol_stop*96*3)/2+2000)
         for well in stop]
    except AttributeError:
        pass

    all_wells_multi = [
        col for plate in elisa_plates
        for col in plate.rows()[0]]

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause('Replace tipracks before resumin')
            pip.reset_tipracks()
            pick_up(pip)

    def slow_withdraw(pip, well, delay_seconds=1.0):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 10

    def slow_descend(pip, well, delay_seconds=1.0, z_offset=0.2):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.bottom(z_offset))
        pip.default_speed *= 10

    def wash(vol, reagent, remove_supernatant=True, time_incubation=0):

        # distribute reagent
        pick_up(m300)
        num_reagent_cols_per_channel = 36/len(reagent)  # 3 plates possible
        for i, well in enumerate(all_wells_multi):
            source = reagent[int(i//num_reagent_cols_per_channel)]
            m300.aspirate(vol, source)
            slow_withdraw(m300, source)
            m300.dispense(vol, well.top(-2), rate=2)

        if time_incubation > 0:
            m300.move_to(reagent[-1].top())
            ctx.delay(minutes=time_incubation,
                      msg=f'Incubating for {time_incubation}')

        if remove_supernatant:
            for well in all_wells_multi:
                if not m300.has_tip:
                    pick_up(m300)
                slow_descend(m300, well)
                m300.aspirate(vol)
                slow_withdraw(m300, well)
                m300.blow_out(waste)
                m300.drop_tip()
        else:
            m300.drop_tip()

    # protocol steps
    ctx.delay(minutes=60, msg='Incubating for 1 hour')

    all_wells_first_half = [
        well for plate in elisa_plates
        for col in plate.columns()[1:6]
        for well in col][:(num_samples-8)*2]
    all_wells_second_half = [
        well for plate in elisa_plates
        for col in plate.columns()[7:12]
        for well in col][:(num_samples-8)*2]

    # transfer samples initially
    for i, sample in enumerate(sample_plate.wells()[8:num_samples]):
        dest_set = all_wells_first_half[i*2:(i+1)*2] + \
            all_wells_second_half[i*2:(i+1)*2]
        pick_up(p300)
        for d in dest_set:
            p300.aspirate(vol_sample, sample)
            slow_withdraw(p300, sample)
            p300.dispense(vol_sample, d.bottom(2))
            slow_withdraw(p300, d)
        p300.drop_tip()

    initial_sample_destination_sets = [
        plate.columns()[col_ind]
        for plate in elisa_plates
        for col_ind in [0, 6]
    ]
    samples_1_8 = sample_plate.wells()[:8]
    for i, s in enumerate(samples_1_8):
        pick_up(p300)
        for dest_set in initial_sample_destination_sets:
            d = dest_set[i]
            p300.aspirate(vol_sample, s)
            slow_withdraw(p300, s)
            p300.dispense(vol_sample, d.bottom(2))
            slow_withdraw(p300, d)
        p300.drop_tip()

    # wash sequences
    for _ in range(3):
        wash(vol_wash, pbst)
    wash(vol_a6029, a6029, time_incubation=60)

    wash(vol_wash, pbst)
    wash(vol_tmb, tmb, remove_supernatant=False, time_incubation=15)
    wash(vol_stop, stop, remove_supernatant=False)

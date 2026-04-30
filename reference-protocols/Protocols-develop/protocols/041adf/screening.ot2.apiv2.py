import math
from opentrons.types import Point
from opentrons import protocol_api, types

metadata = {
    'protocolName': 'Reaction Library Screening',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, mount_m20, mount_m300] = get_values(  # noqa: F821
        'num_samples', 'mount_m20', 'mount_m300')

    # [num_samples, mount_m20, mount_m300] = 60, 'left', 'right'
    lw_deepwell = 'nest_96_wellplate_2000ul'

    vol_dmso = 8.7
    vol_teaa = 2.9
    vol_h2o = 1.0
    vol_oligo = 25.0
    vol_azides = 3.6
    vol_cu_ligand = 5.4
    vol_sodium_ascorbate = 5.4
    vol_acetone1 = 300.0
    vol_sodium_acetate = 30.0
    vol_acetone2 = 200.0
    do_mix_acetone = True

    # modules and labware
    hs = ctx.load_module('heaterShakerModuleV1', '7')
    hs_plate = hs.load_labware(
        lw_deepwell, 'reaction plate')
    hs.close_labware_latch()
    azides_plate = ctx.load_labware(lw_deepwell, '1',
                                    'azides')
    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['10', '4']]
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['5', '9']]
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2', 'reservoir')
    oligo_plate = ctx.load_labware('roarprinted_48_wellplate_1500ul', '11',
                                   'oligos')
    supernatant_plates = [
        ctx.load_labware(lw_deepwell, slot, f'supernatant plate {i+1}')
        for i, slot in enumerate(['3', '6'])]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', mount_m20,
                              tip_racks=tipracks20)
    m300 = ctx.load_instrument('p300_multi_gen2', mount_m300,
                               tip_racks=tipracks300)

    # reagents
    num_cols = math.ceil(num_samples/6)
    # num_rows = math.ceil(num_samples/10)
    oligos = oligo_plate.rows()[0][:3]
    [teaa, h2o, dmso, sodium_ascorbate, cu_ligand] = reservoir.rows()[0][:5]
    acetone = reservoir.rows()[0][6:12]
    sodium_acetate = reservoir.rows()[0][5]
    reaction_samples = hs_plate.rows()[0][1:1+num_cols]
    azides = azides_plate.rows()[0][1:1+num_cols]
    [supernatant_samples1, supernatant_samples2] = [
        plate.rows()[0][1:1+num_cols] for plate in supernatant_plates]

    default_current = 0.6
    offset_pickup_counter = {m20: 0, m300: 0}

    def pick_up(pip, num_tips=8):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause('Replace the tips')
            pip.reset_tipracks()
            pip.pick_up_tip()

    def pick_up_single(pip):

        current_modifier = 1/8
        current = default_current*current_modifier

        instr = types.Mount.RIGHT if pip.mount == 'right' else types.Mount.LEFT
        # if not ctx.is_simulating():
        ctx._hw_manager.hardware._attached_instruments[
            instr].update_config_item('pick_up_current', current)

        tip_loc = [
            tip for col in pip.tip_racks[-1].columns()[::-1]
            for tip in col[::-1]][offset_pickup_counter[pip]]
        offset_pickup_counter[pip] += 1

        pip.pick_up_tip(tip_loc)

        # reset current to default
        # if not ctx.is_simulating():
        ctx._hw_manager.hardware._attached_instruments[
            instr].update_config_item('pick_up_current', default_current)

    def wick(well, pip, side=1):
        pip.move_to(well.bottom().move(Point(x=side*well.diameter/2*0.8, z=3)))

    def slow_withdraw(well, pip, z=0, delay_seconds=2.0):
        ctx.max_speeds['A'] = 10
        ctx.max_speeds['Z'] = 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top(z))
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def custom_touch_tip(loc, pip, z=-1):
        pip.default_speed /= 5
        if loc.length:
            magnitude = loc.length/2
        else:
            magnitude = loc.diameter/2
        touch_points = [
            loc.top().move(Point(x=side*magnitude, z=z)) for side in [-1, 1]]
        for t_p in touch_points:
            pip.move_to(t_p)
        pip.default_speed *= 5

    def reagent_transfer(vol, reagent, destinations, num_tips=8,
                         new_tip='once', mix_reps=0, mix_vol=0, touch_tip=True,
                         rate=1.0, h_asp=1.0, h_disp=4.0):
        pip = m20 if vol <= 20 else m300
        if num_tips == 8:
            pick_up_func = pick_up
        else:
            pick_up_func = pick_up_single
        if new_tip == 'once':
            pick_up_func(pip, num_tips=num_tips)
        for d in destinations:
            if not pip.has_tip:
                pick_up_func(pip)
            pip.aspirate(vol, reagent.bottom(1), rate=rate)
            if touch_tip:
                custom_touch_tip(reagent, pip)
            slow_withdraw(reagent, pip)
            pip.dispense(vol, d.bottom(0.5), rate=rate)
            if mix_reps > 0:
                pip.mix(mix_reps, mix_vol, d.bottom(2), rate=rate)
            if touch_tip:
                slow_withdraw(d, pip, z=-1*d.depth/2)
                custom_touch_tip(d, pip, -1*d.depth/2)
            slow_withdraw(d, pip)
            if new_tip == 'always':
                pip.drop_tip()
        if pip.has_tip:
            pip.drop_tip()

    channel_index = 0
    channel_vol = 0
    max_vol = acetone[0].max_volume * 0.90  # 90% of capacity

    def check_acetone(vol):
        nonlocal channel_index
        nonlocal channel_vol
        vol_total = vol * 8  # multichannel
        if channel_vol + vol_total > max_vol:
            channel_index += 1
            channel_vol = 0
        if channel_index == len(acetone):
            ctx.pause('Refill acetone (reservoir channels 7-12).')
            channel_index = 0
            channel_vol = 0
        channel_vol += vol_total
        return acetone[channel_index]

    # transfer initial reagents to reaction plate
    reagent_transfer(vol_dmso, dmso, reaction_samples)
    reagent_transfer(vol_teaa, teaa, reaction_samples)
    reagent_transfer(vol_h2o, h2o, reaction_samples)

    # transfer oligos
    all_oligo_dests = [
        well for col in hs_plate.columns()[1:1+num_cols]
        for well in col[1:7]][:num_samples]
    num_oligos = len(oligos)
    max_dests_per_oligo = math.ceil(len(all_oligo_dests)/num_oligos)
    oligo_dest_sets = [
        all_oligo_dests[i*max_dests_per_oligo:(i+1)*max_dests_per_oligo]
        if i < num_oligos - 1
        else all_oligo_dests[i*max_dests_per_oligo:]
        for i in range(num_oligos)
    ]
    for oligo, oligo_dest_set in zip(oligos, oligo_dest_sets):
        reagent_transfer(vol_oligo, oligo, oligo_dest_set, num_tips=1,
                         new_tip='always', rate=0.5, h_asp=5.0, h_disp=10.0)

    # transfer remaining reagents
    for azide, d in zip(azides, reaction_samples):
        reagent_transfer(vol_azides, azide, [d])

    reagent_transfer(vol_cu_ligand, cu_ligand, reaction_samples,
                     new_tip='always', rate=0.2)
    reagent_transfer(vol_sodium_ascorbate, sodium_ascorbate, reaction_samples,
                     new_tip='always', mix_reps=3, mix_vol=10)

    # heater shaker incubation
    hs.set_and_wait_for_temperature(37)
    hs.set_and_wait_for_shake_speed(200)
    ctx.delay(minutes=1)
    hs.deactivate_shaker()

    ctx.pause('Resume when ready.')

    # add acetone
    pick_up(m300)
    ctx.delay(seconds=2)
    num_asp = math.ceil(
        vol_acetone1/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_asp = round(vol_acetone1/num_asp, 2)
    for i, d in enumerate(reaction_samples):
        for n in range(num_asp):
            acetone_channel = check_acetone(vol_per_asp)
            if i == 0 and n == 0:
                m300.mix(2, 300, acetone_channel.bottom(2))  # pre-wet
            m300.aspirate(vol_per_asp, acetone_channel.bottom(2))
            slow_withdraw(acetone_channel, m300, z=-1)
            custom_touch_tip(acetone_channel, m300)
            m300.dispense(vol_per_asp, d.top(-1))
            if n == num_asp - 1 and do_mix_acetone:
                m300.mix(5, 200, d.bottom(5))
            ctx.delay(seconds=2)
            custom_touch_tip(d, m300)
    m300.drop_tip()

    # add sodium acetate
    pick_up(m300)
    for i, d in enumerate(reaction_samples):
        if i == 0:
            m300.mix(2, 300, sodium_acetate.bottom(2))  # pre-wet
            ctx.delay(seconds=2)
        m300.aspirate(vol_sodium_acetate, sodium_acetate.bottom(2))
        slow_withdraw(sodium_acetate, m300, z=-1)
        custom_touch_tip(sodium_acetate, m300)
        m300.dispense(300, d.top(-1))
        ctx.delay(seconds=2)
        custom_touch_tip(d, m300)
    m300.drop_tip()

    ctx.pause('Resume when ready.')

    vol_supernatant = sum([vol_dmso, vol_teaa, vol_h2o, vol_oligo, vol_azides,
                           vol_cu_ligand, vol_sodium_ascorbate, vol_acetone1,
                           vol_sodium_acetate])*2

    supernatant_height = 7.0

    # transfer supernatant 1
    num_asp = math.ceil(
        vol_supernatant/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_asp = round(vol_supernatant/num_asp, 2)
    for s, d in zip(reaction_samples, supernatant_samples1):
        pick_up(m300)
        for _ in range(num_asp):
            m300.aspirate(vol_per_asp, s.bottom(supernatant_height), rate=0.5)
            slow_withdraw(s, m300, z=-1)
            custom_touch_tip(s, m300)
            m300.dispense(vol_per_asp, d.bottom(4), rate=0.5)
            slow_withdraw(d, m300, z=-1)
            custom_touch_tip(d, m300)
        m300.drop_tip()

    # add acetone 2
    pick_up(m300)
    num_asp = math.ceil(
        vol_acetone2/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_asp = round(vol_acetone2/num_asp, 2)
    for i, d in enumerate(reaction_samples):
        x_offset = d.length/2 if d.length else d.diameter/2
        for n in range(num_asp):
            acetone_channel = check_acetone(vol_per_asp)
            if i == 0 and n == 0:
                m300.mix(2, 300, acetone_channel.bottom(2))  # pre-wet
                ctx.delay(seconds=2)
            m300.aspirate(vol_per_asp, acetone_channel.bottom(2))
            slow_withdraw(acetone_channel, m300, z=-1)
            custom_touch_tip(acetone_channel, m300)
            m300.move_to(d.top().move(Point(x=x_offset, z=-1)))
            m300.dispense(vol_per_asp)
            ctx.delay(seconds=2)
            custom_touch_tip(d, m300)

    ctx.home()

    ctx.pause('Resume when ready')

    # transfer supernatant 2
    num_asp = math.ceil(
        vol_acetone2/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_asp = round(vol_acetone2/num_asp, 2)
    for s, d in zip(reaction_samples, supernatant_samples2):
        for _ in range(num_asp):
            if not m300.has_tip:
                pick_up(m300)
            m300.aspirate(vol_per_asp, s.bottom(supernatant_height), rate=0.5)
            slow_withdraw(s, m300, z=-1)
            custom_touch_tip(s, m300)
            m300.dispense(vol_per_asp, d.bottom(4), rate=0.5)
            slow_withdraw(d, m300, z=-1)
            custom_touch_tip(d, m300)
        m300.drop_tip()

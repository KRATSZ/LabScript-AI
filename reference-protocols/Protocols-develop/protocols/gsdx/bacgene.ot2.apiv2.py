import math
from opentrons.types import Point, Mount


metadata = {
    'protocolName': 'BACGene',
    'author': 'Nick Diehl <ndiehl@opentrons.com',
    'apiLevel': '2.14'
}

# total number of samples not to exceed 96
# (allow for positive and negative)
DO_CREATE_LYSIS_BUFFER = True
DO_DISTRIBUTE_LYSIS_BUFFER = True
DO_TRANSFER_SAMPLE_TO_LYSIS = True
DO_TRANSFER_SAMPLE_TO_PCR = True
DO_TRANSFER_POSITIVE_CONTROL = True
DO_MIX = True
DO_SET_TEMP = True
REUSING_LYSIS_BUFFER = True
OFFSET_Y_LYSIS_BUFFER_LISTERIA = 13.0
OFFSET_Z_LYSIS_BUFFER_LISTERIA = -4.5
OFFSET_Y_LYSIS_BUFFER_SALMONELLA = 11.0  # magnitude (positive number!)
OFFSET_Z_LYSIS_BUFFER_SALMONELLA = -4.5
OFFSET_X_TUBERACK = 0.5
P20_MOUNT = 'left'
P300_MOUNT = 'right'


def run(ctx):

    def flash_lights():
        initial_status = ctx.rail_lights_on
        for _ in range(19):
            ctx.set_rail_lights(not ctx.rail_lights_on)
            ctx.delay(seconds=0.25)
        ctx.set_rail_lights(initial_status)

    [num_samples_listeria, num_samples_salmonella,
     num_samples_listeria_remaining, num_samples_salmonella_remaining,
     sample_rack_type, salmonella_meat, do_flash] = get_values(  # noqa: F821
        'num_samples_listeria', 'num_samples_salmonella',
        'num_samples_listeria_remaining', 'num_samples_salmonella_remaining',
        'sample_rack_type', 'salmonella_meat', 'do_flash')

    # modules
    tempdeck = ctx.load_module('temperature module gen2', '10')
    if DO_SET_TEMP:
        tempdeck.set_temperature(37)

    # labware
    lysis_rack = ctx.load_labware(
        'opentrons_goldstandarddx_17_tuberack_lysis', '6',
        'lysis buffer, C+, enzymes')
    sample_plate = ctx.load_labware(
        sample_rack_type, '7', 'sample plate')

    lysis_plate = tempdeck.load_labware(
        'bioplasticsbv_96_aluminumblock_200ul', 'lysis plate')
    pcr_plate = ctx.load_labware(
        'bioplasticsbv_96_aluminumblock_100ul', '8', 'PCR plate')
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                         '20ul tiprack')
        for slot in ['1', '4', '11']]
    tipracks300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                         '200ul tiprack')
        for slot in ['2', '9']]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2',
                              P20_MOUNT,
                              tip_racks=tipracks20)
    m300 = ctx.load_instrument('p300_multi_gen2',
                               P300_MOUNT,
                               tip_racks=tipracks300)

    num_cols_listeria = math.ceil(num_samples_listeria/8)
    num_cols_salmonella = math.ceil(num_samples_salmonella/8)

    if 1 <= num_samples_listeria <= 2:
        raise Exception(
            f'Invalid number of listeria samples: {num_samples_listeria}.')
    if 1 <= num_samples_salmonella <= 2:
        raise Exception(
            f'Invalid number of salmonella samples: {num_samples_salmonella}.')
    if num_cols_listeria + num_cols_salmonella > 12:
        raise Exception('Combination of listeria and salmonella samples \
exceeds plate capacity')

    # define locations of lysis buffer reagents
    lysis_buffer_listeria = lysis_rack.rows_by_name()['B'][
        1::2]
    lysis_buffer_salmonella = lysis_rack.rows_by_name()['D'][
        1::2]
    enzyme_listeria_1 = lysis_rack.rows_by_name()['B'][
        ::2]
    enzyme_listeria_2 = lysis_rack.rows_by_name()['C']
    enzyme_salmonella = lysis_rack.rows_by_name()['D'][
        ::2]
    positive_control_l = lysis_rack.wells_by_name()['A1']
    positive_control_s = lysis_rack.wells_by_name()['E1']

    # define liquids
    try:
        lysis_buffer_l_prepared_liq = ctx.define_liquid(
            name="listeria lysis buffer (prepared)",
            description="",
            display_color="#B925FF",
        )
        lysis_buffer_l_fresh_liq = ctx.define_liquid(
            name="listeria lysis buffer (fresh)",
            description="",
            display_color="#E4ABFF",
        )
        lysis_buffer_s_prepared_liq = ctx.define_liquid(
            name="salmonella lysis buffer (prepared)",
            description="",
            display_color="#FFD600",
        )
        lysis_buffer_s_fresh_liq = ctx.define_liquid(
            name="salmonella lysis buffer (fresh)",
            description="",
            display_color="#FFF2AD",
        )
        enzyme_listeria_1_liq = ctx.define_liquid(
            name="listeria enzyme 1",
            description="",
            display_color="#000fde",
        )
        enzyme_listeria_2_liq = ctx.define_liquid(
            name="listeria enzyme 2",
            description="",
            display_color="#ffa500",
        )
        enzyme_salmonella_liq = ctx.define_liquid(
            name="salmonella enzyme",
            description="",
            display_color="#000fde",
        )
        positive_control_l_liq = ctx.define_liquid(
            name="listeria postive control",
            description="",
            display_color="#ffff00",
        )
        positive_control_s_liq = ctx.define_liquid(
            name="salmonella positive control",
            description="",
            display_color="#ffff00",
        )
        samples_listeria_liq_sample = ctx.define_liquid(
            name="listeria samples",
            description="",
            display_color="#0EFFFB",
        )
        samples_listeria_liq_lysis = ctx.define_liquid(
            name="listeria samples",
            description="",
            display_color="#0756EA",
        )
        samples_listeria_liq_pcr = ctx.define_liquid(
            name="listeria samples",
            description="",
            display_color="#130183",
        )
        samples_salmonella_liq_sample = ctx.define_liquid(
            name="salmonella samples",
            description="",
            display_color="#F6096D",
        )
        samples_salmonella_liq_lysis = ctx.define_liquid(
            name="salmonella samples",
            description="",
            display_color="#FF0000",
        )
        samples_salmonella_liq_pcr = ctx.define_liquid(
            name="salmonella samples",
            description="",
            display_color="#A92F00",
        )
    except AttributeError:
        pass

    samples_single_listeria = sample_plate.wells()[:num_samples_listeria]
    num_cols_offset_samples_listeria = math.ceil(num_samples_listeria/8)
    samples_single_salmonella = sample_plate.wells()[
        num_cols_offset_samples_listeria*8:
        num_cols_offset_samples_listeria*8+num_samples_salmonella]
    lysis_single_listeria = lysis_plate.wells()[:num_samples_listeria]
    lysis_single_salmonella = lysis_plate.wells()[
        num_cols_offset_samples_listeria*8:
        num_cols_offset_samples_listeria*8+num_samples_salmonella]
    pcr_single_listeria = pcr_plate.wells()[:num_samples_listeria]
    pcr_single_salmonella = pcr_plate.wells()[
        num_cols_offset_samples_listeria*8:
        num_cols_offset_samples_listeria*8+num_samples_salmonella]

    # load liquids
    vol_sample = 5.0

    try:
        if num_samples_listeria > 0:
            positive_control_l.load_liquid(
                positive_control_l_liq, volume=vol_sample)
        if num_samples_salmonella > 0:
            positive_control_s.load_liquid(
                positive_control_s_liq, volume=vol_sample)
        [well.load_liquid(samples_listeria_liq_sample,
                          volume=round(30/len(samples_single_listeria)))
         for well in samples_single_listeria[
            :max(0, len(samples_single_listeria)-2)]]
        [well.load_liquid(samples_salmonella_liq_sample,
                          volume=round(10/len(samples_single_salmonella)))
         for well in samples_single_salmonella[
            :max(0, len(samples_single_salmonella)-2)]]
        [well.load_liquid(samples_listeria_liq_lysis,
                          volume=round(30/len(lysis_single_listeria)))
         for well in lysis_single_listeria]
        [well.load_liquid(samples_salmonella_liq_lysis,
                          volume=round(10/len(lysis_single_salmonella)))
         for well in lysis_single_salmonella]
        [well.load_liquid(samples_listeria_liq_pcr,
                          volume=round(30/len(pcr_single_listeria)))
         for well in pcr_single_listeria]
        [well.load_liquid(samples_salmonella_liq_pcr,
                          volume=round(10/len(pcr_single_salmonella)))
         for well in pcr_single_salmonella]
    except AttributeError:
        pass

    single_tip_count_map = {m300: 0, m20: 0}
    tip_ref = m300.tip_racks[0].wells()[0]
    default_current = 1

    right = True

    def drop(pip):
        nonlocal right
        offset = 30 if right else -15
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=offset))
        pip.drop_tip(drop_loc)
        right = not right

    def pick_up_single(pip=m300):
        mount = Mount.LEFT if pip.mount == 'left' else Mount.RIGHT
        current_single = 1/8*default_current
        if not ctx.is_simulating():
            # attenuate pickup current
            ctx._hw_manager.hardware._attached_instruments[
                mount].update_config_item(
                    'pick_up_current', current_single)
        pip.pick_up_tip(
            [well
             for col in pip.tip_racks[-1].columns()
             for well in col[::-1]][single_tip_count_map[pip]])
        single_tip_count_map[pip] += 1
        if not ctx.is_simulating():
            # reset pickup current
            ctx._hw_manager.hardware._attached_instruments[
                mount].update_config_item('pick_up_current', default_current)

    def slow_withdraw(pip, well, delay_seconds=2.0, y_offset=0):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(delay_seconds)
        pip.move_to(well.top().move(Point(y=y_offset)))
        pip.default_speed *= 10

    def wick(pip, well, x_magnitude=0.5, z_offset=3.0):
        radius = well.diameter/2 if well.diameter else well.width/2
        pip.default_speed /= 2
        pip.move_to(well.bottom().move(Point(x=x_magnitude*radius,
                                             z=z_offset)))
        pip.default_speed *= 2

    """ create lysis buffer with enzyme """
    if DO_CREATE_LYSIS_BUFFER:

        vol_enzyme = 500.0
        num_trans = math.ceil(vol_enzyme/tip_ref.max_volume)
        vol_per_trans = round(vol_enzyme/num_trans, 1)

        if num_samples_listeria_remaining % 48 == 0 or \
                num_samples_listeria_remaining % 48 == 47:
            num_partial_listeria_buffers = 0
            num_bvs_effective = 0
        else:
            num_partial_listeria_buffers = 1
            if 2*math.ceil(num_samples_listeria_remaining/2) % 48 == 0:
                num_bvs_effective = 48
            else:
                num_bvs_effective = 2*math.ceil(
                    num_samples_listeria_remaining/2) % 48

        num_additional_listeria_buffers = math.ceil(
            ((num_samples_listeria-1) - num_bvs_effective)/48)

        # print(f'partial: {num_partial_listeria_buffers}')
        # print(f'additional: {num_additional_listeria_buffers}')

        enzyme_listeria_1_creation = enzyme_listeria_1[
            num_partial_listeria_buffers:
            num_partial_listeria_buffers+num_additional_listeria_buffers]
        enzyme_listeria_2_creation = enzyme_listeria_2[
            num_partial_listeria_buffers:
            num_partial_listeria_buffers+num_additional_listeria_buffers]
        lysis_buffer_listeria_creation = lysis_buffer_listeria[
            num_partial_listeria_buffers:
            num_partial_listeria_buffers+num_additional_listeria_buffers]
        # print(lysis_buffer_listeria_creation)

        # load partial liq
        if num_samples_listeria > 0:
            try:
                [
                    well.load_liquid(
                        lysis_buffer_l_prepared_liq,
                        volume=11000/num_partial_listeria_buffers)
                    for well in lysis_buffer_listeria[
                        :num_partial_listeria_buffers]]

                # load full liq
                [
                    well.load_liquid(
                        lysis_buffer_l_fresh_liq,
                        volume=11000/num_additional_listeria_buffers)
                    for well in lysis_buffer_listeria[
                        num_partial_listeria_buffers:
                        num_partial_listeria_buffers +
                        num_additional_listeria_buffers]]
                [
                    well.load_liquid(
                        enzyme_listeria_1_liq,
                        volume=500/num_additional_listeria_buffers)
                    for well in enzyme_listeria_1[
                        num_partial_listeria_buffers:
                        num_partial_listeria_buffers +
                        num_additional_listeria_buffers]]
                [
                    well.load_liquid(
                        enzyme_listeria_2_liq,
                        volume=500/num_additional_listeria_buffers)
                    for well in enzyme_listeria_2[
                        num_partial_listeria_buffers:
                        num_partial_listeria_buffers +
                        num_additional_listeria_buffers]]
            except AttributeError:
                pass

        # listeria
        for enzyme1, enzyme2, lysis_buff in zip(
                enzyme_listeria_1_creation,
                enzyme_listeria_2_creation,
                lysis_buffer_listeria_creation):
            # enzyme 1
            pick_up_single(m300)
            for _ in range(num_trans):
                m300.aspirate(
                    vol_per_trans, enzyme1.bottom().move(
                        Point(x=OFFSET_X_TUBERACK, z=1)))
                slow_withdraw(m300, enzyme1)
                m300.move_to(
                    lysis_buff.top().move(
                        Point(x=OFFSET_X_TUBERACK,
                              y=OFFSET_Y_LYSIS_BUFFER_LISTERIA)))
                m300.dispense(
                    vol_per_trans,
                    lysis_buff.bottom().move(
                        Point(x=OFFSET_X_TUBERACK,
                              y=OFFSET_Y_LYSIS_BUFFER_LISTERIA,
                              z=3)))
                m300.blow_out()
                slow_withdraw(
                    m300, lysis_buff, y_offset=OFFSET_Y_LYSIS_BUFFER_LISTERIA)
            drop(m300)

            # enzyme 2
            pick_up_single(m300)
            for i in range(num_trans):
                m300.aspirate(
                    vol_per_trans, enzyme2.bottom().move(
                        Point(x=OFFSET_X_TUBERACK, z=1)))
                slow_withdraw(m300, enzyme2)
                m300.move_to(
                    lysis_buff.top().move(Point(
                        x=OFFSET_X_TUBERACK,
                        y=OFFSET_Y_LYSIS_BUFFER_LISTERIA)))
                m300.dispense(
                    vol_per_trans,
                    lysis_buff.bottom().move(
                        Point(x=OFFSET_X_TUBERACK,
                              y=OFFSET_Y_LYSIS_BUFFER_LISTERIA,
                              z=3)))
                if i == num_trans - 1:
                    if DO_MIX:
                        m300.flow_rate.aspirate *= 2
                        m300.flow_rate.dispense *= 2
                        m300.mix(
                            10, 200,
                            lysis_buff.bottom().move(Point(
                                x=OFFSET_X_TUBERACK,
                                z=3, y=OFFSET_Y_LYSIS_BUFFER_LISTERIA)))
                        m300.flow_rate.aspirate /= 2
                        m300.flow_rate.dispense /= 2
                m300.blow_out(
                    lysis_buff.bottom().move(Point(
                        x=OFFSET_X_TUBERACK,
                        y=OFFSET_Y_LYSIS_BUFFER_LISTERIA, z=3)))
                slow_withdraw(
                    m300, lysis_buff, y_offset=OFFSET_Y_LYSIS_BUFFER_LISTERIA)
            drop(m300)

        # salmonella
        if num_samples_salmonella_remaining % 48 == 0 or \
                num_samples_salmonella_remaining == 47:
            num_partial_salmonella_buffers = 0
            num_bvs_effective = 0
        else:
            num_partial_salmonella_buffers = 1
            if 2*math.ceil(num_samples_salmonella_remaining/2) % 48 == 0:
                num_bvs_effective = 48
            else:
                num_bvs_effective = 2*math.ceil(
                    num_samples_salmonella_remaining/2) % 48

        num_additional_salmonella_buffers = math.ceil(
            ((num_samples_salmonella-1) - num_bvs_effective)/48)

        enzyme_salmonella_creation = enzyme_salmonella[
            num_partial_salmonella_buffers:
            num_partial_salmonella_buffers+num_additional_salmonella_buffers]
        lysis_buffer_salmonella_creation = lysis_buffer_salmonella[
            num_partial_salmonella_buffers:
            num_partial_salmonella_buffers+num_additional_salmonella_buffers]

        # load partial liq
        if num_samples_salmonella > 0:
            try:
                [
                    well.load_liquid(
                        lysis_buffer_s_prepared_liq,
                        volume=11000/num_partial_salmonella_buffers)
                    for well in lysis_buffer_salmonella[
                        :num_partial_salmonella_buffers]]

                # load full liq
                [
                    well.load_liquid(
                        lysis_buffer_s_fresh_liq,
                        volume=11000/num_additional_salmonella_buffers)
                    for well in lysis_buffer_salmonella[
                        num_partial_salmonella_buffers:
                        num_partial_salmonella_buffers +
                            num_additional_salmonella_buffers]]
                [
                    well.load_liquid(
                        enzyme_salmonella_liq,
                        volume=500/num_additional_salmonella_buffers)
                    for well in enzyme_salmonella[
                        num_partial_salmonella_buffers:
                        num_partial_salmonella_buffers +
                            num_additional_salmonella_buffers]]
            except AttributeError:
                pass

        for enzyme, lysis_buff in zip(enzyme_salmonella_creation,
                                      lysis_buffer_salmonella_creation):
            # enzyme
            pick_up_single(m300)
            for i in range(num_trans):
                m300.aspirate(vol_per_trans, enzyme.bottom().move(
                    Point(x=OFFSET_X_TUBERACK, z=1)))
                slow_withdraw(m300, enzyme)
                m300.move_to(
                    lysis_buff.top().move(
                        Point(x=OFFSET_X_TUBERACK,
                              y=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA)))
                m300.dispense(
                    vol_per_trans,
                    lysis_buff.bottom().move(
                        Point(x=OFFSET_X_TUBERACK,
                              y=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA,
                              z=3)))
                if i == num_trans - 1:
                    if DO_MIX:
                        m300.flow_rate.aspirate *= 2
                        m300.flow_rate.dispense *= 2
                        m300.mix(
                            10, 200,
                            lysis_buff.bottom().move(Point(
                                x=OFFSET_X_TUBERACK,
                                z=3, y=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA)))
                        m300.flow_rate.aspirate /= 2
                        m300.flow_rate.dispense /= 2
                m300.blow_out(
                    lysis_buff.bottom().move(
                        Point(x=OFFSET_X_TUBERACK,
                              y=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA,
                              z=3)))
                slow_withdraw(
                    m300, lysis_buff,
                    y_offset=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA)
            drop(m300)

    """ transfer lysis buffer to lysis plate """
    vol_overage = 20

    if num_samples_listeria > 0:
        if DO_DISTRIBUTE_LYSIS_BUFFER:
            lysis_buffer_listeria_dests = lysis_plate.wells()[
                :num_samples_listeria-2] + [
                    lysis_plate.wells()[num_samples_listeria-1]]
            vol_lysis_buffer_listeria = 70.0
            num_dests_per_asp = int(
                (tip_ref.max_volume-vol_overage)//vol_lysis_buffer_listeria)
            num_asp = math.ceil(
                len(lysis_buffer_listeria_dests)/num_dests_per_asp)
            lysis_buffer_listeria_dest_sets = [
                lysis_buffer_listeria_dests[i*num_dests_per_asp:
                                            (i+1)*num_dests_per_asp]
                if i < num_asp - 1
                else lysis_buffer_listeria_dests[i*num_dests_per_asp:]
                for i in range(num_asp)]
            pick_up_single(m300)
            m300.aspirate(
                vol_overage,
                lysis_buffer_listeria[0].bottom().move(Point(
                    y=OFFSET_Y_LYSIS_BUFFER_LISTERIA,
                    z=OFFSET_Z_LYSIS_BUFFER_LISTERIA)))
            num_asp_listeria_remaining = math.ceil(
                (num_samples_listeria_remaining % 48) / 2)
            bump = 24 - num_asp_listeria_remaining \
                if 24 - num_asp_listeria_remaining != 24 else 0
            for i, d_set in enumerate(lysis_buffer_listeria_dest_sets):
                set_ind = i + bump
                lysis_buff = lysis_buffer_listeria[set_ind//24]
                # m300.blow_out(lysis_buff.top(-1))
                m300.aspirate(
                    len(d_set)*vol_lysis_buffer_listeria,
                    lysis_buff.bottom().move(Point(
                        y=OFFSET_Y_LYSIS_BUFFER_LISTERIA,
                        z=OFFSET_Z_LYSIS_BUFFER_LISTERIA)))
                slow_withdraw(
                    m300, lysis_buff, y_offset=OFFSET_Y_LYSIS_BUFFER_LISTERIA)
                for d in d_set:
                    m300.dispense(vol_lysis_buffer_listeria, d.bottom(2))
                    slow_withdraw(m300, d)
            drop(m300)

    if num_samples_salmonella > 0:
        if DO_DISTRIBUTE_LYSIS_BUFFER:
            available_wells = [
                well for col in lysis_plate.columns()[num_cols_listeria:]
                for well in col]
            lysis_buffer_salmonella_dests = available_wells[
                :num_samples_salmonella-2] + [
                    available_wells[num_samples_salmonella-1]]
            vol_lysis_buffer_salmonella = 90.0 if not salmonella_meat else 50.0
            num_dests_per_asp = 2  # hard-set for now
            num_asp = math.ceil(
                len(lysis_buffer_salmonella_dests)/num_dests_per_asp)
            lysis_buffer_salmonella_dest_sets = [
                lysis_buffer_salmonella_dests[i*num_dests_per_asp:
                                              (i+1)*num_dests_per_asp]
                if i < num_asp - 1
                else lysis_buffer_salmonella_dests[i*num_dests_per_asp:]
                for i in range(num_asp)]
            pick_up_single(m300)
            m300.aspirate(
                vol_overage,
                lysis_buffer_salmonella[0].bottom().move(
                    Point(y=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA,
                          z=OFFSET_Z_LYSIS_BUFFER_SALMONELLA)))
            num_asp_salmonella_remaining = math.ceil(
                (num_samples_salmonella_remaining % 48) / 2)
            bump_check = int(48/num_dests_per_asp)
            bump = bump_check - num_asp_salmonella_remaining \
                if bump_check - num_asp_salmonella_remaining != bump_check \
                else 0
            for i, d_set in enumerate(lysis_buffer_salmonella_dest_sets):
                set_ind = i + bump
                lysis_buff = lysis_buffer_salmonella[set_ind//bump_check]
                # m300.blow_out(lysis_buff.top(-1))
                # print('salmonella', i, set_ind, lysis_buff, len(d_set))
                # m300.blow_out(lysis_buff.top(-1))
                m300.aspirate(
                    len(d_set)*vol_lysis_buffer_salmonella,
                    lysis_buff.bottom().move(Point(
                        y=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA,
                        z=OFFSET_Z_LYSIS_BUFFER_SALMONELLA)))
                slow_withdraw(m300, lysis_buff,
                              y_offset=-OFFSET_Y_LYSIS_BUFFER_SALMONELLA)
                for d in d_set:
                    m300.dispense(vol_lysis_buffer_salmonella, d.bottom(2))
                    slow_withdraw(m300, d)
            drop(m300)

    if DO_TRANSFER_SAMPLE_TO_LYSIS:
        """ transfer listeria """
        vol_listeria = 30.0
        num_sample_cols_listeria = math.ceil((num_samples_listeria-2)/8)
        for s, d in zip(sample_plate.rows()[0][:num_sample_cols_listeria],
                        lysis_plate.rows()[0][:num_sample_cols_listeria]):
            if sample_rack_type == 'bioplastics':
                asp_loc = s.bottom(2)
            else:
                asp_loc = s.top(-17.36)
            m300.pick_up_tip()
            m300.aspirate(vol_listeria, asp_loc)
            slow_withdraw(m300, s)
            m300.dispense(vol_listeria, d.bottom(2))
            if DO_MIX:
                m300.mix(3, 50, d.bottom(2))
            m300.blow_out(d.bottom(2))
            slow_withdraw(m300, d)
            drop(m300)

        """ transfer salmonella """
        [pip, vol_salmonella] = [m20, 10.0] \
            if not salmonella_meat else [m300, 50.0]
        num_cols_samples_salmonella = math.ceil((num_samples_salmonella-2)/8)
        for s, d in zip(
                sample_plate.rows()[0][
                    num_cols_listeria:
                    num_cols_listeria+num_cols_samples_salmonella],
                lysis_plate.rows()[0][
                    num_cols_listeria:
                    num_cols_listeria+num_cols_samples_salmonella]):
            pip.pick_up_tip()
            if sample_rack_type == 'bioplastics':
                asp_loc = s.bottom(2)
            else:
                asp_loc = s.top(-17.36)
            pip.aspirate(vol_salmonella, asp_loc)
            slow_withdraw(pip, s)
            pip.dispense(vol_salmonella, d.bottom(2))
            if DO_MIX:
                pip.mix(3, 18, d.bottom(2))
            pip.blow_out(d.bottom(2))
            slow_withdraw(pip, d)
            drop(pip)

    if DO_SET_TEMP:
        ctx.delay(minutes=20, msg='Incubating for 20 minutes @ 37C.')
        tempdeck.set_temperature(95)
        ctx.delay(minutes=10, msg='Incubating for 10 minutes @ 95C.')
        tempdeck.set_temperature(37)

    if DO_TRANSFER_SAMPLE_TO_PCR:
        """ transfer samples to PCR plate """

        # listeria
        if num_samples_listeria > 0:
            for s, d in zip(lysis_plate.rows()[0][:num_cols_listeria],
                            pcr_plate.rows()[0][:num_cols_listeria]):
                m20.pick_up_tip()
                m20.aspirate(5, s.top())  # pre air gap
                m20.aspirate(vol_sample, s)
                slow_withdraw(m20, s)
                m20.dispense(vol_sample, d.bottom(1))
                # if DO_MIX:
                #     m20.mix(3, vol_sample*0.8, d.bottom(1))
                m20.dispense(m20.current_volume, d.bottom(1))
                slow_withdraw(m20, d)
                # wick(m20, d)
                drop(m20)

        # salmonella
        if num_samples_salmonella > 0:
            for s, d in zip(
                    lysis_plate.rows()[0][
                        num_cols_listeria:
                        num_cols_listeria+num_cols_salmonella],
                    pcr_plate.rows()[0][
                        num_cols_listeria:
                        num_cols_listeria+num_cols_salmonella]):
                m20.pick_up_tip()
                m20.aspirate(5, s.top())  # pre air gap
                m20.aspirate(vol_sample, s)
                slow_withdraw(m20, s)
                m20.dispense(vol_sample, d.bottom(1))
                # if DO_MIX:
                #     m20.mix(3, vol_sample*0.8, d.bottom(1))
                m20.dispense(m20.current_volume, d.bottom(1))
                slow_withdraw(m20, d)
                m20.air_gap(5)
                # wick(m20, d)
                drop(m20)

    if DO_TRANSFER_POSITIVE_CONTROL:
        """ transfer positive controls """
        vol_positive_control = vol_sample
        if num_samples_listeria > 0:
            positive_control_l_dest = pcr_plate.wells()[num_samples_listeria-2]
            pick_up_single(m20)
            m20.aspirate(5, positive_control_l_dest.top())  # pre air gap
            m20.aspirate(vol_positive_control, positive_control_l)
            slow_withdraw(m20, positive_control_l)
            m20.dispense(m20.current_volume, positive_control_l_dest.bottom(1))
            slow_withdraw(m20, positive_control_l_dest)
            # if DO_MIX:
            #     m20.mix(3, vol_positive_control*0.8,
            #             positive_control_l_dest.bottom(1))
            # wick(m20, positive_control_l_dest)
            drop(m20)

        if num_samples_salmonella > 0:
            available_wells = [
                well for col in pcr_plate.columns()[num_cols_listeria:]
                for well in col]
            positive_control_s_dest = available_wells[num_samples_salmonella-2]
            pick_up_single(m20)
            m20.aspirate(5, positive_control_s.top())  # pre air gap
            m20.aspirate(vol_positive_control, positive_control_s)
            slow_withdraw(m20, positive_control_s)
            m20.dispense(m20.current_volume, positive_control_s_dest.bottom(1))
            slow_withdraw(m20, positive_control_s_dest)
            # if DO_MIX:
            #     m20.mix(3, vol_positive_control*0.8,
            #             positive_control_s_dest.bottom(1))
            # wick(m20, positive_control_s_dest)
            drop(m20)

    tempdeck.deactivate()

    if do_flash:
        flash_lights()

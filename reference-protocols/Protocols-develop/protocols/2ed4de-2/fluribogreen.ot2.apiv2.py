import math

from opentrons import types
from opentrons.types import Point


metadata = {
    'protocolName': 'FluRibogreen Assay',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samples, reagent_labware, starting_conc, prepare_standard,
     standard_type, p1000_mount, p300_mount] = get_values(  # noqa: F821
        'num_samples', 'reagent_labware', 'starting_conc', 'prepare_standard',
        'standard_type', 'p1000_mount', 'p300_mount')

    final_transfer_vol = 100
    sample_vol = 25
    max_working_vol = 1000
    mix_reps = 10
    max_factor_1_dil = max_working_vol/sample_vol

    # load labwarex
    sample_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '11',
        'sample tuberack')
    deepplate = ctx.load_labware('nest_96_wellplate_2ml_deep', '5',
                                 'standard preparation plate')
    flatplate = ctx.load_labware('corning_96_wellplate_360ul_flat', '2',
                                 'final plate')
    reagent_labware = ctx.load_labware(reagent_labware, '8',
                                       'standards and buffers')
    tipracks1000 = ctx.load_labware('opentrons_96_filtertiprack_1000ul', '7')
    tipracks200 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '6')
    tiprack200m = ctx.load_labware('opentrons_96_filtertiprack_200ul', '9')

    # load pipettes
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=[tipracks1000])
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=[tiprack200m])

    tip_data = {
        'single': {
            'count': 0,
            'tips': [
                well for col in tipracks200.columns()[::-1]
                for well in col[::-1]]
        },
        'multi': {
            'count': 0,
            'tips': tipracks200.rows()[0]
        }
    }

    def pickup_p300(mode='single'):
        current = 0.1 if mode == 'single' else 0.5
        ctx._hw_manager.hardware._attached_instruments[types.Mount.RIGHT].update_config_item('pick_up_current', current)  # noqa:E501
        #
        '''
        ctx._hw_manager.hardware._attached_instruments[
            p300._implementation.get_mount()].update_config_item(
                'pick_up_current', current)
        '''

        p300.pick_up_tip(tip_data[mode]['tips'][tip_data[mode]['count']])
        tip_data[mode]['count'] += 1

    side = 1

    def drop(pip):
        nonlocal side
        center = ctx.loaded_labwares[12].wells()[0].top()
        pip.drop_tip(center.move(Point(x=side*20)))
        side = side * -1

    working_standard_1 = reagent_labware.wells()[5]
    assay_buffer_1 = reagent_labware.wells()[6:9]
    starting_samples = sample_rack.wells()[:num_samples]
    num_sets = math.ceil(num_samples/8)
    all_samples = [
        deepplate.columns()[i*3:(i+1)*3]
        for i in range(1, 1+num_sets)]

    def standard_prep(standard, buffer, column):
        dilution_col = column[:7]
        for vol, dest in zip([900, 700, 500, 300, 100], dilution_col[:5]):
            p1000.pick_up_tip()
            p1000.transfer(vol, standard, dest, new_tip='never')
            drop(p1000)

        for vol, dest in zip([100, 300, 500, 700, 900, 950, 1000],
                             dilution_col):
            p1000.pick_up_tip()
            p1000.transfer(vol, buffer[0], dest, mix_after=(5, 800),
                           new_tip='never')
            drop(p1000)
        pickup_p300('single')
        p300.aspirate(50, standard.bottom(2))
        p300.dispense(50, dilution_col[5].bottom(3))
        p300.mix(1, 100, dilution_col[5].bottom(3))
        drop(p300)
        p1000.pick_up_tip()
        p1000.mix(mix_reps, 800, dilution_col[5])
        drop(p1000)

    def dilute(final_conc, dil_sets, buffer):
        dil_factor = starting_conc/final_conc
        # find necessary dilution factor(s)
        if dil_factor > max_factor_1_dil:
            factors = [10, dil_factor/10]
        else:
            factors = [dil_factor]

        # pre add diluent
        for i, factor in enumerate(factors):
            dil_vol = (factor-1)*sample_vol*(i+1)
            print(dil_vol)
            for j, set in enumerate(dil_sets):
                for k, well in enumerate(set[i]):
                    if j*k+k < num_samples:
                        p1000.pick_up_tip()
                        p1000.transfer(dil_vol,
                                       buffer[1+int((j*8+k)//(num_samples/2))],
                                       well, new_tip='never')
                        drop(p1000)

        p300.flow_rate.aspirate = 40
        p300.flow_rate.dispense = 40
        # transfer sample
        for i, s in enumerate(starting_samples):
            print(sample_vol)
            pickup_p300('single')
            well = dil_sets[i//8][0][i % 8]
            p300.aspirate(sample_vol, s.bottom(2))
            p300.dispense(sample_vol, well.bottom(3))
            p300.mix(1, 20, well.bottom(3))
            drop(p300)
        p300.flow_rate.aspirate = 94
        p300.flow_rate.dispense = 94

        # perform dilution
        for i, factor in enumerate(factors):
            for set in dil_sets:
                pickup_p300('multi')
                total_vol = sample_vol*(i+1)*factor
                mix_vol = total_vol*0.8 if total_vol*0.8 <= 175 else 175
                if i == 0:
                    p300.mix(mix_reps, mix_vol, set[i][0])
                else:
                    print(sample_vol*(i+1))
                    p300.transfer(sample_vol*(i+1), set[i-1][0].bottom(3),
                                  set[i][0].bottom(3),
                                  mix_after=(5, mix_vol),
                                  new_tip='never')
                drop(p300)

        return int(len(factors)-1)

    """ PART 1 """
    if prepare_standard:

        # standard preparation
        standard_prep(working_standard_1, assay_buffer_1,
                      deepplate.columns()[0])

    """ PART 2 """

    # sample normalization (TE or TR)
    sample_1_final_ind = dilute(standard_type, all_samples, assay_buffer_1)

    """ PART 3 """

    # transfer to final black plate
    sources = [deepplate.rows_by_name()['A'][0]] + [
        set[sample_1_final_ind][0] for set in all_samples]
    for i, source in enumerate(sources):
        dest_set = flatplate.rows()[0][i*3:(i+1)*3]
        for dest in dest_set:
            p300.pick_up_tip()
            p300.transfer(final_transfer_vol, source.bottom(3), dest.bottom(3),
                          mix_before=(mix_reps, 0.8*final_transfer_vol),
                          new_tip='never')
            drop(p300)

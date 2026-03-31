metadata = {
    'protocolName': '''Illumina DNA Prep with Enrichment:
    Part 1 - Tagmentation, Clean Up, Amplify Tagmented DNA''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [twb_rate, sample_count, disp_vol, engage_time
     ] = get_values(  # noqa: F821
      'twb_rate', 'sample_count', 'disp_vol', 'engage_time')

    ctx.set_rail_lights(True)

    if sample_count < 1 or sample_count > 12:
        raise Exception('Invalid number of samples (must be 1-12).')

    # tips and pipettes
    tips300 = [ctx.load_labware("opentrons_96_filtertiprack_200ul", '5')]
    p300s = ctx.load_instrument(
        "p300_single_gen2", 'right', tip_racks=tips300)
    tips20 = [ctx.load_labware("opentrons_96_filtertiprack_20ul", '4')]
    p20s = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)

    # temperature module
    temp = ctx.load_module('Temperature Module', '9')
    temp_block = temp.load_labware(
        "opentrons_24_aluminumblock_nest_2ml_snapcap")
    reagents_temp = {}
    for reagent, well in zip(
     ['smb', 'eew', 'empty 1', 'empty 2', 'empty 3', 'empty 4', 'empty 5'],
     ['A1', 'B1', 'A2', 'A3', 'A4', 'A5', 'A6']):
        reagents_temp[reagent] = temp_block.wells_by_name()[well]

    # helper function to avoid edge wells during thermocycling steps
    def no_edges(plate):
        return [
         well for column in [
          column for column in plate.columns()[1:11]] for well in column[1:7]]

    # thermocycler module
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    tc_plate = tc.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    [heat_wells, pcr_wells] = [
     no_edges(tc_plate)[
      start_index:sample_count + start_index] for start_index in [0, 12]]

    # magnetic module
    mag = ctx.load_module('magnetic module gen2', '6')
    mag_plate = mag.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    mag.disengage()
    [mag_wells, post_pcr_mag_wells, clean_mag_wells, sup_mag_wells] = [
     mag_plate.wells()[
      start_index:sample_count + start_index] for start_index in [
      0, 16, 32, 48]]

    # initial samples
    sample_plate = ctx.load_labware(
     "nest_96_wellplate_100ul_pcr_full_skirt", '1')
    samples = sample_plate.wells()[:sample_count]

    # block
    block = ctx.load_labware(
     "opentrons_24_aluminumblock_nest_2ml_snapcap", '3')
    reagents_block = {}
    for reagent, well in zip(
     ['eblt', 'tbs', 'empty 1', 'st2', 'epm', 'empty 2', 'rsb', 'nhb2',
      'enrich', 'ehb2'],
     ['A1', 'B1', 'C1', 'D1', 'A2', 'B2', 'C2', 'D2', 'A3', 'B3']):
        reagents_block[reagent] = block.wells_by_name()[well]

    # reservoir
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", '2')
    reagents_res = {}
    for reagent, well in zip(
     ['twb', 'water', 'beads', 'waste', 'etoh'],
     ['A1', 'A2', 'A3', 'A4', 'A5']):
        reagents_res[reagent] = reservoir.wells_by_name()[well]

    # mix eBLT and tbs, 20 ul to cycler wells, add 30 ul sample and mix
    p300s.transfer(
     138, reagents_block['eblt'],
     reagents_block['empty 1'], mix_before=(10, 100))
    p300s.pick_up_tip()
    p300s.transfer(
     138, reagents_block['tbs'], reagents_block['empty 1'],
     mix_after=(10, 100), new_tip='never')
    p300s.distribute(
     20, reagents_block['empty 1'], heat_wells,
     new_tip='never', disposal_volume=disp_vol)
    p300s.drop_tip()
    p300s.transfer(
     30, samples, heat_wells, mix_after=(10, 40), new_tip='always')

    # 55 Celsius 5 minutes
    tc.set_lid_temperature(75)
    tc.close_lid()
    profile = [
            {'temperature': 55, 'hold_time_seconds': 5},
            {'temperature': 10, 'hold_time_seconds': 30}]
    tc.execute_profile(steps=profile, repetitions=1, block_max_volume=50)
    tc.open_lid()
    tc.deactivate_lid()

    # add st2 and mix, transfer to magnetic module, engage magnets, remove sup
    p20s.transfer(10, reagents_block['st2'], heat_wells, new_tip='always')
    for well in heat_wells:
        p300s.pick_up_tip()
        p300s.mix(10, 50, well.bottom())
        p300s.drop_tip()

    p300s.transfer(60, heat_wells, mag_wells, new_tip='always')
    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=engage_time)
    p300s.transfer(60, mag_wells, reagents_res['waste'], new_tip='always')
    mag.disengage()

    # reduce asp and disp rates, add twb, mix, engage magnets, remove sup
    # repeat twice, prepare mix on 3rd rep
    p300s.flow_rate.aspirate = twb_rate
    p300s.flow_rate.dispense = twb_rate
    for rep in range(3):
        if rep == 1:
            ctx.set_rail_lights(False)
            ctx.pause("Please refill the p300 tip box.")
            ctx.set_rail_lights(True)
            p300s.reset_tipracks()
        p300s.transfer(
         100, reagents_res['twb'], mag_wells,
         mix_after=(10, 70), new_tip='always')
        mag.engage()
        if rep == 2:
            p300s.transfer(
             [138, 138], reagents_block['epm'],
             [reagents_block['empty 2'], reagents_block['empty 2']])
            p300s.pick_up_tip()
            p300s.transfer(
             [138, 138], reagents_res['water'],
             [reagents_block['empty 2'].top(), reagents_block[
              'empty 2'].top()], new_tip='never')
            p300s.mix(10, 200, reagents_block['empty 2'].bottom())
            p300s.drop_tip()
        ctx.delay(minutes=engage_time - 1)
        p300s.transfer(100, mag_wells, reagents_res['waste'], new_tip='always')

    # set asp and disp rates to default, add 40 ul of mix, mix after
    p300s.flow_rate.aspirate = 94
    p300s.flow_rate.dispense = 94
    mag.disengage()
    p300s.transfer(
     40, reagents_block['empty 2'], mag_wells,
     mix_after=(10, 30), new_tip='always')

    # transfer to cycler, add index, mix, pcr
    p300s.transfer(45, mag_wells, pcr_wells, new_tip='always')

    ctx.set_rail_lights(False)
    ctx.pause('''Please remove the 96 well plate from the thermocycler
                 and add 10 ul from the index adapter plate to A3-H3, A4-B4.
                 Then return the plate to the thermocycler.''')
    ctx.set_rail_lights(True)

    for well in pcr_wells:
        p300s.pick_up_tip()
        p300s.mix(10, 40, well.bottom())
        p300s.drop_tip()

    # pcr profiles
    profiles = [
     [{'temperature': 72, 'hold_time_seconds': 180}],
     [{'temperature': 98, 'hold_time_seconds': 180}],
     [{'temperature': temp, 'hold_time_seconds': sec} for temp,
      sec in zip([98, 60, 72], [20, 30, 60])]]

    # run pcr
    tc.close_lid()
    tc.set_lid_temperature(105)
    for profile, reps in zip(profiles, [1, 1, 9]):
        tc.execute_profile(
         steps=profile, repetitions=reps, block_max_volume=50)
    tc.set_block_temperature(10)
    tc.open_lid()
    tc.deactivate_lid()

    ctx.set_rail_lights(False)
    ctx.pause('''Part 1 - Tagmentation, Clean Up,
                 Amplify Tagmented DNA steps are complete.''')

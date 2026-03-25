metadata = {
    'protocolName': '''Illumina DNA Prep with Enrichment:
     Part 2 - Clean Up and Pool Libraries, Hybridize and Capture Probes,
     Amplify Enriched Library, Clean Up Enriched Library''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [sample_count, engage_time
     ] = get_values(  # noqa: F821
      'sample_count', 'engage_time')

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
    tc.set_block_temperature(10)
    tc_plate = tc.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    [pcr_wells] = [no_edges(tc_plate)[
     start_index:sample_count + start_index] for start_index in [12]]

    # magnetic module
    mag = ctx.load_module('magnetic module gen2', '6')
    mag_plate = mag.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    mag.disengage()
    [mag_wells, post_pcr_mag_wells, clean_mag_wells, sup_mag_wells,
     final_mag_wells] = [mag_plate.wells()[
      start_index:sample_count + start_index] for start_index in [
      0, 16, 32, 48, 64]]

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
    for reagent, well in zip(['twb', 'water', 'beads', 'waste', 'etoh'],
                             ['A1', 'A2', 'A3', 'A4', 'A5']):
        reagents_res[reagent] = reservoir.wells_by_name()[well]

    # mix, transfer to magnetic module, engage magnets, transfer to new wells
    for well in pcr_wells:
        p300s.pick_up_tip()
        p300s.mix(10, 40, well.bottom())
        p300s.drop_tip()
    p300s.transfer(45, pcr_wells, post_pcr_mag_wells, new_tip='always')
    mag.engage()
    ctx.delay(minutes=engage_time)
    p300s.transfer(45, post_pcr_mag_wells, clean_mag_wells, new_tip='always')
    mag.disengage()

    # mix beads, add 88 ul, add 20 ul water, mix, engage magnets
    p300s.pick_up_tip()
    p300s.mix(10, 200, reagents_res['beads'])
    p300s.transfer(
     88, reagents_res['beads'], [well.top() for well in clean_mag_wells],
     new_tip='never')
    p300s.drop_tip()
    p300s.distribute(
     20, reagents_res['water'], [well.top() for well in clean_mag_wells])
    for well in clean_mag_wells:
        p300s.pick_up_tip()
        p300s.mix(10, 100, well.bottom())
        p300s.drop_tip()
    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=engage_time + 2)

    # mix beads, distribute, transfer sup, apply magnets, remove sup
    p300s.pick_up_tip()
    p300s.mix(10, 200, reagents_res['beads'])
    p300s.distribute(
     20, reagents_res['beads'], [well for well in sup_mag_wells],
     new_tip='never')
    p300s.drop_tip()
    p300s.transfer(
     150, [well for well in clean_mag_wells], [well for well in sup_mag_wells],
     mix_after=(10, 100), new_tip='always')
    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=engage_time + 2)
    p300s.transfer(
     150, [well for well in sup_mag_wells], reagents_res['waste'].top(),
     new_tip='always')

    ctx.set_rail_lights(False)
    ctx.pause('Please refill the tip boxes.')
    ctx.set_rail_lights(True)
    p300s.reset_tipracks()

    # add etoh, 30 sec, remove, repeat
    for rep in range(2):
        p300s.pick_up_tip()
        p300s.transfer(
         100, reagents_res['etoh'], [well.top() for well in sup_mag_wells],
         air_gap=20, new_tip='never')
        p300s.drop_tip()
        ctx.delay(seconds=30)
        p300s.transfer(
         100, [well.top() for well in sup_mag_wells],
         reagents_res['waste'].top(), air_gap=20, new_tip='always')

    # air dry
    ctx.delay(minutes=5)

    # add 17 ul RSB
    p20s.pick_up_tip()
    p20s.transfer(
     17, reagents_block['rsb'], [well.top() for well in sup_mag_wells],
     new_tip='never')
    p20s.drop_tip()

    ctx.pause('''Please remove the plate from the magnetic module, seal and
                 vortex (1800 rpm 2 min). Then, return plate to magnetic module
                 and wait 2 minutes. Spin the plate briefly. Then return plate
                 again to magnetic module and click resume.''')

    ctx.delay(minutes=2)

    # 15 ul to clean mag mod wells, 2.5 ul to A5 on thermocycler module
    p20s.transfer(
     15, [well for well in sup_mag_wells], [well for well in final_mag_wells],
     new_tip='always')
    p20s.transfer(
     2.5, [well for well in sup_mag_wells], tc_plate.wells_by_name()['A5'],
     new_tip='always')
    p20s.pick_up_tip()
    p20s.mix(10, 20, tc_plate.wells_by_name()['A5'])
    p20s.drop_tip()

    ctx.pause('''Please remove plate from magnetic module to perform analysis.
                 Then resume''')

    p300s.transfer(50, reagents_block['nhb2'], tc_plate.wells_by_name()['A5'])
    p20s.transfer(10, reagents_block['enrich'], tc_plate.wells_by_name()['A5'])
    p20s.pick_up_tip()
    p20s.transfer(
     10, reagents_block['ehb2'], tc_plate.wells_by_name()['A5'],
     new_tip='never')
    p20s.drop_tip()
    p300s.pick_up_tip()
    p300s.mix(10, 90, tc_plate.wells_by_name()['A5'])
    p300s.drop_tip()

    tc.close_lid()

    ctx.pause("""Please remove reagents from the 24-well aluminum block
                 and place the block on the temperature module.
                 Allow the block to pre-heat to 62 degrees Celsius. Please
                 remove the thermocycler plate, spin, and place it back
                 on the thermocycler.""")

    temp.set_temperature(62)

    # temperature profiles
    profiles = [
     [{'temperature': 95, 'hold_time_seconds': 300}],
     [{'temperature': temp, 'hold_time_seconds': sec} for temp,
      sec in zip([94 - (num*2) for num in range(16)], [60]*16)],
     [{'temperature': 62, 'hold_time_seconds': 5400}]]

    # cycling
    tc.close_lid()
    tc.set_lid_temperature(105)
    for profile in profiles:
        tc.execute_profile(
         steps=profile, repetitions=1, block_max_volume=70)

    ctx.pause("""Please place 300 ul SMB in A1, 2 mL EEW in B1,
                 empty tubes in A2 and A3 of the temperature module.""")

    tc.open_lid()
    tc.deactivate_lid()

    # 100 ul from cycler A5 to tube on temp mod, mix smb, add smb to tube
    p300s.transfer(
     100, tc_plate.wells_by_name()['A5'], reagents_temp['empty 1'])
    p300s.pick_up_tip()
    p300s.mix(10, 200, reagents_temp['smb'])
    p300s.transfer(
     [125, 125], reagents_temp['smb'], [
      reagents_temp['empty 1'], reagents_temp['empty 1']], new_tip='never')
    p300s.mix(10, 200, reagents_temp['empty 1'])
    ctx.delay(minutes=15)

    ctx.pause("Please place new 96-well plate on the magnetic module.")
    p300s.mix(10, 200, reagents_temp['empty 1'])  # step 90
    p300s.transfer(
     [175, 175], reagents_temp['empty 1'], [
      mag_plate.wells_by_name()['A1'], mag_plate.wells_by_name()['A2']],
     new_tip='never')
    mag.engage()
    ctx.delay(minutes=engage_time)

    for (w1, w2, w3, w4), tube in zip(
     [('A1', 'A2', 'B1', 'B2'), ('B1', 'B2', 'D1', 'D2'),
      ('D1', 'D2', 'E1', 'E2')], ['empty 2', 'empty 3', 'empty 4']):
        # remove sup
        p300s.transfer([175, 175], [
         mag_plate.wells_by_name()[w1], mag_plate.wells_by_name()[w2]],
         reagents_res['waste'], new_tip='never')
        p300s.drop_tip()
        mag.disengage()
        # add eew, mix, 62 degrees 5 min
        p300s.pick_up_tip()
        p300s.transfer(
         100, reagents_temp['eew'],
         [mag_plate.wells_by_name()[w1], mag_plate.wells_by_name()[w2]],
         new_tip='never')
        for well in [w1, w2]:
            p300s.mix(10, 90, mag_plate.wells_by_name()[well])
            p300s.transfer(
             100, mag_plate.wells_by_name()[well], reagents_temp[tube],
             new_tip='never')
        p300s.mix(10, 100, reagents_temp[tube])
        ctx.delay(minutes=5)
        # transfer to magnetic module, apply magnets
        p300s.transfer(
         100, reagents_temp[tube],
         [mag_plate.wells_by_name()[w3], mag_plate.wells_by_name()[w4]],
         new_tip='never')
        mag.engage()
        ctx.delay(minutes=engage_time)

    mag.engage()
    ctx.delay(minutes=engage_time)
    p300s.transfer(
     175, [mag_plate.wells_by_name()['E1'], mag_plate.wells_by_name()['E2']],
     reagents_res['waste'], new_tip='never')
    p300s.drop_tip()
    mag.disengage()
    p300s.transfer(
     100, reagents_temp['eew'],
     [mag_plate.wells_by_name()['E1'], mag_plate.wells_by_name()['E2']],
     mix_after=(10, 90), new_tip='always')
    p300s.pick_up_tip()
    for well in ['E1', 'E2']:
        p300s.mix(10, 90, mag_plate.wells_by_name()[well])
    # remove sup
    p300s.transfer(
     200, [mag_plate.wells_by_name()['E1'], mag_plate.wells_by_name()['E2']],
     reagents_res['waste'], new_tip='never')
    p300s.drop_tip()
    mag.disengage()

    ctx.pause('''Please remove the magnetic module plate, spin briefly,
                 and return the plate to the magnetic module.''')

    mag.engage()
    ctx.delay(minutes=engage_time)
    p20s.pick_up_tip()
    # remove residual supernatant
    p20s.transfer(
     20, [mag_plate.wells_by_name()['E1'], mag_plate.wells_by_name()['E2']],
     reagents_res['waste'], new_tip='never')
    p20s.drop_tip()

    mag.disengage()

    ctx.pause('''Please remove the plate from the magnetic module,
                 add elution to wells E1 and E2, vortex, spin,
                 and return the plate to the magnetic module.''')

    tc.open_lid()

    mag.engage()
    ctx.delay(minutes=engage_time)

    p20s.pick_up_tip()
    p20s.transfer(
     [10, 10],
     [mag_plate.wells_by_name()['E1'], mag_plate.wells_by_name()['E2']],
     tc_plate.wells_by_name()['A6'], new_tip='never')

    ctx.pause('''Please add 4 ul of ET2, 5 ul of EPM and 20 ul PPM
                 to well A6 on thermal cycler.''')

    # set slow aspiration and dispense rates
    p20s.flow_rate.aspirate = 3
    p20s.flow_rate.dispense = 3
    p20s.mix(10, 20, tc_plate.wells_by_name()['A6'])
    p20s.drop_tip()
    p20s.flow_rate.aspirate = 7.56
    p20s.flow_rate.dispense = 7.56

    # temperature profiles
    profiles = [
     [{'temperature': 98, 'hold_time_seconds': 30}],
     [{'temperature': temp, 'hold_time_seconds': sec} for temp,
      sec in zip([98, 60, 72], [10, 30, 30])]]

    # cycling
    tc.close_lid()
    tc.set_lid_temperature(105)
    for profile, reps in zip(profiles, [1, 12]):
        tc.execute_profile(
         steps=profile, repetitions=reps, block_max_volume=50)

    tc.open_lid()
    tc.deactivate_lid()

    p300s.transfer(
     50, tc_plate.wells_by_name()['A6'], mag_plate.wells_by_name()['A3'])
    p300s.pick_up_tip()
    p300s.mix(10, 200, reagents_res['beads'])
    p300s.transfer(
     45, reagents_res['beads'], mag_plate.wells_by_name()['A3'],
     mix_after=(10, 70), new_tip='never')
    p300s.drop_tip()
    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=engage_time)

    for rep in range(3):
        p300s.transfer(
         100, mag_plate.wells_by_name()['A3'], reagents_res['waste'].top(),
         air_gap=20)
        if rep != 2:
            p300s.transfer(
             100, reagents_res['etoh'], mag_plate.wells_by_name()['A3'],
             air_gap=20)
            ctx.delay(seconds=30)

    # air dry
    ctx.delay(minutes=5)
    mag.disengage()

    ctx.pause('''Please remove the plate from the magnetic module,
                 add 32 ul RSB, wait 5 min, vortex, spin.
                 Then place the plate back on the magnetic module.''')

    mag.engage()
    ctx.delay(minutes=engage_time)

    p300s.transfer(
     30, mag_plate.wells_by_name()['A3'], mag_plate.wells_by_name()['A12'])

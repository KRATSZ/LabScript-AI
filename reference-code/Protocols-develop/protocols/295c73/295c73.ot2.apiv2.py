import math

metadata = {
    'protocolName': 'swiftbiosci.com accel-amplicon-plus-egfr-pathway-panel',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, mm_volume
     ] = get_values(  # noqa: F821
      'sample_count', 'mm_volume')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if sample_count < 1 or sample_count > 24:
        raise Exception('Invalid number of DNA samples (must be 1-24).')

    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    pause_attention("""PCR set up: Pre-cool temp module to 4 degrees, pre-heat
    cycler block (98) and lid (105) with OT app settings, sample plate slot 1
    with up to 24 samples (in column order A1-H1), master mix tube A1 of block
    on slot 5.""")

    # tips, p20 single, p300 multi
    tips20 = [ctx.load_labware("opentrons_96_filtertiprack_20ul", '3')]
    p20s = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)
    tips300 = [ctx.load_labware("opentrons_96_filtertiprack_200ul", '4')]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)
    tip_max = 150
    named_tips = {}
    for name, well in zip([
     'etoh_tips', 'sup_tips', 'index_rxn_tips'], ['A1', 'A2', 'A5']):
        named_tips[name] = tips300[0][well]

    # helper functions
    def no_edges(plate):
        return [well for column in [
         column for column in plate.columns()[1:11]] for well in column[1:7]]

    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    def etoh_settings():
        p300m.flow_rate.blow_out = 300

    def default_settings():
        p300m.flow_rate.blow_out = 94

    def rep_max_transfer(
     remaining, source, dest, tip_max_vol=tip_max, air=0, blow=0,
     touch=False):
        vol = tip_max_vol - air
        while remaining > vol:
            p300m.aspirate(vol, source)
            if air > 0:
                p300m.air_gap(air)
            p300m.dispense(tip_max_vol, dest)
            if blow > 0:
                for rep in range(blow):
                    if rep > 0:
                        p300m.aspirate(tip_max, dest)
                    ctx.delay(seconds=1)
                    p300m.blow_out(dest)
            if touch is True:
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
            remaining -= vol
        p300m.aspirate(remaining, source)
        if air > 0:
            p300m.air_gap(air)
        p300m.dispense(remaining + air, dest)
        if blow > 0:
            for rep in range(blow):
                if rep > 0:
                    p300m.aspirate(tip_max, dest)
                ctx.delay(seconds=1)
                p300m.blow_out(dest)
        if touch is True:
            p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)

    def reuse_tips(which_tips):
        p300m.reset_tipracks()
        p300m.starting_tip = named_tips[which_tips]

    # temp mod 4 deg, 96-well block, 96-well plate, DNA samples and master mix
    temp = ctx.load_module('Temperature Module', '6')
    output_plate = temp_plate = temp.load_labware(
     'opentrons_96_aluminumblock_nest_wellplate_100ul')
    temp.set_temperature(4)
    pcr_setups = no_edges(temp_plate)[:sample_count]

    # pre-chilled aluminum block containing master mix tube in well A1
    block = ctx.load_labware(
     'opentrons_24_aluminumblock_nest_2ml_snapcap', '5')
    mm = beads = index_rxn_mx = peg_nacl = block.wells_by_name()['A1']

    # thermocycler pre-heated block (98) and lid (105)
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    tc_plate = tc.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tc.set_lid_temperature(105)
    tc.set_block_temperature(98)

    # magnetic module disengaged
    mag = ctx.load_module('magnetic module gen2', 9)
    mag_plate = mag.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    mag.disengage()
    mag_samps = mag_plate.wells()[:sample_count]
    mag_samps_indx = mag_plate.wells()[32:sample_count + 32]

    # 96-well plate slot 1 (sample plate, later index plate)
    temporary_plate = ctx.load_labware(
     "nest_96_wellplate_100ul_pcr_full_skirt", '1')
    initial_dna = indexes = temporary_plate.wells()[:sample_count]

    # reservoir for etoh, waste, te
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", '2')
    [etoh, waste, post_pcr_te] = [reservoir.wells_by_name()[
     well] for well in ['A1', 'A3', 'A5']]

    # PCR setup: p300m "single channel" distribute master mix to 4 degree wells
    p300m.pick_up_tip(tips300[0]['H9'])
    p300m.well_bottom_clearance.aspirate = 8
    p300m.aspirate(10, mm, rate=0.25)
    ctx.delay(seconds=1)
    for chunk in create_chunks(pcr_setups, 6):
        p300m.aspirate(len(chunk)*mm_volume, mm, rate=0.25)
        ctx.delay(seconds=3)
        slow_tip_withdrawal(p300m, mm)
        if p300m.well_bottom_clearance.aspirate >= 3:
            p300m.well_bottom_clearance.aspirate -= 2
        for well in chunk:
            p300m.dispense(20, well.bottom(2), rate=0.25)
            ctx.delay(seconds=2)
            slow_tip_withdrawal(p300m, well)
    p300m.drop_tip()
    p300m.well_bottom_clearance.aspirate = 1

    # mix DNA with master mix at 4 degrees
    for dna, rxn in zip(initial_dna, pcr_setups):
        p20s.pick_up_tip()
        p20s.aspirate(10, dna)
        p20s.dispense(8, rxn)
        for rep in range(5):
            p20s.aspirate(15, rxn.bottom(2), rate=0.5)
            ctx.delay(seconds=1)
            p20s.dispense(15, rxn.bottom(2), rate=0.5)
            ctx.delay(seconds=1)
        slow_tip_withdrawal(p20s, rxn, to_center=True)
        p20s.dispense(2, rxn.center())
        ctx.delay(seconds=1)
        p20s.blow_out()
        p20s.touch_tip(rxn, radius=0.75, v_offset=-2, speed=10.0)
        p20s.drop_tip()

    pause_attention("""Set up complete. Please transfer plate from temperature
    module to pre-heated cycler and resume to run PCR.""")

    # cycling profiles
    profiles = [[{
     'temperature': temp, 'hold_time_seconds': sec
     } for temp, sec in zip([98], [30])], [{
      'temperature': temp, 'hold_time_seconds': sec
      } for temp, sec in zip([98, 63, 65], [10, 300, 60])], [{
       'temperature': temp, 'hold_time_seconds': sec
       } for temp, sec in zip([98, 64], [10, 60])], [{
        'temperature': temp, 'hold_time_seconds': sec
        } for temp, sec in zip([65], [60])]]

    # run pcr
    tc.close_lid()
    for profile, reps in zip(profiles, [1, 4, 23, 1]):
        tc.execute_profile(
         steps=profile, repetitions=reps, block_max_volume=30)
    tc.set_block_temperature(4, hold_time_seconds=30)
    tc.deactivate_block()
    tc.deactivate_lid()
    tc.open_lid()

    # post pcr clean up
    pause_attention(
      """Post-PCR clean up: place beads (A1 of block in slot 5) and ethanol
      (A1 of reservoir in slot 2) on OT-2 deck.""")

    # one-tip dispense beads to columns of mag plate
    num_cols = math.ceil(sample_count / 8)
    p300m.pick_up_tip(tips300[0]['G9'])
    p300m.aspirate(10, beads, rate=0.25)
    ctx.delay(seconds=1)
    for rep in range(10):
        p300m.aspirate(100, beads.bottom(2), rate=0.25)
        ctx.delay(seconds=2)
        p300m.dispense(100, beads.bottom(2), rate=0.25)
        ctx.delay(seconds=2)
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p300m.aspirate(144, beads, rate=0.25)
        ctx.delay(seconds=5)
        slow_tip_withdrawal(p300m, beads)
        for well in column[:4]:
            p300m.dispense(36, well.bottom(2), rate=0.25)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(p300m, well)
        if index == len(mag_plate.columns()[:num_cols]) - 1:
            p300m.aspirate(136, beads, rate=0.25)
        else:
            p300m.aspirate(144, beads, rate=0.25)
        ctx.delay(seconds=5)
        slow_tip_withdrawal(p300m, beads)
        for well in column[4:]:
            p300m.dispense(36, well.bottom(2), rate=0.25)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(p300m, well)
    p300m.drop_tip()

    # post-PCR sample to mag mod (reformat columns of 6 to columns of 8), mix
    for tip, source, dest in zip(['C10', 'A10', 'E11', 'A11', 'G12', 'A12'],
                                 ['B2', 'B3', 'D3', 'B4', 'F4', 'B5'],
                                 ['A1', 'G1', 'A2', 'E2', 'A3', 'C3']):
        p300m.pick_up_tip(tips300[0][tip])
        p300m.aspirate(30, tc_plate.wells_by_name()[source], rate=0.5)
        ctx.delay(seconds=1)
        p300m.dispense(25, mag_plate.wells_by_name()[dest], rate=0.5)
        ctx.delay(seconds=1)
        for rep in range(10):
            p300m.aspirate(30, mag_plate.wells_by_name()[dest], rate=0.25)
            ctx.delay(seconds=2)
            if rep == 9:
                p300m.dispense(35, mag_plate.wells_by_name()[dest], rate=0.25)
            else:
                p300m.dispense(30, mag_plate.wells_by_name()[dest], rate=0.25)
            ctx.delay(seconds=2)
        p300m.drop_tip()

    # set thermocycler block temperature to 37 for indexing step
    tc.set_block_temperature(37)

    # magnets engaged, let stand 5 min
    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=5)

    # remove sup
    reuse_tips('sup_tips')
    for column in mag_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        p300m.aspirate(60, column[0].bottom(2), rate=0.25)
        ctx.delay(seconds=2)
        p300m.dispense(60, waste.top())
        ctx.delay(seconds=1)
        p300m.return_tip()

    # wash 2x 180 ul 80% etoh, reuse tips
    etoh_settings()
    p300m.reset_tipracks()
    p300m.pick_up_tip()
    for repeat in range(2):
        if repeat == 1:
            reuse_tips('etoh_tips')
            p300m.pick_up_tip()
        # prewet tips with ethanol
        for rep in range(2):
            p300m.aspirate(100, etoh.bottom(2))
            p300m.dispense(100, etoh.bottom(2))
        for column in mag_plate.columns()[:num_cols]:
            rep_max_transfer(
             180, etoh.bottom(2), column[0].top(), air=15, blow=2)
        p300m.return_tip()
        reuse_tips('sup_tips')
        for column in mag_plate.columns()[:num_cols]:
            p300m.pick_up_tip()
            rep_max_transfer(
             180, column[0].bottom(2), waste.top(), air=15, blow=2)
            p300m.return_tip()

    pause_attention("""Indexing: Place index plate (slot 1) and
    index rxn mx tube (A1 chilled block on slot 5) on OT-2 deck.""")

    # aspirate last traces of etoh
    reuse_tips('sup_tips')
    for column in mag_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        rep_max_transfer(30, column[0].bottom(2), waste.top(), air=15, blow=2)
        p300m.return_tip()
    default_settings()
    ctx.comment("Beads drying for 3 minutes.")
    ctx.delay(minutes=3)
    mag.disengage()

    # indexing post-pcr beads, one-tip pickup, rxn mix to bead pellets
    p300m.pick_up_tip(tips300[0]['F9'])
    for chunk in create_chunks(mag_samps, 3):
        p300m.aspirate(105, index_rxn_mx.bottom(2))
        for well in chunk:
            p300m.dispense(35, well.top(-2))
    p300m.drop_tip()

    # indices to bead pellets, mix, transfer beads to 37 degree cycler plate
    p20s.transfer(
      15, [well.bottom(2) for well in indexes[:sample_count]],
      [mag_samp.bottom(2) for mag_samp in mag_samps], new_tip='always')

    p300m.transfer(
      55, [mag_col[0].bottom(2) for mag_col in mag_plate.columns()[:num_cols]],
      [indx_col[0].bottom(2) for indx_col in tc_plate.columns()[6:num_cols+6]],
      mix_before=(5, 27), new_tip='always', trash=False)

    # define thermocycler profile for indexing
    profile5 = [{'temperature': 37, 'hold_time_minutes': 20}]
    tc.close_lid()
    tc.execute_profile(steps=profile5, repetitions=1)
    tc.deactivate_block()

    pause_attention("""Second clean up: Place PEG NaCl (A1 of block in slot 5)
    and TE (A5 of reservoir in slot 2) on OT-2 deck. Replenish ethanol
    (A1 of reservoir in slot 2).""")

    # post-indexing clean up, PEG NaCl to fresh mag plate wells, 1-tip pickup
    p300m.pick_up_tip(tips300[0]['E9'])
    p300m.well_bottom_clearance.aspirate = 8
    p300m.aspirate(10, peg_nacl, rate=0.25)
    ctx.delay(seconds=1)
    for chunk in create_chunks(mag_samps_indx, 3):
        p300m.aspirate(len(chunk)*42.5, peg_nacl, rate=0.25)
        ctx.delay(seconds=5)
        slow_tip_withdrawal(p300m, peg_nacl)
        if p300m.well_bottom_clearance.aspirate >= 2:
            p300m.well_bottom_clearance.aspirate -= 1
        for well in chunk:
            p300m.dispense(42.5, well.bottom(2), rate=0.25)
            ctx.delay(seconds=2)
            slow_tip_withdrawal(p300m, well)
    p300m.drop_tip()
    p300m.well_bottom_clearance.aspirate = 1

    # indexed sample to mag plate, mix with PEG NaCl
    tc.open_lid()
    reuse_tips('index_rxn_tips')
    p300m.transfer(50, [
     indx_col[0].bottom(2) for indx_col in tc_plate.columns()[6:num_cols+6]],
      [mag_col[0].bottom(2) for mag_col in mag_plate.columns()[4:num_cols+4]],
      mix_after=(4, 45), new_tip='always', trash=False)

    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=5)

    # remove supernatant
    reuse_tips('index_rxn_tips')
    for column in mag_plate.columns()[4:num_cols+4]:
        p300m.pick_up_tip()
        p300m.aspirate(92, column[0].bottom(2), rate=0.25)
        ctx.delay(seconds=2)
        slow_tip_withdrawal(p300m, column[0])
        p300m.dispense(92, waste.top(), rate=0.25)
        ctx.delay(seconds=2)
        p300m.blow_out()
        p300m.return_tip()

    # post_indexing wash 2x 180 ul 80% etoh
    etoh_settings()
    reuse_tips('etoh_tips')
    p300m.pick_up_tip()
    for repeat in range(2):
        if repeat == 1:
            reuse_tips('etoh_tips')
            p300m.pick_up_tip()
        # prewet tips with ethanol
        for rep in range(2):
            p300m.aspirate(100, etoh.bottom(2))
            p300m.dispense(100, etoh.bottom(2))
        for column in mag_plate.columns()[4:num_cols+4]:
            rep_max_transfer(
             180, etoh.bottom(2), column[0].top(), air=15, blow=2)
        p300m.return_tip()
        reuse_tips('index_rxn_tips')
        for column in mag_plate.columns()[4:num_cols+4]:
            p300m.pick_up_tip()
            rep_max_transfer(
             180, column[0].bottom(2), waste.top(), air=15, blow=2)
            p300m.return_tip()

    pause_attention("""Place output plate on temperature module.""")

    # aspirate last traces of etoh
    reuse_tips('index_rxn_tips')
    for column in mag_plate.columns()[4:num_cols+4]:
        p300m.pick_up_tip()
        rep_max_transfer(30, column[0].bottom(2), waste.top(), air=15, blow=2)
        p300m.return_tip()
    default_settings()
    ctx.comment("Beads drying for 3 minutes.")
    ctx.delay(minutes=3)
    mag.disengage()

    # elute, mix, transfer eluate to output plate and hold at 4 degrees C
    p20s.transfer(20, post_pcr_te, [
     well.bottom() for well in mag_plate.wells()[32:sample_count+32]],
     mix_after=(4, 10), new_tip='always')
    ctx.delay(minutes=2)
    mag.engage()
    ctx.delay(minutes=5)
    p20s.transfer(20, [well.bottom() for well in mag_plate.wells()[
     32:sample_count+32]], [well.bottom() for well in output_plate.wells()[
      :sample_count]], new_tip='always')

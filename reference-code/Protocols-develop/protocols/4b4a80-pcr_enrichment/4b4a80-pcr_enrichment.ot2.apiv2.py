import math

metadata = {
    'protocolName': '''NEBNext Ultra II FS DNA Library Prep Kit for Illumina
    E6177S/L (for 1-24 DNA samples): Step 5: PCR Enrichment''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [pcr_labware, pcr_cycles, sample_count, post_size_selection_volume,
     q5_volume, q5_well, i5_volume, i5_well, i7_volume, i7_well,
     empty_vial_well, spri_beads_volume, spri_beads_well, etoh_volume,
     etoh_well, te_volume, te_well
     ] = get_values(  # noqa: F821
      'pcr_labware', 'pcr_cycles', 'sample_count',
      'post_size_selection_volume', 'q5_volume', 'q5_well', 'i5_volume',
      'i5_well', 'i7_volume', 'i7_well', 'empty_vial_well',
      'spri_beads_volume', 'spri_beads_well', 'etoh_volume', 'etoh_well',
      'te_volume', 'te_well')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if sample_count < 1 or sample_count > 24:
        raise Exception('Invalid number of samples (must be 1-24).')

    # turn off rail lights to bring the pause to the user's attention
    ctx.set_rail_lights(False)
    ctx.pause(f"""Please pre-cool the
    temperature module to 4 degrees via settings in the Opentrons app prior to
    running this protocol. Please transfer Q5 master mix to well {q5_well}, i5
    to well {i5_well}, i7 to well {i7_well} of the 4 degree temperature module
    on the OT-2 deck.""")
    ctx.set_rail_lights(True)

    # setup p300 single channel, p300 multi channel, tips
    tips300s = [ctx.load_labware("opentrons_96_tiprack_300ul", '3')]
    tips300m = [
     ctx.load_labware("opentrons_96_tiprack_300ul", '6'),
     ctx.load_labware("opentrons_96_tiprack_300ul", '9')]
    [p300s, p300m] = [
     ctx.load_instrument(pipette, side, tip_racks=tips)
     for pipette, side, tips in zip(
      ["p300_single_gen2", "p300_multi_gen2"],
      ['left', 'right'], [tips300s, tips300m])]

    # setup temperature module at 4 degrees for Q5 master mix, i5, i7
    temp = ctx.load_module('Temperature Module', '2')
    temp_reagents = temp.load_labware(
        'opentrons_24_aluminumblock_nest_0.5ml_screwcap',
        'Opentrons 24-Well Aluminum Block')
    temp.set_temperature(4)

    # setup thermocycler
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    tc_plate = tc.load_labware(pcr_labware)

    # setup magnetic module (magnets disengaged)
    mag = ctx.load_module('magnetic module gen2', '4')
    mag_plate = mag.load_labware(pcr_labware)
    mag.disengage()

    # sample locations (first three columns of thermocycler plate)
    post_size_selection_sample = tc_plate.wells()[:sample_count]

    # reagent setup: Q5 mastermix, i5, i7, etoh, te
    q5, i5, i7, mixture = [
     temp_reagents.wells_by_name()[well] for well in [
      q5_well, i5_well, i7_well, empty_vial_well]]

    p300s.pick_up_tip()
    p300s.mix(10, 250, q5.bottom(1))
    p300s.drop_tip()

    for volume, source in zip([q5_volume, i5_volume, i7_volume], [q5, i5, i7]):
        p300s.transfer(
         (sample_count + 1)*volume, source, mixture, new_tip='once')

    p300s.pick_up_tip()
    p300s.mix(10, (q5_volume*sample_count) / 2, mixture)
    p300s.drop_tip()

    reservoir = ctx.load_labware("nest_12_reservoir_15ml", '5')
    etoh, te = [
     reservoir.wells_by_name()[well] for well in [etoh_well, te_well]]

    # add q5 mixture to post size selection samples and mix
    mixture_volume = q5_volume + i5_volume + i7_volume
    p300s.transfer(
     mixture_volume, mixture, post_size_selection_sample,
     mix_after=(10, (post_size_selection_volume + mixture_volume)*0.8),
     new_tip="always")

    # define PCR enrichment profiles
    profile1 = [{'temperature': 98, 'hold_time_seconds': 30}]
    profile2 = [
        {'temperature': 98, 'hold_time_seconds': 10},
        {'temperature': 65, 'hold_time_seconds': 75}]
    profile3 = [
        {'temperature': 65, 'hold_time_minutes': 5}]

    # run pcr
    tc.set_lid_temperature(105)
    rxn_volume = post_size_selection_volume + mixture_volume
    tc.execute_profile(
      steps=profile1, repetitions=1, block_max_volume=rxn_volume)
    tc.execute_profile(
      steps=profile2, repetitions=pcr_cycles, block_max_volume=rxn_volume)
    tc.execute_profile(
      steps=profile3, repetitions=1, block_max_volume=rxn_volume)
    tc.set_block_temperature(4)
    tc.set_lid_temperature(22)
    tc.open_lid()

    # reagent set up spri beads
    spri_beads = temp_reagents.wells_by_name()[spri_beads_well]

    ctx.set_rail_lights(False)
    ctx.pause(f"""PCR enrichment steps are finished. Please remove the plate
    from the thermocycler, spin, and place the plate on the magnetic module.
    Please place vortexed SPRI beads in well {spri_beads_well} of the
    temperature module. Please place freshly prepared 80% ethanol in well
    {etoh_well} and 0.1X TE in well {te_well} of the reagent reservoir.""")
    ctx.set_rail_lights(True)

    # add SPRI beads to post pcr enrichment samples on the magnetic module
    post_pcr_sample = mag_plate.wells()[:sample_count]
    num_cols = math.ceil(sample_count / 8)
    post_pcr_sample_m = mag_plate.rows()[0][:num_cols]
    p300s.transfer(
     spri_beads_volume, spri_beads, post_pcr_sample,
     mix_before=(4, 250), mix_after=(4, (rxn_volume + spri_beads_volume) / 2),
     new_tip='always')

    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=5)

    # remove supernatant to trash
    p300m.transfer(
     rxn_volume + spri_beads_volume, post_pcr_sample_m,
     ctx.fixed_trash['A1'], new_tip='always')

    # wash beads 2X, adjust gantry speed, flow_rate, air_gaps for ethanol
    p300m.default_speed = 200
    p300m.flow_rate.aspirate = 75
    p300m.flow_rate.dispense = 50
    for rep in range(2):
        p300m.pick_up_tip()
        p300m.transfer(
         etoh_volume, etoh, [well.top() for well in post_pcr_sample_m],
         air_gap=20, new_tip='never', trash=False)
        p300m.return_tip()
        ctx.delay(seconds=30)
        p300m.transfer(
         etoh_volume, post_pcr_sample_m, ctx.fixed_trash['A1'],
         air_gap=20, new_tip='always')

    # aspirate last traces of etoh
    p300m.transfer(
     50, [well.bottom(1) for well in post_pcr_sample_m],
     ctx.fixed_trash['A1'], air_gap=5, new_tip='always')

    # reset to default gantry speed, aspirate and dispense flow rates
    p300m.default_speed = 400
    p300m.flow_rate.aspirate = 94
    p300m.flow_rate.dispense = 94

    ctx.delay(
     seconds=90, msg="letting bead pellet air dry for 1 minute 30 seconds")

    # elute
    mag.disengage()
    p300m.transfer(
     te_volume, te, post_pcr_sample_m, mix_after=(3, te_volume / 2),
     new_tip='always')
    ctx.delay(minutes=7)
    mag.engage()
    ctx.delay(minutes=5)

    # set up fresh 96-well plate for eluate
    eluate_plate = ctx.load_labware(pcr_labware, '1')
    eluted_samples_m = eluate_plate.rows()[0][:num_cols]

    # transfer eluate to eluate plate
    p300m.transfer(
     te_volume, post_pcr_sample_m, eluted_samples_m, new_tip='always')

    ctx.comment("PCR enrichment step is complete")
    ctx.set_rail_lights(False)

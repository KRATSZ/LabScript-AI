import math

metadata = {
    'protocolName': '''NEBNext Ultra II FS DNA Library Prep Kit for Illumina
    E6177S/L (for 1-24 DNA samples): Step 4: Size Selection''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [pcr_labware, sample_count, post_user_sample_volume, water_volume,
     water_well, spri_beads_right_volume, spri_beads_left_volume,
     spri_beads_well, etoh_volume, etoh_well, te_volume, te_well, eluate_volume
     ] = get_values(  # noqa: F821
      'pcr_labware', 'sample_count', 'post_user_sample_volume', 'water_volume',
      'water_well', 'spri_beads_right_volume', 'spri_beads_left_volume',
      'spri_beads_well', 'etoh_volume', 'etoh_well', 'te_volume', 'te_well',
      'eluate_volume')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if sample_count < 1 or sample_count > 24:
        raise Exception('Invalid number of samples (must be 1-24).')

    # turn off rail lights to bring the pause to the user's attention
    ctx.set_rail_lights(False)
    ctx.pause(f"""Please pre-cool the
    temperature module to 4 degrees via settings in the Opentrons app prior to
    running this protocol. Please transfer vortexed SPRI beads to well
    {spri_beads_well} of the 4 degree temperature module on the OT-2 deck.
    Please transfer water to well {water_well}, freshly prepared 80% ethanol to
    well {etoh_well}, and 0.1X TE to well {te_well} of the reagent reservoir on
    the OT-2 deck.""")
    ctx.set_rail_lights(True)

    # setup p20 single channel, p300 multi channel, tips
    tips20 = [ctx.load_labware("opentrons_96_filtertiprack_20ul", '3')]
    tips300 = [
     ctx.load_labware("opentrons_96_tiprack_300ul", '6'),
     ctx.load_labware("opentrons_96_tiprack_300ul", '9')]
    p20 = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)
    p300 = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # setup temperature module at 4 degrees for SPRI beads
    temp = ctx.load_module('Temperature Module', '2')
    temp_reagents = temp.load_labware(
        'opentrons_24_aluminumblock_nest_0.5ml_screwcap',
        'Opentrons 24-Well Aluminum Block')
    temp.set_temperature(4)

    # setup magnetic module with 96-well plate containing post user samples
    mag = ctx.load_module('magnetic module gen2', '4')
    mag_plate = mag.load_labware(pcr_labware)
    mag.disengage()

    # sample locations (first three columns of magnetic module plate)
    post_user_sample = mag_plate.wells()[:sample_count]
    num_cols = math.ceil(sample_count / 8)
    post_user_sample_m = mag_plate.rows()[0][:num_cols]

    # reagent setup: SPRI beads, water, etoh, te
    spri_beads = temp_reagents.wells_by_name()[spri_beads_well]
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", '5')
    water, etoh, te = [
     reservoir.wells_by_name()[well] for well in [
      water_well, etoh_well, te_well]]

    # add water to samples and mix
    p300.transfer(
     water_volume, water, post_user_sample_m,
     mix_after=(4, (post_user_sample_volume + water_volume) / 2),
     new_tip="always")

    # add SPRI beads to samples for 0.2X right-side selection and mix
    p20.transfer(
     spri_beads_right_volume, spri_beads, post_user_sample,
     mix_before=(6, 15), mix_after=(6, 15), new_tip='always')

    ctx.delay(minutes=5)
    mag.engage()
    ctx.delay(minutes=5)

    # 96-well plate to contain right-side sups, remove sups to this plate
    size_sel_plate = ctx.load_labware(pcr_labware, '7')
    right_sup_sample_m = size_sel_plate.rows()[0][:num_cols]

    p300.transfer(
     post_user_sample_volume + water_volume + spri_beads_right_volume,
     post_user_sample_m, right_sup_sample_m, new_tip='always')
    mag.disengage()

    # remove bead pellets, place right-side supernatants on magnetic module
    ctx.set_rail_lights(False)
    ctx.pause("""Please remove the plate (containing right-side selection bead
    pellets) from the magnetic module. Please put the size selection plate
    (containing right-side selection supernatants) on the magnetic module.""")
    ctx.set_rail_lights(True)

    # add 2nd beads to sups for 0.375X left-side selection, 2nd sup to trash
    p20.transfer(
     spri_beads_left_volume, spri_beads, post_user_sample,
     mix_before=(6, 15), mix_after=(6, 15), new_tip='always')
    ctx.delay(minutes=7)
    mag.engage()
    ctx.delay(minutes=5)
    p300.transfer(
     post_user_sample_volume + water_volume + spri_beads_right_volume,
     post_user_sample_m, ctx.fixed_trash['A1'], new_tip='always')

    # wash beads 2X, adjust gantry speed, flow_rate, air_gaps for ethanol
    p300.default_speed = 200
    p300.flow_rate.aspirate = 75
    p300.flow_rate.dispense = 50
    for rep in range(2):
        p300.pick_up_tip()
        p300.transfer(
         etoh_volume, etoh, [well.top() for well in post_user_sample_m],
         air_gap=15, new_tip='never', trash=False)
        p300.return_tip()
        ctx.delay(seconds=30)
        p300.transfer(
         etoh_volume, post_user_sample_m, ctx.fixed_trash['A1'],
         air_gap=15, new_tip='always')

    # aspirate last traces of etoh
    p300.transfer(
     50, [well.bottom(1) for well in post_user_sample_m],
     ctx.fixed_trash['A1'], air_gap=5, new_tip='always')

    # reset to default gantry speed, aspirate and dispense flow rates
    p300.default_speed = 400
    p300.flow_rate.aspirate = 94
    p300.flow_rate.dispense = 94

    ctx.delay(
     seconds=90, msg="letting bead pellet air dry for 1 minute 30 seconds")

    # elute
    mag.disengage()
    p20.transfer(
     te_volume, te, post_user_sample,
     mix_after=(3, te_volume / 2), new_tip='always')
    ctx.delay(minutes=7)
    mag.engage()
    ctx.delay(minutes=5)

    # set up fresh 96-well plate for eluate
    eluate_plate = ctx.load_labware(pcr_labware, '1')
    eluted_samples = eluate_plate.wells()[:sample_count]

    # transfer eluate to eluate plate
    p20.transfer(
     eluate_volume, post_user_sample, eluted_samples, new_tip='always')

    ctx.comment("Size selection step is complete")
    ctx.set_rail_lights(False)

metadata = {
    'protocolName': '''NEBNext Ultra II FS DNA Library Prep Kit for Illumina
                    E6177S/L (for 1-24 DNA samples): Step 2: Fragmentation''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [pcr_labware, sample_count, fragmentation_minutes, sample_volume,
     rxn_bf_volume, rxn_bf_well, enz_mx_volume, enz_mx_well, empty_vial_well
     ] = get_values(  # noqa: F821
      'pcr_labware', 'sample_count', 'fragmentation_minutes', 'sample_volume',
      'rxn_bf_volume', 'rxn_bf_well', 'enz_mx_volume', 'enz_mx_well',
      'empty_vial_well')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if sample_count < 1 or sample_count > 24:
        raise Exception('Invalid number of DNA samples (must be 1-24).')

    # turn off rail lights to bring the pause to the user's attention
    ctx.set_rail_lights(False)
    ctx.pause(f"""Please pre-cool the
    temperature module to 4 degrees via settings in the Opentrons app prior to
    running this protocol. Please add reaction buffer to well {rxn_bf_well},
    enzyme mix to well {enz_mx_well}, and an empty vial to well
    {empty_vial_well} of the 4 degree temperature module on the OT-2 deck.""")
    ctx.set_rail_lights(True)

    # setup p20 single channel, p300 single channel, tips
    tips20 = [ctx.load_labware("opentrons_96_filtertiprack_20ul", '6')]
    tips300 = [ctx.load_labware("opentrons_96_tiprack_300ul", '3')]
    p20 = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)
    p300 = ctx.load_instrument(
        "p300_single_gen2", 'right', tip_racks=tips300)

    # setup temperature module at 4 degrees for reaction buffer and enzyme mix
    temp = ctx.load_module('Temperature Module', '2')
    temp_reagents = temp.load_labware(
        'opentrons_24_aluminumblock_nest_0.5ml_screwcap',
        'Opentrons 24-Well Aluminum Block')
    temp.set_temperature(4)

    # setup cycler for rxn buffer and enzyme mix addition to initial samples
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    tc_plate = tc.load_labware(pcr_labware)

    # DNA sample locations in first three columns of thermocycler plate
    initial_sample = tc_plate.wells()[:sample_count]

    # reagent setup: combine reaction buffer and enzyme mix
    mixture_volume = rxn_bf_volume + enz_mx_volume
    rxn_buffer, enz_mx, mixture = [
     temp_reagents.wells_by_name()[well] for well in [
      rxn_bf_well, enz_mx_well, empty_vial_well]]
    p300.transfer((sample_count + 1)*rxn_bf_volume, rxn_buffer, mixture)
    p300.transfer(
     (sample_count + 1)*enz_mx_volume, enz_mx, mixture,
     mix_after=(4, (mixture_volume * sample_count) / 2))

    # add mixture (rxn buffer + enzyme mixture) to initial DNA samples and mix
    p20.transfer(
     mixture_volume, mixture, initial_sample,
     mix_after=(3, (mixture_volume + sample_volume) / 2), new_tip="always")

    # define fragmentation protocol profiles
    profiles = [
     [{'temperature': 37, 'hold_time_minutes': fragmentation_minutes}],
     [{'temperature': 65, 'hold_time_minutes': 30}]]

    # run fragmentation protocol
    tc.close_lid()
    tc.set_lid_temperature(75)

    for profile in profiles:
        tc.execute_profile(
         steps=profile,
         repetitions=1, block_max_volume=sample_volume + mixture_volume)

    tc.set_block_temperature(4)
    tc.set_lid_temperature(22)
    tc.open_lid()

    ctx.comment("Fragmentation step is complete")
    ctx.set_rail_lights(False)

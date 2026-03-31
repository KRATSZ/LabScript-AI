metadata = {
    'protocolName': 'Reformat 96 Well Plates to 384 Well Plate for qPCR',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [p20_mount, tip_type, temperature, plate1_samples, plate2_samples,
        plate3_samples, plate4_samples, mm_vol, mm_res_vol,
        sample_vol, sample_air_gap,
        aspiration_height] = get_values(  # noqa: F821
        "p20_mount", "tip_type", "temperature", "plate1_samples",
        "plate2_samples", "plate3_samples", "plate4_samples", "mm_vol",
        "mm_res_vol", "sample_vol", "sample_air_gap", "aspiration_height")

    # Load Labware
    pcr_plate = ctx.load_labware(
        'appliedbiosystems_microamp_optical_384_wellplate_30ul', 1,
        '384 Well PCR Plate')
    sample_plates = [ctx.load_labware('kingfisher_96_deepwell_plate_2ml', slot,
                     f'Plate {idx}') for slot, idx in zip([5, 6, 2, 3],
                     [1, 2, 3, 4])]
    tipracks = [ctx.load_labware(tip_type, slot) for slot in range(7, 11)]
    temp_mod = ctx.load_module('temperature module', '4')
    tuberack = temp_mod.load_labware(
                'opentrons_24_aluminumblock_nest_1.5ml_snapcap')

    # Load Pipette
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tipracks)

    mm_volumes = dict.fromkeys(tuberack.wells(), 0)

    def mm_tracker(vol):
        '''mm_tracker() will track how much mastermix
        was used up per tube. If the volume of
        a given well is greater than mm_res_vol
        it will remove it from the dictionary and iterate
        to the next tube which will act as the reservoir.'''
        well = next(iter(mm_volumes))
        if mm_volumes[well] >= mm_res_vol:
            del mm_volumes[well]
            well = next(iter(mm_volumes))
        mm_volumes[well] = mm_volumes[well] + vol
        ctx.comment(f'''{int(mm_volumes[well])} uL of master mix
                    used from {well}''')
        return well

    # Wells by quadrant in 384 well plate
    quad1 = [well for i in range(12) for well in
             pcr_plate.columns()[i][:8]][:plate1_samples]
    quad1 = quad1 + pcr_plate.columns()[11][6:8]
    quad2 = [well for i in range(12, 24) for well in
             pcr_plate.columns()[i][:8]][:plate2_samples]
    quad2 = quad2 + pcr_plate.columns()[23][6:8]
    quad3 = [well for i in range(12) for well in
             pcr_plate.columns()[i][8:16]][:plate3_samples]
    quad3 = quad3 + pcr_plate.columns()[11][14:16]
    quad4 = [well for i in range(12, 24) for well in
             pcr_plate.columns()[i][8:16]][:plate4_samples]
    quad4 = quad4 + pcr_plate.columns()[23][14:16]
    quad_wells = quad1 + quad2 + quad3 + quad4

    # Patient sample wells
    plate1 = sample_plates[0].wells()[:plate1_samples]
    plate1.append(sample_plates[0].wells()[95])
    plate2 = sample_plates[1].wells()[:plate2_samples]
    plate2.append(sample_plates[1].wells()[95])
    plate3 = sample_plates[2].wells()[:plate3_samples]
    plate3.append(sample_plates[2].wells()[95])
    plate4 = sample_plates[3].wells()[:plate4_samples]
    plate4.append(sample_plates[3].wells()[95])
    sample_wells = plate1 + plate2 + plate3 + plate4

    # Set Temp Mod to Temperature
    temp_mod.set_temperature(temperature)
    ctx.pause(f'''Temperature is now at {temperature}. Please place your
              reagents in the correct positions.''')

    # # Transfer mastermix to PCR plate
    # p20.pick_up_tip()
    # for well in quad_wells:
    #     p20.distribute(mm_vol, mm_tracker(mm_vol), well,
    #                    new_tip='never')
    # p20.drop_tip()

    # Transfer patient samples to PCR plate
    for source, dest in zip(sample_wells, quad_wells):
        p20.transfer(sample_vol, source.bottom(z=aspiration_height), dest,
                     new_tip='always')

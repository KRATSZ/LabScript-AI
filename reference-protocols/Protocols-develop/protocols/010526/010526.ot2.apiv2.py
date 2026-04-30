metadata = {
    'protocolName': 'Restriction Digests',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [p20_mount, p300_mount, sample_container, tube_type, input_csv,
        rxn_vol, enzyme_vol, enz_asp_rate, enz_disp_rate, digest_duration,
        heat_kill_temperature, heat_kill_duration,
        temp_mod_temperature, sample_asp_height] = get_values(  # noqa: F821
        "p20_mount", "p300_mount", "sample_container", "tube_type",
        "input_csv", "rxn_vol", "enzyme_vol", "enz_asp_rate", "enz_disp_rate",
        "digest_duration", "heat_kill_temperature", "heat_kill_duration",
        "temp_mod_temperature", "sample_asp_height")

    # Load Labware
    tc_mod = ctx.load_module('thermocycler module')
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    temp_mod = ctx.load_module('temperature module gen2', 1)
    temp_block = temp_mod.load_labware(
                        'opentrons_24_aluminumblock_18x0.5ml_3x1.5ml_3x1.5ml')
    tiprack_20ul = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
                    for slot in [3, 5]]
    tiprack_300ul = ctx.load_labware('opentrons_96_tiprack_300ul', 6)
    if sample_container == "tuberacks":
        tuberacks = [ctx.load_labware(tube_type, slot) for slot in [2, 4]]
    elif sample_container == "plate":
        sample_plate = ctx.load_labware(
                        'nest_96_wellplate_100ul_pcr_full_skirt', 2)

    # Load Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack_20ul)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tiprack_300ul])

    # CSV Data
    data = [[val.strip().upper() for val in line.split(',')]
            for line in input_csv.splitlines()[1:]
            if line and line.split(',')[0]]

    # Helper Functions
    temp_block_wells = temp_block.wells()
    excluded_wells = [temp_block.wells()[i] for i in [3, 7, 11, 15, 19, 23]]
    available_enzyme_wells = [well for well in temp_block_wells
                              if well not in excluded_wells]

    def change_flow_rates(pip, asp_speed, disp_speed):
        pip.flow_rate.aspirate = asp_speed
        pip.flow_rate.dispense = disp_speed

    def reset_flow_rates(pip):
        if pip.name == 'p20_single_gen2':
            pip.flow_rate.aspirate = 7.6
            pip.flow_rate.dispense = 7.6
        else:
            pip.flow_rate.aspirate = 92.86
            pip.flow_rate.dispense = 92.86

    def slow_tip_withdrawal(current_pipette, well_location, to_center=False):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            current_pipette.move_to(well_location.top())
        else:
            current_pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    water_tracker = {temp_block['D1']: 1500, temp_block['D2']: 1500}

    def getWater(vol):
        nonlocal water_tracker
        well = next(iter(water_tracker))
        if water_tracker[well] < vol:
            del water_tracker[well]
            if len(water_tracker) == 0:
                ctx.pause("Please refill the water tubes.")
                water_tracker = {temp_block['D1']: 1500,
                                 temp_block['D2']: 1500}
            well = next(iter(water_tracker))
        water_tracker[well] -= vol
        ctx.comment(f"{water_tracker[well]} uL of water remaining in {well}")
        return well

    # Load Reagents
    buffer = temp_block['D6']

    # Load Enzymes by Alphabetical Order
    enzymes_db = {}
    enzymes_list = []

    for line in data:
        enzymes = line[4].split(';')
        for enzyme in enzymes:
            if enzyme.strip() not in enzymes_list:
                enzymes_list.append(enzyme.strip())

    enzymes_list = sorted(enzymes_list)

    for i, enzyme in enumerate(enzymes_list):
        enzymes_db[enzyme] = available_enzyme_wells[i]

    # Sample Wells
    samples = len(data)
    sample_wells = []
    if sample_container == "tuberacks":
        sample_wells = [tube for rack in tuberacks for tube
                        in rack.wells()][:samples]
    elif sample_container == "plate":
        sample_wells = sample_plate.wells()[:samples]

    # Protocol Steps
    temp_mod.start_set_temperature(temp_mod_temperature)
    ctx.pause('''Load Enzymes into the Aluminum
              Block on the Temperature Module.''')
    tc_mod.set_block_temperature(4)

    # Transfer Water to PCR Wells
    for line in data:
        water_vol = float(line[3])
        dest = line[5]
        pip = p300 if water_vol > 20 else p20
        if not pip.has_tip:
            pip.pick_up_tip()
        pip.transfer(water_vol, getWater(water_vol), tc_plate[dest],
                     new_tip='never')

    if p20.has_tip:
        p20.drop_tip()

    if p300.has_tip:
        p300.drop_tip()

    # Transfer Buffer to PCR Wells
    p20.pick_up_tip()
    for line in data:
        buffer_vol = rxn_vol * 0.1
        dest = line[5]
        p20.transfer(buffer_vol, buffer, tc_plate[dest], new_tip="never")
    p20.drop_tip()

    # Transfer Samples to PCR Wells
    for line, src in zip(data, sample_wells):
        sample_vol = float(line[2])
        dest = line[5]
        pip = p300 if sample_vol > 20 else p20
        pip.transfer(sample_vol, src.bottom(sample_asp_height), tc_plate[dest],
                     mix_after=(2, 20))

    # Transfer Enzyme to PCR Wells
    temp_mod.await_temperature(temp_mod_temperature)
    change_flow_rates(p20, enz_asp_rate, enz_disp_rate)
    for line in data:
        enzymes = line[4].split(';')
        dest = line[5]
        for enzyme in enzymes:
            p20.pick_up_tip()
            p20.aspirate(enzyme_vol, enzymes_db[enzyme.strip()])
            slow_tip_withdrawal(p20, enzymes_db[enzyme.strip()],
                                to_center=True)
            p20.touch_tip()
            p20.dispense(enzyme_vol, tc_plate[dest].bottom(0.5))
            p20.mix(6, 20, tc_plate[dest])
            slow_tip_withdrawal(p20, tc_plate[dest])
            p20.drop_tip()
    reset_flow_rates(p20)

    # Thermocycler Incubation
    tc_mod.close_lid()
    tc_mod.set_block_temperature(37, hold_time_seconds=digest_duration,
                                 block_max_volume=rxn_vol)
    tc_mod.set_lid_temperature(70)
    tc_mod.set_block_temperature(heat_kill_temperature,
                                 hold_time_seconds=heat_kill_duration,
                                 block_max_volume=rxn_vol)
    tc_mod.set_block_temperature(4, block_max_volume=rxn_vol)
    tc_mod.open_lid()

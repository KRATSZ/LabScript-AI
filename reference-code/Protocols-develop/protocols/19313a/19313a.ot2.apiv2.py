"""Protocol."""
import os
import csv
from opentrons.types import Point

metadata = {
    'protocolName': 'RNA Extraction with Magnetic Life',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [num_samp, reset_tipracks, mix_reps1, mix_reps2, mix_reps_wash1,
     mix_reps_wash2, mix_reps_elution1, mix_reps_elution2, settling_1,
     settling_2, settling_3, settling_wash, settling_drying, settling_elution1,
     settling_elution2, wash1_vol, wash2_vol, elution_vol, lysis_vol, move_vol,
     binding_buffer_vol, final_vol, heating_module_temp, mag_height_1,
     waste_water_mode, asp_height, length_from_side,
     p300_mount] = get_values(  # noqa: F821
        "num_samp", "reset_tipracks", "mix_reps1", "mix_reps2",
        "mix_reps_wash1", "mix_reps_wash2", "mix_reps_elution1",
        "mix_reps_elution2", "settling_1", "settling_2", "settling_3",
        "settling_wash", "settling_drying", "settling_elution1",
        "settling_elution2", "wash1_vol", "wash2_vol", "elution_vol",
        "lysis_vol", "move_vol", "binding_buffer_vol", "final_vol",
        "heating_module_temp", "mag_height_1", "waste_water_mode",
        "asp_height", "length_from_side", "p300_mount")

    if not 0 <= num_samp <= 4:
        raise Exception('Please enter a sample number between 1-4')

    # load labware
    mag_mod = ctx.load_module('magnetic module gen2', '7')
    mag_plate = mag_mod.load_labware(
        'innovationlaboratoryproducts_96_wellplate_1000ul', label='Mag Plate')
    reagent_tuberack = ctx.load_labware(
                'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', '4',
                label='Reagent Tuberack')
    waste_tuberack = ctx.load_labware(
                            'opentrons_6_tuberack_falcon_50ml_conical', '5',
                            label='Waste Tuberack')
    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                  for slot in ['8', '9']]
    temp_mod = ctx.load_module('temperature module gen2', '10')
    temp_rack = temp_mod.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul',
        label='Temperature tuberack')
    tiprack200 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '11')

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2',
                               p300_mount,
                               tip_racks=tiprack300)

    # Tip tracking between runs
    if not ctx.is_simulating():
        file_path = '/data/csv/tiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial tip count tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    tip_count_list = []
    if ctx.is_simulating():
        tip_count_list = [0, 0]
    elif reset_tipracks:
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    num_one = int(tip_count_list[0])
    num_two = int(tip_count_list[1])
    starting_tip_regular = num_one
    starting_tip_filter = num_two

    tips_300 = [tip for tiprack in tiprack300 for tip in tiprack.wells()]
    regular_tip_count = num_one
    regular_parked_tip_nums = {0: starting_tip_regular,
                               1: starting_tip_regular+1,
                               2: starting_tip_regular+2,
                               3: starting_tip_regular+3}

    def pick_up300(sample_tip=num_one, use_park=False):
        nonlocal regular_tip_count
        if regular_tip_count == 95:
            ctx.pause("Replace all 300ul non-filter tip racks")
            regular_tip_count = 0
            p300.pick_up_tip(tips_300[regular_tip_count+num_samp])
            regular_tip_count += 1
        elif use_park:
            p300.pick_up_tip(tips_300[regular_parked_tip_nums[sample_tip]])
        else:
            p300.pick_up_tip(tips_300[regular_tip_count+num_samp])
            regular_tip_count += 1

    filter_tip_count = num_two
    filter_parked_tip_nums = {0: starting_tip_filter,
                              1: starting_tip_filter+1,
                              2: starting_tip_filter+2,
                              3: starting_tip_filter+3}

    def pick_up_filter(sample_tip=num_two, use_park=False):
        nonlocal filter_tip_count
        if filter_tip_count == 95:
            ctx.pause("Replace all 200ul filter tip racks")
            filter_tip_count = 0
            p300.pick_up_tip(tiprack200.wells()[filter_tip_count+num_samp])
            filter_tip_count += 1
        elif use_park:
            p300.pick_up_tip(tips_300[filter_parked_tip_nums[sample_tip]])
        else:
            p300.pick_up_tip(tiprack200.wells()[filter_tip_count+num_samp])
            filter_tip_count += 1

    # load reagents
    elution_buffer = reagent_tuberack.wells_by_name()['C2'].bottom(z=20)
    binding_buffer = reagent_tuberack.wells_by_name()['A3'].bottom(z=20)
    rps_wash_buffer = reagent_tuberack.wells_by_name()['A4'].bottom(z=20)
    wash_buffer = reagent_tuberack.wells_by_name()['B3'].bottom(z=20)
    samples = mag_plate.rows()[0][:12:3][:num_samp]
    samples_second_well = mag_plate.rows()[0][1:12:3][:num_samp]
    samples_third_well = mag_plate.rows()[0][2:12:3][:num_samp]
    waste = waste_tuberack.wells()[0].bottom(z=80)

    def remove_supernatant(vol, index, loc, loc_length_from_side,):
        ctx.comment('Removing Supernatant')
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-loc_length_from_side)*side))
        p300.aspirate(vol, aspirate_loc, rate=0.1)
        p300.dispense(vol, waste)
        p300.blow_out()

    # initialize temp mod and magnetic mod
    temp_mod.set_temperature(heating_module_temp)
    mag_mod.engage(height_from_base=mag_height_1)

    if not waste_water_mode:
        ctx.comment('\n\n\n\nNormal Mode')
        mag_mod.disengage()
        # binding
        ctx.delay(minutes=settling_drying)
        for i, sample in enumerate(samples):
            pick_up_filter()
            p300.aspirate(binding_buffer_vol, binding_buffer)
            p300.dispense(binding_buffer_vol, sample)
            p300.mix(mix_reps2, 200, sample, rate=3)
            p300.touch_tip()
            p300.drop_tip()
        mag_mod.engage(height_from_base=mag_height_1)
        ctx.delay(minutes=settling_2)

        # remove 200ul of supernatant
        for i, sample in enumerate(samples):
            pick_up_filter(i, use_park=True)
            remove_supernatant(200, i, sample, 2.5)
            p300.return_tip()
        mag_mod.disengage()
        ctx.comment('End Normal Mode\n\n\n\n\n\n\n\n\n')

    if waste_water_mode:
        # remove storage buffer
        ctx.delay(minutes=settling_3)
        for i, sample in enumerate(samples):
            pick_up300(i, use_park=True)
            for _ in range(5):
                p300.aspirate(300, sample)
                p300.dispense(300, waste)
                p300.blow_out()
            p300.return_tip()
        mag_mod.disengage()
        ctx.comment('\n\n\n')

    # RPS wash
    ctx.comment("RPS")
    for sample in samples:
        pick_up300()
        p300.aspirate(wash1_vol, rps_wash_buffer)
        p300.dispense(wash1_vol, sample)
        p300.mix(mix_reps_wash1, wash1_vol, sample, rate=4)
        p300.drop_tip()
    ctx.comment('\n\n\n')

    mag_mod.engage(height_from_base=mag_height_1)
    ctx.delay(minutes=settling_wash)
    for i, sample in enumerate(samples):
        pick_up300(i, use_park=True)
        remove_supernatant(200, i, sample, 2.5)
        p300.blow_out()
        p300.return_tip()
        mag_mod.disengage()
    ctx.comment('\n\n\n')

    # five washes
    ctx.comment('Five washes')
    for wash in range(5):
        for sample in samples:
            pick_up300()
            p300.aspirate(wash2_vol, wash_buffer)
            p300.dispense(wash2_vol, sample)
            p300.mix(mix_reps_wash1, wash2_vol, sample, rate=3)
            p300.drop_tip()
        mag_mod.engage(height_from_base=mag_height_1)
        ctx.delay(minutes=settling_wash)
        for i, sample in enumerate(samples):
            pick_up300(i, use_park=True)
            remove_supernatant(200, i, sample, 2.5)
            p300.return_tip()
        mag_mod.disengage()
    ctx.comment('\n\n\n')

    mag_mod.engage(height_from_base=mag_height_1)
    ctx.delay(minutes=settling_wash)
    for i, (sample, dest) in enumerate(zip(samples, temp_rack.rows()[3])):
        pick_up300(i, use_park=True)
        p300.aspirate(100, sample, rate=0.1)
        p300.dispense(100, waste)
        p300.return_tip()
    mag_mod.disengage()
    ctx.delay(minutes=settling_drying)
    ctx.comment('\n\n\n')

    for sample, dest in zip(samples, temp_rack.rows()[3]):
        pick_up300()
        p300.aspirate(elution_vol, elution_buffer)
        p300.dispense(elution_vol, sample)
        p300.mix(mix_reps_elution1, 80, sample, rate=2.5)
        p300.aspirate(60, sample)
        p300.dispense(60, dest)
        p300.blow_out()
        p300.drop_tip()
    ctx.comment('\n\n\n')

    # elution on Aluminum block
    ctx.delay(minutes=settling_2)
    for i, (source, samp_well2) in enumerate(zip(temp_rack.rows()[3],
                                                 samples_second_well)):
        pick_up300(i, use_park=True)
        p300.mix(mix_reps_elution1, 80, source, rate=2.5)
        p300.return_tip()
    ctx.delay(minutes=settling_2)
    for i, (source, samp_well2) in enumerate(zip(temp_rack.rows()[3],
                                                 samples_second_well)):
        pick_up300(i, use_park=True)
        p300.mix(mix_reps_elution1, 80, source, rate=2.5)
        p300.aspirate(100, source)
        p300.dispense(100, samp_well2)
        p300.return_tip()
    ctx.comment('\n\n\n')

    # Transfer
    mag_mod.engage(height_from_base=mag_height_1)
    ctx.delay(minutes=settling_drying)
    for i, (samp_well2, samp_well3) in enumerate(zip(samples_second_well,
                                                     samples_third_well)):
        pick_up_filter(i, use_park=True)
        p300.aspirate(final_vol, samp_well2, rate=0.1)
        p300.dispense(final_vol, samp_well3)
        p300.return_tip()
        mag_mod.disengage()
    ctx.comment('\n\n\n')

    num_one = regular_tip_count
    num_two = filter_tip_count

    # write updated tipcount to CSV
    new_tip_count = str(num_one)+", "+str(num_two)+"\n"
    if not ctx.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

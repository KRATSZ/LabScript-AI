import os
import csv

metadata = {
    'protocolName': 'Swift 2S Turbo DNA Library Kit Protocol: Part 2/3 - \
    Ligation Clean-Up & PCR Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.10'
}


def run(protocol):
    [pip_tip, p300tips, mag_gen, samps, a_i] = get_values(  # noqa: F821
     'pip_tip', 'p300tips', 'mag_gen', 'samps', 'a_i')

    if mag_gen == 'magdeck':
        mag_height = 13.6
    else:
        mag_height = 6.8

    # Labware Setup
    pip_type, tip_name = pip_tip.split()
    small_tips = protocol.load_labware(tip_name, '5')
    big_tips1 = protocol.load_labware(p300tips, '6')
    big_tips2 = protocol.load_labware(p300tips, '9')

    small_pip = protocol.load_instrument(pip_type, 'left')
    p300 = protocol.load_instrument('p300_multi', 'right')

    rt_reagents = protocol.load_labware(
        'nest_12_reservoir_15ml', '2')

    tempdeck = protocol.load_module('Temperature Module', '3')

    cool_reagents = tempdeck.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap',
        'Opentrons 24-Well Aluminum Block')

    magdeck = protocol.load_module(mag_gen, '4')
    mag_plate = magdeck.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'NEST 96-Well Plate')

    reaction_plate = protocol.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '1')

    # Tip tracking between runs
    if not protocol.is_simulating():
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
    if protocol.is_simulating():
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    spip_count = int(tip_count_list[0])
    bpip_count = int(tip_count_list[1])

    def small_pick_up():
        nonlocal spip_count

        if spip_count == 96:
            small_pip.home()
            protocol.pause('Out of tips. Please replace tips in slot 5 and \
            click RESUME.')
            small_tips.reset()
            spip_count = 0

        small_pip.pick_up_tip(small_tips.wells()[spip_count])

        spip_count += 1

    def big_pick_up():
        nonlocal bpip_count

        if bpip_count == 24:
            p300.home()
            protocol.pause('Out of tips. Please replace tips in slot 5 and \
            click RESUME.')
            big_tips1.reset()
            big_tips2.reset()
            bpip_count = 0

        if bpip_count <= 11:
            p300.pick_up_tip(big_tips1.columns()[bpip_count][0])
        else:
            p300.pick_up_tip(big_tips2.columns()[bpip_count-12][0])

        bpip_count += 1

    # if using the P20, change the aspirate/dispense/blow out rates
    if pip_type == 'p20_single_gen2':
        small_pip.flow_rate.aspirate = 25
        small_pip.flow_rate.dispense = 50
        small_pip.flow_rate.blow_out = 1000

    # Reagent Setup

    pcr_mm = cool_reagents.wells_by_name()['A3']

    beads = rt_reagents.wells_by_name()['A1']
    ethanol = rt_reagents.wells_by_name()['A3']
    te = rt_reagents.wells_by_name()['A6']
    waste = rt_reagents.wells_by_name()['A11']

    ezp = 0
    pps = 3
    ms = 0

    enzymatic_prep_samples = reaction_plate.columns()[ezp]
    pcr_prep_samples = reaction_plate.columns()[pps]
    mag_samples = mag_plate.columns()[ms]

    enzymatic_300 = [enzymatic_prep_samples[0]]
    pcr_300 = [pcr_prep_samples[0]]
    mag_300 = [mag_samples[0]]

    samp_l = [enzymatic_prep_samples, pcr_prep_samples, mag_samples]
    samp_pl = [reaction_plate, reaction_plate, mag_plate]
    samp_300 = [enzymatic_300, pcr_300, mag_300]

    nums = [ezp, pps, ms]

    samps = int(samps)

    if samps > 8:
        for s, t, plate, n in zip(samp_l, samp_300, samp_pl, nums):
            s += plate.columns()[n+1]
            t.append(plate.columns()[n+1][0])
        if samps > 16:
            for s, t, plate, n in zip(samp_l, samp_300, samp_pl, nums):
                s += plate.columns()[n+2]
                t.append(plate.columns()[n+2][0])

    # Actively cool the samples and enzymes
    tempdeck.set_temperature(4)

    # Ligation Purification
    # Transfer samples to the Magnetic Module
    p300.flow_rate.aspirate = 10
    for enz_samp, mag_samp in zip(enzymatic_300, mag_300):
        big_pick_up()
        p300.aspirate(60, enz_samp)
        p300.dispense(60, mag_samp.top(-4))
        p300.blow_out(mag_samp.top(-4))
        p300.drop_tip()

    # Transfer beads to the samples on the Magnetic Module
    p300.flow_rate.aspirate = 75
    big_pick_up()
    p300.mix(10, 200, beads)

    for mag_samp in mag_300:
        if not p300.hw_pipette['has_tip']:
            big_pick_up()
        p300.flow_rate.aspirate = 10
        p300.flow_rate.dispense = 10
        p300.aspirate(48, beads)
        p300.default_speed = 50
        p300.move_to(mag_samp.top(-2))
        p300.default_speed = 400
        p300.dispense(48, mag_samp.top(-5))
        p300.blow_out()
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50
        p300.mix(10, 80, mag_samp.top(-13.5))
        p300.blow_out(mag_samp.top(-5))
        p300.drop_tip()

    # Incubating for 5 minutes
    protocol.comment("Incubating for 5 minutes.")
    protocol.delay(minutes=5)

    # Engage Magnetic Module
    magdeck.engage(height=mag_height)
    protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
    protocol.delay(minutes=6)

    # Remove supernatant
    p300.flow_rate.aspirate = 20
    p300.flow_rate.dispense = 50

    for mag_samp in mag_300:
        big_pick_up()
        p300.aspirate(108, mag_samp.bottom(2))
        p300.dispense(108, waste.top(-1))
        p300.drop_tip()

    # Wash samples 2X with 180uL of 80% EtOH
    p300.default_speed = 200
    p300.flow_rate.aspirate = 75
    p300.flow_rate.dispense = 50

    for _ in range(2):
        for mag_samp in mag_300:
            if not p300.hw_pipette['has_tip']:
                big_pick_up()
            p300.aspirate(10, ethanol.top())
            p300.aspirate(180, ethanol)
            p300.air_gap(5)
            p300.dispense(210, mag_samp.top(-2))
        if samps == 8:
            protocol.delay(seconds=15)
        for mag_samp in mag_300:
            if not p300.hw_pipette['has_tip']:
                big_pick_up()
            p300.aspirate(5, mag_samp.top())
            p300.aspirate(190, mag_samp)
            p300.air_gap(5)
            p300.dispense(210, waste.top(-1))
            p300.drop_tip()

    # remove residual ethanol
    for mag_samp in mag_300:
        big_pick_up()
        p300.aspirate(30, mag_samp.bottom(-0.5))
        p300.air_gap(5)
        p300.drop_tip()

    protocol.comment("Letting beads dry for 3 minutes.")
    protocol.delay(minutes=3)
    magdeck.disengage()

    # Elute clean ligation product
    for mag_samp in mag_300:
        big_pick_up()
        p300.aspirate(22, te)
        p300.dispense(22, mag_samp.top(-12))
        p300.blow_out(mag_samp.top())
        p300.flow_rate.aspirate = 100
        p300.flow_rate.dispense = 200
        p300.mix(10, 20, mag_samp.top(-13.5))
        p300.blow_out(mag_samp.top())
        p300.flow_rate.aspirate = 75
        p300.flow_rate.dispense = 50
        p300.drop_tip()

    # Incubate for 2 minutes
    protocol.comment("Incubating for 2 minutes.")
    protocol.delay(minutes=2)

    # Engage Magnetic Module
    protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
    magdeck.engage(height=mag_height)
    protocol.delay(minutes=6)

    # Transfer clean samples to aluminum block plate.
    for mag_samp, pcr_samp in zip(mag_300, pcr_300):
        big_pick_up()
        p300.aspirate(22, mag_samp.bottom(0.25))
        p300.dispense(22, pcr_samp)
        p300.blow_out(pcr_samp.top())
        p300.drop_tip()

    # Disengage Magnetic Module ofr PCR purification protocol
    magdeck.disengage()

    # PCR Prep
    # Transfer Dual Indexes to the samples
    p8 = ['B'+str(i) for i in range(1, 7)] + ['C1', 'C2']
    p16 = ['C'+str(i) for i in range(3, 7)] + ['D'+str(i) for i in range(1, 5)]

    if a_i == 'no':
        protocol.pause('Please manually add indexes to samples now. When done \
        replace plate and click RESUME.')
    else:
        if samps != 24:
            primers = [cool_reagents[well] for well in p8]
            if samps == 16:
                primers += [cool_reagents[well] for well in p16]
            for primer, well in zip(primers, pcr_prep_samples):
                small_pick_up()
                small_pip.aspirate(5, primer.top(-24))
                small_pip.dispense(5, well)
                small_pip.drop_tip()
        if samps == 24:
            primers8 = [cool_reagents[well] for well in p8]
            primers16 = [cool_reagents[well] for well in p8+p16]
            for primer, well in zip(primers16, pcr_prep_samples[:16]):
                small_pick_up()
                small_pip.aspirate(5, primer.top(-24))
                small_pip.dispense(5, well)
                small_pip.drop_tip()
            protocol.pause('Please remove initial indexes and replace with \
            remaining 8 in row B, C1, and C2. Click RESUME when ready.')
            for primer, well in zip(primers8, pcr_prep_samples[16:]):
                small_pick_up()
                small_pip.aspirate(5, primer.top(-24))
                small_pip.dispense(5, well)
                small_pip.drop_tip()
    # Transfer PCR Master Mix to the samples
    small_pick_up()

    if tip_name == 'opentrons_96_filtertiprack_10ul':
        mix_vol = 10
    else:
        mix_vol = small_pip.max_volume

    small_pip.mix(6, mix_vol, pcr_mm)
    small_pip.blow_out()

    def small_pip_trans(vol, src, dest):
        if vol > small_pip.max_volume:
            while vol > mix_vol:
                if not small_pip.hw_pipette['has_tip']:
                    small_pick_up()
                small_pip.aspirate(mix_vol*0.9, src)
                small_pip.dispense(mix_vol*0.9, dest)
                small_pip.blow_out()
                small_pip.drop_tip()
                vol -= mix_vol*0.9
            small_pick_up()
            small_pip.aspirate(vol, src)
            small_pip.dispense(vol, dest)
        else:
            small_pip.aspirate(vol, src)
            small_pip.dispense(vol, dest)

    for well in pcr_prep_samples:
        if not small_pip.hw_pipette['has_tip']:
            small_pick_up()
        small_pip_trans(25, pcr_mm, well.top(-12))
        small_pip.blow_out()
        small_pip.mix(10, 10, well.top(-13.5))
        small_pip.blow_out(well.top(-12))
        small_pip.drop_tip()

    tempdeck.deactivate()
    protocol.comment("Place samples in thermocycler for PCR. \
    Temp deck is turned off. Put reagents on temp deck back in the -20")

    # write updated tipcount to CSV
    new_tip_count = str(spip_count)+", "+str(bpip_count)+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

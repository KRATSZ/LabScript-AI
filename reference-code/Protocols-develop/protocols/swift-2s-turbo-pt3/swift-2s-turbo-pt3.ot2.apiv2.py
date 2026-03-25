import os
import csv

metadata = {
    'protocolName': 'Swift 2S Turbo DNA Library Kit Protocol: Part 3/3 - \
    Final Clean-Up',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.10'
}


def run(protocol):
    [p300tips, mag_gen, samps] = get_values(  # noqa: F821
     'p300tips', 'mag_gen', 'samps')

    if mag_gen == 'magdeck':
        mag_height = 13.6
    else:
        mag_height = 6.8

    # Labware Setup
    big_tips1 = protocol.load_labware(p300tips, '6')
    big_tips2 = protocol.load_labware(p300tips, '9')
    p300 = protocol.load_instrument('p300_multi', 'right')

    rt_reagents = protocol.load_labware(
        'nest_12_reservoir_15ml', '2')

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

    # Reagent Setup
    beads = rt_reagents.wells_by_name()['A1']
    ethanol2 = rt_reagents.wells_by_name()['A4']
    te = rt_reagents.wells_by_name()['A6']
    waste2 = rt_reagents.wells_by_name()['A12']

    col_no = [3, 6, 3]

    pcr_prep_samples = [reaction_plate['A3']]
    purified_samples = [reaction_plate['A6']]
    mag_samples = [mag_plate['A3']]

    samps = int(samps)

    plate_list = [pcr_prep_samples, purified_samples, mag_samples]

    if samps > 8:
        for n, plate in zip(col_no, plate_list):
            plate.append(reaction_plate.columns()[n][0])
        if samps > 16:
            for n, plate in zip(col_no, plate_list):
                plate.append(reaction_plate.columns()[n+1][0])

    # PCR Purification

    # Transfer samples to the Magnetic Module
    p300.flow_rate.aspirate = 10
    for pcr_samps, mag_samps in zip(pcr_prep_samples, mag_samples):
        big_pick_up()
        p300.aspirate(60, pcr_samps)
        p300.dispense(60, mag_samps.top(-4))
        p300.blow_out(mag_samps.top(-4))
        p300.drop_tip()

    # Transfer beads to the samples in PCR strip
    p300.flow_rate.aspirate = 75
    big_pick_up()
    p300.mix(5, 60, beads)

    for mag_samps in mag_samples:
        if not p300.hw_pipette['has_tip']:
            big_pick_up()
        p300.flow_rate.aspirate = 10
        p300.flow_rate.dispense = 10
        p300.aspirate(32.5, beads)
        p300.default_speed = 50
        p300.dispense(32.5, mag_samps.top(-12))
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50
        p300.blow_out()
        p300.mix(10, 60, mag_samps.top(-13.5))
        p300.blow_out()
        p300.drop_tip()

    # Incubate for 5 minutes, then engage Magnetic Module and incubate
    protocol.comment('Incubating for 5 minutes.')
    protocol.delay(minutes=5)

    magdeck.engage(height=mag_height)
    protocol.delay(minutes=5)

    # Aspirate supernatant
    for mag_samps in mag_samples:
        big_pick_up()
        p300.aspirate(82.5, mag_samps.bottom(2))
        p300.dispense(82.5, waste2)
        p300.drop_tip()

    # Wash samples 2x with 180ul of 80% EtOH
    for _ in range(2):
        for mag_samps in mag_samples:
            if not p300.hw_pipette['has_tip']:
                big_pick_up()
            p300.aspirate(5, ethanol2.top())
            p300.aspirate(180, ethanol2)
            p300.air_gap(10)
            p300.dispense(200, mag_samps.top(-2))
        if samps == 8:
            protocol.delay(seconds=15)
        for mag_samps in mag_samples:
            if not p300.hw_pipette['has_tip']:
                big_pick_up()
            p300.aspirate(5, mag_samps.top())
            p300.aspirate(190, mag_samps.bottom(1.5))
            p300.air_gap(5)
            p300.dispense(210, waste2)
            p300.drop_tip()

    # Remove residual 80% EtOH
    for mag_samps in mag_samples:
        big_pick_up()
        p300.aspirate(30, mag_samps.bottom(0.5))
        p300.air_gap(5)
        p300.drop_tip()

    protocol.delay(minutes=2)
    magdeck.disengage()

    # Elute clean product
    for mag_samps in mag_samples:
        big_pick_up()
        p300.aspirate(22, te)
        p300.dispense(22, mag_samps.top(-12))
        p300.blow_out(mag_samps.top())
        p300.mix(10, 20, mag_samps.top(-13.5))
        p300.blow_out(mag_samps.top())
        p300.drop_tip()

    # Incubate for 2 minutes, then engage Magnetic Module
    protocol.comment("Incubating for 2 minutes, \
    then engaging Magnetic Module.")
    protocol.delay(minutes=2)

    magdeck.engage(height=mag_height)
    protocol.delay(minutes=5)

    # Transfer clean samples to aluminum block plate.
    for mag_samps, p_samps in zip(mag_samples, purified_samples):
        big_pick_up()
        p300.aspirate(20, mag_samps)
        p300.dispense(22, p_samps.top(-12))
        p300.blow_out()
        p300.drop_tip()

    # Collect clean product
    magdeck.disengage()
    protocol.comment("Clean up complete. Store samples in 4C or -20C for \
    long term storage.")

    # write updated tipcount to CSV
    new_tip_count = str(spip_count)+", "+str(bpip_count)+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

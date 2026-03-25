import os
import csv

metadata = {
    'protocolName': 'Protein Labeling with Incubation',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [numSamps, numInc, sampLabware,
     tempGen, resetTips] = get_values(  # noqa: F821
     'numSamps', 'numInc', 'sampLabware', 'tempGen', 'resetTips')

    # load labware
    tips20 = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', s) for s in [9, 6, 3]]
    tips300 = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', s) for s in [8, 11, 10]]

    p20 = protocol.load_instrument(
        'p20_single_gen2', 'right', tip_racks=tips20)
    p300 = protocol.load_instrument(
        'p300_single_gen2', 'left', tip_racks=tips300)

    tempDeck = protocol.load_module(tempGen, '4')
    tempPlate = tempDeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul')
    reagentRack = protocol.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
        '7', 'Aluminum Block with 1.5mL Tubes containing Reagents')
    mixPlate = protocol.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt',
        '5', 'NEST 96 PCR Plate for mixing')
    destPlate = protocol.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt',
        '1', 'NEST 96 PCR Plate for Samples')
    sampRack = protocol.load_labware(
        sampLabware, '2', 'Aluminum Block containing Samples')

    # Create and update variables

    if not 1 <= numSamps <= 19:
        raise Exception('Number of Samples should be between 1 and 19.')

    tempDeck.deactivate()

    protocol.set_rail_lights(True)

    initSamps = sampRack.wells()[:numSamps]  # samples in rack
    mixSamps = mixPlate.wells()[:numSamps]  # samples + reagents
    tempChunks = [
        tempPlate.wells()[i * 5:(i + 1) * 5] for i in range(
            (len(tempPlate.wells()) + 5 - 1) // 5)][:numSamps]
    tempWells = tempPlate.wells()[:numSamps*5]
    destWells = destPlate.wells()[:numSamps*5]
    buff1 = reagentRack['A1']
    labelling = reagentRack['A2']
    tris = reagentRack['A3']
    sampBuffs = reagentRack.rows()[1]

    # Tip tracking between runs
    if not protocol.is_simulating():
        file_path = '/data/csv/tiptracking407d5e.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial tip count tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    tip_count_list = []
    # first value is 300uL tips; second is 20uL tips
    if protocol.is_simulating() or resetTips:
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    tips300flat = [well for rack in tips300 for well in rack.wells()]
    tips20flat = [well for rack in tips20 for well in rack.wells()]
    tipState = {
        p300: [tips300flat, tip_count_list[0]],
        p20: [tips20flat, tip_count_list[1]]
        }

    def pick_up(pip):
        if tipState[pip][1] == 96*3:
            for _ in range(10):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                protocol.delay(seconds=1)
            protocol.pause(f"Please replace tips for {pip}")
            pip.reset_tipracks()
            tipState[pip][1] = 0
        pip.pick_up_tip(tipState[pip][0][tipState[pip][1]])
        tipState[pip][1] += 1

    # 1. Transfer 5.8uL buffer to samp wells on mix plate
    protocol.comment('\nTransferring 5.8uL of Buffer to Mix Plate\n')

    pick_up(p20)

    for samp in mixSamps:
        p20.transfer(5.8, buff1, samp, new_tip='never')

    p20.drop_tip()

    # 2. Transfer 58.1uL of samp to mix plate
    protocol.comment('\nTransferring 58.1uL of Sample to Mix Plate\n')

    for src, dest in zip(initSamps, mixSamps):
        pick_up(p300)
        p300.transfer(58.1, src, dest, new_tip='never')
        p300.drop_tip()

    # 3. Transfer 2.9uL of labelling reagent to mix plate
    protocol.comment('\nTransferring 2.9uL of Labelling Reagent to Samples\n')

    for samp in mixSamps:
        pick_up(p20)
        p20.transfer(2.9, labelling, samp, mix_after=(15, 20), new_tip='never')
        p20.drop_tip()

    # 4. Incubate for 1 hour
    protocol.comment('\nIncubating for 1 hour\n')

    protocol.delay(minutes=60)

    # 5. Transfer 58.1 Tris to each well and mix
    # 6. Distributing 20uL to 5 wells on Temperature module
    protocol.comment('\nAdding 58.1uL of Tris to each Sample & \
    Distributing 20uL 5-times to Temperature Module\n')

    for samp, dests in zip(mixSamps, tempChunks):
        pick_up(p300)
        p300.transfer(58.1, tris, samp, mix_after=(5, 100), new_tip='never')
        p300.aspirate(110, samp)
        for dest in dests:
            p300.dispense(20, dest)
        p300.dispense(10, samp)
        p300.drop_tip()

    # 7. Transfer 180uL of buffers to samples on temperature module
    protocol.comment('\nTransferring 180uL buffer to corresponding samples\n')

    for dests in tempChunks:
        for src, dest in zip(sampBuffs, dests):
            pick_up(p300)
            p300.transfer(180, src, dest, mix_after=(5, 180), new_tip='never')
            p300.drop_tip()

    # 8. Transfer 20uL of samp to final plate
    protocol.comment('\nTransferring 20uL of sample to final plate\n')
    for src, dest in zip(tempWells, destWells):
        pick_up(p20)
        p20.transfer(20, src, dest, mix_before=(5, 20), new_tip='never')
        p20.drop_tip()

    # 9. Set Temperature Module to 37
    # 10. Perform step 8 at 1, 2, and 4 day intervals (based on parameter)

    times = [1, 1, 2]  # create intervals for delay

    for time in times[:numInc]:
        tempDeck.set_temperature(37)

        protocol.comment(f'\nIncubating for {time} day(s)\n')
        protocol.delay(minutes=time*24*60)

        protocol.comment('\nPreparing for sample transfer to final plate\n')

        for _ in range(20):
            protocol.set_rail_lights(not protocol.rail_lights_on)
            protocol.delay(seconds=1)

        for src, dest in zip(tempWells, destWells):
            pick_up(p20)
            p20.transfer(20, src, dest, mix_before=(5, 20), new_tip='never')
            p20.drop_tip()

    # Protocol complete; save tip state
    new_tip_count = str(tipState[p300][1])+", "+str(tipState[p20][1])+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

    protocol.set_rail_lights(False)
    protocol.comment('\nProtocol complete!')

metadata = {
    'protocolName': 'Custom PCR Setup from CSV',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.10'
    }


def run(protocol):
    [transferCSV, pipMnt] = get_values(  # noqa: F821
        'transferCSV', 'pipMnt')

    # load labware and pipettes
    tips = [
        protocol.load_labware(
            'opentrons_96_filtertiprack_20ul', s) for s in [4, 7, 10]
            ]
    p20 = protocol.load_instrument('p20_single_gen2', pipMnt, tip_racks=tips)

    srcPlate, preampPlate = [
        protocol.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt', s) for s in [1, 2]
            ]
    loadPlate = protocol.load_labware('corning_384_wellplate_112ul_flat', '3')

    tubeRack = protocol.load_labware(
        'opentrons_24_tuberack_nest_1.5ml_snapcap', '5')
    preampMix = tubeRack['A1']
    oaMix = tubeRack['D6']

    # take data from CSV
    srcPos = []
    preampPos = []
    loadPos1 = []
    loadPos2 = []
    for line in [r for r in transferCSV.strip().splitlines() if r][1:]:
        positions = line.split(',')
        srcPos.append(positions[0])
        preampPos.append(positions[2])
        loadPos1.append(positions[3])
        loadPos2.append(positions[4])

    # create function for flashing lights with message

    def msgLights(msg):
        for _ in range(5):
            protocol.set_rail_lights(not protocol.rail_lights_on)
            protocol.delay(seconds=1)
        protocol.pause(msg)
        protocol.set_rail_lights(not protocol.rail_lights_on)

    # calculate volumes needed
    preampVol = 2.5*len(srcPos)
    preExtra = round(0.1*preampVol)
    oaVol = 7.5*len(srcPos)
    oaExtra = round(0.1*oaVol)

    # begin protocol
    protocol.set_rail_lights(True)

    preampMsg = "Please ensure the Source Plate and Preamp Plate are placed \
    on the deck (slots 1 and 2, respectively). \
    The Preamp mastermix should be loaded in A1 of the Tube Rack (slot 4). \
    At least {}uL should be in the tube, \
    but approximately 10% extra is recommended ({}uL). \
    When ready, click RESUME".format(preampVol, preExtra)
    msgLights(preampMsg)

    # transfer preamp mix, then transfer samples
    p20.pick_up_tip()

    for well in preampPos:
        if p20.current_volume < 2.5:
            p20.mix(2, 20, preampMix)
            p20.aspirate(20, preampMix)
        p20.dispense(2.5, preampPlate[well])

    p20.dispense(p20.current_volume, preampMix)
    p20.drop_tip()

    for s, d in zip(srcPos, preampPos):
        p20.transfer(
            2.5, srcPlate[s], preampPlate[d],
            mix_before=(3, 5), mix_after=(3, 4)
            )

    # message user to let them know that the robot is ready for amplification
    ampMsg = "Preamp plate is ready. Please remove from robot for \
    amplification off deck. After amplification, click RESUME."
    msgLights(ampMsg)

    # message to user to prepare for final step
    oaMsg = "Please ensure the Preamp Plate and Loading Plate are placed \
    on the deck (slots 2 and 3, respectively). \
    The OpenArray mastermix should be loaded in D6 of the Tube Rack (slot 4). \
    At least {}uL should be in the tube, \
    but approximately 10% extra is recommended ({}uL). \
    When ready, click RESUME".format(oaVol, oaExtra)
    msgLights(oaMsg)

    # transfer OpenArray Master Mix and samples

    p20.pick_up_tip()

    for p1, p2 in zip(loadPos1, loadPos2):
        if p20.current_volume < 2.5:
            p20.mix(2, 15, oaMix)
            p20.aspirate(15, oaMix)
        p20.dispense(3.75, loadPlate[p1])
        p20.dispense(3.75, loadPlate[p2])

    p20.dispense(p20.current_volume, oaMix)
    p20.drop_tip()

    for s, p1, p2 in zip(preampPos, loadPos1, loadPos2):
        p20.transfer(
            1.25, preampPlate[s], loadPlate[p1],
            mix_before=(3, 5), mix_after=(3, 4)
            )
        p20.transfer(
            1.25, preampPlate[s], loadPlate[p2],
            mix_before=(3, 5), mix_after=(3, 4)
            )

    protocol.comment("Protocol complete! Please start OpenArray process.")

    protocol.set_rail_lights(False)

import math

metadata = {
    'protocolName': 'Arcis Blood Extraction and PCR Setup',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(protocol):
    [p50_mnt, p300_mnt, samps] = get_values(  # noqa: F821
        'p50_mnt', 'p300_mnt', 'samps')

    # load labware and pipette
    pip50 = protocol.load_instrument('p50_multi', p50_mnt)
    pip300 = protocol.load_instrument('p300_multi', p300_mnt)

    tip1 = protocol.load_labware('opentrons_96_tiprack_300ul', '5', 'Tips')
    tip2 = protocol.load_labware('opentrons_96_tiprack_300ul', '6', 'Tips')
    tips = tip1.rows()[0] + tip2.rows()[0]

    trough = protocol.load_labware(
        'usascientific_12_reservoir_22ml', '4', 'Reservoir')
    cplate = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '1', 'Corning Plate')

    biop1 = protocol.load_labware(
        'bioplastics_96_wellplate_100ul', '2', 'Bioplastics Plate 1')
    biop2 = protocol.load_labware(
        'bioplastics_96_wellplate_100ul', '3', 'Bioplastics Plate 2')

    reagent1 = trough.wells()[0]
    reagent2 = trough.wells()[1]
    mm = trough.wells()[2]
    sample = trough.wells()[3]

    if samps > 56 or samps < 1:
        raise Exception('Number of Samples should be between 1 and 56.')

    num_cols = math.ceil(samps/8)

    bp1 = biop1.rows()[0][:num_cols]
    bp2 = biop2.rows()[0][:num_cols]
    cp = cplate.rows()[0][:num_cols]

    tipcount = 0

    def pick_up(pip):
        nonlocal tipcount
        if tipcount == 24:
            pip50.home()
            protocol.pause('Out of tips. Please replace tips in slots 5 & 6.')
            tipcount = 0

        if pip == pip50:
            pip50.pick_up_tip(tips[tipcount])
        else:
            pip300.pick_up_tip(tips[tipcount])

        tipcount += 1

    # transfer 150 ul reagent 1

    pick_up(pip300)

    for row in cp:
        pip300.transfer(150, reagent1, row, new_tip='never')

    pip300.drop_tip()

    # transfer 20 ul reagent 2

    pick_up(pip50)

    for row in bp1:
        pip50.transfer(20, reagent2, row, new_tip='never')

    pip50.drop_tip()

    # transfer 30ul of sample to reagent 1

    for row in cp:
        pick_up(pip300)
        pip300.transfer(30, sample, row, new_tip='never')
        pip300.drop_tip()

    # transfer 5ul of sample to reagnet 2

    for src, dest in zip(cp, bp1):
        pick_up(pip50)
        pip50.transfer(5, src, dest, new_tip='never')
        pip50.drop_tip()

    # transfer 20uL mastermix

    pick_up(pip50)

    for row in bp2:
        pip50.transfer(20, mm, row, new_tip='never')

    pip50.transfer(20, mm, biop2.wells('A12'), new_tip='never')

    pip50.drop_tip()

    # tranfer 5uL of samples+reagents to mastermix

    for src, dest in zip(bp1, bp2):
        pick_up(pip50)
        pip50.transfer(5, src, dest, new_tip='never')
        pip50.drop_tip()

    protocol.comment('Congratulations. Protocol is now complete.')

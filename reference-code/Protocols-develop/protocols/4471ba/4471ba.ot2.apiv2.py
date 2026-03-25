metadata = {
    'protocolName': 'Custom Plate Filling (Flipped)',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [mnt, vol, cols] = get_values(  # noqa: F821
        'mnt', 'vol', 'cols')

    # load labware and pipettes
    p300 = protocol.load_instrument('p300_multi_gen2', mount=mnt)
    tips = protocol.load_labware('opentrons_300ul_tiprack_flipped', '4')
    res = protocol.load_labware('beckmancoulter_8_reservoir_19000ul', '10')

    plate1, plate2 = [
        protocol.load_labware(
            'simport_96_wellplate_flipped', s) for s in ['8', '2']
            ]

    # Create variable lists based on number of columns
    reagent = res.wells()[:cols]
    tip_list = [[tips[j+'1'], tips[j+'5']] for j in 'ABCDEFGH'][:cols]
    well_list = [
        [plate1[j+'1'], plate2[j+'1'],
         plate1[j+'5'], plate2[j+'5']] for j in 'ABCDEFGH'][:cols]

    for re, tip, wells in zip(reagent, tip_list, well_list):
        p300.pick_up_tip(tip[0])
        for well in wells[:2]:
            p300.aspirate(vol, re)
            p300.dispense(vol, well)
        p300.drop_tip()
        p300.pick_up_tip(tip[1])
        for well in wells[2:]:
            p300.aspirate(vol, re)
            p300.dispense(vol, well)
        p300.drop_tip()

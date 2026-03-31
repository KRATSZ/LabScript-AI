metadata = {
    'protocolName': 'Ethanol Transfer',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p300mnt, p20mnt] = get_values(  # noqa: F821
        'p300mnt', 'p20mnt')

    # load labware and pipettes
    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', '3')]
    p20 = protocol.load_instrument('p20_multi_gen2', p20mnt, tip_racks=tips20)
    p300 = protocol.load_instrument('p300_multi_gen2', p300mnt)

    magdeck = protocol.load_module('magdeck', '4')
    magplate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    magrows = magplate.rows()[0]

    res = protocol.load_labware('usascientific_12_reservoir_22ml', '1')
    tips1 = protocol.load_labware('opentrons_96_tiprack_300ul', '7').rows()[0]
    tips2 = protocol.load_labware('opentrons_96_tiprack_300ul', '10').rows()[0]

    p300.flow_rate.aspirate = 100
    p300.flow_rate.dispense = 150
    p20.flow_rate.dispense = 50

    magdeck.engage()

    # Ethanol addition and removal
    def ethanol_wash(src1, src2, tips, waste):
        src = [res.wells()[src1] for _ in range(6)]
        src += [res.wells()[src2] for _ in range(6)]
        for tip, s, well in zip(tips, src, magrows):
            p300.pick_up_tip(tip)
            p300.aspirate(150, s)
            p300.dispense(150, well)
            p300.return_tip()

        protocol.comment('Incubating for 30 seconds')
        protocol.delay(seconds=30)

        p300.flow_rate.aspirate = 50
        for tip, well in zip(tips, magrows):
            p300.pick_up_tip(tip)
            p300.aspirate(150, well)
            p300.dispense(150, res.wells()[waste].top())
            p300.drop_tip()
        p300.flow_rate.aspirate = 100

    ethanol_wash(0, 1, tips1, 9)

    ethanol_wash(2, 3, tips2, 10)

    for well in magrows:
        p20.pick_up_tip()
        p20.aspirate(15, well.bottom(0.2))
        p20.dispense(15, res.wells()[11].top())
        p20.drop_tip()

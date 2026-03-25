metadata = {
    'protocolName': 'Ethanol Transfer with User',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p300mnt, p20mnt] = get_values(  # noqa: F821
        'p300mnt', 'p20mnt')

    # load labware and pipettes
    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', '3')]
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '6')]
    p20 = protocol.load_instrument('p20_multi_gen2', p20mnt, tip_racks=tips20)
    p300 = protocol.load_instrument(
        'p300_multi_gen2', p300mnt, tip_racks=tips300)

    magdeck = protocol.load_module('magdeck', '4')
    magplate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    magrows = magplate.rows()[0]

    res = protocol.load_labware('usascientific_12_reservoir_22ml', '1')
    waste = res['A12'].top()

    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 150
    p20.flow_rate.dispense = 50

    magdeck.engage()

    protocol.comment("Incubating on MagDeck for 5 minutes.")
    protocol.delay(minutes=5)

    protocol.comment("Removing 150uL of liquid from each well")
    for well in magrows:
        p300.pick_up_tip()
        p300.aspirate(150, well)
        p300.dispense(150, waste)
        p300.drop_tip()

    for i in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)

    protocol.pause("Remove plate and centrifuge. Click RESUME when ready")

    protocol.comment("Incubating on MagDeck for 3 minutes.")
    protocol.delay(minutes=3)

    for well in magrows:
        p20.pick_up_tip()
        p20.aspirate(15, well.bottom(0.2))
        p20.dispense(15, waste)
        p20.aspirate(15, well.bottom(0.2))
        p20.dispense(15, waste)
        p20.drop_tip()

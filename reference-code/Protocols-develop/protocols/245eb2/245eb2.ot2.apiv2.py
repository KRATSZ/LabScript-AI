import math

metadata = {
    'protocolName': 'Nucleic Acid Extraction',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p300mnt, num_samples] = get_values(  # noqa: F821
        'p300mnt', 'num_samples')

    # load labware and pipettes
    num_cols = math.ceil(num_samples/8)
    tips300 = [protocol.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['1', '2', '4', '7', '10', '11']]

    all_tips = [tr['A'+str(i)] for tr in tips300 for i in range(1, 13)]
    [tips1, tips2, tips3, tips4, tips5, tips6] = [
        all_tips[i:i+num_cols] for i in range(0, num_cols*6, num_cols)
        ]

    magdeck = protocol.load_module('magdeck', '6')
    magheight = 13.7
    magplate = magdeck.load_labware('axygen_96_wellplate_300ul')
    magsamps = magplate.rows()[0][:num_cols]
    magdeck.disengage()

    elutionplate = protocol.load_labware('axygen_96_wellplate_300ul', '3')
    elutes = elutionplate.rows()[0][:num_cols]

    res = protocol.load_labware('nest_12_reservoir_15ml', '5')
    beads = res['A8']
    etoh1 = [w for w in [res['A6'], res['A5']] for _ in range(6)][:num_cols]
    etoh2 = [w for w in [res['A4'], res['A3']] for _ in range(6)][:num_cols]
    ebuff = res['A1']

    waste = protocol.load_labware('nest_1_reservoir_195ml', '9',
                                  'Liquid Waste').wells()[0].top()

    p300 = protocol.load_instrument('p300_multi_gen2', p300mnt)

    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 150
    p300.flow_rate.blow_out = 300

    # Add 20uL of beads and mix
    protocol.comment('Adding 20ul of magbeads to samples...')
    for well, tip in zip(magsamps, tips1):
        p300.pick_up_tip(tip)
        p300.aspirate(20, beads)
        p300.dispense(20, well)
        p300.mix(10, 30, well)
        p300.blow_out()
        p300.drop_tip()

    protocol.comment('Incubating for 5 minutes (no magnet)...')
    protocol.delay(minutes=5)

    magdeck.engage(height=magheight)

    protocol.comment('Incubating for 3 minutes (mag engaged)...')
    protocol.delay(minutes=3)

    p300.flow_rate.aspirate = 20
    protocol.comment('Removing supernatant...')
    for well, tip in zip(magsamps, tips2):
        p300.pick_up_tip(tip)
        p300.aspirate(60, well)
        p300.dispense(60, waste)
        p300.drop_tip()

    def eth_wash(tiprack, reagent):
        """This function will add ethanol, wait, then remove it"""
        p300.flow_rate.aspirate = 100
        p300.flow_rate.dispense = 50

        p300.pick_up_tip(tiprack[0])

        for well, etoh in zip(magsamps, reagent):
            p300.aspirate(150, etoh)
            p300.dispense(150, well.top(-5))
            p300.blow_out(well.top(-5))

        protocol.comment('Incubating for 1 minute (mag engaged)...')
        protocol.delay(minutes=1)

        p300.flow_rate.aspirate = 20
        p300.flow_rate.dispense = 150
        protocol.comment('Removing supernatant...')
        for well, tip in zip(magsamps, tiprack):
            if not p300.hw_pipette['has_tip']:
                p300.pick_up_tip(tip)
            p300.aspirate(150, well)
            p300.dispense(150, waste)
            p300.drop_tip()

    protocol.comment('Beginning ethanol wash 1...')
    eth_wash(tips3, etoh1)

    protocol.comment('Beginning ethanol wash 2...')
    eth_wash(tips4, etoh2)

    protocol.comment('Air drying for 5 minutes...')
    protocol.delay(minutes=5)

    magdeck.disengage()
    p300.flow_rate.aspirate = 50
    protocol.comment('Adding elution buffer...')
    for well, tip in zip(magsamps, tips5):
        p300.pick_up_tip(tip)
        p300.aspirate(50, ebuff)
        p300.dispense(50, well)
        p300.mix(10, 40, well)
        p300.blow_out()
        p300.drop_tip()

    magdeck.engage(height=magheight)
    protocol.comment('Incubating for 5 minutes (mag engaged)...')
    protocol.delay(minutes=5)

    p300.flow_rate.aspirate = 20
    p300.flow_rate.dispense = 50

    for src, dest, tip in zip(magsamps, elutes, tips6):
        p300.pick_up_tip(tip)
        p300.aspirate(50, src)
        p300.dispense(50, dest)
        p300.blow_out()
        p300.drop_tip()

    magdeck.disengage()
    protocol.comment('Protocol complete!')

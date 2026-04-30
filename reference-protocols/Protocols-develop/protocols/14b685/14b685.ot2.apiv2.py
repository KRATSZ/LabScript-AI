import math

metadata = {
    'protocolName': 'PCR Clean-Up for Illumina 16S',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [p300mnt, p20mnt, mag_mod, num_samples, s_vol] = get_values(  # noqa: F821
        'p300mnt', 'p20mnt', 'mag_mod', 'num_samples', 's_vol')

    # load labware and pipette
    magDeck = protocol.load_module(mag_mod, '10')
    magPlate = magDeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    res = protocol.load_labware('nest_12_reservoir_15ml', '7')

    end = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '1')

    tips20 = [protocol.load_labware('opentrons_96_filtertiprack_20ul', '4')]

    all_tips = [
        protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', s).rows()[0] for s in [
                '8', '9', '5', '6', '2', '3']
                ]
    flat_tips = [tips for rack in all_tips for tips in rack]

    m20 = protocol.load_instrument('p20_multi_gen2', p20mnt, tip_racks=tips20)
    m300 = protocol.load_instrument('p300_multi_gen2', p300mnt)

    # variable declarations
    waste = protocol.load_labware('nest_1_reservoir_195ml', '11')['A1']
    num_cols = math.ceil(num_samples/8)
    tips1, tips2, tips3, tips4, tips5, tips6 = [
        flat_tips[i:i+num_cols] for i in range(0, num_cols*6, num_cols)
        ]
    magSamps = magPlate.rows()[0][:num_cols]
    elutes = end.rows()[0][:num_cols]
    beads = res['A1']
    etoh1 = [res['A2']]*6+[res['A3']]*6
    etoh2 = [res['A4']]*6+[res['A5']]*6
    tris = res['A6']

    m300.flow_rate.aspirate = 100
    m300.flow_rate.dispense = 100
    m300.flow_rate.blow_out = 200

    def supernatant(vol, tips, utips, rtips=False):
        m300.flow_rate.aspirate = 50
        for well, tip, utip in zip(magSamps, tips, utips):
            m300.pick_up_tip(tip)
            m300.aspirate(vol, well)
            m300.dispense(vol, waste)
            m300.blow_out()
            if rtips:
                m300.drop_tip(utip)
            else:
                m300.drop_tip()
        m300.flow_rate.aspirate = 100

    magDeck.disengage()

    init_vol = 20 + s_vol
    # Add 20uL of beads
    protocol.comment('Adding 20uL of beads to wells...')
    for well, tip in zip(magSamps, tips1):
        m300.pick_up_tip(tip)
        m300.aspirate(20, beads)
        m300.dispense(20, well)
        m300.mix(10, init_vol)
        m300.blow_out()
        m300.drop_tip()

    protocol.comment('Incubating at room temp for 5 minutes...')
    protocol.delay(minutes=5)
    magDeck.engage()
    protocol.comment('Incubating for 2 minutes with MagDeck engaged...')
    protocol.delay(minutes=2)

    protocol.comment('Removing supernatant...')
    supernatant(init_vol, tips2, tips1)
    magDeck.disengage()

    # Ethanol Wash 1
    protocol.comment('Adding 195uL ethanol for wash 1...')
    for well, etoh, tip, utip in zip(magSamps, etoh1, tips3, tips2):
        m300.pick_up_tip(tip)
        m300.aspirate(195, etoh)
        m300.dispense(195, well)
        m300.blow_out()
        m300.drop_tip(utip)

    magDeck.engage()
    protocol.delay(seconds=30)

    protocol.comment('Removing supernatant...')
    supernatant(195, tips2, tips1, True)
    magDeck.disengage()

    # Ethanol Wash 2
    protocol.comment('Adding 195uL ethanol for wash 2...')
    for well, etoh, tip, utip in zip(magSamps, etoh2, tips4, tips3):
        m300.pick_up_tip(tip)
        m300.aspirate(195, etoh)
        m300.dispense(195, well)
        m300.blow_out()
        m300.drop_tip(utip)

    magDeck.engage()
    protocol.delay(seconds=30)

    protocol.comment('Removing supernatant...')
    supernatant(195, tips3, tips2, True)

    # Removing any excess ethanol with P20-Multi
    m20.transfer(20, magSamps, waste, new_tip='always')
    magDeck.disengage()

    protocol.comment('Air drying for 10 minutes...')
    protocol.delay(minutes=10)

    protocol.comment('Adding Tris/water to samples...')
    for well, tip, utip in zip(magSamps, tips5, tips3):
        m300.pick_up_tip(tip)
        m300.aspirate(30, tris)
        m300.dispense(30, well)
        m300.mix(5, 30)
        m300.blow_out()
        m300.drop_tip(utip)

    protocol.comment('Incubating for 2 minutes...')
    protocol.delay(minutes=2)
    magDeck.engage()
    protocol.comment('Incubating for 2 minutes with MagDeck engaged...')
    protocol.delay(minutes=2)

    m300.flow_rate.aspirate = 25
    protocol.comment('Transferring elutes to clean PCR plate in slot 1...')
    for src, dest, tip, utip in zip(magSamps, elutes, tips6, tips4):
        m300.pick_up_tip(tip)
        m300.aspirate(25, src)
        m300.dispense(25, dest)
        m300.blow_out()
        m300.drop_tip(utip)

    protocol.comment('Protocol complete!')

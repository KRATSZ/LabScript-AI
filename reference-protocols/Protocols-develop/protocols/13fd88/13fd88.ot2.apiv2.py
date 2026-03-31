from opentrons import types

metadata = {
    'protocolName': 'Protein Purification with Magnetic NI Resin',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):

    # load labware and pipettes
    tips = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', str(s)) for s in [10, 11, 8, 9]]

    m300 = protocol.load_instrument('p300_multi_gen2', 'left')

    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '1')
    bper = reservoir['A1']
    resin = reservoir['A3']
    wb1 = reservoir['A5']
    wb2 = reservoir['A7']
    e_buffer = reservoir['A9']

    plates = [
        protocol.load_labware(
            'greiner_96_wellplate',
            str(slot)) for slot in [5, 6, 2]]

    [plate1, plate2, plate3] = [plate.rows()[0] for plate in plates]

    magdeck = protocol.load_module('magnetic module gen2', '7')
    magplate = magdeck.load_labware('greiner_96_wellplate')
    magwells = magplate.rows()[0]

    deepplate = protocol.load_labware('nest_96_wellplate_2ml_deep', '4')
    deepwells = deepplate.rows()[0]

    e_plate = protocol.load_labware('chromtech_96_filter_wellplate', '3')
    elutes = e_plate.rows()[0]

    [tips1, tips2, tips3, tips4] = [rack.rows()[0] for rack in tips]

    m300.flow_rate.aspirate = 100
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 200

    magheight = 20

    # Adding 100uL of B-PER lysis buffer to deep well plate
    protocol.comment("Adding 100uL of B-PER lysis buffer to deep well plate")

    for well, tip in zip(deepwells, tips1):
        m300.pick_up_tip(tip)
        m300.aspirate(100, bper)
        m300.air_gap(20)
        m300.dispense(120, well)
        m300.mix(10, 150, well)
        m300.blow_out()
        m300.drop_tip()

    protocol.comment("Incubating for 15 minutes...")
    protocol.delay(minutes=15)
    for i in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)

    pmsg = "Please remove deepwell plate and centrifuge. When done, \
    replace on deck and click RESUME"
    protocol.pause(pmsg)

    # Transfer 95uL cell lysate to magplate
    protocol.comment("Transferring 95uL cell lysate to magdeck")
    for src, dest, tip in zip(deepwells, magwells, tips2):
        m300.pick_up_tip(tip)
        m300.aspirate(95, src.bottom(3))
        m300.air_gap(20)
        m300.dispense(115, dest)
        m300.blow_out()
        m300.drop_tip()

    # Adding 20uL of magnetic resin
    protocol.comment("Adding 20uL of magnetic NI resin to each well")
    for dest, tsrc, tdest in zip(magwells, tips3, tips1):
        m300.pick_up_tip(tsrc)
        m300.mix(5, 20, resin)
        m300.aspirate(20, resin)
        m300.dispense(20, dest)
        m300.mix(5, 110, dest)
        m300.blow_out()
        m300.drop_tip(tdest)

    for i in range(1, 6):
        protocol.comment("Mixing %d of 5 times..." % i)
        for well, tip in zip(magwells, tips1):
            m300.pick_up_tip(tip)
            m300.mix(5, 110, well)
            m300.blow_out()
            m300.return_tip()

    protocol.comment("Engaging magdeck for 3 minutes.")
    magdeck.engage(height=magheight)
    protocol.delay(minutes=3)

    def super_removal(vol, d_plate, tips):
        m300.flow_rate.aspirate = 30
        for idx, (src, dest, tip) in enumerate(zip(magwells, d_plate, tips)):
            side = -1 if idx % 2 == 0 else 1
            m300.pick_up_tip(tip)
            m300.aspirate(
                vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            m300.air_gap(20)
            m300.dispense(vol+20, dest)
            m300.drop_tip()
        m300.flow_rate.aspirate = 100

    protocol.comment("Transferring 120uL of Supernatant to plate 2 (slot 5)")

    super_removal(120, plate1, tips1)

    protocol.comment("Adding 100uL of Wash Buffer")
    magdeck.disengage()

    for well, tsrc, tdest in zip(magwells, tips4, tips2):
        m300.pick_up_tip(tsrc)
        m300.aspirate(100, wb1)
        m300.air_gap(20)
        m300.dispense(120, well)
        m300.mix(3, 90, well)
        m300.blow_out()
        m300.drop_tip(tdest)

    magdeck.engage(height=magheight)

    for i in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)

    protocol.pause("Please add tips to slots 8/9; plates to remaining slots")

    protocol.comment("Transferring 100uL of Supernatant to plate 3 (slot 6)")
    super_removal(100, plate2, tips2)

    protocol.comment("Adding 100uL of Wash Buffer")
    magdeck.disengage()

    for well, tsrc, tdest in zip(magwells, tips3, tips2):
        m300.pick_up_tip(tsrc)
        m300.aspirate(100, wb2)
        m300.air_gap(20)
        m300.dispense(120, well)
        m300.mix(3, 90, well)
        m300.blow_out()
        m300.drop_tip(tdest)

    protocol.comment("Engaging magdeck for 3 minutes.")
    magdeck.engage(height=magheight)
    protocol.delay(minutes=3)

    protocol.comment("Transferring 100uL of Supernatant to plate 4 (slot 2)")
    super_removal(100, plate3, tips2)

    magdeck.disengage()
    protocol.comment("Adding 50uL of Elution Buffer")

    for well, tsrc, tdest in zip(magwells, tips4, tips3):
        m300.pick_up_tip(tsrc)
        m300.aspirate(50, e_buffer)
        m300.air_gap(20)
        m300.dispense(70, well)
        m300.mix(5, 45, well)
        m300.blow_out()
        m300.drop_tip(tdest)

    protocol.comment("Engaging magdeck for 3 minutes.")
    magdeck.engage(height=magheight)
    protocol.delay(minutes=3)

    protocol.comment("Transferring 50uL of elution to filter plate")
    super_removal(50, elutes, tips3)

    protocol.comment("Protocol complete!")

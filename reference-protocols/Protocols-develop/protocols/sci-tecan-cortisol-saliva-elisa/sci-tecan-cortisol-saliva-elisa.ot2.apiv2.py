from opentrons.types import Point

metadata = {
    'protocolName': 'Tecan Cortisol ELISA w/ Heater Shaker',
    'author': 'Boren Lin',
    'description': '',
    'apiLevel': '2.13'
}

NUM_STRIPS = 12

VOL_SAMPLE = 50
VOL_ENZ_POD = 100
VOL_SUB = 100
VOL_STOP = 100
VOL_WASH = 250

H = 0.2

total_cols = NUM_STRIPS


def run(ctx):

    # Load Labware, Module and Pipette
    hs_mod = ctx.load_module('heaterShakerModuleV1', 3)
    working_plate = hs_mod.load_labware('tecan_elisa_96well_hs')

    sample_plate = ctx.load_labware(
        'thermoscientific_96_wellplate_v_450', 1, 'samples')
    reagent_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', 4, 'reagents')
    wash_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', 5, 'wash')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', 9, 'waste')

    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in [7, 11, 10]]
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tiprack)

    # Locations
    eia = working_plate.rows()[0][:total_cols]
    sample = sample_plate.rows()[0][:total_cols]
    enzymePOD = reagent_plate.rows()[0][0]
    substrate = reagent_plate.rows()[0][1]
    stop = reagent_plate.rows()[0][2]
    wash = wash_plate.rows()[0][:total_cols]
    waste = waste_res.wells()[0]

    # Transfer liquid
    def transfer(vol, start, end, mix):
        # mix = 1, mix; mix = 0, dont mix
        if mix == 1:
            m300.mix(2, vol, start, rate=2)
        m300.aspirate(vol, start)
        m300.dispense(vol, end.top(z=-3).move(Point(x=-1)), rate=0.75)
        m300.blow_out()
        m300.move_to(end.top(z=2), speed=2)

    # Discard liquid
    def discard(vol, start, end):
        m300.aspirate(vol, start.bottom(z=H).move(Point(x=-2.7)), rate=0.2)
        m300.move_to(start.top(z=2), speed=2)
        m300.dispense(vol, end.top(z=-5))

    def incubation(s_speed, s_time, temp, incubation_time):

        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(s_speed)
        if temp >= 37:
            hs_mod.set_and_wait_for_temperature(temp)
        ctx.delay(minutes=s_time)
        hs_mod.deactivate_shaker()
        ctx.delay(minutes=incubation_time-s_time)
        hs_mod.deactivate_heater()

    # protocol
    hs_mod.open_labware_latch()
    ctx.pause('Move the ELISA Plate to the Shaker')
    hs_mod.close_labware_latch()

    # Sample + Enzyme POD incubation
    for i in range(total_cols):
        m300.pick_up_tip()
        transfer(VOL_SAMPLE, sample[i], eia[i], 1)
        m300.drop_tip()

    m300.pick_up_tip()
    m300.mix(2, VOL_ENZ_POD, enzymePOD, rate=2)
    for i in range(total_cols):
        transfer(VOL_ENZ_POD, enzymePOD, eia[i], 0)
    m300.drop_tip()

    incubation(500, 120, 25, 120)

    m300.pick_up_tip()
    supernatant = VOL_SAMPLE+VOL_ENZ_POD
    for j in range(total_cols):
        discard(supernatant*1.1, eia[j], waste)
        m300.blow_out()
    m300.drop_tip()

    # Washing x4
    for _ in range(4):
        m300.pick_up_tip()
        for i in range(total_cols):
            transfer(VOL_WASH, wash[i], eia[i], 0)
        for j in range(total_cols):
            discard(VOL_WASH*1.1, eia[j], waste)
            m300.blow_out()
        m300.drop_tip()

    # Substrate incubation
    m300.pick_up_tip()
    m300.mix(2, VOL_SUB, substrate, rate=2)
    for i in range(total_cols):
        transfer(VOL_SUB, substrate, eia[i], 0)
    m300.drop_tip()

    incubation(500, 30, 25, 30)

    # Reaction stop
    m300.pick_up_tip()
    m300.mix(2, VOL_STOP, stop, rate=2)
    for i in range(total_cols):
        transfer(VOL_STOP, stop, eia[i], 0)
    m300.drop_tip()

    hs_mod.open_labware_latch()
    ctx.pause('Move the ELISA Plate to the Reader')

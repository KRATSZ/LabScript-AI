from opentrons.types import Point

metadata = {
    'protocolName': 'bead-based ELISA',
    'author': 'Boren Lin',
    'source': '',
    'apiLevel': '2.13'
}

########################

COL_SAMPLES = 12

ASP_HEIGHT = 0.2
LENGTH_FROM_CENTER = 2
MAG_HEIGHT = 4.2

SAMPLE_VOL = 100
BEAD_VOL = 20
AB_HRP_VOL = 100
SUBSTRATE_VOL = 100
STOP_VOL = 50
FINAL_VOL = 100

WASH_VOL = 250
WASH_TIMES = 3

SHAKING_SPEEND = 1000
INCUBATION_TIME = 60

#########################


def run(ctx):

    # load labware

    hs_mod = ctx.load_module('heaterShakerModuleV1', 1)
    mag_mod = ctx.load_module('magnetic module gen2', 9)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    reagent_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', 11, 'reagents')
    wash1_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', 5, 'wash')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', 6, 'waste')
    final_plate = ctx.load_labware(
        'corning_96_wellplate_360ul_flat', 7, 'final')
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', 10)
    tiprack_final = ctx.load_labware(
        'opentrons_96_tiprack_300ul', 4, 'tips for final transfer')
    tiprack_reuse = ctx.load_labware(
        'opentrons_96_tiprack_300ul', 3, 'tips for reuse')
    pip = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack])

    # liquids

    beads = reagent_plate.rows()[0][0]
    ab_HRP = reagent_plate.rows()[0][1]
    substrate = reagent_plate.rows()[0][2]
    stop = reagent_plate.rows()[0][3]
    wash1 = wash1_plate.rows()[0][:COL_SAMPLES]
    waste = waste_res.wells()[0]
    working_cols = mag_plate.rows()[0][:COL_SAMPLES]
    final_cols = final_plate.rows()[0][:COL_SAMPLES]

    def transfer_reagent(vol, source):

        hs_mod.close_labware_latch()

        pip.pick_up_tip()
        for i in range(COL_SAMPLES):
            position = working_cols[i]
            if i == 0:
                pip.mix(10, vol, source.bottom(z=2), rate=3)
            pip.mix(2, vol, source.bottom(z=1))
            pip.aspirate(vol, source.bottom(z=0.5))
            pip.air_gap(10)
            pip.dispense(vol+10, position.top(z=-5), rate=3)
            pip.blow_out()
            pip.touch_tip()
        pip.drop_tip()

    def incubation(speed, time):

        hs_mod.close_labware_latch()

        hs_mod.set_and_wait_for_shake_speed(speed)
        ctx.delay(minutes=time)
        hs_mod.deactivate_shaker()

    def washing(discard_vol, wash_vol, wash_rev, times):

        hs_mod.close_labware_latch()

        # discard supernatant
        mag_mod.engage(height_from_base=MAG_HEIGHT)
        ctx.delay(minutes=2)

        x = 0
        for i in range(COL_SAMPLES):
            pip.pick_up_tip(tiprack_reuse.well(x))
            side = -1 if i % 2 == 0 else 1
            aspirate_loc = working_cols[i].bottom(z=ASP_HEIGHT).move(
                            Point(x=LENGTH_FROM_CENTER*side))
            pip.aspirate(discard_vol*1.1, aspirate_loc, rate=0.5)
            pip.dispense(discard_vol*1.1, waste.top(z=-5))
            pip.blow_out()
            pip.return_tip()
            x = x + 8

        mag_mod.disengage()

        # add, mix and remove wash buffer
        for j in range(times):
            pip.pick_up_tip()
            for k in range(COL_SAMPLES):
                position = working_cols[k]
                pip.aspirate(wash_vol, wash_rev[k])
                pip.dispense(wash_vol, position.top(z=-2))
                pip.touch_tip()
            pip.drop_tip()

            y = 0
            for m in range(COL_SAMPLES):
                position = working_cols[m]
                pip.pick_up_tip(tiprack_reuse.well(y))
                pip.mix(10, wash_vol*0.75, position.bottom(z=1), rate=3)
                pip.return_tip()
                y = y + 8

            mag_mod.engage(height_from_base=MAG_HEIGHT)
            ctx.delay(minutes=2)

            z = 0
            for n in range(COL_SAMPLES):
                pip.pick_up_tip(tiprack_reuse.well(z))
                side = -1 if n % 2 == 0 else 1
                aspirate_loc = working_cols[n].bottom(z=ASP_HEIGHT).move(
                                Point(x=LENGTH_FROM_CENTER*side))
                pip.aspirate(wash_vol*1.1, aspirate_loc, rate=0.5)
                pip.dispense(wash_vol*1.1, waste.top(z=-5))
                pip.blow_out()
                pip.return_tip()
                z = z + 8

            mag_mod.disengage()

    # protocol

    ctx.comment('\n\n\n~~~~~~~~Target Capture~~~~~~~~\n')
    ctx.pause('Load the Plate onto the Magnet')
    transfer_reagent(BEAD_VOL, beads)
    hs_mod.open_labware_latch()
    ctx.pause('Move the Plate to the Shaker')
    incubation(SHAKING_SPEEND, INCUBATION_TIME)
    hs_mod.open_labware_latch()
    ctx.pause('Move the Plate to the Magnet')
    washing(SAMPLE_VOL+BEAD_VOL, WASH_VOL, wash1, WASH_TIMES)

    ctx.comment('\n\n\n~~~~~~~~Detection Ab Binding~~~~~~~~\n')
    transfer_reagent(AB_HRP_VOL, ab_HRP)

    p = 0
    for pp in range(COL_SAMPLES):
        position = working_cols[pp]
        pip.pick_up_tip(tiprack_reuse.well(p))
        pip.mix(5, AB_HRP_VOL*0.75, position.bottom(z=1), rate=3)
        pip.return_tip()
        p = p + 8

    hs_mod.open_labware_latch()
    ctx.pause('Move the Plate to the Shaker')
    incubation(SHAKING_SPEEND, INCUBATION_TIME)
    hs_mod.open_labware_latch()
    ctx.pause('Move the Plate to the Magnet')
    washing(AB_HRP_VOL, WASH_VOL, wash1, WASH_TIMES)

    ctx.comment('\n\n\n~~~~~~~~Signal Development~~~~~~~~\n')
    transfer_reagent(SUBSTRATE_VOL, substrate)

    q = 0
    for qq in range(COL_SAMPLES):
        position = working_cols[qq]
        pip.pick_up_tip(tiprack_reuse.well(q))
        pip.mix(5, SUBSTRATE_VOL*0.75, position.bottom(z=1), rate=3)
        pip.return_tip()
        q = q + 8

    hs_mod.open_labware_latch()
    ctx.pause('Move the Plate to the Shaker')
    incubation(SHAKING_SPEEND, 5)
    hs_mod.open_labware_latch()
    ctx.pause('Move the Plate to the Magnet')
    transfer_reagent(STOP_VOL, stop)

    mag_mod.engage(height_from_base=MAG_HEIGHT)
    ctx.delay(minutes=2)

    a = 0
    for aa in range(COL_SAMPLES):
        pip.pick_up_tip(tiprack_final.well(a))
        side = -1 if aa % 2 == 0 else 1
        aspirate_loc = working_cols[aa].bottom(z=2).move(
                        Point(x=LENGTH_FROM_CENTER*side))
        position = final_cols[aa]
        pip.aspirate(FINAL_VOL, aspirate_loc, rate=2)
        pip.dispense(FINAL_VOL, position.top(z=-2), rate=2)
        pip.drop_tip()
        a = a + 8

    mag_mod.disengage()

    ctx.pause('Ready for OD measurement')

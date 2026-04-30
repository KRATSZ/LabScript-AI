import math
from opentrons import types

metadata = {
    "protocolName": "Tagmentation and Bead Cleanup",
    "author": "Rami Farawi <rami.farawi@opentrons.com>",
    "source": "Custom Protocol Request",
    "apiLevel": "2.13"
}


def run(ctx):

    [num_samp, barcode_sample_plate, water_vol,
        barcode_vol, temp_mod_temp,
        p300_mount, m20_mount] = get_values(  # noqa: F821
        "num_samp", "barcode_sample_plate",
        "water_vol", "barcode_vol", "temp_mod_temp", "p300_mount",
        "m20_mount")

    num_samp = int(num_samp)

    if barcode_sample_plate == "fisher_96_wellplate_200ul":
        temp_mod_plate = "fisher_96_aluminumblock_200ul"

    elif barcode_sample_plate == "bulldog_96_wellplate_200ul":
        temp_mod_plate = "bulldog_96_aluminumblock_200ul"

    else:
        temp_mod_plate = "opentrons_96_aluminumblock_biorad_wellplate_200ul"

    # labware
    mag_mod = ctx.load_module("magnetic module gen2", 4)
    mag_plate = mag_mod.load_labware("nest_96_wellplate_2ml_deep")
    temp_mod = ctx.load_module("temperature module gen2", 6)
    res = ctx.load_labware("nest_12_reservoir_15ml", 2)
    sample_plate = ctx.load_labware(barcode_sample_plate, 3)
    dest_plate = temp_mod.load_labware(temp_mod_plate, 6)
    barcode_plate = ctx.load_labware(barcode_sample_plate, 1)
    reag_rack = ctx.load_labware("opentrons_24_aluminumblock_nest_2ml_snapcap", 5)  # noqa: E501

    tips300 = [ctx.load_labware("opentrons_96_filtertiprack_200ul", slot)
               for slot in [8]]
    tips20 = [ctx.load_labware("opentrons_96_tiprack_20ul", slot)
              for slot in [9, 10, 11]]

    # pipettes
    m20 = ctx.load_instrument("p20_multi_gen2", m20_mount, tip_racks=tips20)
    p300 = ctx.load_instrument("p300_single_gen2", p300_mount,
                               tip_racks=tips300)

    p300.flow_rate.blow_out = 0.33*p300.flow_rate.blow_out
    m20.flow_rate.blow_out = 0.33*m20.flow_rate.blow_out

    # functions
    # apply speed limit to departing tip
    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == "right":
            axis = "A"
        else:
            axis = "Z"
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    def resuspend_pellet(well, pip, mvol, reps=5):
        """
        "resuspend_pellet" will forcefully dispense liquid over the pellet
        after the magdeck engage in order to more thoroughly resuspend the
        pellet. param well: The current well that the resuspension will occur
        in. param pip: The pipet that is currently attached/ being used.
        param mvol: The volume that is transferred before the mixing steps.
        param reps: The number of mix repetitions that should occur. Note~
        During each mix rep, there are 2 cycles of aspirating from center,
        dispensing at the top and 2 cycles of aspirating from center,
        dispensing at the bottom (5 mixes total)
        """

        rightLeft = int(str(well).split(" ")[0][1:]) % 2
        """
        "rightLeft" will determine which value to use in the list of "top" and
        "bottom" (below), based on the column of the "well" used.
        In the case that an Even column is used, the first value of "top" and
        "bottom" will be used, otherwise, the second value of each will be
        used.
        """
        center = well.bottom().move(types.Point(x=0, y=0, z=0.8))
        top = [
            well.bottom().move(types.Point(x=-1, y=1, z=0.4)),
            well.bottom().move(types.Point(x=1, y=1, z=0.4))
        ]
        bottom = [
            well.bottom().move(types.Point(x=-1, y=0, z=0.4)),
            well.bottom().move(types.Point(x=1, y=0, z=0.4))
        ]

        pip.flow_rate.dispense = 500
        pip.flow_rate.aspirate = 150

        mix_vol = 200

        pip.move_to(center)
        for _ in range(reps):
            for _ in range(2):
                pip.aspirate(mix_vol, center)
                pip.dispense(mix_vol, top[rightLeft])
            for _ in range(2):
                pip.aspirate(mix_vol, center)
                pip.dispense(mix_vol, bottom[rightLeft])

    # mapping
    num_col = math.ceil(num_samp/8)
    dna_vol = 9 - water_vol
    # ethanol = reservoir.wells()[0]
    water = res.wells()[0]
    dest_cols = dest_plate.rows()[0][:num_col]
    dna_samples = sample_plate.rows()[0][:num_col]
    barcode_wells = barcode_plate.rows()[0][:num_col]
    pool_wells = [mag_plate.wells()[0], mag_plate.wells()[1]]
    bead_vol = 10*num_samp/2
    beads = reag_rack.wells()[0]
    trash = res.wells()[-1].top(z=-5)
    ethanol = res.wells()[1]

    # protocol
    ctx.comment("\n---------------ADDING WATER----------------\n\n")
    m20.pick_up_tip()
    for col in dest_cols:
        m20.aspirate(water_vol, water)
        m20.dispense(water_vol, col)
    m20.drop_tip()

    ctx.comment("\n---------------ADDING BARCODE----------------\n\n")
    # CHANGE MIX ########################################################

    for s, d in zip(barcode_wells, dest_cols):
        m20.pick_up_tip()

        m20.aspirate(barcode_vol, s.bottom(z=0.8), rate=0.1)
        # slow_tip_withdrawal(m20, d)
        m20.dispense(barcode_vol, d)
        m20.mix(7, 4, d)
        m20.move_to(d.bottom(z=5))
        ctx.delay(2)
        m20.blow_out(d.bottom(z=5))

        m20.drop_tip()
    #
    ctx.comment("\n---------------ADDING DNA----------------\n\n")

    for s, d in zip(dna_samples, dest_cols):
        m20.pick_up_tip()
        m20.aspirate(dna_vol, s.bottom(z=0.8))
        m20.dispense(dna_vol, d)
        m20.mix(3, 5, d)
        slow_tip_withdrawal(m20, d)
        ctx.delay(seconds=2)
        m20.blow_out(d.top())
        m20.touch_tip()
        m20.drop_tip()

    ctx.pause("Move plate to thermocycler then bring back on slot 6.")

    ctx.comment("\n---------------POOLING INTO COL----------------\n\n")
    pool_col = mag_plate.rows()[0][0]
    m20.pick_up_tip()  # do we change tip here or keep tip
    for col in dest_cols:
        m20.aspirate(11, col.bottom(z=0.5))
        m20.dispense(11, pool_col)
    m20.drop_tip()

    ctx.comment("\n---------------POOLING INTO WELLS----------------\n\n")
    p300.pick_up_tip()
    for well in mag_plate.columns()[0][2:5]:

        p300.aspirate(10*num_col+5, well.bottom(z=0.3), rate=1.2)
        p300.dispense(10*num_col+5, pool_wells[0])
        p300.mix(1, 0.8*10*num_col, pool_wells[0])
        p300.blow_out(pool_wells[0].bottom(7))

    for well in mag_plate.columns()[0][5:]:

        p300.aspirate(10*num_col+5, well.bottom(z=0.3), rate=1.2)
        p300.dispense(10*num_col+5, pool_wells[1])
        p300.mix(1, 0.8*10*num_col, pool_wells[1])
        p300.blow_out(pool_wells[1].bottom(7))
    p300.drop_tip()

    ctx.comment("\n---------------ADDING BEADS----------------\n\n")
    p300.pick_up_tip()
    p300.mix(15, 200, beads, rate=1.5)
    ctx.comment("\n")
    for i, pool_well in enumerate(pool_wells):
        if not p300.has_tip:
            p300.pick_up_tip()
        num_transfers = math.floor(bead_vol / 200)
        leftover_vol = bead_vol % 200
        for _ in range(num_transfers):
            p300.aspirate(200, beads, rate=0.6)
            slow_tip_withdrawal(p300, beads)
            p300.dispense(200, pool_well)

        p300.aspirate(leftover_vol, beads, rate=0.1)
        p300.dispense(leftover_vol, pool_well)
        resuspend_pellet(pool_well, p300, 200, reps=8)
        p300.drop_tip()
        ctx.comment("\n\n")

    ctx.delay(minutes=5)

    mag_mod.engage(offset=-1)

    ctx.delay(seconds=7*60)

    supernatant_volume = bead_vol*2
    num_transfers = math.floor(supernatant_volume / 200)
    leftover_vol = supernatant_volume % 200

    p300.pick_up_tip()
    m20.pick_up_tip()
    for pool_well in pool_wells:

        for _ in range(num_transfers):
            p300.aspirate(200, pool_well.bottom(z=0.6), rate=0.1)
            p300.dispense(200, trash)
            ctx.delay(seconds=2)
            p300.blow_out()

        p300.aspirate(leftover_vol, pool_well.bottom(z=0.6), rate=0.1)
        p300.dispense(leftover_vol, trash)

        ctx.delay(seconds=2)
        p300.blow_out()

    m20.aspirate(20, pool_wells[0].bottom(z=0.6), rate=0.1)
    ctx.delay(seconds=2)
    m20.blow_out(trash)
    m20.dispense(20, trash)
    ctx.delay(seconds=2)
    m20.blow_out(trash)
    p300.drop_tip()

    mag_mod.disengage()

    if not m20.has_tip:
        m20.pick_up_tip()

    if not p300.has_tip:
        p300.pick_up_tip()

    ctx.comment("\n---------------TWO WASHES----------------\n\n")
    for i in range(2):
        if not p300.has_tip:
            p300.pick_up_tip()
        for pool_well in pool_wells:
            for _ in range(3):
                p300.aspirate(200, ethanol)
                p300.dispense(200, pool_well.top(), rate=0.5)
                p300.move_to(pool_well.top())
                ctx.delay(seconds=4)
                p300.blow_out()
        ctx.comment("\n")

        for pool_well in pool_wells:
            resuspend_pellet(pool_well, p300, 200, reps=8)
            p300.mix(15, 200,
                     pool_well.bottom(z=1), rate=1.5)
        ctx.comment("\n")

        p300.move_to(pool_well.top())

        mag_mod.engage(offset=-1)
        ctx.delay(seconds=7*60)
        for pool_well in pool_wells:
            for _ in range(3 if i == 0 else 2):
                p300.aspirate(200, pool_well.bottom(z=0.6), rate=0.1)
                p300.dispense(200, trash)
                ctx.delay(seconds=4)
                p300.blow_out()
        if i == 0:
            m20.aspirate(20, pool_wells[0].bottom(z=0.6), rate=0.1)
            m20.dispense(20, trash)
            ctx.delay(seconds=2)
            p300.blow_out()
        mag_mod.disengage()

    mag_mod.disengage()
    resuspend_pellet(pool_wells[1], p300, 200, reps=8)
    p300.aspirate(200, pool_wells[1])
    p300.dispense(200, pool_wells[0])
    p300.mix(10, 200, pool_wells[0])
    p300.move_to(pool_wells[0].top())
    mag_mod.engage()
    ctx.delay(seconds=7*60)
    ctx.pause("Samples are all consolidated with ethanol in A1")

    for _ in range(2):
        p300.aspirate(200, pool_wells[0].bottom(z=0.6), rate=0.1)
        p300.dispense(200, trash)
        ctx.delay(seconds=4)
        p300.blow_out()

    if not m20.has_tip:
        m20.pick_up_tip()
    m20.aspirate(20, pool_wells[0].bottom(z=0.6), rate=0.1)
    m20.dispense(20, trash)
    ctx.delay(seconds=2)
    p300.blow_out()

    p300.drop_tip()
    m20.drop_tip()

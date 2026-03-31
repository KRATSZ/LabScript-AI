import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''ArcBio RNA Workflow Continuous:
    Pre-PCR Instrument: Part-2: cDNA Synthesis''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [clearance_bead_resuspension, offset_x_resuspension, count_samples,
     clearance_reservoir, height_engage, time_engage, offset_x,
     time_dry] = get_values(  # noqa: F821
      'clearance_bead_resuspension', 'offset_x_resuspension', 'count_samples',
      'clearance_reservoir', 'height_engage', 'time_engage', 'offset_x',
      'time_dry')

    ctx.set_rail_lights(True)

    if not 1 <= count_samples <= 96:
        raise Exception('Invalid sample count (must be 1-96).')

    num_cols = math.ceil(count_samples / 8)

    # helper functions

    # notify user to replenish tips
    def pick_up_or_refill(pip, vol=200):
        nonlocal tipCtr
        try:
            if vol == 200:
                pip.pick_up_tip()
            else:
                if tipCtr < len(tips300.rows()[0]):
                    pip.pick_up_tip(tips300.rows()[0][tipCtr])
                    tipCtr += 1
                else:
                    tipCtr = 0
                    ctx.pause(
                     """Please Refill the 300 uL Tip Box
                     and Empty the Tip Waste""")
                    pip.pick_up_tip(tips300.rows()[0][tipCtr])
                    tipCtr += 1
        except OutOfTipsError:
            ctx.pause(
             """Please Refill the {} Tip Boxes
             and Empty the Tip Waste""".format(pip))
            pip.reset_tipracks()
            pip.pick_up_tip()

    # set liquid volume
    def liq_volume(wells, vol):
        for well in wells:
            well.liq_vol = vol

    # return liquid height in a well
    def liq_height(well):
        if well.diameter is not None:
            radius = well.diameter / 2
            cse = math.pi*(radius**2)
        elif well.length is not None:
            cse = well.length*well.width
        else:
            cse = None
        if cse:
            return well.liq_vol / cse
        else:
            raise Exception("""Labware definition must
                supply well radius or well length and width.""")

    # tips, p20 multi, p300 multi
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [10, 11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    tips200 = [
     ctx.load_labware(
      "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [7, 8]]
    tips300 = ctx.load_labware("opentrons_96_tiprack_300ul", 9)
    tipCtr = 0
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips200)

    # reagents block for EDTA, RT Master Mix 1, RT Master Mix 2
    # blockplate is twintec 200 uL plate on block by itself(use 3 mm clearance)
    blockplate = reagents = ctx.load_labware(
     'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '2', 'Reagents')
    [edta, rt_mm1, rt_mm2] = [reagents.columns()[index] for index in [0, 1, 2]]

    # reservoir for beads and tris
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5', 'Reservoir')

    beads = reservoir.wells()[:3]
    liq_volume(beads, 9600)

    tris = reservoir.wells()[-1]

    # reservoir for 80 percent ethanol
    etoh = ctx.load_labware(
     'nest_1_reservoir_195ml', '6', '80 percent etoh').wells()[0]
    liq_volume([etoh], 96000)
    waste = ctx.load_labware(
     'nest_1_reservoir_195ml', '4', '80 percent etoh').wells()[0]

    # input samples
    temp = ctx.load_module('temperature module gen2', '3')
    sampleplate200 = temp.load_labware(
     'eppendorf_twintec_on_opentrons_metal_block_033822',
     "Sample Plate at 4 Degrees")
    temp.set_temperature(4)

    # magnetic module with 200 uL twin tec and adapter
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()
    mag_plate = mag.load_labware(
     'eppendorf_twintex_clickbio_adapter', 'Mag Plate')

    ctx.comment("STEP - EDTA")
    p20m.transfer(
     0.8, edta[0],
     [column[0] for column in sampleplate200.columns()[:num_cols]],
     mix_after=(1, 10), new_tip='always')

    ctx.comment("STEP - Transfer half volume to new 200 uL PCR plate")

    ctx.pause("""Place fresh 200 uL twin tec plate on chilled aluminum block
    in slot 2. Resume.""")

    for index, column in enumerate(sampleplate200.columns()[:num_cols]):
        p300m.pick_up_tip()
        p300m.mix(10, 65, column[0])
        p300m.aspirate(40.4, column[0])
        # blockplate clearance 3 mm due to coded labware def (block+tubestrip)
        d = blockplate.columns()[index][0]
        p300m.dispense(40.4, d.bottom(3))
        # blockplate 2mm below top use -0.5 mm due to coded labware
        p300m.move_to(
         d.top(-0.5).move(types.Point(x=d.diameter / 2, y=0, z=0)))
        ctx.delay(seconds=0.5)
        p300m.blow_out()
        p300m.move_to(d.top())
        p300m.air_gap(20)
        p300m.drop_tip()

    ctx.comment("STEP - RNA Concentration and RT setp 1")

    def beadwells():
        yield from beads

    beadwell = beadwells()
    source = next(beadwell)
    reps = math.ceil(120 / tips300.wells()[0].max_volume)

    # add beads to plate 1
    for index, column in enumerate(sampleplate200.columns()[:num_cols]):

        # repeat when volume exceeds tip capacity
        for rep in range(reps):

            pick_up_or_refill(p300m, 300)

            # switch wells and premix if volume depleted
            if source.liq_vol <= 1920:
                source = next(beadwell)
                ht_premix = liq_height(source) + 3
                for mix in range(5):
                    p300m.aspirate(
                     200, source.bottom(clearance_reservoir), rate=0.5)
                    p300m.dispense(200, source.bottom(ht_premix), rate=0.5)

            # premix beads before 1st aspiration
            if index == 0:
                ht_premix = liq_height(source) + 3
                for mix in range(5):
                    p300m.aspirate(
                     200, source.bottom(clearance_reservoir), rate=0.5)
                    p300m.dispense(200, source.bottom(ht_premix), rate=0.5)

            p300m.aspirate(
             120 / reps, source.bottom(clearance_reservoir), rate=0.5)
            ctx.delay(seconds=1)
            source.liq_vol -= (960 / reps)
            p300m.dispense(120 / reps, column[0])
            p300m.mix(10, 128, column[0].bottom(2))
            p300m.move_to(
             column[0].top(-2).move(types.Point(
              x=column[0].diameter / 2, y=0, z=0)))
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.move_to(column[0].top())
            p300m.drop_tip()

    ctx.delay(minutes=15)

    ctx.pause(
        '''Move plate1 (temperature module) to the magnetic module. Resume.''')

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage,
              msg='Move plate2 from slot 2 to the temperature module')

    # add beads to plate 2
    for index, column in enumerate(sampleplate200.columns()[:num_cols]):

        # repeat when volume exceeds tip capacity
        for rep in range(reps):

            pick_up_or_refill(p300m, 300)

            # switch wells and premix if volume depleted
            if source.liq_vol <= 1920:
                source = next(beadwell)
                ht_premix = liq_height(source) + 3
                for mix in range(5):
                    p300m.aspirate(
                     200, source.bottom(clearance_reservoir), rate=0.5)
                    p300m.dispense(200, source.bottom(ht_premix), rate=0.5)

            # premix beads before 1st aspiration
            if index == 0:
                ht_premix = liq_height(source) + 3
                for mix in range(5):
                    p300m.aspirate(
                     200, source.bottom(clearance_reservoir), rate=0.5)
                    p300m.dispense(200, source.bottom(ht_premix), rate=0.5)

            p300m.aspirate(
             120 / reps, source.bottom(clearance_reservoir), rate=0.5)
            ctx.delay(seconds=1)
            source.liq_vol -= (960 / reps)
            p300m.dispense(120 / reps, column[0])
            p300m.mix(10, 128, column[0].bottom(2))
            p300m.move_to(
             column[0].top(-2).move(types.Point(
              x=column[0].diameter / 2, y=0, z=0)))
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.move_to(column[0].top())
            p300m.drop_tip()

    ctx.delay(minutes=15)  # this delay can probably be reduced or removed

    # remove supernatant from plate 1
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)
        p300m.aspirate(200, column[0].bottom(4), rate=0.33)
        p300m.dispense(200, waste.top())
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.aspirate(
         50, column[0].bottom(1).move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x, y=0, z=0)), rate=0.33)
        p300m.dispense(70, waste.top(), rate=2)
        ctx.delay(seconds=1)
        p300m.blow_out()
        p300m.drop_tip()

    for repeat in range(2):
        # add ethanol
        pick_up_or_refill(p300m, 300)
        for column in mag_plate.columns()[:num_cols]:
            for rep in range(2):
                etoh.liq_vol -= 1600
                ht = liq_height(etoh) - 3 if liq_height(etoh) - 3 > 1 else 1
                p300m.aspirate(200, etoh.bottom(ht))
                p300m.air_gap(20)
                p300m.dispense(220, column[0].top())
                ctx.delay(seconds=0.5)
                p300m.blow_out()
        p300m.drop_tip()

        ctx.delay(seconds=30)

        # remove sup
        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m, 300)
            p300m.aspirate(200, column[0].bottom(4), rate=0.33)
            p300m.aspirate(75, column[
             0].bottom(1).move(types.Point(x={True: 1}.get(
              not index % 2, -1)*offset_x, y=0, z=0)), rate=0.33)
            p300m.air_gap(20)
            p300m.dispense(295, waste.top())
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.air_gap(20)
            p300m.drop_tip()

    # air dry plate 1 bead pellets
    ctx.delay(minutes=time_dry)

    mag.disengage()

    # resuspend bead pellet in Tris
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p20m.pick_up_tip()
        p20m.aspirate(13, tris.bottom(clearance_reservoir))
        loc = column[0].bottom(clearance_bead_resuspension).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x_resuspension, y=0, z=0))
        p20m.dispense(13, loc, rate=3)
        for rep in range(10):
            p20m.aspirate(13, column[0].bottom(1))
            p20m.dispense(13, loc, rate=3)
        p20m.drop_tip()

    ctx.delay(minutes=5)

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    ctx.pause(
     '''Place a fresh 200 uL PCR plate and pre-chilled aluminum block
     in slot 2. Resume.''')

    # transfer plate 1 eluate to fresh PCR plate in slot 2
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        p20m.aspirate(13, column[0].bottom().move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x, y=0, z=0)))
        # use 3 mm clearance for blockplate due to block+tubestrip labware def
        p20m.dispense(13, blockplate.columns()[index][0].bottom(3))
        p20m.move_to(
         blockplate.columns()[index][0].top(-2).move(types.Point(
          x=column[0].diameter / 2, y=0, z=0)))
        p20m.blow_out()
        p20m.move_to(blockplate.columns()[index][0].top(2))
        p20m.drop_tip()

    mag.disengage()

    ctx.pause(
     '''Remove plate1 (magnetic module) from the deck. Move plate2
     (temperature module) to the magnetic module. Resume.''')

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    # remove supernatant from plate 2
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)
        p300m.aspirate(200, column[0].bottom(4), rate=0.33)
        p300m.dispense(200, waste.top())
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.aspirate(
         50, column[0].bottom(1).move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x, y=0, z=0)), rate=0.33)
        p300m.dispense(70, waste.top(), rate=2)
        ctx.delay(seconds=1)
        p300m.blow_out()
        p300m.drop_tip()

    for repeat in range(2):
        # add ethanol
        pick_up_or_refill(p300m, 300)
        for column in mag_plate.columns()[:num_cols]:
            for rep in range(2):
                etoh.liq_vol -= 1600
                ht = liq_height(etoh) - 3 if liq_height(etoh) - 3 > 1 else 1
                p300m.aspirate(200, etoh.bottom(ht))
                p300m.air_gap(20)
                p300m.dispense(220, column[0].top())
                ctx.delay(seconds=0.5)
                p300m.blow_out()
        p300m.drop_tip()

        ctx.delay(seconds=30)

        # remove sup
        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m, 300)
            p300m.aspirate(200, column[0].bottom(4), rate=0.33)
            p300m.aspirate(75, column[
             0].bottom(1).move(types.Point(x={True: 1}.get(
              not index % 2, -1)*offset_x, y=0, z=0)), rate=0.33)
            p300m.air_gap(20)
            p300m.dispense(295, waste.top())
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.air_gap(20)
            p300m.drop_tip()

    # air dry plate 2 bead pellets
    ctx.delay(minutes=time_dry)

    mag.disengage()

    # resuspend bead pellet in previous eluate
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p20m.pick_up_tip()
        # use 3 mm clearance for blockplate due to block+tubestrip labware def
        p20m.aspirate(13, blockplate.columns()[index][0].bottom(3))
        loc = column[0].bottom(clearance_bead_resuspension).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x_resuspension, y=0, z=0))
        p20m.dispense(13, loc, rate=3)
        for rep in range(10):
            p20m.aspirate(13, column[0].bottom(1))
            p20m.dispense(13, loc, rate=3)
        p20m.drop_tip()

    ctx.delay(
     minutes=5, msg='''Place a fresh twin tec 200 uL PCR plate
     on the temperature module''')

    # combine RT master mix 1 and eluted sample
    for column in sampleplate200.columns()[:num_cols]:
        pick_up_or_refill(p20m)
        p20m.transfer(6, rt_mm1[0], column[0], new_tip='never')
        p20m.drop_tip()

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        p20m.aspirate(11, column[0].bottom().move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x, y=0, z=0)))
        p20m.dispense(11, sampleplate200.columns()[index][0])
        for rep in range(10):
            p20m.aspirate(13, sampleplate200.columns()[index][0])
            p20m.dispense(13, sampleplate200.columns()[index][0])
            if rep == 9:
                p20m.move_to(sampleplate200.columns()[index][0].top(-2).move(
                 types.Point(x=column[0].diameter / 2, y=0, z=0)))
                p20m.blow_out()
                p20m.move_to(sampleplate200.columns()[index][0].top())
        p20m.drop_tip()

    ctx.pause(
     '''Transfer the plate (temperature module) to the off-deck thermocycler
     for fragmentation. Return plate to the temperature module. Resume.''')

    ctx.comment("STEP - cDNA Synthesis")

    # add RT master mix 2
    for column in sampleplate200.columns()[:num_cols]:
        pick_up_or_refill(p20m)
        p20m.aspirate(3, rt_mm2[0])
        p20m.dispense(3, column[0])
        for rep in range(10):
            p20m.aspirate(16, column[0])
            p20m.dispense(16, column[0])
            if rep == 9:
                p20m.move_to(column[0].top(-2).move(types.Point(
                 x=column[0].diameter / 2, y=0, z=0)))
                p20m.blow_out()
                p20m.move_to(column[0].top())
        p20m.drop_tip()

    ctx.pause(
     '''cDNA Synthesis protocol complete. Proceed to off deck cycler steps
     and cDNA Library Prep protocol''')

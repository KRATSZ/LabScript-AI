import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''ArcBio DNA Workflow Continuous:
    Post-PCR Instrument: DNA-POST-PCR-3 Library Purification''',
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

    # reservoir for beads and tris
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5', 'Reservoir')

    beads = reservoir.wells()[0]
    tris = reservoir.wells()[-1]

    # reservoir for 80 percent ethanol
    etoh = ctx.load_labware(
     'nest_1_reservoir_195ml', '6', '80 percent etoh').wells()[0]
    liq_volume([etoh], 48000)
    waste = ctx.load_labware(
     'nest_1_reservoir_195ml', '4', '80 percent etoh').wells()[0]

    # plate at 4 degrees on the temperature module
    temp = ctx.load_module('temperature module gen2', '3')
    plate2 = temp.load_labware(
     'eppendorftwin.tec96_96_aluminumblock_200ul',
     "Plate 2 at Rooom Temperature")

    # magnetic module with sample plate
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()
    mag_plate = mag.load_labware(
     'eppendorf_96_wellplate_200ul', 'Mag Plate')

    ctx.comment("STEP - KAPA Pure Beads")

    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        p300m.aspirate(
         40, beads.bottom(clearance_reservoir), rate=0.5)
        ctx.delay(seconds=1)
        p300m.dispense(40, column[0])
        p300m.mix(10, 64, column[0])
        p300m.drop_tip()

    ctx.delay(minutes=10)

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    ctx.comment("remove supernatant")

    # remove supernatant
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.aspirate(60, column[0].bottom(4), rate=0.33)
        p300m.aspirate(
         60, column[0].bottom(1).move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x, y=0, z=0)), rate=0.33)
        p300m.dispense(140, waste.top(), rate=2)
        ctx.delay(seconds=1)
        p300m.blow_out()
        p300m.drop_tip()

    ctx.comment("STEP - 80 Percent EtOH")

    for repeat in range(2):
        # add ethanol
        pick_up_or_refill(p300m, 300)
        for column in mag_plate.columns()[:num_cols]:
            etoh.liq_vol -= 1600
            ht = liq_height(etoh) - 3 if liq_height(etoh) - 3 > 1 else 1
            p300m.aspirate(200, etoh.bottom(ht))
            p300m.air_gap(20)
            p300m.dispense(220, column[0].top())
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.air_gap(20)
        p300m.drop_tip()

        ctx.delay(seconds=30)

        # remove sup
        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m, 300)
            loc = column[0].bottom(1).move(types.Point(x={True: 1}.get(
              not index % 2, -1)*offset_x, y=0, z=0))
            p300m.aspirate(180, column[0].bottom(4), rate=0.33)
            p300m.aspirate(50, loc, rate=0.33)
            p300m.air_gap(20)
            p300m.dispense(250, waste.top())
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.air_gap(20)
            p300m.drop_tip()

    mag.disengage()

    # air dry bead pellets
    ctx.delay(minutes=time_dry)

    ctx.comment("STEP - Tris")

    # resuspend bead pellet in Tris
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)
        p300m.aspirate(22, tris.bottom(clearance_reservoir))
        loc = column[0].bottom(clearance_bead_resuspension).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x_resuspension, y=0, z=0))
        p300m.dispense(22, loc, rate=3)
        for rep in range(10):
            p300m.aspirate(22, column[0].bottom(1))
            p300m.dispense(22, loc, rate=3)
        p300m.drop_tip()

    ctx.delay(minutes=2)

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    ctx.pause(
     '''Place a fresh 200 uL PCR plate on the temperature module. Resume.''')

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        p20m.transfer(
         20, column[0].bottom().move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x, y=0, z=0)),
         plate2.columns()[index][0],
         new_tip='never')
        p20m.drop_tip()

    ctx.pause(
     '''DNA Post-PCR steps complete.''')

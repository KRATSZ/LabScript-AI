import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''ArcBio DNA Workflow Continuous:
    Pre-PCR Instrument: DNA-PRE-PCR-3 Library Purification Indexing''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [incubate_samples_with_beads, temp_mod_setting, manual_bead_resuspension,
     clearance_bead_resuspension, offset_x_resuspension, count_samples,
     clearance_reservoir, height_engage, time_engage, offset_x,
     time_dry] = get_values(  # noqa: F821
      'incubate_samples_with_beads', 'temp_mod_setting',
      'manual_bead_resuspension', 'clearance_bead_resuspension',
      'offset_x_resuspension', 'count_samples', 'clearance_reservoir',
      'height_engage', 'time_engage', 'offset_x', 'time_dry')

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

    # fill columns with liquid
    def fill_cols(columns, wellcapacity, welldead, num_tfers, transfer_vol,
                  reagentname, channels=8):
        wellspercol = len(columns[0])
        total = num_tfers*transfer_vol*channels
        usable = wellspercol*(wellcapacity - welldead)
        tferspercol = math.floor(usable / (channels*transfer_vol))
        used = tferspercol*channels*transfer_vol
        remaining = total
        for column in columns:
            last = remaining
            for well in column:
                if remaining > used:
                    well.liq_vol = welldead + tferspercol*transfer_vol*(
                     channels / wellspercol)
                    remaining -= used / wellspercol
                else:
                    if remaining > 0:
                        well.liq_vol = welldead + (last / wellspercol)
                        remaining -= remaining / wellspercol
                    else:
                        well.liq_vol = 0
        for column in columns:
            if column[0].liq_vol:
                ctx.comment("Fill column {0} with {1} ul {2}".format(
                 column[0], column[0].liq_vol, reagentname))
        ctx.pause()

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

    # apply 10 mm/sec limit when tip leaves liquid
    def slow_tip_withdrawal(current_pipette, well_location):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        current_pipette.move_to(well_location.top())
        ctx.max_speeds[axis] = None

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

    # reagents block for sequencing indexes and enzyme 16
    reagents = ctx.load_labware(
     'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '2', 'Reagents')
    enzyme16 = [reagents.columns()[index] for index in [0, 1]]
    indexes = reagents.columns()[:num_cols]

    # reservoir for beads and tris
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5', 'Reservoir')

    beads = reservoir.wells()[0]
    liq_volume([beads], 7800)

    tris = reservoir.wells()[-1]
    liq_volume([tris], 9240)

    # reservoir for 80 percent ethanol
    etoh = ctx.load_labware(
     'nest_1_reservoir_195ml', '6', '80 percent etoh').wells()[0]
    liq_volume([etoh], 48000)
    waste = ctx.load_labware(
     'nest_1_reservoir_195ml', '4', '80 percent etoh').wells()[0]

    # plate at 4 degrees on the temperature module
    temp = ctx.load_module('temperature module gen2', '3')
    plate4deg = temp.load_labware(
     'eppendorf_twintec_on_opentrons_metal_block_033822',
     "Plate at 4 Degrees C")
    if temp_mod_setting:
        temp.set_temperature(temp_mod_setting)

    # magnetic module with sample plate
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()
    mag_plate = mag.load_labware(
     'eppendorf_twintex_clickbio_adapter', 'Mag Plate')

    ctx.comment("STEP - Tris")

    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        tris.liq_vol -= 480
        ht = liq_height(tris) - 3 if liq_height(tris) - 3 > 1 else 1
        p300m.transfer(60, tris.bottom(ht), column[0], new_tip='never')
        p300m.drop_tip()

    ctx.comment("STEP - KAPA Pure Beads")

    for index, column in enumerate(mag_plate.columns()[:num_cols]):

        pick_up_or_refill(p300m)

        beads.liq_vol -= 520
        ht = liq_height(beads) - 3 if liq_height(beads) - 3 > 1 else 1

        if index == 0:
            ht_premix = liq_height(beads) + 3
            for rep in range(5):
                p300m.aspirate(
                 200, beads.bottom(clearance_reservoir), rate=0.5)
                p300m.dispense(200, beads.bottom(ht_premix), rate=0.5)

        p300m.aspirate(
         65, beads.bottom(ht), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p300m, beads)
        p300m.move_to(
         beads.top(-2).move(types.Point(x=beads.length / 2, y=0, z=0)))
        p300m.move_to(beads.top())

        p300m.dispense(65, column[0].bottom(4))

        for rep in range(10):
            p300m.aspirate(140, column[0].bottom(2))
            p300m.dispense(140, column[0].bottom(4))

        p300m.move_to(
         column[0].top(-2).move(types.Point(
          x=column[0].diameter / 2, y=0, z=0)))
        p300m.blow_out()
        p300m.move_to(column[0].top())

        p300m.drop_tip()

    if incubate_samples_with_beads:
        ctx.delay(minutes=10)

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    ctx.comment("remove supernatant")

    # remove supernatant
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.aspirate(180, column[0].bottom(4), rate=0.33)
        p300m.dispense(200, waste.top(), rate=2)
        ctx.delay(seconds=1)
        p300m.blow_out()
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.aspirate(
         50, column[0].bottom(1).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0)), rate=0.33)
        p300m.dispense(70, waste.top(), rate=2)
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
            loc = column[0].bottom(1).move(types.Point(x={True: -1}.get(
              not index % 2, 1)*offset_x, y=0, z=0))
            p300m.aspirate(180, column[0].bottom(4), rate=0.2)
            p300m.aspirate(50, loc, rate=0.2)
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
        p20m.pick_up_tip()
        p20m.aspirate(16, tris.bottom(clearance_reservoir))
        loc = column[0].bottom(clearance_bead_resuspension).move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x_resuspension, y=0, z=0))
        p20m.dispense(16, loc, rate=3)
        if not manual_bead_resuspension:
            for rep in range(10):
                p20m.aspirate(16, column[0].bottom(1))
                rt = 3 if rep < 9 else 0.5
                p20m.dispense(16, loc, rate=rt)
                if rep == 9:
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p20m, column[0])
                    p20m.move_to(
                     column[0].top(-2).move(types.Point(
                      x=column[0].diameter / 2, y=0, z=0)))
                    p20m.blow_out()
                    p20m.move_to(column[0].top())
        p20m.drop_tip()

    if manual_bead_resuspension:
        ctx.pause("""Cover, vortex, spin, incubate,
        uncover and return the plate. Resume""")
    else:
        ctx.delay(minutes=2)

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    ctx.pause(
     '''Place a fresh 200 uL PCR plate on the temperature module.
     Place index plate on the reagents block. Resume.''')

    ctx.comment("STEP - Sequencing Indexes")

    # pierce foil, combine 10 uL index pair and eluted sample
    for index, column in enumerate(plate4deg.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        source = indexes[index][0]
        p20m.move_to(source.top(2))
        p20m.move_to(source.top(-1))
        p20m.drop_tip()
        pick_up_or_refill(p20m)
        p20m.move_to(source.top(2))
        p20m.transfer(10, source.bottom(7.2), column[0], new_tip='never')
        p20m.drop_tip()

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        p20m.transfer(
         15, column[0].bottom().move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0)),
         plate4deg.columns()[index][0],
         mix_after=(2, 15), new_tip='never')
        p20m.drop_tip()

    ctx.comment("STEP - Enzyme 16")

    fill_cols(enzyme16, 200, 30, num_cols, 25, 'enzyme16')

    def enzwells():
        yield from [column[0] for column in enzyme16]

    enzwell = enzwells()
    source = next(enzwell)

    for column in plate4deg.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        if source.liq_vol <= 30:
            source = next(enzwell)
        source.liq_vol -= 25
        ht = liq_height(source) - 3 if liq_height(source) - 3 > 1 else 1
        p300m.aspirate(
         25, source.bottom(ht), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p300m, source)
        p300m.dispense(25, column[0])
        for rep in range(10):
            p300m.aspirate(40, column[0].bottom(1), rate=0.5)
            p300m.dispense(40, column[0].bottom(5), rate=0.5)
            if rep == 9:
                slow_tip_withdrawal(p300m, column[0])
        p300m.drop_tip()

    ctx.pause(
     '''Continue to DNA-POST-PCR-1 Purification Post Indexing protocol.''')

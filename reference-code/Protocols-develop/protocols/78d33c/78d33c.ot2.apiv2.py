import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''ArcBio DNA Workflow Continuous:
    Pre-PCR Instrument: DNA-PRE-PCR-1 Concentration Fragmentation''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [incubate_samples_with_beads, temp_mod_setting,
     clearance_bead_resuspension, offset_x_resuspension, count_samples,
     clearance_12wellreservoir, clearance_12wellreservoir, height_engage,
     time_engage, offset_x, time_dry] = get_values(  # noqa: F821
      'incubate_samples_with_beads', 'temp_mod_setting',
      'clearance_bead_resuspension', 'offset_x_resuspension', 'count_samples',
      'clearance_12wellreservoir', 'clearance_12wellreservoir',
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
                if tipCtr < len(tiplist):
                    pip.pick_up_tip(tiplist[tipCtr])
                    tipCtr += 1
                else:
                    tipCtr = 0
                    ctx.pause(
                     """Please Refill the 300 uL Tip Boxes
                     and Empty the Tip Waste""")
                    pip.pick_up_tip(tiplist[tipCtr])
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
        # ctx.pause()

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

    # yield list chunks of length n
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    # tips, p20 multi, p300 multi
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [6, 9]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    tips200 = [ctx.load_labware(
      "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [5]]
    tips300 = [ctx.load_labware(
     "opentrons_96_tiprack_300ul", str(slot)) for slot in [10, 11]]
    tipCtr = 0
    tiplist = []
    for box in tips300:
        tiplist.extend(box.rows()[0])
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips200)

    # reagents block for Fragmentation Master Mix
    reagents = ctx.load_labware(
     'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '2', 'Reagents')
    [fragmentation_mm] = [reagents.columns()[index] for index in [0]]

    # reservoir for beads and tris
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '8', 'Reservoir')

    beads = reservoir.columns()[:3]
    fill_cols(beads, 10000, 1512, num_cols, 126, "beads")
    deadvol_res = 1512

    tris = reservoir.wells()[-1]

    # reservoir for 80 percent ethanol
    etoh = ctx.load_labware(
     'nest_1_reservoir_195ml', '7', '80 percent etoh').wells()[0]
    liq_volume([etoh], 48000)
    waste = ctx.load_labware(
     'nest_1_reservoir_195ml', '4', 'Waste').wells()[0]

    # input samples
    temp = ctx.load_module('temperature module gen2', '3')
    output_plate = temp.load_labware(
     'eppendorf_twintec_on_opentrons_metal_block_033822',
     "Output plate at 4 Degrees C")
    if temp_mod_setting:
        temp.set_temperature(temp_mod_setting)

    # magnetic module with deep well plate
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()
    mag_plate = mag.load_labware(
     'eppendorf_twintex_clickbio_adapter', 'Mag Plate')

    ctx.comment("STEP - KAPA Pure Beads")

    def beadwells():
        yield from [column[0] for column in beads]

    beadwell = beadwells()
    source = next(beadwell)

    for index, column in enumerate(mag_plate.columns()[:num_cols]):

        pick_up_or_refill(p300m)

        if source.liq_vol <= deadvol_res:
            source = next(beadwell)

            ht_premix = liq_height(source) + 3

            # premix beads - aspirate low, dispense high
            for rep in range(5):
                p300m.aspirate(
                 200, source.bottom(clearance_12wellreservoir), rate=0.5)
                p300m.dispense(200, source.bottom(ht_premix), rate=0.5)

        # extra bead premix prior to the first usage
        if index == 0:
            ht_premix = liq_height(source) + 3
            for rep in range(5):
                p300m.aspirate(
                 200, source.bottom(clearance_12wellreservoir), rate=0.5)
                p300m.dispense(200, source.bottom(ht_premix), rate=0.5)

        # aspirate beads - use tip height avoiding overimmersion
        source.liq_vol -= 126*p300m.channels
        ht = liq_height(source) - 3 if liq_height(source) - 3 > 1 else 1

        p300m.aspirate(
         126, source.bottom(ht), rate=0.5)
        ctx.delay(seconds=1)
        # tip departs slowly to minimize beads on tip exterior
        slow_tip_withdrawal(p300m, source)

        # side tip touch in reservoir - minimize beads on tip exterior
        p300m.move_to(
         source.top(-2).move(types.Point(x=source.length / 2, y=0, z=0)))
        p300m.move_to(source.top())

        p300m.dispense(126, column[0].bottom(4))

        for rep in range(10):
            p300m.aspirate(149, column[0].bottom(4))
            p300m.dispense(149, column[0].bottom(4))

        # side tip touch after dispense - minimize beads on tip exterior
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

    # remove supernatant
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)

        p300m.aspirate(200, column[0].bottom(4), rate=0.33)

        p300m.dispense(200, waste.top())
        p300m.move_to(column[0].top())
        p300m.air_gap(20)

        # to avoid beads - left if index is even, right if odd
        direction = -1 if not index % 2 else 1

        # apply move of magntidue x_offset to the location for aspiration
        loc_asp = column[0].bottom(1).move(types.Point(
         x=direction*offset_x, y=0, z=0))

        p300m.aspirate(50, loc_asp, rate=0.33)

        p300m.dispense(70, waste.top(), rate=2)
        ctx.delay(seconds=1)
        p300m.blow_out()
        p300m.drop_tip()

    for repeat in range(2):
        # add ethanol
        pick_up_or_refill(p300m, 300)
        for column in mag_plate.columns()[:num_cols]:

            etoh.liq_vol -= 200*p300m.channels
            ht = liq_height(etoh) - 3 if liq_height(etoh) - 3 > 1 else 1

            p300m.aspirate(200, etoh.bottom(ht))
            p300m.air_gap(20)

            p300m.dispense(220, column[0].top())
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.air_gap(20)

        ctx.delay(seconds=30)

        # remove sup
        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            if not p300m.has_tip:
                pick_up_or_refill(p300m, 300)

            # to avoid beads - left if index is even, right if odd
            direction = -1 if not index % 2 else 1

            # apply move of magnitude x_offset to the location for aspiration
            loc_asp = column[0].bottom(1).move(types.Point(
             x=direction*offset_x, y=0, z=0))

            p300m.aspirate(180, column[0].bottom(4), rate=0.2)
            p300m.aspirate(50, loc_asp, rate=0.2)
            p300m.air_gap(20)

            p300m.dispense(250, waste.top())
            ctx.delay(seconds=0.5)
            p300m.blow_out()
            p300m.air_gap(20)

            p300m.drop_tip()

        # to improve completeness of removal
        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)
            for clearance in [0.7, 0.4, 0.2, 0]:

                # to avoid beads - left if index is even, right if odd
                direction = -1 if not index % 2 else 1

                # apply move of magntidue x_offset to the location for asp
                loc_asp = column[0].bottom(clearance).move(types.Point(
                 x=direction*offset_x, y=0, z=0))

                p300m.aspirate(25, loc_asp)

            p300m.drop_tip()

    # air dry bead pellets
    ctx.delay(minutes=time_dry)

    mag.disengage()

    # resuspend bead pellet in Tris
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p20m.pick_up_tip()

        p20m.aspirate(16, tris.bottom(clearance_12wellreservoir))

        # to target beads - right if index is even, left if odd
        direction = 1 if not index % 2 else -1

        # apply move of magntidue x_offset to the location for dispense
        loc_disp = column[0].bottom(clearance_bead_resuspension).move(
         types.Point(x=direction*offset_x_resuspension, y=0, z=0))

        # resuspend beads
        p20m.dispense(16, loc_disp, rate=3)
        for rep in range(10):

            p20m.aspirate(16, column[0].bottom(1))

            # dispense rate 3x default except 0.5X default for last mix
            rt = 3 if rep < 9 else 0.5
            p20m.dispense(16, loc_disp, rate=rt)

            # delay and slow depart after last mix
            if rep == 9:
                ctx.delay(seconds=1)
                slow_tip_withdrawal(p20m, column[0])

                # side touch to minimize beads on tip exterior
                p20m.move_to(
                 column[0].top(-2).move(types.Point(
                  x=column[0].diameter / 2, y=0, z=0)))
                p20m.blow_out()
                p20m.move_to(column[0].top())

        p20m.drop_tip()

    ctx.delay(minutes=2)

    mag.engage(height=height_engage)
    ctx.delay(minutes=time_engage)

    # combine Fragmentation Master Mix and eluted sample
    pick_up_or_refill(p20m)

    # adding fragmentation mastermix to output plate
    for chunk in create_chunks(output_plate.columns()[:num_cols], 4):

        p20m.aspirate(4*len(chunk)+4, fragmentation_mm[0])

        for column in chunk:
            p20m.dispense(4, column[0])

        p20m.dispense(4, fragmentation_mm[0])

    p20m.drop_tip()

    p20m.flow_rate.aspirate = 3.5

    # transfer eluate to output plate and mix
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)

        # to avoid beads - left if index is even, right if odd
        direction = -1 if not index % 2 else 1

        # apply move of magntidue x_offset to the location for aspiration
        loc_asp = column[0].bottom(1).move(types.Point(
         x=direction*offset_x, y=0, z=0))

        p20m.aspirate(14, loc_asp)

        p20m.move_to(loc_asp.move(types.Point(x=0, y=0, z=1)))
        ctx.delay(seconds=1)

        p20m.dispense(14, output_plate.columns()[index][0].bottom(1))

        for rep in range(5):
            p20m.aspirate(11, output_plate.columns()[index][0].bottom(1))
            p20m.dispense(11, output_plate.columns()[index][0].bottom(1))

        p20m.blow_out()
        p20m.drop_tip()

    mag.disengage()

    ctx.comment(
     '''Remove output plate on the Temperature Module for off-deck cycler steps.
     Then continue to DNA-PRE-PCR-2 Adapter Ligation protocol.''')

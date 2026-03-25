import math
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''ArcBio DNA Workflow Continuous:
    Post-PCR Instrument: DNA-PRE-PCR-2 Adapter Ligation''',
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
    def pick_up_or_refill(pip):
        try:
            pip.pick_up_tip()
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
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips200)

    # reagents block for Post Index Cleanup Enzyme Mix
    reagents = ctx.load_labware(
     'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '2', 'Reagents')
    [reagent12, adapters, enz1, enz2] = [
     reagents.columns()[index] for index in [0, 1, 2, 3]]
    for strip in [enz1, enz2]:
        liq_volume(strip, 195)

    # sample plate at 4 degrees
    temp = ctx.load_module('temperature module gen2', '3')
    sampleplate = temp.load_labware(
     'eppendorf_twintec_on_opentrons_metal_block_033822',
     "Sample Plate at 4 Degrees")
    temp.set_temperature(4)

    # magnetic module
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()

    ctx.comment("STEP - Reagent 12")

    # add reagent 12
    p20m.transfer(
     2, reagent12[0], [
      column[0] for column in sampleplate.columns()[:num_cols]],
     mix_after=(10, 16), new_tip='always')

    ctx.delay(minutes=2)

    # placeholder comment to separate the delay and the pause
    ctx.comment("Reagent 12")

    ctx.pause('''Transfer sample plate to pre-heated,
    off-deck cycler for 1 minute. Then return the plate
    to the Temperature Module at 4 degrees and resume.''')

    ctx.comment("Holding at 4 degrees for 2 minutes")

    ctx.delay(minutes=2)

    ctx.comment("STEP - Adapters")

    # add adapters
    p20m.transfer(
     4, adapters[0], [
      column[0] for column in sampleplate.columns()[:num_cols]],
     mix_after=(2, 10), new_tip='always')

    ctx.comment("STEP - Enzyme Mix")

    def enztubes():
        yield from [enz1[0], enz2[0]]

    enztube = enztubes()
    source = next(enztube)

    # add enzyme mix
    for column in sampleplate.columns()[:num_cols]:
        p300m.pick_up_tip()
        if source.liq_vol <= 39:
            source = next(enztube)
        ht = liq_height(source) + 1 if liq_height(source) + 1 > 1 else 1
        source.liq_vol -= 26
        p300m.aspirate(26, source.bottom(ht), rate=0.33)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p300m, source)
        p300m.dispense(26, column[0], rate=0.33)
        ctx.delay(seconds=1)
        for rep in range(10):
            p300m.aspirate(37, column[0], rate=0.33)
            ctx.delay(seconds=1)
            p300m.dispense(37, column[0], rate=0.33)
            ctx.delay(seconds=1)
            if rep == 9:
                slow_tip_withdrawal(p300m, column[0])
                p300m.blow_out()
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
        p300m.drop_tip()

    ctx.pause(
     '''Adapter Ligation protocol complete.
     Proceed to off deck cycler steps
     and Library Purification Indexing protocol''')

import math
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''ArcBio DNA Workflow Continuous:
    Post-PCR Instrument: DNA-POST-PCR-2 Post Indexing''',
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

    # tips, p20 multi, p300 multi
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [10, 11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)

    # reagents block for Post Index Cleanup Enzyme Mix
    reagents = ctx.load_labware(
     'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '2', 'Reagents')
    [postindexcleanup_enz_mx] = [reagents.columns()[index] for index in [0]]

    # sample plate at 4 degrees
    temp = ctx.load_module('temperature module gen2', '3')
    sampleplate = temp.load_labware(
     'eppendorftwin.tec96_96_aluminumblock_200ul',
     "Sample Plate at 4 Degrees")
    temp.set_temperature(4)

    # magnetic module with twin tec plate
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()

    ctx.comment("STEP - Post-Indexing Cleanup Enzyme Mixture")

    # add enzyme mixture
    for column in sampleplate.columns()[:num_cols]:
        pick_up_or_refill(p20m)
        p20m.transfer(
         5, postindexcleanup_enz_mx[0], column[0], new_tip='never')
        for rep in range(10):
            p20m.aspirate(20, column[0])
            p20m.dispense(20, column[0].bottom(5))
        p20m.drop_tip()

    ctx.pause(
     '''Post-indexing purification protocol complete.
     Proceed to off deck cycler steps
     and library purification protocol''')

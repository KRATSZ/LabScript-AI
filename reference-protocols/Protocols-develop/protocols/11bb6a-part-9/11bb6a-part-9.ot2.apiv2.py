import math
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''NEBNext Quarter Volume Library Prep Step 9:
    Fragment Analyzer''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_plates] = get_values(  # noqa: F821
      'sample_count', 'labware_plates')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if sample_count < 48 or sample_count > 96:
        raise Exception('Number of samples must be 48-96')

    # tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [10]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [7]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module empty
    ctx.load_module('Temperature Module', '1')

    # magnetic module empty
    mag = ctx.load_module('magnetic module gen2', '9')
    mag.disengage()

    reservoir = ctx.load_labware(
     'nest_12_reservoir_15ml', '5', '12-well Reservoir')
    [diluentbf] = [
     reservoir.wells_by_name()[name] for name in ['A9']]
    deadvol_reservoir_1 = 1800
    diluentbf.liq_vol = num_cols*8*22 + deadvol_reservoir_1

    fragment_analyzer_plate = ctx.load_labware(
     'biorad_96_fragment_analyzer_plate_aluminumblock_200ul', '6',
     'Fragment Analyzer Plate')

    libraries_plate = ctx.load_labware(labware_plates, '3', 'Libraries Plate')

    # alert user to reagent volumes needed
    ctx.comment("\nEnsure reagents in sufficient volume are present on deck\n")
    for volume, units, reagent, location in zip(
     [math.ceil(diluentbf.liq_vol / 1000)],
     ['mL'],
     ['diluent buffer'],
     [diluentbf]):
        ctx.comment(
         "\n{0} {1} {2} in {3}\n".format(
          str(volume), units, reagent.upper(), location))

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

    # return liquid height in a well
    def liq_height(well, effective_diameter=None):
        if well.diameter:
            if effective_diameter:
                radius = effective_diameter / 2
            else:
                radius = well.diameter / 2
            csa = math.pi*(radius**2)
        else:
            csa = well.length*well.width
        return well.liq_vol / csa

    # apply speed limit to departing tip
    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    ctx.comment(
     "\nStep - diluent bf to fragment analyzer plate (all wells except H12)\n")

    if num_cols < 12:

        p300m.transfer(
         22, diluentbf, [
          column[0] for column in fragment_analyzer_plate.columns()[
           :num_cols]])

    else:

        p300m.transfer(
         22, diluentbf, [
          column[0] for column in fragment_analyzer_plate.columns()[:11]])

        # skip well H12
        p300m.pick_up_tip(tips300[0]['B2'])  # pick up 7 tips
        p300m.transfer(
         22, diluentbf,
         fragment_analyzer_plate.columns()[-1][0], new_tip='never')
        p300m.drop_tip()

    ctx.comment("\nStep - 2 uL library sample to fragment analyzer plate\n")

    p20m.transfer(2, [
     column[0] for column in libraries_plate.columns()[:num_cols]], [
     column[0] for column in fragment_analyzer_plate.columns()[:num_cols]],
     new_tip='always')

    ctx.comment("\nFinished. Proceed to measure concentration.\n")

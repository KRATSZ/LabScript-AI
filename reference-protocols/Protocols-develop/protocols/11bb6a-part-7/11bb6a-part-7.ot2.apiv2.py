import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''NEBNext Quarter Volume Library Prep Step 7:
    PCR Enrichment''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [i7row, i5col, sample_count, labware_plates, labware_tempmod,
     engage_height, offset_x] = get_values(  # noqa: F821
      'i7row', 'i5col', 'sample_count', 'labware_plates', 'labware_tempmod',
      'engage_height', 'offset_x')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if sample_count < 48 or sample_count > 96:
        raise Exception('Number of samples must be 48-96')

    # for 1-tip pickup with p20m
    reduced_pick_up_current = 0.15

    # constrain reduced_pick_up_current value to acceptable range
    if reduced_pick_up_current < 0.1 or reduced_pick_up_current > 0.15:
        raise Exception('''Invalid value for reduced_pick_up_current parameter
                           (must be between 0.1 and 0.15).''')

    # tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [10, 3, 6]]   # slot 10 first for 1-tip on p20m
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module with Q5 mastermix
    temp = ctx.load_module('Temperature Module', '1')
    block = temp.load_labware(labware_tempmod)
    [q5] = [
     block.wells_by_name()[name] for name in ['A1']]
    deadvol_tube = 10
    temp.set_temperature(4)
    q5.liq_vol = 12*num_cols*8 + deadvol_tube + 20

    # magnetic module with library prep plate or size plate
    mag = ctx.load_module('magnetic module gen2', '9')
    mag_plate = mag.load_labware(
     labware_plates, 'Library Prep Plate or Size Plate (96xA)')
    mag.engage(height_from_base=engage_height)

    # i7 indexes
    i7_plate = ctx.load_labware(
     'eppendorf_96_wellplate_200ul', '5', 'i7 indexes')
    i7_row = i7_plate.rows()[i7row]

    # i5 indexes
    i5_plate = ctx.load_labware(
     'eppendorf_96_wellplate_200ul', '2', 'i5 indexes')
    i5_col = i5_plate.columns()[i5col]

    # PCR plate
    pcr_plate = ctx.load_labware(labware_plates, '8', 'PCR Plate')

    # Reagent Plate
    reagent_plate = ctx.load_labware(labware_plates, '7', 'Reagent Plate')

    # alert user to reagent volumes needed
    ctx.comment("Ensure reagents in sufficient volume are present on deck.")
    for volume, units, reagent, location in zip(
     [q5.liq_vol],
     ['uL'],
     ['q5 mastermix'],
     [q5]):
        ctx.comment(
         "{0} {1} {2} in {3}".format(
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

    # *******************************************************************

    # capture and report original value for p20m pick_up_current
    default_current = ctx._hw_manager.hardware.\
        _attached_instruments[p20m._implementation.get_mount()].\
        config.pick_up_current

    ctx.comment("""Tip pick-up current for the p20 multi-channel pipette
    initially configured to {} mAmp.""".format(str(default_current)))

    # temporarily reduce p20m pick_up_current for one-channel tip pickup
    ctx._hw_manager.hardware._attached_instruments[
     p20m._implementation.get_mount()].update_config_item(
     'pick_up_current', reduced_pick_up_current)

    ctx.comment("""Tip pick-up current configuration for the p20 multi-channel
    pipette temporarily reduced to {} mAmp for one-tip pickup.""".format(
     str(reduced_pick_up_current)))

    # ********************************************************************

    ctx.comment("Step - p20m 'one tip' add selected row i7 to PCR Plate")

    disposal_vol = 2

    tip_list = [*reversed(sorted(
     [tip for column in tips20[0].columns()[:2] for tip in column],
     key=lambda x: x.well_name[0]))][:num_cols]

    for column, tip, i7well in zip(
     pcr_plate.columns()[:num_cols],
     tip_list,
     i7_row[:num_cols]):

        p20m.pick_up_tip(tip)  # picking up tip from row H

        p20m.aspirate(8+disposal_vol, i7well.bottom(1))

        for well in column:

            p20m.dispense(1, well.bottom(1))

        p20m.dispense(disposal_vol, i7well.bottom(1))

        p20m.drop_tip()

    # ********************************************************************

    # reset p20m pick_up_current to original value
    ctx._hw_manager.hardware._attached_instruments[
     p20m._implementation.get_mount()].update_config_item(
     'pick_up_current', default_current)

    ctx.comment("""Tip pick-up current for the p20 multi-channel pipette
    restored to initial value of {} mAmp for standard 8-tip pickup.""".format(
     str(ctx._hw_manager.hardware._attached_instruments[
      p20m._implementation.get_mount()].config.pick_up_current)))

    # ********************************************************************

    ctx.comment(
     "Step - 1-tip p300m add Q5 Mastermix to Reagent Plate column 6")

    p300m.pick_up_tip(tips300[0]['H12'])

    for row in reagent_plate.rows():

        v = 12*num_cols + 2

        q5.liq_vol -= v
        ht_tube = liq_height(q5) - 3 if liq_height(q5) - 3 > 1 else 1

        p300m.aspirate(v+5, q5.bottom(ht_tube), rate=0.5)
        ctx.delay(seconds=2)
        slow_tip_withdrawal(p300m, q5)

        p300m.dispense(v, row[5].bottom(1), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p300m, row[5])

        p300m.dispense(5, q5.bottom(ht_tube), rate=0.5)

    p300m.drop_tip()

    ctx.comment("Step - p20m transfer Q5 Mastermix to PCR Plate")

    source = reagent_plate.columns()[5][0]

    for column in pcr_plate.columns()[:num_cols]:

        p20m.pick_up_tip()

        p20m.aspirate(12, source.bottom(1), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p20m, source)

        p20m.dispense(12, column[0].bottom(1))
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p20m, column[0])

        p20m.drop_tip()

    ctx.comment("Step - p20m add selected column i5 to PCR Plate")

    for column in pcr_plate.columns()[:num_cols]:

        pick_up_or_refill(p20m)

        p20m.aspirate(1, i5_col[0].bottom(1), rate=0.5)

        p20m.dispense(1, column[0].bottom(1))
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p20m, column[0])

        p20m.drop_tip()

    ctx.comment("Step - 10 uL sample to PCR plate")

    p20m.flow_rate.aspirate = 3.5

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)

        loc_asp = column[0].bottom(1).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0))

        p20m.aspirate(10, loc_asp)

        p20m.move_to(loc_asp.move(types.Point(x=0, y=0, z=1)))
        ctx.delay(seconds=1)

        p20m.dispense(10, pcr_plate.columns()[index][0].bottom(1))

        for rep in range(5):
            p20m.aspirate(19, pcr_plate.columns()[index][0].bottom(1))
            p20m.dispense(19, pcr_plate.columns()[index][0].bottom(1))

        p20m.blow_out()
        p20m.drop_tip()

    p20m.flow_rate.aspirate = 7.6

    mag.disengage()

    ctx.comment("Finished")

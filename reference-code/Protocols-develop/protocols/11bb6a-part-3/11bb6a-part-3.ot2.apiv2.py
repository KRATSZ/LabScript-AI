from opentrons import types
import math

metadata = {
    'protocolName': 'NEBNext Quarter Volume Library Prep Step 3: End Prep',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.12'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_plates, labware_tempmod, engage_height, offset_x
     ] = get_values(  # noqa: F821
      'sample_count', 'labware_plates', 'labware_tempmod', 'engage_height',
      'offset_x')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if sample_count < 48 or sample_count > 96:
        raise Exception('Number of samples must be 48-96.')

    # tips, p20 single, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [7, 10, 11]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [8]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module at 4 C with reagent tubes
    temp = ctx.load_module('Temperature Module', '1')
    block = temp.load_labware(
     labware_tempmod)
    [enz_mx, ep_buffer_and_mx, mm] = [
     block.wells_by_name()[name] for name in ['A1', 'A2', 'A3']]
    deadvol_tube = 10
    temp.set_temperature(4)

    mag = ctx.load_module('magnetic module gen2', '9')
    mag_plate = mag.load_labware(labware_plates, 'PCR Plate (96xA)')
    mag.engage(height_from_base=engage_height)

    reagent_plate = ctx.load_labware(labware_plates, '6', 'Reagent Plate')

    libraryprep_plate = ctx.load_labware(
     labware_plates, '3', 'Library Prep Plate')

    # enzyme mix volume 6 uL per column of samples
    enz_mx.liq_vol = 6*num_cols + deadvol_tube + 5

    # ep buffer and mix volume 14 uL per column of samples
    ep_buffer_and_mx.liq_vol = 14*num_cols + deadvol_tube + 5

    # mastermix volume
    mm.liq_vol = 0

    # alert user to reagent volumes needed
    ctx.comment("Ensure reagents in sufficient volume are present on deck.")
    for volume, reagent, location in zip(
     [math.ceil(enz_mx.liq_vol), math.ceil(ep_buffer_and_mx.liq_vol)],
     ['enzyme mix', 'ep buffer and mix'],
     [enz_mx, ep_buffer_and_mx]):
        ctx.comment(
         "{0} uL {1} in {2}".format(str(volume), reagent.upper(), location))

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

    ctx.comment("STEP - transferring enzyme mix to mastermix tube")

    p300m.pick_up_tip(tips300[0]['H12'])

    vol = 1.05*(6*num_cols)    # 5 percent overage

    p300m.aspirate(vol, enz_mx.bottom(0.5))
    p300m.dispense(vol, mm)
    p300m.drop_tip()

    # increment volume of mastermix
    mm.liq_vol += vol

    ctx.comment("STEP - transferring EP buffer to mastermix tube and mixing")

    vol = 1.05*(14*num_cols)    # 5 percent overage

    p300m.pick_up_tip(tips300[0]['H11'])
    p300m.transfer(
     vol, ep_buffer_and_mx.bottom(0.5), mm, mix_after=(10, 16*num_cols),
     new_tip='never')

    # increment volume of mastermix
    mm.liq_vol += vol

    ctx.comment("STEP - transferring mastermix to Reagent Plate 1st column")

    vol = 2.5*num_cols+1    # extra 1 uL

    for index, well in enumerate(reagent_plate.columns()[0]):

        # increment volume of mastermix
        mm.liq_vol -= vol

        # height of top of mastermix in tube
        ht = liq_height(mm) + 1.5 if liq_height(mm) + 1.5 > 1 else 1

        # tip height avoiding over-immersion but also getting all the liquid
        clearance = ht if index < 7 else 0.5

        p300m.aspirate(vol, mm.bottom(clearance))
        p300m.dispense(vol, well)
    p300m.drop_tip()

    ctx.comment("STEP - 2.5 uL mastermix to wells of Library Prep Plate")

    p20m.transfer(
     2.5, reagent_plate.columns()[0][0].bottom(0.5),
     [column[0] for column in libraryprep_plate.columns()[:num_cols]])

    ctx.comment("STEP - 12.5 uL sample wells of the Library Prep Plate")

    p20m.flow_rate.aspirate = 3.5

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p20m.pick_up_tip()

        loc_asp = column[0].bottom(1).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0))

        p20m.aspirate(12.5, loc_asp)

        p20m.move_to(loc_asp.move(types.Point(x=0, y=0, z=1)))
        ctx.delay(seconds=1)

        p20m.dispense(12.5, libraryprep_plate.columns()[index][0].bottom(1))

        for rep in range(5):
            p20m.aspirate(12, libraryprep_plate.columns()[index][0].bottom(1))
            p20m.dispense(12, libraryprep_plate.columns()[index][0].bottom(1))

        p20m.blow_out()
        p20m.drop_tip()

    p20m.flow_rate.aspirate = 7.6

    mag.disengage()

    ctx.comment("Proceed to incubation on off-deck PCR machine")

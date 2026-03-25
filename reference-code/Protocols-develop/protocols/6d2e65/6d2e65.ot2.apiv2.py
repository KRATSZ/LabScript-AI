import math
from opentrons import types

metadata = {
    'protocolName': '''Auto_Manual Hybrid Bead Cleanup 96-wells_v2''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, clearance_bead_pellet, x_offset_bead_pellet,
     clearance_elution, x_offset_elution, flow_rate_elution
     ] = get_values(  # noqa: F821
      'sample_count', 'clearance_bead_pellet', 'x_offset_bead_pellet',
      'clearance_elution', 'x_offset_elution', 'flow_rate_elution')

    ctx.set_rail_lights(True)

    # restrict clearances to 0-4 mm and x offsets to 0-2.5 mm
    if not 1 <= sample_count <= 96:
        raise Exception('Invalid number of samples (must be 1-96).')
    if not 0 <= x_offset_bead_pellet <= 2.5:
        raise Exception('x_offset_bead_pellet must be between 0 and 2.5 mm.')
    if not 0 <= clearance_bead_pellet <= 4:
        raise Exception('clearance_bead_pellet must be between 0 and 4 mm.')
    if not 0 <= x_offset_elution <= 2.5:
        raise Exception('x_offset_elution must be between 0 and 2.5 mm.')
    if not 0 <= clearance_elution <= 4:
        raise Exception('clearance_elution must be between 0 and 4 mm.')

    # tips, p300 multi gen2
    tips300 = [
     ctx.load_labware(
      'opentrons_96_filtertiprack_200ul', str(slot)) for slot in [
      5, 6, 7, 8, 10, 11]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'left', tip_racks=tips300)

    """
    helper functions for tip parking
    """
    named_tips = {}

    def name_the_tips(tip_box, name_list, well_list):
        for name in name_list:
            if name != 'current_tip':
                if name not in named_tips.keys():
                    named_tips[name] = []
        for name, well in zip(name_list, well_list):
            if name != 'current_tip':
                named_tips[name].append(tip_box[well])
            else:
                named_tips[name] = tip_box[well]

    def capture_current_starting_tip():
        for index, box in enumerate(tips300):
            if box.next_tip() is not None:
                current_starting_tip = box.next_tip()
                name_the_tips(tips300[index], ['current_tip'], [
                 current_starting_tip.well_name])
                return (tips300[index], current_starting_tip.well_name)
                break

    # number of sample columns
    num_cols = math.ceil(sample_count / 8)

    # CLEAN PLATE (slot 1)
    clean_plate = ctx.load_labware(
     'neptunescientificgeneseescientificadaptor_96_wellplate_200ul',
     '1', 'CLEAN PLATE')

    # NO MAG (slot 2)
    no_mag = ctx.load_labware(
     'neptunescientificgeneseescientificadaptor_96_wellplate_200ul',
     '2', 'NO MAG')

    # MAGPLATE (slot 3)
    mag_plate = ctx.load_labware(
     'alpaqua96sneptune_96_wellplate_200ul', '3', 'MAGPLATE')

    # NEST 12 well reservoir (slot 4)
    reagent_reservoir = ctx.load_labware(
     'nest_12_reservoir_15ml', '4')
    [beads, etoh_1, etoh_2, water, waste_1, waste_2] = [
     reagent_reservoir.wells_by_name()[well] for well in [
      'A1', 'A2', 'A3', 'A4', 'A12', 'A11']]

    # step 1: 36 ul beads at 30 ul/sec to NO MAG columns
    for column in no_mag.columns()[:num_cols]:
        p300m.flow_rate.aspirate = 50
        p300m.flow_rate.dispense = 50
        p300m.pick_up_tip()
        p300m.mix(2, 50, beads.bottom(1))
        p300m.flow_rate.aspirate = 30
        p300m.flow_rate.dispense = 30
        p300m.transfer(
         36, beads.bottom(1), column[0].bottom(3), new_tip='never')
        p300m.mix(6, 40, column[0].bottom(2))
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.return_tip()

    # step 2: pause with message
    ctx.pause("""
    Bring to hood. Incubate 2 minutes, set on mag plate until clear (~5 min).
    Aspirate out all liquid. Set MagPlate in Slot 3 and Resume.
    """)

    # step 3: 80 ul EtOH (A2) at 20 ul/sec to MAGPLATE columns
    p300m.flow_rate.aspirate = 20
    p300m.flow_rate.dispense = 20
    p300m.transfer(
     80, etoh_1.bottom(1), [
      column[0].bottom(26) for column in mag_plate.columns()[:num_cols]])

    # step 4: 80 ul MAGPLATE sup (aspirate to side to avoid bead pellet)
    # at 20 ul/sec to NEST reservoir A12 (dispense from top), return tips
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        ccst = capture_current_starting_tip()
        name_the_tips(ccst[0], ['sup_tips'], [
         named_tips['current_tip'].well_name])
        p300m.pick_up_tip()
        if index % 2 != 1:
            # offset to right (for even columns) to avoid bead pellet
            aspirate_location = column[0].bottom(
             clearance_bead_pellet).move(
             types.Point(x=x_offset_bead_pellet, y=0, z=0))
        else:
            # offset to left (for odd columns) to avoid bead pellet
            aspirate_location = column[0].bottom(
             clearance_bead_pellet).move(
             types.Point(x=-1*x_offset_bead_pellet, y=0, z=0))
        p300m.move_to(column[0].top())
        ctx.max_speeds['Z'] = 10
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(40, column[0].bottom(4))
        p300m.aspirate(40, aspirate_location)
        p300m.move_to(column[0].top())
        ctx.max_speeds['Z'] = None
        p300m.air_gap(20)
        p300m.dispense(100, waste_1.top(3))
        p300m.air_gap(20)
        p300m.return_tip()

    # step 5: 80 ul EtOH (A3) at 20 ul/sec to MAGPLATE columns
    p300m.flow_rate.aspirate = 20
    p300m.flow_rate.dispense = 20
    p300m.transfer(
     80, etoh_2.bottom(1), [
      column[0].bottom(26) for column in mag_plate.columns()[:num_cols]])

    # step 6: 80 ul MAGPLATE sup (aspirate to side to avoid bead pellet)
    # at 20 ul/sec to NEST reservoir A11 (dispense from top), return tips
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p300m.pick_up_tip(named_tips['sup_tips'][index])
        if index % 2 != 1:
            # offset to right (for even columns) to avoid bead pellet
            aspirate_location = column[0].bottom(clearance_bead_pellet).move(
             types.Point(x=x_offset_bead_pellet, y=0, z=0))
        else:
            # offset to left (for odd columns) to avoid bead pellet
            aspirate_location = column[0].bottom(clearance_bead_pellet).move(
             types.Point(x=-1*x_offset_bead_pellet, y=0, z=0))
        p300m.move_to(column[0].top())
        ctx.max_speeds['Z'] = 10
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(40, column[0].bottom(4))
        p300m.aspirate(40, aspirate_location)
        p300m.move_to(column[0].top())
        ctx.max_speeds['Z'] = None
        p300m.air_gap(20)
        p300m.dispense(100, waste_2.bottom(3.5))
        p300m.air_gap(20)
        p300m.drop_tip()

    # step 7: pause with message
    ctx.pause("Bead Drying. Move plate to Slot 2 (Blue GenSci rack).")

    # step 8: 43 ul water to NO MAG at 30 ul/sec, mix 6X to resuspend beads
    p300m.flow_rate.aspirate = flow_rate_elution
    p300m.flow_rate.dispense = flow_rate_elution
    for index, column in enumerate(no_mag.columns()[:num_cols]):
        p300m.pick_up_tip()
        p300m.aspirate(43, water.bottom(1))
        if index % 2 != 1:
            # offset to left (for even columns) to be closer to bead pellet
            dispense_location = column[0].bottom(clearance_elution).move(
             types.Point(x=-1*x_offset_elution, y=0, z=0))
        else:
            # offset to right (for odd columns) to be closer to bead pellet
            dispense_location = column[0].bottom(clearance_elution).move(
             types.Point(x=x_offset_elution, y=0, z=0))
        p300m.move_to(column[0].top())
        p300m.move_to(column[0].bottom(4))
        p300m.dispense(43, dispense_location)
        p300m.mix(6, 40, dispense_location)
        p300m.move_to(column[0].top())
        p300m.air_gap(20)
        p300m.drop_tip()

    # step 9: pause with message
    ctx.pause("""
    Incubate 2 min with beads. Move to Slot 3 (MagPlate).
    Resume when solution is clear.
    """)

    # step 10: 40 ul MAGPLATE eluate to CLEAN PLATE at 20 ul/sec
    p300m.flow_rate.aspirate = 20
    p300m.flow_rate.dispense = 20
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        p300m.pick_up_tip()
        if index % 2 != 1:
            # offset to right (for even columns) to avoid bead pellet
            aspirate_location = column[0].bottom(2).move(
             types.Point(x=x_offset_bead_pellet, y=0, z=0))
        else:
            # offset to left (for odd columns) to avoid bead pellet
            aspirate_location = column[0].bottom(2).move(
             types.Point(x=-1*x_offset_bead_pellet, y=0, z=0))
        p300m.move_to(column[0].top())
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(40, aspirate_location)
        p300m.dispense(40, clean_plate.columns()[index][0].bottom(0.5))
        p300m.mix(1, 20, clean_plate.columns()[index][0].bottom(0.5))
        p300m.move_to(clean_plate.columns()[index][0].top())
        p300m.air_gap(20)
        p300m.drop_tip()

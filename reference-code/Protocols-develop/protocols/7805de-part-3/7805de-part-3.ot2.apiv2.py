import math
from opentrons import types
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''NEBNext Ultra II Directional RNA Library Prep Kit
    for Illumina with poly(A) selection: part 3 -
    End Prep, Adapter Ligation and Bead Clean Up''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_pcr_plate,
     labware_reservoir, labware_tube_strip, clearance_sample_plate,
     clearance_reservoir, clearance_strip_tubes, clearance_bead_pellet,
     delay_beads, flow_rate_beads, engage_time, engage_offset, dry_time,
     x_offset_bead_pellet
     ] = get_values(  # noqa: F821
      'sample_count', 'labware_pcr_plate',
      'labware_reservoir', 'labware_tube_strip', 'clearance_sample_plate',
      'clearance_reservoir', 'clearance_strip_tubes', 'clearance_bead_pellet',
      'delay_beads', 'flow_rate_beads', 'engage_time', 'engage_offset',
      'dry_time', 'x_offset_bead_pellet')

    ctx.set_rail_lights(True)
    if not 1 <= sample_count <= 24:
        raise Exception('Invalid number of samples (must be 1-24).')

    # tips, p20 multi gen2, p300 multi gen2
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [2, 5]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    tips300 = [ctx.load_labware(
     "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [6, 9]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    """
    helper functions
    """

    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    def pick_up_or_refill(current_pipette):
        try:
            current_pipette.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             """Please Refill the {} Tip Boxes
             and Empty the Tip Waste""".format(current_pipette))
            current_pipette.reset_tipracks()
            current_pipette.pick_up_tip()

    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    def aspirate_with_delay(current_pipette, volume, source, delay_seconds):
        current_pipette.aspirate(volume, source)
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)

    def dispense_with_delay(current_pipette, volume, dest, delay_seconds):
        current_pipette.dispense(volume, dest)
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)

    def mix_with_delay(current_pipette, volume, location, delay_seconds):
        current_pipette.aspirate(volume, location)
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        current_pipette.dispense(volume, location)
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)

    def slow_tip_withdrawal(current_pipette, well_location, to_center=False):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            current_pipette.move_to(well_location.top())
        else:
            current_pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    def pre_wet(current_pipette, volume, location):
        for rep in range(2):
            current_pipette.aspirate(volume, location)
            current_pipette.dispense(volume, location)

    def set_default_clearances(
     current_pipette, aspirate_setting, dispense_setting):
        if 0 < aspirate_setting < 5 and 0 < dispense_setting < 5:
            current_pipette.well_bottom_clearance.aspirate = aspirate_setting
            current_pipette.well_bottom_clearance.dispense = dispense_setting

    def restore_default_clearances(current_pipette):
        current_pipette.well_bottom_clearance.aspirate = 1
        current_pipette.well_bottom_clearance.dispense = 1

    def viscous_flow_rates(current_pipette):
        current_pipette.flow_rate.aspirate = flow_rate_beads
        current_pipette.flow_rate.dispense = flow_rate_beads
        current_pipette.flow_rate.blow_out = flow_rate_beads

    def etoh_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2' or
           current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 92.86
            current_pipette.flow_rate.dispense = 92.86
            current_pipette.flow_rate.blow_out = 300

    def default_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2' or
           current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 92.86
            current_pipette.flow_rate.dispense = 92.86
            current_pipette.flow_rate.blow_out = 92.86
        elif (current_pipette.name == 'p20_multi_gen2' or
              current_pipette.name == 'p20_single_gen2'):
            current_pipette.flow_rate.aspirate = 7.56
            current_pipette.flow_rate.dispense = 7.56
            current_pipette.flow_rate.blow_out = 7.56

    def reuse_tips(current_pipette, which_tips):
        current_pipette.reset_tipracks()
        current_pipette.starting_tip = named_tips[which_tips]

    named_tips = {}

    def name_the_tips(tip_box, name_list, well_list):
        for name, well in zip(
         name_list, well_list):
            named_tips[name] = tip_box[well]

    ctx.delay(seconds=10)
    pause_attention("""
    Set up for End Prep and Adapter Ligation:

    sample plate (from part 2) in pre-chilled aluminum block on deck slot 7
    (50 ul double-stranded cDNA with
    up to 24 samples arranged in columns of 8).

    Reagents in strip tubes on 4 degree temp module:
    column 1 - end prep reaction buffer
    column 2 - end prep enzyme mix
    column 3 - diluted NEBNext adapter
    column 4 - NEBNext ligation enhancer
    column 5 - NEBNext Ligation Master Mix
    column 6 - USER enzyme

    p20 tips in slots 2 and 5
    p300 tips in slots 6 and 9
    """)

    ctx.comment("""
    reagent reservoir in deck slot 1:
    col 1 - beads
    col 2 - freshly prepared 80 percent ethanol
    col 4 - 0.1x TE
    col 10 - waste
    col 11 - waste
    col 12 - waste
    """)
    reagent_reservoir = ctx.load_labware(
     labware_reservoir, '1', 'Reagent Reservoir')
    [beads, etoh, te, waste_1, waste_2, waste_3] = [
     reagent_reservoir.wells_by_name()[
      well] for well in ['A1', 'A2', 'A4', 'A10', 'A11', 'A12']]

    ctx.comment("""
    mag plate on magnetic module
    """)
    mag = ctx.load_module('magnetic module gen2', '4')
    mag.disengage()
    mag_plate = mag.load_labware(labware_pcr_plate, 'Mag Plate')

    ctx.comment("""
    reagent block for tube strips on 4 degree temperature module
    """)
    temp = ctx.load_module('temperature module gen2', '3')
    reagent_block = temp.load_labware(labware_tube_strip, '4 Degree Block')
    [ep_rxn_bf, ep_enz, adapt, lig_enhance, lig_mm, user] = [
     reagent_block.columns_by_name()[str(name + 1)] for name in [*range(6)]]

    ctx.comment("""
    Sample plate in deck slot 7:
    on pre-chilled aluminum block
    containing 50 ul double-stranded cDNA
    samples arranged in columns of 8
    up to 24 samples total
    {} samples in this run
    """.format(str(sample_count)))
    num_cols = math.ceil(sample_count / 8)
    sample_plate = ctx.load_labware(
     "opentrons_96_aluminumblock_nest_wellplate_100ul", '7',
     'cDNA Sample Plate on Chilled Aluminum Block')

    ctx.comment("""
    elution plate in deck slot 8
    """)
    elution_plate = ctx.load_labware(labware_pcr_plate, '8', 'Elution Plate')

    ctx.comment("""
    end prep:
    add end prep reaction buffer
    add end prep enzyme mix
    mix thoroughly
    """)
    p20m.transfer(
     7, ep_rxn_bf[0].bottom(clearance_strip_tubes), [column[0].bottom(
      clearance_sample_plate) for column in sample_plate.columns()[
      :num_cols]], new_tip='always')
    p20m.transfer(
     3, ep_enz[0].bottom(clearance_strip_tubes), [column[0].bottom(
      clearance_sample_plate) for column in sample_plate.columns()[
      :num_cols]], new_tip='always')
    for column in sample_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        p300m.mix(10, 50, column[0].bottom(clearance_sample_plate))
        p300m.drop_tip()

    pause_attention("""
        pausing for off-deck steps

        first, spin the plate
        then, on thermocycler-

        30 min 20 C
        30 min 65 C
        hold 4 C

        immediately place plate in pre-chilled aluminum block
        and return to deck slot 7 for adapter ligation
        resume
        """)

    ctx.comment("""
    adapter ligation:
    add diluted adapter
    add ligation enhancer
    add ligation master mix
    mix thoroughly

    liquid handling method for master mix:
    slow flow rate for aspiration and dispense
    wait for liquid to finish moving after aspiration and dispense
    withdraw tip slowly from liquid
    """)
    p20m.transfer(
     2.5, adapt[0].bottom(clearance_strip_tubes), [column[0].bottom(
      clearance_sample_plate) for column in sample_plate.columns()[
      :num_cols]], new_tip='always')
    p20m.transfer(
     1, lig_enhance[0].bottom(clearance_strip_tubes), [column[0].bottom(
      clearance_sample_plate) for column in sample_plate.columns()[
      :num_cols]], new_tip='always')
    viscous_flow_rates(p300m)
    for column in sample_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        aspirate_with_delay(p300m, 30, lig_mm[0].bottom(
         clearance_strip_tubes), delay_beads)
        slow_tip_withdrawal(p300m, lig_mm[0])
        dispense_with_delay(p300m, 30, column[0].bottom(
         clearance_sample_plate), delay_beads)
        for repeat in range(10):
            mix_with_delay(p300m, 80, column[0].bottom(
             clearance_sample_plate), delay_beads)
        slow_tip_withdrawal(p300m, column[0])
        p300m.drop_tip()
    default_flow_rates(p300m)

    pause_attention("""
        pausing for off-deck steps

        spin

        thermocycler:
        15 min 20 C

        return the sample plate
        resume
        """)

    ctx.comment("""
    add USER enzyme
    mix
    """)
    for column in sample_plate.columns()[:num_cols]:
        pick_up_or_refill(p20m)
        p20m.aspirate(3, user[0].bottom(clearance_strip_tubes))
        p20m.dispense(3, column[0].bottom(clearance_sample_plate))
        p20m.drop_tip()
        p300m.pick_up_tip()
        p300m.mix(10, 50, column[0].bottom(clearance_sample_plate))
        p300m.drop_tip()

    pause_attention("""
        pausing for off-deck steps

        thermocycler:
        15 min 37 C

        return the sample plate to the magnetic module

        set up for bead clean up:
        replenish the tip boxes
        empty the tip waste
        add reagents to reservoir in deck slot 1:
        col 1 - beads
        col 2 - freshly prepared 80 percent ethanol
        col 4 - 0.1x TE
        place elution plate in deck slot 8
        resume
        """)
    p300m.reset_tipracks()
    p20m.reset_tipracks()
    ctx.comment("""
    bead clean up of ligation reaction
    move half the cDNA volume to a second well
    """)
    p300m.transfer(48, [column[0].bottom(
     clearance_sample_plate) for column in mag_plate.columns()[:num_cols]], [
     column[0].bottom(clearance_sample_plate) for column in mag_plate.columns(
     )[6:num_cols+6]], new_tip='always')

    ctx.comment("""
    add beads and mix, wait

    liquid handling method for beads:
    slow flow rate for aspiration and dispense
    wait for liquid to finish moving after aspiration and dispense
    withdraw tip slowly from liquid
    """)
    viscous_flow_rates(p300m)
    for column in mag_plate.columns()[
     :num_cols]+mag_plate.columns()[6:num_cols+6]:
        p300m.pick_up_tip()
        p300m.mix(3, 100, beads.bottom(clearance_reservoir), rate=2)
        aspirate_with_delay(p300m, 43.5, beads.bottom(
         clearance_reservoir), delay_beads)
        slow_tip_withdrawal(p300m, beads)
        dispense_with_delay(p300m, 43.5, column[0].bottom(
         clearance_sample_plate), delay_beads)
        p300m.mix(10, 50, column[0].bottom(2), rate=2)
        p300m.drop_tip()
    default_flow_rates(p300m)
    ctx.delay(minutes=10)
    pause_attention("""
    spin and return the plate
    resume
    """)
    mag.engage()
    ctx.delay(minutes=engage_time)
    ctx.comment("""
    remove sup

    add 80 percent ethanol
    remove sup
    repeat

    liquid handling method for ethanol:
    prewet tips
    15 ul air gap
    dispense from top
    repeated delayed blowout
    increased blow out flow rate
    """)
    for column in mag_plate.columns()[
     :num_cols]+mag_plate.columns()[6:num_cols+6]:
        pick_up_or_refill(p300m)
        if mag_plate.columns().index(column) % 2 != 1:
            # offset to left for odd col no to avoid bead pellet
            aspirate_location = column[0].bottom(
             clearance_bead_pellet).move(
             types.Point(x=-1*x_offset_bead_pellet, y=0, z=0))
        else:
            # offset to right for even col no to avoid bead pellet
            aspirate_location = column[0].bottom(
             clearance_bead_pellet).move(
             types.Point(x=x_offset_bead_pellet, y=0, z=0))
        p300m.move_to(column[0].top())
        ctx.max_speeds['Z'] = 10
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(50, column[0].bottom(4), rate=0.33)
        p300m.aspirate(50, aspirate_location, rate=0.33)
        p300m.move_to(column[0].top())
        ctx.max_speeds['Z'] = None
        p300m.air_gap(20)
        p300m.dispense(120, waste_1.top())
        p300m.air_gap(15)
        p300m.drop_tip()
    etoh_flow_rates(p300m)
    for repeat in range(2):
        pick_up_or_refill(p300m)
        for column in mag_plate.columns()[
         :num_cols]+mag_plate.columns()[6:num_cols+6]:
            pre_wet(p300m, 100, etoh.bottom(clearance_reservoir))
            p300m.aspirate(100, etoh.bottom(clearance_reservoir))
            p300m.air_gap(15)
            p300m.dispense(115, column[0].top())
            for rep in range(3):
                if rep > 0:
                    p300m.aspirate(100, column[0].top())
                ctx.delay(seconds=1)
                p300m.blow_out(column[0].top())
        p300m.drop_tip()
        if repeat == 0:
            wst = waste_2
            pause_attention(
             """Please Refill the p300 Tip Boxes
             and Empty the Tip Waste""")
            p300m.reset_tipracks()
        else:
            wst = waste_3
        for column in mag_plate.columns()[
         :num_cols]+mag_plate.columns()[6:num_cols+6]:
            pick_up_or_refill(p300m)
            if mag_plate.columns().index(column) % 2 != 1:
                # offset to left for odd col no to avoid bead pellet
                aspirate_location = column[0].bottom(
                 clearance_bead_pellet).move(
                 types.Point(x=-1*x_offset_bead_pellet, y=0, z=0))
            else:
                # offset to right for even col no to avoid bead pellet
                aspirate_location = column[0].bottom(
                 clearance_bead_pellet).move(
                 types.Point(x=x_offset_bead_pellet, y=0, z=0))
            p300m.move_to(column[0].top())
            ctx.max_speeds['Z'] = 10
            p300m.move_to(column[0].bottom(4))
            p300m.aspirate(60, column[0].bottom(4), rate=0.33)
            p300m.aspirate(50, aspirate_location, rate=0.33)
            p300m.move_to(column[0].top())
            ctx.max_speeds['Z'] = None
            p300m.air_gap(20)
            p300m.dispense(130, wst.top())
            for rep in range(3):
                if rep > 0:
                    p300m.aspirate(150, wst.top())
                ctx.delay(seconds=1)
                p300m.blow_out(wst.top())
            p300m.air_gap(15)
            p300m.drop_tip()
    default_flow_rates(p300m)
    mag.disengage()
    pause_attention("""
    remove plate, spin and return the plate to the magnetic module
    resume
    """)
    mag.engage()
    ctx.delay(minutes=1)
    pause_attention("""
    manually remove last traces of ethanol with 10 ul tip
    resume
    """)
    ctx.comment("""
    air dry beads
    """)
    ctx.delay(minutes=dry_time)
    mag.disengage()
    ctx.comment("""
    add TE and mix
    """)
    for column in mag_plate.columns()[
     :num_cols]+mag_plate.columns()[6:num_cols+6]:
        pick_up_or_refill(p20m)
        # offset to right to target beads (odd col numbers)
        if mag_plate.columns().index(column) % 2 != 1:
            f = 1
        # offset to left to target beads (even col numbers)
        else:
            f = -1
        p20m.transfer(
         8.5, te.bottom(clearance_reservoir), column[0].bottom(
          clearance_sample_plate).move(types.Point(
           x=f*x_offset_bead_pellet, y=0, z=0)
           ), mix_after=(10, 5), new_tip='never')
        p20m.drop_tip()
    pause_attention("""
    spin and return the plate
    resume
    """)
    ctx.delay(minutes=2)
    mag.engage()
    ctx.delay(minutes=engage_time)
    ctx.comment("""
    combine eluates and transfer to elution plate
    """)
    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        # offset to left to avoid beads (odd col numbers)
        if mag_plate.columns().index(column) % 2 != 1:
            f = -1
        # offset to right to avoid beads (even col numbers)
        else:
            f = 1
        p20m.aspirate(7.5, column[0].bottom(clearance_bead_pellet).move(
         types.Point(x=f*x_offset_bead_pellet, y=0, z=0)), rate=0.33)
        p20m.aspirate(
         7.5, mag_plate.columns()[index+6][0].bottom(
          clearance_bead_pellet).move(types.Point(
           x=f*x_offset_bead_pellet, y=0, z=0)), rate=0.33)
        p20m.dispense(
         15, elution_plate.columns()[index][0].bottom(clearance_sample_plate))
        p20m.drop_tip()

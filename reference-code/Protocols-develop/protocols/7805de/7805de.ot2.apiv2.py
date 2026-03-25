import math
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''NEBNext Ultra II Directional RNA Library Prep Kit
    for Illumina with poly(A) selection: part 1 -
    RNA Isolation, Fragmentation and Priming''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_pcr_plate,
     labware_reservoir, labware_tube_strip, clearance_reservoir,
     clearance_sample_plate, clearance_bead_pellet, clearance_strip_tubes,
     flow_rate_beads, delay_beads, engage_offset, engage_time, dry_time
     ] = get_values(  # noqa: F821
      'sample_count', 'labware_pcr_plate',
      'labware_reservoir', 'labware_tube_strip', 'clearance_reservoir',
      'clearance_sample_plate', 'clearance_bead_pellet',
      'clearance_strip_tubes', 'flow_rate_beads', 'delay_beads',
      'engage_offset', 'engage_time', 'dry_time')

    ctx.set_rail_lights(True)
    if not 1 <= sample_count <= 24:
        raise Exception('Invalid number of samples (must be 1-24).')

    # tips, p20 multi gen2, p300 multi gen2
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [2]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    tips300 = [
     ctx.load_labware(
      "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [6, 9]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    """
    helper functions
    """

    def pick_up_or_refill(current_pipette):
        try:
            current_pipette.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             """Please Refill the {} Tip Boxes
                and Empty the Tip Waste.""".format(current_pipette))
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
    Set up for RNA Isolation, Fragmentation, Priming:

    RNA sample plate in deck slot 7 (50 ul total RNA)
    (up to 24 samples arranged in columns of 8).

    Reagents in strip tubes on 4 degree temp module:
    column 1 - first-strand rxn bf/random primers
    (mixed and prepared see NEB instructions)

    p20 tips in slot 2, p300 tips in slot 6 and 9.
    """)

    ctx.comment("""
    reagent reservoir in deck slot 1:
    col 1 - washed (NEB instructions) oligo dT beads
    col 2 - wash buffer
    col 3 - Tris buffer
    col 4 - RNA binding buffer
    col 10,11,12 - waste
    """)
    reagent_reservoir = ctx.load_labware(
     labware_reservoir, '1', 'Reagent Reservoir')
    [oligo_dt_beads, wash_buffer,
     tris_buffer, rna_binding_buffer, waste_1, waste_2, waste_3] = [
     reagent_reservoir.wells_by_name()[well] for well in [
      'A1', 'A2', 'A3', 'A4', 'A10', 'A11', 'A12']]

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
    [fs_rxn_bf_random_primers] = [
     reagent_block.columns_by_name()[str(name + 1)] for name in [*range(1)]]

    ctx.comment("""
    RNA sample plate in deck slot 7:
    containing 50 ul total RNA
    samples arranged in columns of 8
    up to 24 samples total
    {} samples in this run
    """.format(str(sample_count)))
    num_cols = math.ceil(sample_count / 8)
    sample_plate = elution_plate = ctx.load_labware(
     labware_pcr_plate, '7', 'RNA Sample Plate')

    ctx.comment("""
    add beads to RNA and mix
    wait, engage magnet, wait

    liquid handling method for beads:
    slow flow rate for aspiration and dispense
    wait for liquid to finish moving after aspiration and dispense
    withdraw tip slowly from liquid
    """)
    viscous_flow_rates(p300m)
    for column in sample_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        p300m.mix(3, 100, oligo_dt_beads.bottom(clearance_reservoir), rate=2)
        aspirate_with_delay(p300m, 50, oligo_dt_beads.bottom(
         clearance_reservoir), delay_beads)
        slow_tip_withdrawal(p300m, oligo_dt_beads)
        dispense_with_delay(p300m, 50, column[0].bottom(
         clearance_sample_plate), delay_beads)
        p300m.mix(6, 50, column[0].bottom(3), rate=2)
        p300m.drop_tip()
    default_flow_rates(p300m)

    pause_attention("""
        pausing for off-deck thermocycler steps

        denaturation and binding:
        5 min 65 C
        30 sec 4 C

        return plate to the magnetic module and resume
        as soon as temperature reaches 4 degrees
        """)

    ctx.comment("""
        mix beads
        room temp 5 min
        engage magnets
        wait
        remove sup
        disengage magnet

        two repeats:
        add wash and mix
        engage magnets
        remove sup
        disengage magnets
        """)
    viscous_flow_rates(p300m)
    for column in mag_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        p300m.mix(6, 50, column[0].bottom(3), rate=2)
        slow_tip_withdrawal(p300m, column[0])
        p300m.drop_tip()
    default_flow_rates(p300m)
    ctx.delay(minutes=5)
    mag.engage(offset=engage_offset)
    ctx.delay(minutes=engage_time)
    for column in mag_plate.columns()[:num_cols]:
        p300m.pick_up_tip()
        p300m.aspirate(100, column[0].bottom(clearance_bead_pellet))
        p300m.air_gap(15)
        p300m.dispense(115, waste_1.top())
        p300m.air_gap(15)
        p300m.drop_tip()
    mag.disengage()
    for rep in range(2):
        for column in mag_plate.columns()[:num_cols]:
            pick_up_or_refill(p300m)
            p300m.aspirate(150, wash_buffer.bottom(clearance_reservoir))
            p300m.dispense(150, column[0].bottom(clearance_sample_plate))
            viscous_flow_rates(p300m)
            p300m.mix(10, 75, column[0].bottom(3), rate=2)
            slow_tip_withdrawal(p300m, column[0])
            default_flow_rates(p300m)
            p300m.drop_tip()
        mag.engage(offset=engage_offset)
        ctx.delay(minutes=engage_time)
        for column in mag_plate.columns()[:num_cols]:
            pick_up_or_refill(p300m)
            if rep == 0:
                wst = waste_1
            else:
                wst = waste_2
            p300m.aspirate(150, column[0].bottom(clearance_bead_pellet))
            p300m.air_gap(15)
            p300m.dispense(165, wst.top())
            p300m.air_gap(15)
            p300m.drop_tip()
        mag.disengage()

    ctx.comment("""
        add Tris buffer
        mix
        """)
    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        p300m.aspirate(50, tris_buffer.bottom(clearance_reservoir))
        p300m.dispense(50, column[0].bottom(clearance_sample_plate))
        viscous_flow_rates(p300m)
        p300m.mix(10, 25, column[0].bottom(2), rate=2)
        slow_tip_withdrawal(p300m, column[0])
        default_flow_rates(p300m)
        p300m.drop_tip()

    pause_attention("""
        pausing for off-deck thermocycler steps

        2 min 80 C
        30 sec 25 C

        return plate to magnetic module and resume
        """)

    ctx.comment("""
        add RNA binding buffer
        mix
        room temp 5 min
        engage magnets
        remove sup
        disengage magnets
        """)
    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        p300m.aspirate(50, rna_binding_buffer.bottom(clearance_reservoir))
        p300m.dispense(50, column[0].bottom(clearance_sample_plate))
        viscous_flow_rates(p300m)
        p300m.mix(10, 25, column[0].bottom(2), rate=2)
        slow_tip_withdrawal(p300m, column[0])
        default_flow_rates(p300m)
        p300m.drop_tip()
    ctx.delay(minutes=5)
    mag.engage(offset=engage_offset)
    ctx.delay(minutes=engage_time)
    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        p300m.aspirate(100, column[0].bottom(clearance_bead_pellet))
        p300m.air_gap(15)
        p300m.dispense(115, waste_2.top())
        p300m.air_gap(15)
        p300m.drop_tip()
    mag.disengage()
    ctx.comment("""
        add wash buffer
        mix
        """)
    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        p300m.aspirate(150, wash_buffer.bottom(clearance_reservoir))
        p300m.dispense(150, column[0].bottom(clearance_sample_plate))
        viscous_flow_rates(p300m)
        p300m.mix(10, 75, column[0].bottom(3), rate=2)
        slow_tip_withdrawal(p300m, column[0])
        default_flow_rates(p300m)
        p300m.drop_tip()
    ctx.comment("""
        engage magnets
        remove sup
        """)
    mag.engage(offset=engage_offset)
    ctx.delay(minutes=engage_time)
    for column in mag_plate.columns()[:num_cols]:
        pick_up_or_refill(p300m)
        p300m.aspirate(150, column[0].bottom(clearance_bead_pellet))
        p300m.air_gap(15)
        p300m.dispense(165, waste_3.top())
        p300m.air_gap(15)
        p300m.drop_tip()
    mag.disengage()
    pause_attention("""
        Remove and spin the plate.
        Then return it to the magnetic module. Resume.""")
    mag.engage(offset=engage_offset)
    ctx.delay(minutes=1)
    pause_attention("""
        Manually remove traces of supernatant with a 10 ul tip. Resume.""")
    mag.disengage()
    ctx.comment("""
        add first strand synthesis rxn bf random primer mix
        mix
        """)
    for column in mag_plate.columns()[:num_cols]:
        p20m.pick_up_tip()
        p20m.aspirate(
         11.5, fs_rxn_bf_random_primers[0].bottom(clearance_strip_tubes))
        p20m.dispense(11.5, column[0].bottom(clearance_sample_plate))
        p20m.mix(10, 5, column[0].bottom(1), rate=2)
        slow_tip_withdrawal(p20m, column[0])
        p20m.drop_tip()

    pause_attention("""
        pausing for off-deck thermocycler steps

        15 min 94 C
        ***plate on ice 1 min as it reaches 65 degrees***
        ***do not wait until plate reaches 4 degrees***
        30 sec 4 C

        spin plate
        return plate to magnetic module
        place fresh pcr plate in deck slot 7
        resume
        """)
    ctx.comment("""
        engage magnet
        wait
        transfer 10 ul sup to elution plate
        """)
    mag.engage(offset=engage_offset)
    ctx.delay(minutes=2)
    p20m.transfer(
     10, [column[0].bottom(
      clearance_bead_pellet) for column in mag_plate.columns()[
       :num_cols]], [column[0].bottom(
        clearance_sample_plate) for column in elution_plate.columns()[
        :num_cols]], new_tip='always')
    pause_attention("""
        put elution plate on ice
        proceed with first strand cDNA synthesis

        part 1 process steps
        RNA isolation, fragmentation and priming
        are complete
        """)

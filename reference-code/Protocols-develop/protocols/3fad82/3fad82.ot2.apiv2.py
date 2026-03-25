import math

metadata = {
    'protocolName': '''Quarter Volume NEBNext Ultra II DNA Library Prep Kit for
    Illumina: part 1''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_tips20, labware_pcr_plate, clearance_mm_plate,
     clearance_samp_plate, flow_rate_ligation_mx, delay_lig_mm
     ] = get_values(  # noqa: F821
      'sample_count', 'labware_tips20', 'labware_pcr_plate',
      'clearance_mm_plate', 'clearance_samp_plate', 'flow_rate_ligation_mx',
      'delay_lig_mm')

    ctx.set_rail_lights(True)

    # tips, p20 multi gen2
    tips20 = [ctx.load_labware(labware_tips20, str(slot)) for slot in [
     2, 3, 5, 6]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)

    """
    helper functions
    """
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

    def set_default_clearances(
     current_pipette, aspirate_setting, dispense_setting):
        if 0 < aspirate_setting < 5 and 0 < dispense_setting < 5:
            current_pipette.well_bottom_clearance.aspirate = aspirate_setting
            current_pipette.well_bottom_clearance.dispense = dispense_setting

    def restore_default_clearances(current_pipette):
        current_pipette.well_bottom_clearance.aspirate = 1
        current_pipette.well_bottom_clearance.dispense = 1

    def viscous_flow_rates(current_pipette):
        current_pipette.flow_rate.aspirate = flow_rate_ligation_mx
        current_pipette.flow_rate.dispense = flow_rate_ligation_mx
        current_pipette.flow_rate.blow_out = flow_rate_ligation_mx

    def default_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2'
           or current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 92.86
            current_pipette.flow_rate.dispense = 92.86
            current_pipette.flow_rate.blow_out = 92.86
        elif (current_pipette.name == 'p20_multi_gen2'
              or current_pipette.name == 'p20_single_gen2'):
            current_pipette.flow_rate.aspirate = 7.56
            current_pipette.flow_rate.dispense = 7.56
            current_pipette.flow_rate.blow_out = 7.56

    ctx.comment("""
    master mix plate in deck slot 4:
    col 1 - End Prep Enzyme Mx + End Prep Rxn Bf
    col 2 - Adapter
    col 3 - Ligation Master Mx + Ligation Enhancer
    col 4 - USER enzyme
    """)
    master_mix_plate = ctx.load_labware(
     labware_pcr_plate, '4', 'Master Mix Plate')
    [end_prep, adapter, lig_mm, user] = [master_mix_plate.columns_by_name()[
     str(column)] for column in [1, 2, 3, 4]]

    ctx.comment("""
    sample plate in thermocycler module:
    samples arranged in columns of 8
    up to 96 samples total
    {} samples in this run
    """.format(str(sample_count)))
    num_cols = math.ceil(sample_count / 8)
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    sample_plate = tc.load_labware(labware_pcr_plate, 'Sample Plate')

    ctx.comment("""
    add end prep mix to samples
    incubate in cycler:
    15 min 37 C, 30 min 65 C, hold 20 C
    """)
    for column in sample_plate.columns()[:num_cols]:
        p20m.transfer(2.25, end_prep[0].bottom(clearance_mm_plate), column[
         0].bottom(clearance_samp_plate), mix_after=(3, 4), new_tip='always')
    tc.close_lid()
    tc.set_lid_temperature(100)
    for temp, sec in zip([37, 65, 20], [900, 1800, 30]):
        tc.set_block_temperature(temp)
        ctx.delay(seconds=sec)
    tc.open_lid()
    tc.deactivate_lid()

    ctx.comment("""
    add adapter to samples
    """)
    for column in sample_plate.columns()[:num_cols]:
        p20m.transfer(1, adapter[0].bottom(clearance_mm_plate), column[
         0].bottom(clearance_samp_plate), new_tip='always')

    ctx.comment("""
    add ligation mix to samples
    mix
    incubate in cycler:
    15 min 20 C

    liquid handling method for ligation mix:
    slow flow rate for aspiration and dispense
    wait for liquid to finish moving after aspiration and dispense
    dispense to a surface
    withdraw tip slowly from liquid
    """)

    viscous_flow_rates(p20m)
    for column in sample_plate.columns()[:num_cols]:
        p20m.pick_up_tip()
        aspirate_with_delay(p20m, 7.75, lig_mm[0].bottom(
         clearance_mm_plate), delay_lig_mm)
        slow_tip_withdrawal(p20m, lig_mm[0])
        dispense_with_delay(p20m, 7.75, column[0].bottom(
         clearance_samp_plate), delay_lig_mm)
        for repeat in range(3):
            mix_with_delay(p20m, 10, column[0].bottom(
             clearance_samp_plate), delay_lig_mm)
        p20m.drop_tip()
    default_flow_rates(p20m)

    tc.close_lid()
    tc.set_block_temperature(20)
    ctx.delay(minutes=15)
    tc.open_lid()

    ctx.comment("""
    add USER enzyme to samples
    incubate in cycler:
    15 min 37 C, hold 4 C
    """)
    for column in sample_plate.columns()[:num_cols]:
        p20m.transfer(0.75, user[0].bottom(clearance_mm_plate), column[
         0].bottom(clearance_samp_plate), mix_after=(3, 8), new_tip='always')
    tc.close_lid()
    tc.set_lid_temperature(47)
    for temp, sec in zip([37, 4], [900, 30]):
        tc.set_block_temperature(temp)
        ctx.delay(seconds=sec)

    pause_attention(
     """Process steps for part 1 are complete. Click resume to open the
     cycler lid. Proceed to part 2.""")
    tc.open_lid()

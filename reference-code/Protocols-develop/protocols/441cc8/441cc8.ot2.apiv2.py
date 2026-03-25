metadata = {
    'protocolName': '''Prepare Stock Plates for Indexing with Universal
    Illumina Primers''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [flow_rate_mm, delay_distribute, delay_reagent_prep, clearance_distribute,
     clearance_reagent_prep, p300m_side, labware_pcr_plate, labware_200ul_tips,
     labware_reservoir
     ] = get_values(  # noqa: F821
      'flow_rate_mm', 'delay_distribute', 'delay_reagent_prep',
      'clearance_distribute', 'clearance_reagent_prep', 'p300m_side',
      'labware_pcr_plate', 'labware_200ul_tips', 'labware_reservoir')

    # tips, p300 multi
    tips300 = [ctx.load_labware(labware_200ul_tips, '7')]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", p300m_side, tip_racks=tips300)

    """
    helper functions
    """
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
        current_pipette.flow_rate.aspirate = flow_rate_mm
        current_pipette.flow_rate.dispense = flow_rate_mm
        current_pipette.flow_rate.blow_out = flow_rate_mm

    def default_flow_rates(current_pipette):
        current_pipette.flow_rate.aspirate = 94
        current_pipette.flow_rate.dispense = 94
        current_pipette.flow_rate.blow_out = 94

    """
    master mix in A1 of reservoir in deck slot 10
    pcr plates in slot order according to plate map
    primer plate is last pcr plate in slot 4
    """
    reservoir = ctx.load_labware(labware_reservoir, '10')
    mm = reservoir.wells_by_name()['A1']
    [*pcr_plates] = [ctx.load_labware(labware_pcr_plate, str(
     slot)) for slot in [1, 2, 3, 6, 9, 11, 8, 5, 4]]
    primer_plate = pcr_plates[-1]

    ctx.comment("""
    suspend primer column in master mix
    distribute 14 ul to corresponding column of each pcr plate

    liquid handling method for master mix:
    slow flow rate for aspiration and dispense
    wait for liquid to finish moving after aspiration and dispense
    avoid introducing air into liquid (avoid complete dispenses)
    dispense to a surface
    withdraw tip slowly from liquid
    """)
    viscous_flow_rates(p300m)
    for index, column in enumerate(primer_plate.columns()):
        set_default_clearances(
         p300m, clearance_reagent_prep, clearance_reagent_prep)
        p300m.pick_up_tip()
        for repeat in range(10):
            mix_with_delay(p300m, 180, mm, delay_seconds=delay_reagent_prep)
        aspirate_with_delay(p300m, 130, mm, delay_reagent_prep)
        slow_tip_withdrawal(p300m, mm)
        dispense_with_delay(
         p300m, 120, column[0], delay_seconds=delay_reagent_prep)
        for repeat in range(10):
            mix_with_delay(
             p300m, 100, column[0], delay_seconds=delay_reagent_prep)
        set_default_clearances(
         p300m, clearance_distribute, clearance_distribute)
        aspirate_with_delay(
         p300m, 125, column[0], delay_seconds=delay_reagent_prep)
        slow_tip_withdrawal(p300m, column[0])
        for plate in pcr_plates:
            dispense_with_delay(
             p300m, 14, plate.columns()[index][0],
             delay_seconds=delay_distribute)
            slow_tip_withdrawal(p300m, plate.columns()[index][0])
        p300m.return_tip()

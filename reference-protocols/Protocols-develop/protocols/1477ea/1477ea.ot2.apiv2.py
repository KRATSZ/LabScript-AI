from types import MethodType
import csv

metadata = {
    'protocolName': 'Cherrypicking Final',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [park_tips, reduced_speed_limit, uploaded_csv] = get_values(  # noqa: F821
        "park_tips", "reduced_speed_limit", "uploaded_csv")

    # lines from uploaded csv file
    [*csv_lines] = uploaded_csv.splitlines()
    csv_reader = csv.DictReader(csv_lines)

    # tips, p300 multi, p20 single, LB reservoir, source and destination plates
    tips300 = [ctx.load_labware(
     'opentrons_96_filtertiprack_200ul', str(slot)) for slot in [10, 11]]
    p300m = ctx.load_instrument("p300_multi_gen2", 'left', tip_racks=tips300)

    # empty tiprack for parking 200 ul tips from step 2
    if park_tips:
        park300 = ctx.load_labware(
         'opentrons_96_filtertiprack_200ul', '9', 'DROP USED 200ul TIPS HERE')
        spots300 = park300.rows()[0]

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '7')]
    p20s = ctx.load_instrument("p20_single_gen2", 'right', tip_racks=tips20)

    # empty tiprack for parking 20 ul tips from steps 3 and 4
    if park_tips:
        park20 = ctx.load_labware(
         'opentrons_96_filtertiprack_20ul', '3', 'DROP USED 20ul TIPS HERE')
        spots20 = park20.wells()

    # set default flow rates for p20 to match PD tool default values
    p20s.flow_rate.aspirate = 3.78
    p20s.flow_rate.dispense = 3.78

    [lb, source, dest] = [ctx.load_labware(
     labware, str(slot), display_name) for labware, slot, display_name in zip(
     ['nest_1_reservoir_195ml', 'white_96well_plate_340ul',
      'tpp_96well_plate_340ul'
      ], [5, 8, 6], [
      'NEST 1 WELL RESERVOIR 195 ML', 'SOURCE', 'DESTINATION'])]

    # unbound method
    def slow_tip_withdrawal(self, speed_limit, well_location, to_center=False):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        previous_limit = None
        if axis in ctx.max_speeds.keys():
            for key, value in ctx.max_speeds.items():
                if key == axis:
                    previous_limit = value
        ctx.max_speeds[axis] = speed_limit
        if to_center is False:
            self.move_to(well_location.top())
        else:
            self.move_to(well_location.center())
        ctx.max_speeds[axis] = previous_limit

    # bind method to pipette
    for pipette_object in [p20s, p300m]:
        for method in [slow_tip_withdrawal]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # apply speed limit to X-,Y-,A- and Z-axis motion
    if reduced_speed_limit:
        ctx.max_speeds['X'] = 250
        ctx.max_speeds['Y'] = 250
        ctx.max_speeds['A'] = 250
        ctx.max_speeds['Z'] = 250

    # step 1: p300m transfer 198 ul LB to destination columns with same tips
    p300m.transfer(198, lb['A1'].bottom(3), [
     column[0].bottom(1.5) for column in dest.columns()])

    # step 2: p300m mix 10 columns of SOURCE 80 ul 5X
    for index, column in enumerate(source.columns()[1:11]):
        p300m.pick_up_tip()
        p300m.mix(5, 80, column[0].bottom(1.5))
        p300m.slow_tip_withdrawal(10, column[0])
        p300m.air_gap(15)
        if park_tips:
            p300m.drop_tip(spots300[index])
        else:
            p300m.drop_tip()

    # step 3: p20s 2 ul SOURCE A2, A11, 30 custom to DESTINATION top
    # step 4: p20s 2 ul SOURCE 30 custom, H2, H11 to DESTINATION bottom
    # top dispense of air gap volume to replicate PD tool behavior
    for index, line in enumerate(csv_reader):
        p20s.pick_up_tip()
        p20s.aspirate(2, source.wells_by_name()[line['source well']].bottom(1))
        p20s.slow_tip_withdrawal(
         10, source.wells_by_name()[line['source well']])
        p20s.air_gap(2)
        p20s.dispense(2, dest.wells_by_name()[line['destination well']].top())
        p20s.dispense(
         2, dest.wells_by_name()[line['destination well']].bottom(0.5))
        p20s.mix(
         5, 5, dest.wells_by_name()[line['destination well']].bottom(0.5))
        p20s.slow_tip_withdrawal(
         10, dest.wells_by_name()[line['destination well']])
        p20s.air_gap(5)
        if park_tips:
            p20s.drop_tip(spots20[index])
        else:
            p20s.drop_tip()

    # park step 5 tips in empty tiprack in slot 10
    if park_tips:
        spots300 = tips300[0].rows()[0]

    # step 5: p300m mix columns of DESTINATION 80 ul 5X
    for index, column in enumerate(dest.columns()):
        p300m.pick_up_tip()
        p300m.mix(5, 80, column[0].bottom(1.5))
        p300m.slow_tip_withdrawal(10, column[0])
        p300m.air_gap(15)
        if park_tips:
            p300m.drop_tip(spots300[index])
        else:
            p300m.drop_tip()

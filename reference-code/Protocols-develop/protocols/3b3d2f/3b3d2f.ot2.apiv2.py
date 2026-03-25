import csv

metadata = {
    'protocolName': 'Plate Loading for ddPCR',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [plate_count, clearance_ddpcr_plate, clearance_water, plate_map_1_csv,
     plate_map_2_csv, plate_map_3_csv, plate_map_4_csv
     ] = get_values(  # noqa: F821
        "plate_count", "clearance_ddpcr_plate", "clearance_water",
        "plate_map_1_csv", "plate_map_2_csv", "plate_map_3_csv",
        "plate_map_4_csv")

    plate_map_csv = [
     plate_map_1_csv, plate_map_2_csv, plate_map_3_csv, plate_map_4_csv]

    # tips, p20 single
    tips20 = [ctx.load_labware(
     'opentrons_96_filtertiprack_20ul', str(slot)) for slot in [10, 11]]
    p20s = ctx.load_instrument("p20_single_gen2", 'right', tip_racks=tips20)

    # ddPCR plate and temperature block
    [ddpcr_plate] = [
     ctx.load_labware(
      labware, str(slot), display_name) for labware, slot, display_name in zip(
      ['biorad_96_wellplate_200ul_pcr'], [5], ['ddPCR Plate'])]
    temp = ctx.load_module('temperature module gen2', '3')
    tube_block = temp.load_labware(
     'opentrons_24_aluminumblock_nest_2ml_snapcap', '4 Degree Tube Block')
    temp.set_temperature(4)

    # to yield next available temperature block well
    def block_wells():
        well_list = tube_block.wells()+["reload block"]+tube_block.wells()
        yield from well_list

    # to load ddPCR plate according to uploaded plate map
    def load_plate(text_string, source, clearance):
        for key, column in zip(map_columns.keys(), ddpcr_plate.columns()):
            for index, value in enumerate(map_columns[key]):
                if text_string in value:
                    p20s.pick_up_tip()
                    p20s.aspirate(5.5, source.bottom(clearance))
                    p20s.dispense(
                     5.5, column[index].bottom(clearance_ddpcr_plate))
                    slow_tip_withdrawal(p20s, column[index])
                    p20s.drop_tip()

    # helper function to apply speed limit to departing tip
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

    for rep in range(plate_count):

        # to yield next available well
        block_well = block_wells()

        ctx.delay(seconds=10)
        ctx.pause("""Please load reaction mix (first), water (second), then
                     plate map number {} samples (third and beyond) in
                     column-wise order like A1-D1, A2-D2 etc. into pre-chilled
                     4 degree temperature block. If samples exceed block
                     capacity, the OT-2 will automatically pause for
                     re-loading at the right time. Please make sure the tip
                     boxes are full to start when loading a new plate.
                     """.format(str(rep+1)))
        p20s.reset_tipracks()

        # plate map data lines from uploaded csv
        first_empty_line, *csv_lines = plate_map_csv[rep].splitlines()
        map_columns = {}
        for line in csv.DictReader(csv_lines):
            for num in range(12):
                if str(num+1) in map_columns:
                    map_columns[str(num+1)].append(line[str(num+1)])
                else:
                    map_columns[str(num+1)] = []
                    map_columns[str(num+1)].append(line[str(num+1)])

        # number of wells to fill based on plate map
        wells_to_fill = 0
        for key in map_columns.keys():
            for text_string in map_columns[key]:
                if text_string:
                    wells_to_fill += 1

        # starting clearance to avoid over-immersion of tip
        starting_clearance = (wells_to_fill*0.24) + 1

        # step 1: 16.5 ul rxn mix to ddPCR plate wells receiving a sample
        reaction_mixture = next(block_well)
        p20s.pick_up_tip()
        p20s.aspirate(
         3.5, reaction_mixture.bottom(starting_clearance), rate=0.5)
        ctx.delay(seconds=2)
        for key, column in zip(map_columns.keys(), ddpcr_plate.columns()):
            for index, value in enumerate(map_columns[key]):
                if value:
                    p20s.aspirate(16.5, reaction_mixture.bottom(
                     starting_clearance), rate=0.5)
                    ctx.delay(seconds=2)
                    slow_tip_withdrawal(p20s, reaction_mixture)
                    starting_clearance -= 0.24
                    p20s.dispense(16.5, column[index].bottom(
                     clearance_ddpcr_plate), rate=0.5)
                    slow_tip_withdrawal(p20s, column[index])
                    ctx.delay(seconds=2)
                    if starting_clearance < 1:
                        starting_clearance = 1
        p20s.drop_tip()

        # step 2: add 5.5 ul water to NTC wells shown in plate map
        water = next(block_well)
        load_plate("NTC", water, clearance_water)

        # step 3: add 5.5 ul sample RNA template to wells shown in plate map
        replicate = None
        for key, column in zip(map_columns.keys(), ddpcr_plate.columns()):
            for index, value in enumerate(map_columns[key]):
                if "Sample" in value:
                    if value != replicate:
                        source = next(block_well)
                    if source == "reload block":
                        ctx.pause("""Please load remaining samples in
                                     column-wise order starting with A1 like
                                     A1-D1, A2-D2 etc.) and
                                     postive control (last) in temperature
                                     block.""")
                        source = next(block_well)
                    p20s.pick_up_tip()
                    p20s.aspirate(5.5, source.bottom(clearance_water))
                    p20s.dispense(
                     5.5, column[index].bottom(clearance_ddpcr_plate))
                    slow_tip_withdrawal(p20s, column[index])
                    p20s.drop_tip()
                    replicate = value

        # step 4: add 5.5 ul positive control RNA to wells shown in plate map
        pos_ctrl = next(block_well)
        load_plate("+Control", pos_ctrl, clearance_water)

import math

metadata = {
    "protocolName": "Anti-PEG ELISA",
    "author": "Steve Plonk <protocols@opentrons.com>",
    "apiLevel": "2.9"
}


def run(ctx):

    # get parameter values from json
    [sample_count, labware_tube_rack, labware_sample_plate,
     labware_elisa_plate, clearance_sample_tube,
     clearance_sample_prep] = get_values(  # noqa: F821
      "sample_count", "labware_tube_rack", "labware_sample_plate",
      "labware_elisa_plate", "clearance_sample_tube", "clearance_sample_prep")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if not 1 <= sample_count <= 56:
        raise Exception('Invalid number of samples (must be 1-56).')

    # tips, p300 multi, p300 single
    tips300 = [
     ctx.load_labware(
      'opentrons_96_tiprack_300ul', str(slot)) for slot in [10, 11]]
    p300m = ctx.load_instrument("p300_multi_gen2", 'left', tip_racks=tips300)
    p300s = ctx.load_instrument("p300_single_gen2", 'right', tip_racks=tips300)

    # 24 tube racks, sample plates, ELISA plates
    [*tube_racks] = [ctx.load_labware(labware_tube_rack, str(
     slot), "24 Tube Rack") for slot in [1, 4, 7]]
    [*sample_plates] = [ctx.load_labware(labware_sample_plate, str(
     slot), "Sample Plate") for slot in [2, 5]]
    [*elisa_plates] = [ctx.load_labware(labware_elisa_plate, str(
     slot), "ELISA Plate") for slot in [3, 6, 9]]

    # to yield well pairs
    def pairs(plate):
        pairs = []
        for column, next_column in zip(plate.columns()[
         ::2], plate.columns()[1::2]):
            for well, next_well in zip(column, next_column):
                pair = (well, next_well)
                pairs.append(pair)
        yield from pairs

    # to yield next plate
    def get_plate(plates):
        yield from plates

    sp_plate = get_plate(sample_plates)
    sp_wells = pairs(next(sp_plate))

    # IgG, IgM, IgE standards
    standards = [tube_racks[2][well] for well in ["A4", "A5", "A6"]]

    # standards serial dilution
    [*serial_dilutions] = [sample_plates[1].columns_by_name()[
     name] for name in ['5', '7', '9']]

    # transfer samples to sample prep plates in duplicate
    working_sample_count = sample_count
    for i, rack in enumerate(tube_racks[:math.ceil(sample_count / 24)]):
        if working_sample_count < 24:
            index = working_sample_count
        else:
            index = 24
        for tube in rack.wells()[:index]:
            p300s.pick_up_tip()
            p300s.aspirate(50, tube.bottom(clearance_sample_tube))
            try:
                pair = next(sp_wells)
            except StopIteration:
                sp_wells = pairs(next(sp_plate))
                pair = next(sp_wells)
            p300s.dispense(25, pair[0].top())
            p300s.dispense(25, pair[1].bottom(clearance_sample_prep))
            p300s.mix(3, 100, pair[1].bottom(clearance_sample_prep))
            p300s.drop_tip()
        working_sample_count -= 24

    # serial dilution of IgG, IgM and IgE standards
    for index, standard in enumerate(standards):
        p300s.transfer(70, standard.bottom(
         clearance_sample_tube), serial_dilutions[index][0].bottom(
         clearance_sample_prep), mix_after=(3, 100))
    for series in serial_dilutions:
        for well, next_well in zip(series[:8], series[1:]):
            p300s.transfer(70, well.bottom(
             clearance_sample_prep), next_well.bottom(
             clearance_sample_prep), mix_after=(3, 100))

    # 56 samples to ELISA plates
    working_sample_count = sample_count
    num_cols = 2*math.ceil(working_sample_count / 8)
    for index, column in enumerate(
     (sample_plates[0].columns()+sample_plates[1].columns())[:num_cols]):
        if not p300m.has_tip:
            p300m.pick_up_tip()
        if index % 2 == 0:
            row_index = 0
            col_index = index
            p300m.mix(3, 100, column[0].bottom(clearance_sample_prep))
        else:
            row_index = 1
            col_index = index - 1
        p300m.aspirate(225, column[0].bottom(clearance_sample_prep))
        col = int(3*(col_index / 2))
        for plate in elisa_plates:
            for well in plate.rows()[row_index][col:3+col]:
                p300m.dispense(25, well.top())
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
        if row_index == 1:
            p300m.drop_tip()

    # standard curves to ELISA plates
    for col, index in zip([4, 6, 8], [0, 1, 2]):
        p300m.pick_up_tip()
        p300m.aspirate(
         100, sample_plates[1].columns()[col][0].bottom(clearance_sample_prep))
        for column in elisa_plates[index].columns()[22:24]:
            p300m.dispense(25, column[0].top())
            p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
            p300m.dispense(25, column[1].top())
            p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
        p300m.drop_tip()

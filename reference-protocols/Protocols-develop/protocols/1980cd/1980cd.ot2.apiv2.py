metadata = {
    "apiLevel": "2.5",
    "protocolName": "Sarah Daley Protocol (check mesoscale.com link)",
    "author": ""}


def run(ctx):

    step, test_plates = get_values(  # noqa: F821
            'step', 'test_plates')

    if step == 1:
        tip_rack = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '1')]
        p300m = ctx.load_instrument(
            'p300_multi_gen2', "right", tip_racks=tip_rack)

        trough = ctx.load_labware(
            'nest_1_reservoir_195ml',
            '2',
            label='Blocking solution').wells()[0]
        plates = [ctx.load_labware('nest_96_wellplate_200ul_flat', str(
            i), label='Plate {}'.format(i))
            for i in range(3, 12)[:test_plates]]
        for plate in plates:
            p300m.pick_up_tip()
            [p300m.transfer(150, trough, col, new_tip='never')
             for col in plate.rows()[0]]
            p300m.drop_tip()

    if step == 2:
        tip_rack = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '1')]
        p300m = ctx.load_instrument(
            'p300_multi_gen2', "right", tip_racks=tip_rack)

        reagents = ctx.load_labware(
            'nest_12_reservoir_15ml', '2', label='Controls')
        control_1 = reagents.wells_by_name()["A1"]
        control_2 = reagents.wells_by_name()["A2"]

        sample_plate = ctx.load_labware(
            'nest_96_wellplate_200ul_flat', '3', label='Sample plate')
        test_plate_1 = ctx.load_labware(
            'nest_96_wellplate_200ul_flat', '5', label='First test plate')
        test_plate_2 = ctx.load_labware(
            'nest_96_wellplate_200ul_flat',
            '6',
            label='Second test plate')

        for control, well in [(control_1, "A1"), (control_2, "A2")]:
            p300m.pick_up_tip()
            for transfer_well in [
                    test_plate_1.wells_by_name()[well],
                    test_plate_2.wells_by_name()[well]]:
                p300m.transfer(150, control, transfer_well, new_tip='never')
            p300m.drop_tip()

        for test_plate, well_list in [
            (test_plate_1, [
                "A1", "A2", "A3", "A4", "A5"]), (test_plate_2, [
                "A8", "A9", "A10", "A11", "A12"])]:
            for i, from_well in enumerate(
                    [sample_plate.wells_by_name()[well]
                        for well in well_list]):
                p300m.pick_up_tip()
                for destination in [test_plate.columns()[col]
                                    for col in
                                    range(2 + (i * 2), 4 + (i * 2))]:
                    p300m.transfer(
                        150, from_well, destination, new_tip='never')
                p300m.drop_tip()

    if step == 3:
        tip_racks = [
            ctx.load_labware(
                'opentrons_96_filtertiprack_200ul',
                x) for x in [
                '1',
                '4']]
        p300m = ctx.load_instrument(
            'p300_multi_gen2', "right", tip_racks=tip_racks)

        test_plate_1 = ctx.load_labware(
            'nest_96_wellplate_200ul_flat', '5', label='First test plate')
        test_plate_2 = ctx.load_labware(
            'nest_96_wellplate_200ul_flat',
            '6',
            label='Second test plate')

        reagents = ctx.load_labware(
            'nest_12_reservoir_15ml',
            '2',
            label='Detection Antibody')
        detection_antibody = reagents.wells_by_name()["A3"]

        for plate in [test_plate_1, test_plate_2]:
            for col in plate.rows()[0]:
                p300m.transfer(25, detection_antibody, col)

    if step == 4:
        tip_racks = [
            ctx.load_labware(
                'opentrons_96_filtertiprack_200ul',
                x) for x in [
                '1',
                '4']]
        p300m = ctx.load_instrument(
            'p300_multi_gen2', "right", tip_racks=tip_racks)

        test_plate_1 = ctx.load_labware(
            'nest_96_wellplate_200ul_flat', '5', label='First test plate')
        test_plate_2 = ctx.load_labware(
            'nest_96_wellplate_200ul_flat',
            '6',
            label='Second test plate')

        trough = ctx.load_labware(
            'nest_1_reservoir_195ml',
            '2',
            label='Read buffer').wells()[0]

        for plate in [test_plate_1, test_plate_2]:
            for col in plate.rows()[0]:
                p300m.transfer(150, trough, col)

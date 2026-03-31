metadata = {
    "protocolName": "Nanomaterial toxicity assay",
    "author": "",
    "apiLevel": "2.0"}


def run(ctx):

    step = get_values(  # noqa: F821
            'step')
    final_plate = ctx.load_labware(
        'corning_384_wellplate_112ul_flat',
        '3',
        label='Experimental nanoparticle plate')
    if step == 1:
        p20_tip_rack = [ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '1')]
        p300_tip_racks = [
            ctx.load_labware(
                'opentrons_96_filtertiprack_200ul',
                x) for x in [
                '4',
                '7',
                '10',
                '11']]

        p300m = ctx.load_instrument(
            'p300_multi_gen2',
            "right",
            tip_racks=p300_tip_racks)
        p20m = ctx.load_instrument(
            'p20_multi_gen2', "left", tip_racks=p20_tip_rack)

        water = ctx.load_labware(
            'nest_1_reservoir_195ml',
            '2',
            label='DI H2O').wells()[0]
        reagents = ctx.load_labware(
            'nest_12_reservoir_15ml', '5', label='Nanoparticles')

        GO_10 = reagents.wells_by_name()['A1']
        GO_100 = reagents.wells_by_name()['A2']
        MoS2 = reagents.wells_by_name()['A3']
        MoS2_10 = reagents.wells_by_name()['A4']
        MoSe2 = reagents.wells_by_name()['A5']
        MoSe2_10 = reagents.wells_by_name()['A6']

        GO_MoS2_plate = ctx.load_labware(
            'nest_96_wellplate_200ul_flat', '9', label='GO/MoS2 prep plate')
        MoSe2_plate = ctx.load_labware(
            'nest_96_wellplate_200ul_flat',
            '6',
            label='MoSe2 prep plate')

        GO_MoS2_load = [(GO_10, 67),
                        (GO_10, 13),
                        (GO_10, 7),
                        (GO_10, 1),
                        (GO_100, 3),
                        (None, 0),
                        (MoS2, 72),
                        (MoS2, 14),
                        (MoS2, 7),
                        (MoS2, 1),
                        (MoS2_10, 3),
                        (None, 0)]
        MoSe2_load = [(MoSe2, 36),
                      (MoSe2, 7),
                      (MoSe2, 4),
                      (MoSe2_10, 7),
                      (MoSe2_10, 1),
                      (None, 0)]

        for plate, load in zip([GO_MoS2_plate, MoSe2_plate], [
                               GO_MoS2_load, MoSe2_load]):
            for command, col in zip(load, plate.rows()[0][:len(load)]):
                source = command[0]
                vol = command[1]
                p300m.transfer(200 - vol, water, col)
                if source is not None:
                    if vol > 20:
                        p = p300m
                    else:
                        p = p20m
                    p.transfer(vol, source, col)

        for source_cols, target_cols in zip([
            GO_MoS2_plate.rows()[0][:6],
            GO_MoS2_plate.rows()[0][6:],
            MoSe2_plate.rows()[0][:6]],
            [[final_plate.wells_by_name()["A{}".format(i)] for i in r] for r in
                [range(2, 8), range(9, 15), range(16, 22)]]):
            for source_col, target_col in zip(source_cols, target_cols):
                p300m.transfer(25, source_col, target_col, mix_before=(3, 50))

    if step == 2 or step == 3:
        p300_tip_racks = [
            ctx.load_labware(
                'opentrons_96_filtertiprack_200ul',
                x) for x in [
                '1',
                '4',
                '7',
                '8',
                '10',
                '11']]
        p300m = ctx.load_instrument(
            'p300_multi_gen2',
            "right",
            tip_racks=p300_tip_racks)
        pbs = ctx.load_labware(
            'nest_1_reservoir_195ml',
            '2',
            label='10% PBS').wells()[0]
        liquid_trash = ctx.load_labware(
            'nest_1_reservoir_195ml',
            '6',
            label='Liquid Trash').wells()[0]

        final_plate_columns = [
            final_plate.wells_by_name()[
                "A{}".format(i)] for i in list(
                range(
                    2,
                    8)) +
            list(
                range(
                    9,
                    15)) +
            list(
                range(
                    16,
                    22))]
        for _ in range(0, 3):
            for col in final_plate_columns:
                # Better way to do this?
                p300m.pick_up_tip()
                p300m.aspirate(50, pbs)
                p300m.dispense(50, col)
                p300m.aspirate(50, col)
                p300m.dispense(50, liquid_trash)
                p300m.drop_tip()

        if step == 2:
            cells = ctx.load_labware(
                'nest_1_reservoir_195ml',
                '5',
                label='Bacterial cells and media').wells()[0]
            for col in final_plate_columns:
                p300m.transfer(100, cells, col)

        if step == 3:
            for col in final_plate_columns:
                p300m.transfer(100, col, liquid_trash)
                p300m.transfer(50, pbs, col)

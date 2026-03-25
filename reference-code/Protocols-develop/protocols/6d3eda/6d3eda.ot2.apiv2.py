from opentrons import protocol_api

metadata = {"apiLevel": "2.5"}


def run(ctx):
    # Add tip tracking to this protocol
    count, volume, input_labware, output_labware = get_values(  # noqa: F821
            'sample_count', 'volume', 'input_labware', 'output_labware')
    sample_plates = [ctx.load_labware(input_labware, '2')]
    target_plates = [ctx.load_labware(output_labware, '5')]
    tip_racks = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '1')]
    if count > 24:
        sample_plates.append(ctx.load_labware(input_labware, '3'))
        target_plates.append(ctx.load_labware(output_labware, '6'))

    # Variable pipettes?
    p300s = ctx.load_instrument(
            'p300_single_gen2', "right", tip_racks=tip_racks)

    for i, sample_plate in enumerate(sample_plates):
        for well_num, well in enumerate(sample_plate.wells()[:count-(i*24)]):
            try:
                p300s.pick_up_tip()
            except protocol_api.labware.OutOfTipsError:
                ctx.pause("Replace the tips")
                p300s.reset_tipracks()
                p300s.pick_up_tip()
            p300s.transfer(volume, well, target_plates[i].wells()[well_num],
                           blow_out=True, new_tip='never')
            p300s.drop_tip()

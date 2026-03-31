import math

metadata = {
    'protocolName': 'Agar Plating',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_plates, num_samples, transfer_vol, source_plate, pipette_type,
     pipette_mount, tip_type, puncture_agar,
     puncture_depth, mix_sources] = get_values(  # noqa: F821
        'num_plates', 'num_samples', 'transfer_vol', 'source_plate',
        'pipette_type', 'pipette_mount', 'tip_type', 'puncture_agar',
        'puncture_depth', 'mix_sources')

    tiprack20 = ctx.load_labware(tip_type, '1', '20µl tiprack')
    source_plate = ctx.load_labware(source_plate, '2', 'source plate')
    agar_plates = [
        ctx.load_labware('nunc_rectangular_agar_plate', slot,
                         'agar plate ' + str(i+1))
        for i, slot in enumerate(
            ['3', '4', '5', '6', '7', '8', '9', '10', '11'])]

    p20 = ctx.load_instrument(pipette_type, pipette_mount,
                              tip_racks=[tiprack20])
    if p20.type == 'single':
        sources = source_plate.wells()[:num_samples]
        dest_sets = [
            [plate.wells()[i] for plate in agar_plates]
            for i in range(num_samples)]
    else:
        num_cols = math.ceil(num_samples/8)
        sources = source_plate.rows()[0][:num_cols]
        dest_sets = [
            [plate.rows()[0][i] for plate in agar_plates]
            for i in range(num_cols)]

    for source, dest_set in zip(sources, dest_sets):
        p20.pick_up_tip()
        for i, d in enumerate(dest_set):
            if i == 0 and mix_sources:
                p20.mix(5, 10, source)
            p20.aspirate(transfer_vol, source)
            if puncture_agar:
                p20.move_to(d.bottom(-1*puncture_depth))
            p20.dispense(transfer_vol, d.bottom())
        p20.drop_tip()

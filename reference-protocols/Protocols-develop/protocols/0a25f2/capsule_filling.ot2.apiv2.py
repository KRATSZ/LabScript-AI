from opentrons.types import Point

metadata = {
    'protocolName': 'Capsule Filling 3x Custom 10x10 Racks',
    'author': 'Nick <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(ctx):
    num_samples, transfer_vol, p1000_mount = get_values(  # noqa: F821
        'num_samples', 'transfer_vol', 'p1000_mount')

    # labware
    capsule_assembly = ctx.load_labware(
        'custom_300_other_100x500ul_100x500ul_100x500ul', '1')
    tiprack = ctx.load_labware('opentrons_96_tiprack_1000ul', '9')

    # pipette
    p1000 = ctx.load_instrument(
        'p1000_single_gen2', p1000_mount, tip_racks=[tiprack])
    p1000.pick_up_tip()

    capsules_reordered = []
    for x, top in enumerate([True, False]):
        blocks_inds = range(2) if True else range(1)
        for i in blocks_inds:
            for col in capsule_assembly.columns()[x*10:(x+1)*10]:
                for well in col[i*10:(i+1)*10]:
                    capsules_reordered.append(well)

    # transfer from reservoir in trash spot
    source = ctx.loaded_labwares[12].wells()[0].top().move(
        Point(x=0, y=0, z=-20))

    # perform transfers
    for cap in capsules_reordered[:num_samples]:
        p1000.aspirate(100, source.move(Point(z=20)))
        p1000.aspirate(transfer_vol, source)
        p1000.dispense(transfer_vol, cap.top(-1))
        p1000.dispense(p1000.current_volume, cap.top())
    p1000.return_tip()

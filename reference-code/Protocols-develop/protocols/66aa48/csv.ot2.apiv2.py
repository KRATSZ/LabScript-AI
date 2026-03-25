from opentrons.types import Point

metadata = {
    'protocolName': 'CSV Consolidation',
    'author': 'Nick <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [volume_of_each_mutant_to_transfer,
     pipette_mount,
     tip_strategy,
     inactive_CSV,
     decrease_CSV,
     no_change_CSV,
     increase_CSV] = get_values(  # noqa: F821
        'volume_of_each_mutant_to_transfer',
        'pipette_mount',
        'tip_strategy',
        'inactive_CSV',
        'decrease_CSV',
        'no_change_CSV',
        'increase_CSV')

    if volume_of_each_mutant_to_transfer < 5:
        raise Exception('Invalid volume selection.')

    # load labware
    source_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '1',
        'source plate')
    dest_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '4',
        'Eppendorf tuberack for pools'
    )

    tips = ctx.load_labware('opentrons_96_tiprack_300ul', '2')
    p50 = ctx.load_instrument(
        'p50_single', mount=pipette_mount, tip_racks=[tips])

    # parse files and perform pooling
    touch = False if volume_of_each_mutant_to_transfer > 10 else True
    for csv, dest in zip(
            [inactive_CSV, decrease_CSV, no_change_CSV, increase_CSV],
            [well for well in dest_rack.wells()[:4]]
    ):
        sources = [source_plate.wells_by_name()[line.split(',')[0]]
                   for line in csv.splitlines() if line]
        d_offset = dest.bottom().move(Point(
            x=dest.diameter/2, y=0, z=dest.depth*0.9))
        if tip_strategy == 'one tip per pool':
            p50.pick_up_tip()
        for s in sources:
            if not p50.has_tip:
                p50.pick_up_tip()
            p50.transfer(
                volume_of_each_mutant_to_transfer,
                s,
                dest,
                new_tip='never'
            )
            if touch:
                p50.move_to(d_offset)
            p50.blow_out(dest.top())
            if tip_strategy == 'one tip per pool':
                p50.drop_tip()
        if p50.has_tip:
            p50.drop_tip()

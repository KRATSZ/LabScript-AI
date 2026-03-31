import math

metadata = {
    'protocolName': '384-well Plate One-to-One Transfer',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.2'
    }


def run(ctx):
    [p50_mount, dest_plate_type, num_samples,
     transfer_vol] = get_values(  # noqa: F821
        'p50_mount', 'dest_plate_type', 'num_samples', 'transfer_vol')

    # labware
    dest_plate = ctx.load_labware(dest_plate_type, '1', 'destination plate')
    source_plate = ctx.load_labware('greinerbioone_384_wellplate_100ul', '6',
                                    'source plate')
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['7', '8', '10', '11']]

    # pipette
    m50 = ctx.load_instrument('p50_multi', p50_mount, tip_racks=tipracks300)

    # setup sources and destinations
    num_cols = math.ceil(num_samples/8)
    sources, dests = [
        [well for row in plate.rows()[:2] for well in row][:num_cols]
        for plate in [source_plate, dest_plate]]

    m50.transfer(transfer_vol, sources, dests, new_tip='always')

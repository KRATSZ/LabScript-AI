# metadata
metadata = {
    'protocolName': 'Consolidation from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    p20_mount, transfer_csv = get_values(  # noqa: F821
        'p20_mount', 'transfer_csv')

    # load labware
    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2',
        '1.5ml tuberack')
    tipracks = [
        ctx.load_labware('opentrons_96_tiprack_20ul', '1', '20ul tiprack')]

    destination_tube = tuberack.wells()[0]

    # load pipette
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tipracks)

    # parse .csv
    transfer_info = [
        [val.strip() for val in line.split(",")]
        for line in transfer_csv.splitlines()[1:] if line
    ]

    def parse_well(well_name):
        return well_name[0].upper() + str(int(well_name[1:]))

    # perform transfers
    for line in transfer_info:
        well, volume = [line[1], line[3]]
        source = tuberack.wells_by_name()[parse_well(well)]
        vol = float(volume)
        p20.pick_up_tip()
        if vol <= 17:
            p20.aspirate(2, source.top())
        p20.aspirate(vol, source)
        if vol <= 19:
            p20.air_gap(1)
        p20.dispense(p20.current_volume, destination_tube)
        p20.drop_tip()

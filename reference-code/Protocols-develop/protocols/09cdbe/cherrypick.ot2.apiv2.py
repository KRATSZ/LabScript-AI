# metadata
metadata = {
    'protocolName': 'Consolidation from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    plate_type, p20_mount, transfer_csv = get_values(  # noqa: F821
        'plate_type', 'p20_mount', 'transfer_csv')

    # load labware
    source_plates = {
        str(i+1): ctx.load_labware(plate_type, slot, 'plate ' + str(i+1))
        for i, slot in enumerate(['2', '5', '8', '11', '6'])
    }
    tuberack = ctx.load_labware(
        'vwr_15_tuberack_5000ul', '9', 'pooling tuberack')
    tipracks = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot, '20µl tiprack')
        for slot in ['1', '4', '7', '10', '3']
    ]

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
        slot, well, tube, volume = line[:4]
        source = source_plates[slot].wells_by_name()[parse_well(well)]
        destination_tube = tuberack.wells_by_name()[parse_well(tube)]
        vol = float(volume)
        air_vol = (20-vol)/2
        p20.pick_up_tip()
        p20.aspirate(air_vol, source.top())
        p20.aspirate(vol, source)
        p20.aspirate(air_vol, source.top(-1))
        p20.touch_tip(source)
        p20.dispense(20, destination_tube)
        p20.blow_out(destination_tube.bottom(2))
        p20.drop_tip()

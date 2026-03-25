metadata = {
    'protocolName': 'PCR/qPCR prep (Master Mix Transfer)',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [m20_mount] = get_values(  # noqa: F821
        "m20_mount")

    # Load labware
    tiprack = ctx.load_labware('opentrons_96_tiprack_20ul', 10)
    source_plate_1 = ctx.load_labware('nest_12_reservoir_15ml_icetray', 11,
                                      'Source Plate #1')

    for slot in range(1, 9):
        if int(slot) not in ctx.loaded_labwares:
            ctx.load_labware('thermofast_96well_semiskirted_eppendorf_cooler',
                             slot, f'Destination Plate #{slot}')

    # Load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=[tiprack])

    # Setup source and destinations
    mm_1 = source_plate_1['A1']
    mm_2 = source_plate_1['A2']

    sample_set_1 = [ctx.loaded_labwares[i].rows()[0] for i in range(1, 5)]
    sample_set_2 = [ctx.loaded_labwares[i].rows()[0] for i in range(5, 9)]

    m20.pick_up_tip()
    for source, dest in zip([mm_1, mm_2], [sample_set_1, sample_set_2]):
        m20.transfer(16, source, dest, new_tip='never')
    m20.drop_tip()

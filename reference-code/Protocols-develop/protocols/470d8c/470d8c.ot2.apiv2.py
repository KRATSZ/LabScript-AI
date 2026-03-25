metadata = {
    'protocolName': 'PCR/qPCR prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [m300_mount, m20_mount] = get_values(  # noqa: F821
        "m300_mount", "m20_mount")

    # Load labware
    tipracks_20ul = [ctx.load_labware('opentrons_96_tiprack_20ul', slot) for
                     slot in [7, 10, 11]]
    tiprack_300ul = [ctx.load_labware('opentrons_96_tiprack_300ul', 4)]
    source_plate = ctx.load_labware('nest_12_reservoir_15ml_icetray', 1,
                                    'Source Plate #1')
    temp_plates = [ctx.load_labware(
                    'thermofast_96well_semiskirted_eppendorf_cooler',
                    slot, f'Template Plate #{i}') for i, slot
                   in enumerate([8, 5, 2], 1)]
    dest_plates = [ctx.load_labware(
                    'thermofast_96well_semiskirted_eppendorf_cooler',
                    slot, f'Destination Plate #{i}') for i, slot
                   in enumerate([9, 6, 3], 1)]

    # Load pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks_20ul)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack_300ul)

    # Transfer 40 uL of master mix
    m300.pick_up_tip()
    for plate in temp_plates:
        m300.transfer(40, source_plate['A1'], plate.rows()[0], new_tip='never')
    m300.drop_tip()

    # Transfer 10 uL of Template to Destination
    for source, dest in zip(temp_plates, dest_plates):
        m20.transfer(10, source.rows()[0], dest.rows()[0])

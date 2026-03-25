metadata = {
    'protocolName': 'Standard Serial Dilution',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_columns, num_plates] = get_values(  # noqa: F821
        "num_columns", "num_plates")

    if not 1 <= num_columns <= 12:
        raise Exception("Enter a column number between 1-12")
    if not 1 <= num_plates <= 10:
        raise Exception("Enter a plate number between 1-10")

    # custom number of Plates
    custom_plates = [str(i) for i in range(2, num_plates+2)]

    # labware setup
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', '1')
    plates = [ctx.load_labware('corning_96_wellplate_360ul_flat', slot)
              for slot in custom_plates]

    # instrument setup
    p300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack])

    # commands
    num_dilutions = num_columns - 1

    for plate in plates:
        p300.pick_up_tip()
        rows = zip(plate.rows()[0][:num_dilutions],
                   plate.rows()[0][1:num_dilutions+1])
        p300.mix(12, 100, plate.rows()[0][0])
        for source, dest in rows:
            p300.transfer(20, source, dest,
                          mix_after=(12, 100), new_tip='never')
        p300.aspirate(20, plate.rows()[0][num_dilutions])
        p300.drop_tip()

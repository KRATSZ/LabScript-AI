import math

metadata = {
    'protocolName': 'Protocol 2 - PCR setup',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [m20_mount, samples, reservoir_height, pcr_plate_height,
        sample_plate_height] = get_values(  # noqa: F821
        "m20_mount", "samples", "reservoir_height",
        "pcr_plate_height", "sample_plate_height")

    reservoir_height = float(reservoir_height)
    pcr_plate_height = float(pcr_plate_height)
    sample_plate_height = float(sample_plate_height)
    samples = int(samples)
    columns = math.ceil(samples/8)

    # Load Labware
    tiprack1 = ctx.load_labware('opentrons_96_filtertiprack_20ul',
                                1, 'Tip Box 1')
    tiprack2 = ctx.load_labware('opentrons_96_filtertiprack_20ul',
                                2, 'Tip Box 2')
    mastermix = ctx.load_labware('96well_pcr_base_200ul_strip', 7)['A1']
    sample_plate = ctx.load_labware('kingfisher_96_deepwell_plate_2ml', 4)
    pcr_plate = ctx.load_labware(
                'thermofishermicroampfast96well0.1_96_wellplate_100ul', 5)

    # Load Pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=[tiprack1, tiprack2])

    # Aliquot 15uL of Mastermix
    m20.pick_up_tip(tiprack1['A1'])
    for pcr_well in pcr_plate.rows()[0][:columns]:
        m20.transfer(15, mastermix.bottom(reservoir_height),
                     pcr_well.bottom(pcr_plate_height), new_tip='never')
    m20.drop_tip()

    # Aliquot 10 uL of Sample
    for source, dest, tip in zip(sample_plate.rows()[0][:columns],
                                 pcr_plate.rows()[0][:columns],
                                 tiprack2.rows()[0][:columns]):
        m20.pick_up_tip(tip)
        m20.transfer(10, source.bottom(sample_plate_height),
                     dest.bottom(pcr_plate_height), new_tip='never')
        m20.drop_tip()

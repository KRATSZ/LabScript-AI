metadata = {
    'protocolName': 'DNA and Water Transfer with CSV File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [v_csv, p10_mount, p300_mount] = get_values(  # noqa: F821
        "v_csv", "p10_mount", "p300_mount")

    # load Labware
    reservoir = ctx.load_labware('ek_scientific_reservoir', '6')
    pcr_plate = ctx.load_labware('vwrpcr_96_wellplate_200ul', '8')
    tiprack_300 = ctx.load_labware('opentrons_96_tiprack_300ul', '9')
    dna_stock = ctx.load_labware('vwr_square_96_microplate_2000ul', '10')
    tiprack_10 = ctx.load_labware('geb_96_tiprack_10ul', '11')

    # load instruments
    p10 = ctx.load_instrument('p10_single', p10_mount,
                              tip_racks=[tiprack_10])

    p300 = ctx.load_instrument('p300_single', p300_mount,
                               tip_racks=[tiprack_300])

    # csv file --> nested list
    transfer = [[val.strip() for val in line.split(',')]
                for line in v_csv.splitlines()
                if line.split(',')[0].strip()][1:]

    for line in transfer:
        if not p300.has_tip:
            p300.pick_up_tip()
        vol_water = float(line[2])
        well = line[3]
        p300.transfer(vol_water, reservoir['A1'],
                      pcr_plate.wells_by_name()[well], new_tip='never')
    if p300.has_tip:
        p300.drop_tip()

    for line in transfer:
        vol_dna = float(line[1])
        well = line[3]
        p10.transfer(vol_dna, dna_stock.wells_by_name()[well],
                     pcr_plate.wells_by_name()[well])

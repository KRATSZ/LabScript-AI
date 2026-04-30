metadata = {
    'protocolName': 'Pre Normalization Prep',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [csv_samp, dna_plate_type,
        p20_mount, m20_mount] = get_values(  # noqa: F821
            "csv_samp", "dna_plate_type", "p20_mount", "m20_mount")

    # labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 1)
    dna_plate = ctx.load_labware(dna_plate_type, 2)

    final_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 3)

    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in [10, 11]]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips)

    # mapping
    water = reservoir.wells()[0]

    csv_rows = [[val.strip() for val in line.split(',')]
                for line in csv_samp.splitlines()
                if line.split(',')[0].strip()][1:]

    # protocol
    ctx.comment('\n------------ADDING WATER TO FINAL PLATE-------------\n\n')
    p20.pick_up_tip()
    for line in csv_rows:
        dest_well_name = line[0]
        dest_well = final_plate.wells_by_name()[dest_well_name]

        qubit = float(line[2])
        transfer_vol = 50-1250/qubit

        if qubit <= 25:
            continue

        p20.transfer(transfer_vol, water, dest_well, new_tip='never',
                     blow_out=True,
                     blowout_location="destination well")

    p20.drop_tip()

    ctx.comment('\n------------ADDING DNA TO FINAL PLATE-------------\n\n')

    for line in csv_rows:
        p20.pick_up_tip()
        source_well_name = line[0]
        source_well = dna_plate.wells_by_name()[source_well_name]

        dest_well_name = line[0]
        dest_well = final_plate.wells_by_name()[dest_well_name]

        qubit = float(line[2])
        transfer_vol = 1250/qubit

        if qubit <= 25:
            p20.transfer(50, source_well.bottom(z=1 if dna_plate_type == "nest_96_wellplate_100ul_pcr_full_skirt" else -1), dest_well, new_tip='never',  # noqa:E501
                         blow_out=True,
                         blowout_location="destination well")

        else:
            p20.transfer(transfer_vol,
                         source_well.bottom(z=1 if dna_plate_type == "nest_96_wellplate_100ul_pcr_full_skirt" else -1), dest_well, new_tip='never',  # noqa:E501
                         blow_out=True,
                         blowout_location="destination well")

        p20.drop_tip()

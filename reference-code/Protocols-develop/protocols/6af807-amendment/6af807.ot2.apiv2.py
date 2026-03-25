"""Protocol."""


metadata = {
    'protocolName': '384 Well Plate PCR Plate with Triplicates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [num_gene, num_mastermix,
        cdna_vol, p20_mount] = get_values(  # noqa: F821
        "num_gene", "num_mastermix",
        "cdna_vol",
            "p20_mount")

    mmx_vol = 20-cdna_vol

    if not 1 <= num_mastermix <= 16:
        raise Exception("Enter a number of mastermixes between 1-16")
    if not 1 <= num_gene <= 8:
        raise Exception("Enter a number of cDNA 1-8")

    # load labware
    plate = ctx.load_labware('100ul_384_wellplate_100ul', '1')
    mastermix = ctx.load_labware(
                'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '3')
    cDNA = ctx.load_labware(
                'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2')
    tiprack = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
               for slot in [4, 5, 6, 7]]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2',
                              p20_mount, tip_racks=tiprack)

    # ctx
    cDNA_tubes = cDNA.wells()[:num_gene]

    # remove P-row
    chopped_plate = [plate.columns()[i][:num_mastermix]
                     for i in range(0, len(plate.columns()))]

    chunked_columns = [chopped_plate[i:i+3] for i in range(
                      0, len(chopped_plate), 3)]

    # print(chunked_columns)

    # chunk down the column by triplicates
    dispense_wells = [[] for _ in range(24)]
    for i, chunked_column in enumerate(chunked_columns):
        for j in range(0, 24, num_mastermix):
            for col in chunked_column:
                dispense_wells[i].append(col[j:j+num_mastermix])

    # concatanate sublists for each tube
    final_dispense_wells = []
    ctr = 0
    for list in dispense_wells:
        x = []
        for i, sublist in enumerate(list):
            x += sublist
            ctr += 1
            if ctr == 3:
                final_dispense_wells.append([x])
                x = []
                ctr = 0

    # remove empty brackets
    final_dispense_wells = [x for x in final_dispense_wells if x != [[]]]

    airgap = 2
    for tube, chunk in zip(cDNA_tubes, final_dispense_wells):
        p20.pick_up_tip()
        for small_chunk in chunk:
            for well in small_chunk:
                p20.aspirate(cdna_vol, tube)
                # p20.air_gap(airgap)
                p20.dispense(cdna_vol, well)
                # p20.blow_out()
        p20.drop_tip()
        ctx.comment('\n\n')
    ctx.comment('\n\n\n\n\n\n\n')

    airgap = 1
    for row, tube in zip(plate.rows()[:num_mastermix], mastermix.wells()):
        for well in row[:num_gene*3]:
            p20.pick_up_tip()
            p20.aspirate(mmx_vol, tube, rate=0.5)
            p20.air_gap(airgap)
            p20.dispense(mmx_vol+airgap, well, rate=0.5)
            p20.blow_out(well.top())
            p20.drop_tip()
        ctx.comment('\n')

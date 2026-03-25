metadata = {
    'protocolName': 'qPCR Prep with 384 Well Plate',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_samp, cDNA_col_num1, cDNA_col_num2, asp_bottom_clearance,
     disp_bottom_clearance, asp_flowrate_p10, asp_flowrate_p50,
     disp_flowrate_p10, disp_flowrate_p50,
     temp_mod_on, temp, small_pip, big_pip, p10_mount,
     p50_mount] = get_values(  # noqa: F821
        "num_samp", "cDNA_col_num1", "cDNA_col_num2", "asp_bottom_clearance",
        "disp_bottom_clearance", "asp_flowrate_p10", "asp_flowrate_p50",
        "disp_flowrate_p10", "disp_flowrate_p50", "temp_mod_on", "temp",
         "small_pip", "big_pip", "p10_mount", "p50_mount")

    if not 1 <= cDNA_col_num1 <= 12:
        raise Exception("Enter a primer-pair number between 1-12")
    if not 1 <= cDNA_col_num1 <= 12:
        raise Exception("Enter a column number between 1-12")
    if not 0 <= cDNA_col_num2 <= 12:
        raise Exception("Enter a column number between 0-12")
    if cDNA_col_num1 == cDNA_col_num2:
        raise Exception("cDNA columns must be different")

    # load labware
    deepwell_pro = ctx.load_labware('deepwellpro_96_wellplate_450ul', '1')
    pcr_plate = ctx.load_labware('pcr_384_wellplate_50ul', '2')
    primer_pairs = ctx.load_labware('deepwellpro_96_wellplate_450ul', '3')
    temp_mod = ctx.load_module('tempdeck', '4')
    temp_plate = temp_mod.load_labware('biorad_96_aluminumblock_200ul')
    tipracks10 = [ctx.load_labware('opentrons_96_filtertiprack_10ul', slot)
                  for slot in ['6', '9', '10']]
    tiprack200 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '7')

    if temp_mod_on:
        temp_mod.set_temperature(temp)

    # load instruments, define pipette settings
    p10 = ctx.load_instrument(small_pip, p10_mount, tip_racks=tipracks10)
    p50 = ctx.load_instrument(big_pip, p50_mount, tip_racks=[tiprack200])
    p10.well_bottom_clearance.dispense = asp_bottom_clearance
    p10.well_bottom_clearance.dispense = disp_bottom_clearance
    p10.flow_rate.aspirate = asp_flowrate_p10
    p10.flow_rate.dispense = disp_flowrate_p10
    p50.well_bottom_clearance.aspirate = asp_bottom_clearance
    p50.well_bottom_clearance.dispense = disp_bottom_clearance
    p50.flow_rate.aspirate = asp_flowrate_p50
    p50.flow_rate.dispense = disp_flowrate_p50

    # reagents
    supermix = [deepwell_pro.rows()[0][cDNA_col-1]
                for cDNA_col in [cDNA_col_num1, cDNA_col_num2]]
    cDNA_cols = [temp_plate.rows()[0][cDNA_col-1]
                 for cDNA_col in [cDNA_col_num1, cDNA_col_num2]]
    tip_cols200 = [tiprack200.rows()[0][cDNA_col-1]
                   for cDNA_col in [cDNA_col_num1, cDNA_col_num2]]
    tip_cols10 = [tipracks10[2].rows()[0][cDNA_col-1]
                  for cDNA_col in [cDNA_col_num1, cDNA_col_num2]]
    num_col_to_fill = int(num_samp*2)
    num_384_cols = pcr_plate.rows()[0][:num_col_to_fill]

    runs = 2
    if cDNA_col_num2 == 0:
        cDNA_cols.pop()
        runs = 1

    for i, (cDNA_col, supermix_col, tip_col200, tip_col10) in enumerate(zip(
                                                      cDNA_cols, supermix,
                                                      tip_cols200, tip_cols10
                                                      )):

        num_384_cols = pcr_plate.rows()[i][:num_col_to_fill]

        # transfer cDNA to the SuperMix
        ctx.comment('\nMasterMix Preparation-Transfer cDNA to the SuperMix\n')
        p50.pick_up_tip(tip_col200)
        p50.aspirate(30, cDNA_col)
        p50.dispense(30, supermix_col)
        p50.mix(4, 40)
        p50.blow_out(supermix[0].top())
        p50.drop_tip()

        # transfer of mastermixes to pcr Plate
        ctx.comment('\nTransferring Mastermix to PCR Plate\n')
        p10.pick_up_tip(tip_col10)
        for col in num_384_cols:
            p10.aspirate(10, supermix_col)
            p10.dispense(10, col)
        ctx.comment('\n')
        p10.drop_tip()

    # Transfer from PrimerPair-stockPlate to Mastermixes
    pcr_destinations = [pcr_plate.rows()[row_start][i:i+2]
                        for row_start in [0, 1]
                        for i in range(0, len(
                         pcr_plate.rows()[0][:num_samp*2]), 2)]
    rounds = [
              pcr_destinations[:num_samp],
              pcr_destinations[num_samp:]
              ]
    runs = 2
    if cDNA_col_num2 == 0:
        rounds.pop()

    ctx.comment('\nTransfer from PrimerPair-stockPlate to Mastermixes\n')
    for round in rounds:
        for s, d in zip(primer_pairs.rows()[0]*runs, round):
            p10.pick_up_tip()
            p10.aspirate(5, s)
            p10.dispense(2, s)
            [p10.dispense(1, col) for col in d]
            p10.drop_tip()
            ctx.comment('\n')

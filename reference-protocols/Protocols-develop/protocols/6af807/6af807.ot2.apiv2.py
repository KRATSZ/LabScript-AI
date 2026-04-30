"""Protocol."""
import os
import csv
import math


metadata = {
    'protocolName': '384 Well Plate PCR Plate with Triplicates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [cDNA_down_column, num_gene, num_mastermix, dispense_rate, blowout_rate,
        cdna_vol, mmx_vol,
        reset_tipracks, p20_mount] = get_values(  # noqa: F821
        "cDNA_down_column", "num_gene", "num_mastermix", "dispense_rate",
        "blowout_rate", "cdna_vol",
            "mmx_vol", "reset_tipracks", "p20_mount")

    if cDNA_down_column:
        if not 1 <= num_mastermix <= 5:
            raise Exception("Enter a number of mastermixes between 1-5")
        if not 1 <= num_gene <= 24:
            raise Exception("Enter a number of cDNA 1-24")
        num_gene, num_mastermix = num_mastermix, num_gene

    # Tip tracking between runs
    if not ctx.is_simulating():
        file_path = '/data/csv/tiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial tip count tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    tip_count_list = []
    if ctx.is_simulating():
        tip_count_list = [0]
    elif reset_tipracks:
        tip_count_list = [0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    tip_counter = int(tip_count_list[0])

    # load labware
    plate = ctx.load_labware('100ul_384_wellplate_100ul', '1')
    mastermix = ctx.load_labware(
                'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '3')
    cDNA = ctx.load_labware(
                'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2')
    tiprack = ctx.load_labware('opentrons_96_tiprack_20ul', '4')

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2',
                              p20_mount, tip_racks=[tiprack])

    tips = [tip for tip in tiprack.wells()]

    def pick_up():
        nonlocal tip_counter
        if tip_counter == 96:
            ctx.home()
            ctx.pause('Replace 20ul tip rack')
            p20.reset_tipracks()
            tip_counter = 0
            pick_up()
        else:
            p20.pick_up_tip(tips[tip_counter])
            tip_counter += 1

    # ctx
    if cDNA_down_column:
        cDNA_tubes = cDNA.wells()[:num_mastermix]

    else:
        cDNA_tubes = cDNA.wells()[:num_gene]

    # remove P-row
    chopped_plate = [plate.columns()[i][:15]
                     for i in range(0, len(plate.columns()))]

    chunked_columns = [chopped_plate[i:i+num_mastermix] for i in range(
                      0, len(chopped_plate), num_mastermix)]

    # chunk down the column by triplicates
    dispense_wells = [[] for _ in range(24)]
    for i, chunked_column in enumerate(chunked_columns):
        for j in range(0, 24, 3):
            for col in chunked_column:
                dispense_wells[i].append(col[j:j+3])

    # concatanate sublists for each tube
    final_dispense_wells = []
    ctr = 0
    for list in dispense_wells:
        x = []
        for i, sublist in enumerate(list):
            x += sublist
            ctr += 1
            if ctr == num_mastermix:
                final_dispense_wells.append([x])
                x = []
                ctr = 0

    # remove empty brackets
    final_dispense_wells = [x for x in final_dispense_wells if x != [[]]]

    if cDNA_down_column:
        cDNA_wells = [well for col in chopped_plate[:num_mastermix]
                      for well in col[:num_gene*3]]
        cDNA_chunks = [cDNA_wells[i:i+num_gene*3] for i in range(0,
                       len(cDNA_wells), num_gene*3)]

        airgap = 2
        for tube, chunk in zip(cDNA_tubes, cDNA_chunks):
            pick_up()
            for well in chunk:
                p20.aspirate(cdna_vol, tube)
                p20.air_gap(airgap)
                p20.dispense(cdna_vol+airgap, well)
                p20.blow_out()
            p20.drop_tip()
            ctx.comment('\n')
        ctx.comment('\n\n\n\n\n\n\n')

        p20.flow_rate.blow_out = blowout_rate*p20.flow_rate.blow_out
        for tube, chunk in zip(mastermix.wells()[:num_gene],
                               final_dispense_wells):
            pick_up()
            for small_chunk in chunk:
                for well in small_chunk:
                    p20.aspirate(mmx_vol, tube, rate=0.5)
                    ctx.delay(seconds=1)
                    p20.dispense(mmx_vol, well.top(), rate=dispense_rate)
                    ctx.delay(seconds=3)
                    p20.blow_out()
                    p20.touch_tip(radius=0.33)
            p20.drop_tip()

    else:
        airgap = 2
        for tube, chunk in zip(cDNA_tubes, final_dispense_wells):
            pick_up()
            for small_chunk in chunk:
                for well in small_chunk:
                    p20.aspirate(cdna_vol, tube)
                    p20.air_gap(airgap)
                    p20.dispense(cdna_vol+airgap, well)
                    p20.blow_out()
            p20.drop_tip()
            ctx.comment('\n')
        ctx.comment('\n\n\n\n\n\n\n')

        num_rows_in_each_column = []
        remaining_wells = math.floor(num_gene*3 % 15)

        for _ in range(num_mastermix):
            if num_gene >= 5:
                num_rows_in_each_column.append(15)
        for _ in range(num_mastermix):
            if remaining_wells > 0:
                num_rows_in_each_column.append(remaining_wells)

        num_gene_to_dispense = math.ceil(num_gene*3/15)
        p20.flow_rate.blow_out = blowout_rate*p20.flow_rate.blow_out
        for j, tube in enumerate(mastermix.wells()[:num_mastermix]):
            pick_up()
            for i, (column, num_rows) in enumerate(zip(
                                                    chopped_plate[
                                                        j::num_mastermix][
                                                        :num_gene_to_dispense],
                                                    num_rows_in_each_column[
                                                        j::num_mastermix])):
                for well in column[:num_rows]:
                    p20.aspirate(mmx_vol, tube, rate=0.5)
                    ctx.delay(seconds=4)
                    p20.touch_tip(radius=0.7)
                    p20.dispense(mmx_vol, well.top(), rate=dispense_rate)
                    ctx.delay(seconds=1)
                    p20.blow_out()
                    p20.touch_tip(radius=0.7)
            p20.drop_tip()
            ctx.comment('\n')

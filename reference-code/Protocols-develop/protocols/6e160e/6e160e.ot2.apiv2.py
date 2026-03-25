from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Covid Sample Prep to 384 Plate',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [
     num_samp,
     p20_mount,
     m20_mount] = get_values(  # noqa: F821
         "num_samp",
         "p20_mount",
         "m20_mount")

    if not 0 <= num_samp <= 384:
        raise Exception("Enter a sample number 0-384")

    # MODULES
    plate_temp_mod = ctx.load_module('temperature module gen2', '3')
    res_temp_mod = ctx.load_module('temperature module gen2', '6')
    plate_temp_mod.set_temperature(4)
    res_temp_mod.set_temperature(4)

    # LABWARE
    sample_plates = [ctx.load_labware(
                      "biorad_96_wellplate_200ul_pcr",
                      slot, label="the SAMPLE PLATE")
                     for slot in ['2', '5', '8', '11']]
    res = res_temp_mod.load_labware('nest_12_reservoir_15ml')
    plate_384 = plate_temp_mod.load_labware('appliedbiosystems_384_wellplate_40ul')  # noqa: E501

    # TIPRACKS
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                                  label='20uL TIPRACK')
                 for slot in ['1', '4', '7', '9', '10']]

    # INSTRUMENTS
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)

    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tiprack20)

    # protocol
    reagent = res.wells()[0]
    num_full_plates = math.floor(num_samp/96)

    def create_chunks(list, n):
        for i in range(0, len(list), n):
            yield list[i:i+n]

    unfilled_plate = sample_plates[num_full_plates if num_samp < 384 else num_full_plates-1]  # noqa: E501
    leftover_samp = num_samp % 96
    if num_full_plates == 0:
        unfilled_row_start = 0
        unfilled_col_start = 0
    elif num_full_plates == 1:
        unfilled_row_start = 0
        unfilled_col_start = 1
    elif num_full_plates == 2:
        unfilled_row_start = 1
        unfilled_col_start = 0
    elif num_full_plates == 3 or num_full_plates == 4:
        unfilled_row_start = 1
        unfilled_col_start = 1

    unfilled_plate_wells_96 = [well for row in unfilled_plate.rows()
                               for well in row][:leftover_samp]
    unfilled_plate_wells = [well
                            for row in plate_384.rows()[unfilled_row_start::2]
                            for well in row[unfilled_col_start::2]][:leftover_samp]  # noqa: E501

    if num_full_plates > 0:
        ctx.comment('\n\nMOVING REACTION MIX TO PLATE\n')
        col_ctr = 0
        m20.pick_up_tip()
        for row_start, col_start in zip([0, 0, 1, 1][:num_full_plates],
                                        [0, 1, 0, 1]):
            col_ctr = 0

            for _ in range(4):
                m20.aspirate(20, reagent)
                for _ in range(3):
                    m20.dispense(6, plate_384.rows()[row_start][col_start+col_ctr])  # noqa: E501
                    col_ctr += 2
                m20.dispense(2, reagent)
            ctx.comment('\n\n')
        m20.drop_tip()

    if leftover_samp > 0:
        ctx.comment('\n\nMOVING REACTION MIX TO PLATE WITH SINGLE CHANNEL\n')
        p20.pick_up_tip()
        for chunk in create_chunks(unfilled_plate_wells, 3):
            p20.aspirate(20, reagent)
            for well in chunk:
                p20.dispense(6, well)
            p20.dispense(p20.current_volume, reagent)
            ctx.comment('\n\n')
    if p20.has_tip:
        p20.drop_tip()

    ctx.comment('\n\nMOVING SAMPLE TO PLATE\n')
    airgap = 2
    for plate, row_start, col_start in zip(sample_plates[:num_full_plates],
                                           [0, 0, 1, 1],
                                           [0, 1, 0, 1]):
        for source, dest in zip(plate.rows()[0],
                                plate_384.rows()[row_start][col_start::2]):
            m20.pick_up_tip()
            m20.aspirate(4, source)
            m20.air_gap(airgap)
            m20.dispense(airgap, dest.top())
            m20.dispense(4, dest)
            m20.drop_tip()
        ctx.comment('\n\n')

    if leftover_samp > 0:
        ctx.comment('\n\nMOVING SAMPLE TO PLATE WITH SINGLE CHANNEL\n')
        for source, dest in zip(unfilled_plate_wells_96, unfilled_plate_wells):
            p20.pick_up_tip()
            p20.aspirate(4, source)
            p20.air_gap(airgap)
            p20.dispense(airgap, dest.top())
            p20.dispense(4, dest)
            p20.drop_tip()
            ctx.comment('\n\n')

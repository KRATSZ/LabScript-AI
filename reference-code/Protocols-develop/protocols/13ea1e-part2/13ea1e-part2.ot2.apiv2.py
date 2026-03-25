import math
from opentrons import protocol_api


metadata = {
    'protocolName': 'PCR Plate Prep with 384 Well Plate',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_samp, overage_percent, mix_reps,
        p20_mount] = get_values(  # noqa: F821
        "num_samp", "overage_percent",
        "mix_reps",
        "p20_mount")

    if not 0 <= num_samp <= 384:
        raise Exception("Enter a sample number between 1-384")

    num_plates = math.ceil(num_samp/96)
    plates = [str(num+1) for num in range(0, num_plates)]
    overage = 1+overage_percent/100

    if not 0 <= num_samp <= 384:
        raise Exception("Enter a sample number between 1-384")

    # load labware
    sample_plates = [ctx.load_labware('nest_96_wellplate_2200ul', slot)
                     for slot in plates]
    tuberack = ctx.load_labware('opentrons_24_tuberack_1500ul', '5')
    pcr_plate_384 = ctx.load_labware('pr1ma_384_wellplate_50ul', '6')
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['8', '9', '11']]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)

    def pick_up_20():
        try:
            p20.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks.")
            p20.reset_tipracks()
            pick_up_20()

    # protocol
    sample_wells = [well for plate in sample_plates
                    for well in plate.wells()][:num_samp]

    # reagents
    total_mix_vol = 7*overage*num_samp
    num_mastermix_tubes = math.ceil((total_mix_vol)/1000)

    mastermix_tube = tuberack.rows()[0][:num_mastermix_tubes]
    positive_control = tuberack.rows()[3][5]

    liquid_prompt = f'''Please ensure you have:
                    {total_mix_vol/num_mastermix_tubes}ul  of mastermix
                    in all tubes out of
                    {num_mastermix_tubes} mastermix tubes.'''
    ctx.pause(liquid_prompt)

    # plate mapping
    plate1_to_384 = [well for column in pcr_plate_384.columns()[::2]
                     for well in column[::2]][:96 if
                                              num_samp > 96 else num_samp]
    plate2_to_384 = [well for column in pcr_plate_384.columns()[1::2]
                     for well in column[::2]][:96 if num_samp > 192
                                              else num_samp-96
                                              if num_samp-96 > 0 else 0]
    plate3_to_384 = [well for column in pcr_plate_384.columns()[::2]
                     for well in column[1::2]][:96 if
                                               num_samp > 288
                                               else num_samp-192
                                               if num_samp-192 > 0 else 0]
    plate4_to_384 = [well for column in pcr_plate_384.columns()[1::2]
                     for well in column[1::2]][:num_samp-288
                                               if num_samp-288 > 0 else 0]
    if num_samp == 384:
        plate4_to_384.pop()

    plates = {
                0: plate1_to_384,
                1: plate2_to_384,
                2: plate3_to_384,
                3: plate4_to_384
            }

    # distribute mastermix
    airgap = 5
    ctx.comment('Distributing Mastermix')
    pick_up_20()
    p20.aspirate(7, mastermix_tube[0])
    p20.air_gap(airgap)
    p20.dispense(7+airgap, pcr_plate_384.wells()[-1])

    for i, plate in enumerate(sample_plates):
        for source, well in zip(mastermix_tube*num_samp, plates[i]):
            p20.aspirate(7, source)
            p20.dispense(7+airgap, well)
            p20.blow_out()
    p20.drop_tip()
    ctx.comment('\n\n\n\n\n\n')

    # add positive control
    ctx.comment('Adding Positive Control')
    pick_up_20()
    p20.aspirate(5.5, positive_control)
    p20.air_gap(airgap)
    p20.dispense(7+airgap, pcr_plate_384.wells()[-1])
    p20.mix(mix_reps, 12.5, pcr_plate_384.wells()[-1])
    p20.drop_tip()

    # add sample and mix
    ctx.comment('Adding Sample')
    for i, plate in enumerate(sample_plates):
        for s, d in zip(sample_wells, plates[i]):
            pick_up_20()
            p20.aspirate(5.5, s)
            p20.air_gap(airgap)
            p20.dispense(5.5+airgap, d)
            p20.mix(mix_reps, 12.5, d)
            p20.blow_out()
            p20.drop_tip()

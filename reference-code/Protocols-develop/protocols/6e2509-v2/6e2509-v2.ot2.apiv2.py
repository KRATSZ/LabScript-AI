import math

metadata = {
    'protocolName': 'Sample Plate Filling 96 Wells to 384 Well Plate v2',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [samples] = get_values(  # noqa: F821
        "samples")

    # Hardcoded Values
    m20_mount = "right"
    pcr_mix_vol = 7.5
    sample_vol = 5
    sample_asp_height = 3
    sample_disp_height = 3
    mm_asp_height = 1
    mm_disp_height = 1

    # Load Labware
    tipracks_20ul = [ctx.load_labware('opentrons_96_filtertiprack_20ul',
                                      slot) for slot in [10, 11, 7, 8, 9]]
    pcr_mix = ctx.load_labware('thermofisherscientific_96_wellplate_450ul', 6,
                               'PCR Mix Reservoir')['A1']
    pcr_plate = ctx.load_labware(
        'appliedbiosystems_microamp_optical_384_wellplate_30ul', 3,
        '384 Well PCR Plate')
    elution_plates = [ctx.load_labware('molgen_96_well_elution_plate',
                                       slot, f'Elution Plate {i}') for i,
                      slot in enumerate([4, 5, 1, 2], 1)]

    # Load Pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks_20ul)

    # Get columns
    columns = math.ceil(samples / 8)

    # Get sample and dest wells in correct order
    sample_wells = [well for i in range(4) for well in
                    elution_plates[i].rows()[0]][:columns]
    pcr_dests = [a for b in zip(pcr_plate.rows()[0],
                 pcr_plate.rows()[1]) for a in b][:columns]

    # Add RT-PCR Mix use spare tip rack
    m20.pick_up_tip(tipracks_20ul[-1]['A1'])
    for dest in pcr_dests:
        m20.transfer(pcr_mix_vol, pcr_mix.bottom(mm_asp_height),
                     dest.bottom(mm_disp_height),
                     new_tip='never')
    m20.drop_tip()

    # Add RNA Samples
    for source, dest in zip(sample_wells, pcr_dests):
        m20.transfer(sample_vol, source.bottom(sample_asp_height),
                     dest.bottom(sample_disp_height), new_tip='always',
                     mix_after=(5, 5))

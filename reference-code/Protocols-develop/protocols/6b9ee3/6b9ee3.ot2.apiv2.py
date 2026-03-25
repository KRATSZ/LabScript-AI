import math

metadata = {
    'protocolName': 'Mastermix Creation and Sample Transfer',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p_csv, num_samples, ex_opti] = get_values(  # noqa: F821
        'p_csv', 'num_samples', 'ex_opti')

    # load labware and pipettes
    tip20 = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', str(s)) for s in range(1, 4)]

    p20s = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=tip20)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tip20)

    stock = protocol.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        '4', 'Al Block with PCR strips and stock')

    mm = protocol.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        '5', 'Al Block with PCR strips for Mastermix')

    samplePlate = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '6')

    tubeRack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '7')

    num_cols = math.ceil(num_samples/8)
    mm_cols = mm.rows()[0][:num_cols]
    samp_cols = samplePlate.rows()[0][:num_cols*3]
    s_cols = [samp_cols[i:i + 3] for i in range(0, len(samp_cols), 3)]

    # reagents
    optimem = tubeRack['D6']
    viafect = mm['A12']

    # create list of data from csv
    data = [row.split(',') for row in p_csv.strip().splitlines() if row][1:]

    # Add optimem to wells
    protocol.comment('Adding OptiMEM to all sample wells...')
    p20s.pick_up_tip()

    for well in mm.wells()[:num_samples-1]:
        p20s.aspirate(5.3, optimem)
        p20s.dispense(5.3, well)

    if ex_opti != '31.7':
        p20s.aspirate(5.3, optimem)
        p20s.dispense(5.3, mm.wells()[num_samples-1])
    else:
        p20s.aspirate(16, optimem)
        p20s.dispense(16, mm.wells()[num_samples-1])
        p20s.aspirate(15.7, optimem)
        p20s.dispense(15.7, mm.wells()[num_samples-1])

    p20s.drop_tip()

    # Add 4.4ul of sample to well per CSV
    protocol.comment('Adding sample to all sample wells...')
    for d in data:
        p20s.transfer(4.4, stock[d[0].strip()], mm[d[1].strip()])

    # Add 1.3ul of viafect to each well
    protocol.comment('Adding viafect to all sample wells...')
    for col in mm_cols:
        p20m.pick_up_tip()
        p20m.aspirate(1.3, viafect)
        p20m.dispense(1.3, col)
        p20m.mix(3, 20, col)
        p20m.blow_out()
        p20m.drop_tip()

    protocol.pause('Please let incubate for 10 minutes.')

    # transfer
    protocol.comment('Transferring mastermix to samples...')
    for src, dest in zip(mm_cols, s_cols):
        p20m.pick_up_tip()
        p20m.mix(3, 20, src)
        for d in dest:
            p20m.transfer(10, src, d, new_tip='never')
        p20m.drop_tip()

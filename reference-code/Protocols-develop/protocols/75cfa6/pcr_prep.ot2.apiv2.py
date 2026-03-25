import math

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.11'
}


def run(ctx):

    num_samples, p10_mount, m10_mount = get_values(  # noqa: F821
        'num_samples', 'p10_mount', 'm10_mount')

    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2',
        'mastermix tuberack (column 1)')
    tiprack10s = [ctx.load_labware('opentrons_96_tiprack_10ul', '3')]
    tiprack10m = [ctx.load_labware('opentrons_96_tiprack_10ul', '6')]
    tempdeck1 = ctx.load_module('tempdeck', '4')
    pcr_plate = tempdeck1.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul', 'PCR plate')
    tempdeck2 = ctx.load_module('tempdeck', '7')
    sample_plate = tempdeck2.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul', 'sample plate')

    p10 = ctx.load_instrument('p10_single', p10_mount, tip_racks=tiprack10s)
    m10 = ctx.load_instrument('p10_single', m10_mount, tip_racks=tiprack10m)

    mms = tuberack.columns()[0]
    num_cols = math.ceil(num_samples/8)
    samples = sample_plate.rows()[0][:num_cols]

    # set temperature module temperature
    [tempdeck.set_temperature(6) for tempdeck in [tempdeck1, tempdeck2]]
    p10.home()
    ctx.pause("Temperature has reached 6°C. Place your reagents on the \
    Temperature Module(s) before resuming.")

    # transfer master mix
    wells_row_order = [well for row in pcr_plate.rows() for well in row]
    mm_sets = [wells_row_order[i::4] for i in range(4)]
    for mm, dest_set in zip(mms, mm_sets):
        p10.pick_up_tip()
        for d in dest_set:
            p10.transfer(8, mm, d, new_tip='never')
            p10.blow_out(d.bottom(5))
        p10.drop_tip()

    sample_sets = [pcr_plate.rows()[0][i*4:(i+1)*4] for i in range(num_cols)]
    for s, dest_set in zip(samples, sample_sets):
        for d in dest_set:
            m10.transfer(2, s, d, mix_after=(5, 5))

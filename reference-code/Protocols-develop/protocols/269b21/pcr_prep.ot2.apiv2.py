# metadata
metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [num_mm, num_samples, p20_mount] = get_values(  # noqa: F821
        'num_mm', 'num_samples', 'p20_mount')

    # labware
    plate384 = ctx.load_labware(
        'biorad_384_wellplate_50ul', '1', '384-well plate')
    stripblock = ctx.load_labware('genmate_96_aluminumblock_20ul', '2')
    tempdeck = ctx.load_module('tempdeck', '4')
    tubeblock = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    tempdeck.set_temperature(4)
    tiprack20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot, '20µl tiprack')
        for slot in ['5', '6']]

    # pipette
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_mount, tip_racks=tiprack20)

    # mm and sample setup
    mm = [well for row in tubeblock.rows() for well in row][:num_mm]
    samples = [well for row in stripblock.rows() for well in row][:num_samples]
    mm_dests = [
        [well
         for set in [row[i*3:i*3+3]
                     for row in plate384.rows()[r*2:r*2+2]]
         for well in set]
        for r in range(len(plate384.rows())//2)
        for i in range(len(plate384.columns())//3)][:num_mm]
    sample_dests = [
        row[i*6:i*6+6]
        for i in range(len(plate384.columns())//6)
        for row in plate384.rows()][:num_samples]

    # transfer mastermix 6-replicates
    for m, d_set in zip(mm, mm_dests):
        p20.pick_up_tip()
        for d in d_set:
            p20.transfer(10, m, d.bottom(2), new_tip='never')
            p20.blow_out(d.top(-2))
        p20.drop_tip()

    # transfer samples
    for samp, s_set in zip(samples, sample_dests):
        for s in s_set:
            p20.pick_up_tip()
            p20.transfer(5, samp, s.bottom(2), new_tip='never')
            p20.blow_out(s.top(-2))
            p20.drop_tip()

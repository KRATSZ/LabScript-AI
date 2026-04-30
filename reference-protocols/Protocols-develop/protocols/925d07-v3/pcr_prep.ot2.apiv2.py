from opentrons.types import Point
import math

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [rna_plate_type, sample_vol, height_asp_sample, mm_vol, num_samples_1,
     num_samples_2, num_samples_3, num_samples_4,
     m20_mount] = get_values(  # noqa: F821
        'rna_plate_type', 'sample_vol', 'height_asp_sample', 'mm_vol',
        'num_samples_1', 'num_samples_2', 'num_samples_3', 'num_samples_4',
        'm20_mount')

    # load labware
    rna_source_plates = [
        ctx.load_labware(rna_plate_type, slot, f'RNA source plate {i+1}')
        for i, slot in enumerate(['2', '3', '5', '6'])]
    tempdeck = ctx.load_module('temperature module gen2', '4')
    tempdeck.set_temperature(4)
    mm_strips = tempdeck.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        'mastermix strips (1-3)').rows()[0][:3]
    dest_plate = ctx.load_labware('custom_384_wellplate_100ul', '1',
                                  'destination plate')
    tipracks = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['7', '8', '9', '10', '11']]

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)

    num_cols_all = [
        math.ceil(num_samples/8)
        for num_samples in [
            num_samples_1, num_samples_2, num_samples_3, num_samples_4]]
    samples_sources_sets = [
        plate.rows()[0][:num_samples]
        for plate, num_samples in zip(rna_source_plates, num_cols_all)]
    destination_sets = [
        dest_plate.rows()[i][j*12:j*12+num_cols_all[i*2+j]]
        for i in range(2) for j in range(2)]
    mm_destinations = [
        well for set in destination_sets for well in set]

    # pre-add mastermix
    cols_per_mm_strip = 16
    m20.pick_up_tip()
    r_384 = dest_plate.wells()[0].diameter/2
    for i, d in enumerate(mm_destinations):
        mm_source = mm_strips[i//cols_per_mm_strip]
        m20.aspirate(2, mm_source.top())  # pre-air gap
        m20.aspirate(mm_vol, mm_source)
        m20.dispense(m20.current_volume, d.bottom(2))
        m20.move_to(d.bottom().move(Point(x=r_384*0.5, z=2)))
    m20.drop_tip()

    # add samples
    for i, (s_set, d_set) in enumerate(
            zip(samples_sources_sets, destination_sets)):
        ctx.pause(f'Ensure plate {i+1} is on deck before resuming.')
        for s, d in zip(s_set, d_set):
            m20.pick_up_tip()
            m20.aspirate(sample_vol, s.bottom(height_asp_sample))
            m20.aspirate(2, d.bottom(2))
            m20.dispense(m20.current_volume, d.bottom(2))
            m20.drop_tip()

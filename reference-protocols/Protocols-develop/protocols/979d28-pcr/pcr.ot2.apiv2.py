import math
from opentrons.types import Point

metadata = {
    'protocolName': 'qPCR Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.12'
}

dilution_factor = 10.0
dilution_total_volume = 50.0


def run(ctx):

    num_samples, vol_mm, vol_dna, = get_values(  # noqa: F821
        'num_samples', 'vol_mm', 'vol_dna')

    source_plate = ctx.load_labware('vwr_96_aluminumblock_200ul', '11',
                                    'source cDNA plate')
    dil_plate = ctx.load_labware('vwr_96_aluminumblock_200ul', '8',
                                 'dilution plate')
    res = ctx.load_labware('nest_12_reservoir_15ml', '2')
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in ['7']]
    tips200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['10']]
    plate384 = ctx.load_labware('axygen_384_wellplate_50ul', '5',
                                '384-wellplate')

    water = res.wells()[0]
    mm = res.wells()[1]

    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'right', tip_racks=tips200)

    num_cols = math.ceil(num_samples/8)
    sources = source_plate.rows()[0][:num_cols]
    dil_locs = dil_plate.rows()[0][:num_cols]

    dest_sets_384 = [
        row[i*3:(i+1)*3]
        for row in plate384.rows()[:2] for i in range(8)][:num_cols+1]
    all_dests_384 = [well for set in dest_sets_384 for well in set]

    # add mastermix
    m20.pick_up_tip()
    for dest in all_dests_384:
        m20.aspirate(vol_mm, mm)
        m20.dispense(vol_mm, dest)
        m20.move_to(dest.bottom().move(Point(x=-1, z=5)))
    m20.drop_tip()

    # dilute and transfer to 384 wellplate
    water_vol = dilution_total_volume*(dilution_factor-1)/dilution_factor
    vol_dna_dilution = dilution_total_volume/dilution_factor
    m300.pick_up_tip()
    for dest in dil_locs:
        m300.aspirate(water_vol, water)
        m300.dispense(water_vol, dest.bottom(1))
        m300.move_to(dest.bottom().move(Point(x=-2, z=5)))
    m300.drop_tip()

    for source, dest, dest_set in zip(sources, dil_locs,
                                      dest_sets_384[:num_cols]):
        if not m20.has_tip:
            m20.pick_up_tip()
        m20.aspirate(vol_dna_dilution, source)
        m20.dispense(vol_dna_dilution, dest)
        m20.mix(5, 10, dest)
        for final_well in dest_set:
            m20.aspirate(vol_dna, dest)
            m20.move_to(dest.bottom().move(Point(x=-1, z=5)))
            m20.dispense(vol_dna, final_well)
            m20.mix(5, 10, final_well)
            m20.move_to(final_well.bottom().move(Point(x=-1, z=5)))
        m20.drop_tip()

    # add blank
    for dest in dest_sets_384[-1]:
        m20.pick_up_tip()
        m20.aspirate(vol_dna, water)
        m20.dispense(vol_dna_dilution, dest)
        m20.mix(5, 10, dest)
        m20.move_to(dest.bottom().move(Point(x=-1, z=5)))
        m20.drop_tip()

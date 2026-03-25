import math

metadata = {
    'protocolName': 'CYP Induction, Part 3/3',
    'author': 'Nick <ndiehl@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    num_samples, m20_mount = get_values(  # noqa: F821
        'num_samples', 'm20_mount')

    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['1', '4', '7', '10']]
    source_plates = [
        ctx.load_labware('thermofishermicroamp_96_wellplate_200ul', slot,
                         f'source plate {i+1}')
        for i, slot in enumerate(['2', '3'])]
    dest_plates = [
        ctx.load_labware('thermofishermicroamp_96_wellplate_200ul', slot,
                         f'destination plate {i+1}')
        for i, slot in enumerate(['5', '6'])]
    mm = ctx.load_labware('nest_1_reservoir_195ml', '8',
                          'mastermix').wells()[0]

    num_cols = math.ceil(num_samples/8)
    sources = [
        well for plate in source_plates for well in plate.rows()[0][:num_cols]]
    dests = [
        well for plate in dest_plates for well in plate.rows()[0][:num_cols]]

    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20)

    m20.pick_up_tip()
    m20.aspirate(2, mm)
    for d in dests:
        m20.aspirate(18, mm)
        m20.dispense(18, d)
    m20.dispense(m20.current_volume, mm.top())

    for s, d in zip(sources, dests):
        if not m20.has_tip:
            m20.pick_up_tip()
        m20.transfer(2, s, d, new_tip='never')
        m20.drop_tip()

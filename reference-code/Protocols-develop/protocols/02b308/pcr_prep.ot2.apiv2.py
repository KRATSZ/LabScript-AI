from opentrons.types import Point

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [mount_m20, num_plates, num_primers] = get_values(  # noqa: F821
        'mount_m20', 'num_plates', 'num_primers')

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    primers_plate = ctx.load_labware('eppendort_96_deepwell_1000ul', '8',
                                     'primers plate')
    dna_plate = ctx.load_labware('eppendort_96_deepwell_1000ul', '9',
                                 'mastermix/cDNA plate')
    qpcr_plates = [
        ctx.load_labware('appliedbiosystems_384_wellplate_40ul', slot,
                         f'qPCR plate {i+1}')
        for i, slot in enumerate(range(7, 7-num_plates, -1))]
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                         '200µl filtertiprack')
        for slot in ['10', '11']]

    # load P300M pipette
    m20 = ctx.load_instrument(
        'p20_multi_gen2', mount_m20, tip_racks=tips20)

    # locations
    primers = primers_plate.rows()[0][:num_primers]
    dna_sources = dna_plate.rows()[0][:num_plates*2]
    vol_primer = 2.0
    vol_dna = 8.0

    def wick(well, pip=m20, side=1):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.bottom().move(Point(x=side*well.diameter/2*0.8, z=3)))
        pip.move_to(well.top().move(Point(x=side*well.diameter/2*0.8)))
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def slow_withdraw(well, pip=m20, delay=2.0):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        if delay:
            ctx.delay(seconds=delay)
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # transfer primers
    for i, primer in enumerate(primers):
        m20.pick_up_tip()
        for plate in qpcr_plates:
            row = plate.rows()[i % 2]
            shift = (i // 2) * 3
            dests = row[shift:shift+3] + \
                row[shift+12:shift+12+3]
            for d in dests:
                m20.aspirate(vol_primer, primer.bottom(1))
                slow_withdraw(primer)
                m20.dispense(vol_primer, d.bottom(0.5))
                wick(d)
        m20.drop_tip()

    # transfer cDNA + mm
    m20.flow_rate.dispense *= 2
    m20.flow_rate.blow_out *= 2
    vol_pre_air_gap = 20 - vol_dna
    for i, s in enumerate(dna_sources):
        plate = qpcr_plates[i//2]
        half = i % 2
        columns = plate.columns()[half*12:(half+1)*12]
        all_dests = [well for col in columns for well in col[:2]]
        m20.pick_up_tip()
        for d in all_dests:
            m20.aspirate(vol_pre_air_gap, s.top())
            m20.aspirate(vol_dna, s.bottom(1))
            m20.dispense(m20.current_volume, d.top(-1))
        m20.drop_tip()

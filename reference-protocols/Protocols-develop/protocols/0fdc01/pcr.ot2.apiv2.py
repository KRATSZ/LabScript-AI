import math

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Krishna <krishna.soma@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_plates, reps_mix, vol_mm, vol_sample] = get_values(  # noqa: F821
        'num_plates', 'reps_mix', 'vol_mm', 'vol_sample')

    # modules
    tempdeck = ctx.load_module('temperature module gen2', '1')
    tempdeck.set_temperature(4)

    # labware
    reservoir = tempdeck.load_labware('nest_12_reservoir_15ml')
    plate_slots = ['5', '6']
    pcr_plates = [
        ctx.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul',
                         slot)
        for slot in plate_slots]
    sample_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '3',
        'sample plate')

    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '2')]
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '4')]

    # pipettes
    m300 = ctx.load_instrument(
         'p300_multi_gen2', 'left', tip_racks=tiprack300)
    m20 = ctx.load_instrument(
         'p20_multi_gen2', 'right', tip_racks=tiprack20)

    m300.flow_rate.aspirate /= 2
    m20.flow_rate.aspirate /= 2

    # variables
    mm = reservoir.wells()[:num_plates]
    sample_sources = sample_plate.rows()[0]

    def slow_withdraw(well, delay_seconds=1.0, pip=m300):
        pip.default_speed /= 16
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 16

    for n in range(num_plates):
        pcr_plate = pcr_plates[n//2]
        pcr_destinations = pcr_plate.rows()[0]

        # add mastermix with the same tip
        tip_vol_ref = m300.tip_racks[0].wells()[0].max_volume
        num_asp = math.ceil(vol_mm*len(pcr_destinations)/tip_vol_ref)
        max_dests_per_asp = int(math.floor(tip_vol_ref/vol_mm))
        mm_dest_sets = [
            pcr_destinations[i*max_dests_per_asp:(i+1)*max_dests_per_asp]
            if i < num_asp - 1
            else pcr_destinations[i*max_dests_per_asp:]
            for i in range(num_asp)]
        m300.pick_up_tip()
        for d_set in mm_dest_sets:
            m300.aspirate(vol_mm*len(d_set), mm[n//2].bottom(2))
            slow_withdraw(mm[n//2])
            for d in d_set:
                m300.dispense(vol_mm, d.bottom(-2))
                slow_withdraw(d)
        m300.drop_tip()

        # add sample with fresh tips each time, and mix (2x)
        for s, d in zip(sample_sources, pcr_destinations):
            m20.pick_up_tip()
            m20.aspirate(vol_sample, s.bottom(-2))
            slow_withdraw(s, pip=m20)
            m20.dispense(vol_sample, d.bottom(-2))
            m20.mix(reps_mix, 10, d.bottom(-1))
            slow_withdraw(d, pip=m20)
            m20.drop_tip()

        m20.reset_tipracks()

        if n < num_plates - 1:
            ctx.pause(f'Replace 20ul tiprack. Refill mastermix. \
Ensure clean PCR plate on slot {pcr_plates[(n+1)//2].parent} before resuming.')

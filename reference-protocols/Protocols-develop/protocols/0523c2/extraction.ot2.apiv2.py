from opentrons.types import Point
import math

metadata = {
    'protocolName': 'NGS Library Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, vol_sample, mount_m300,
     mount_m20, lw_tuberack] = get_values(  # noqa: F821
        'num_samples', 'vol_sample', 'mount_m300', 'mount_m20', 'lw_tuberack')

    # volumes
    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    # load modules
    tempdeck = ctx.load_module('temperature module gen2', '9')
    tempdeck.set_temperature(4)

    # load labware
    tube_block = tempdeck.load_labware(lw_tuberack)
    dna_plate = ctx.load_labware(
        'eppendorftwintec_96_wellplate_150ul', '5', 'DNA plate')
    output_plate = ctx.load_labware(
        'eppendorftwintec_96_wellplate_150ul', '6', 'output plate')
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', '7')]
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', '8')]

    # load pipettes
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount_m300, tip_racks=tips300)
    m20 = ctx.load_instrument(
        'p20_multi_gen2', mount_m20, tip_racks=tips20)

    def wick(pip, well, side=1, z=3):
        radius = well.diameter/2
        pip.move_to(well.bottom().move(Point(x=side*radius*0.7, z=3)))

    def slow_withdraw(pip, well, delay_seconds=2.0):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def pick_up_single(pip):
        tips_reversed = [
            well for rack in pip.tip_racks for well in rack.wells()[::-1]]
        default_current = 0.8 if pip == m300 else 0.6

        current = default_current/8  # modulate for 1 tip
        ctx._hw_manager.hardware._attached_instruments[
            pip._implementation.get_mount()
            ].update_config_item('pick_up_current', current)

        for tip in tips_reversed:
            if tip.has_tip:
                pip.pick_up_tip(tip)
                return

        ctx.pause(f'Replace {pip} tipracks before resuming.')
        pip.reset_tipracks

    # reagents
    num_cols = math.ceil(num_samples/8)
    samples_m = dna_plate.rows()[0][:num_cols]
    outputs_s = output_plate.wells()[:num_samples]
    outputs_m = output_plate.rows()[0][:num_cols]
    barcodes = [well for row in tube_block.rows() for well in row[2:]]
    mm = tube_block.wells()[0]
    mm_map = {
        'ligase-buffer': {
            'volume': 5.0,
            'tube': tube_block.wells()[1],
            'mix-after': False,
            'min-mix-volume': 0
        },
        'ion-p1-adapter': {
            'volume': 1.0,
            'tube': tube_block.wells()[2],
            'mix-after': False,
            'min-mix-volume': 0
        },
        'dntp-mix': {
            'volume': 1.0,
            'tube': tube_block.wells()[3],
            'mix-after': False,
            'min-mix-volume': 0
        },
        'water': {
            'volume': 37-vol_sample,
            'tube': tube_block.wells()[4],
            'mix-after': True,
            'min-mix-volume': 15
        },
        'dna-ligase': {
            'volume': 1.0,
            'tube': tube_block.wells()[5],
            'mix-after': False,
            'min-mix-volume': 0
        },
        'nick-repair-polymerase': {
            'volume': 4.0,
            'tube': tube_block.wells()[6],
            'mix-after': True,
            'min-mix-volume': 10
        }
    }

    # create mastermix
    min_depths = {
        pip: pip.tip_racks[0].wells()[0].depth - 5 if pip.tip_racks[0].wells()[
            0].depth - 5 < mm.depth else 0.5
        for pip in [m300, m20]
    }

    num_samples_overage = 1 if num_samples < 10 else 2
    num_samples_mm = num_samples + num_samples_overage
    vol_mix_fraction = 0.75
    vol_mm_running = 0
    for reagent_ind, reagent in enumerate(mm_map.values()):
        vol_composition = reagent['volume'] * num_samples_mm
        tube = reagent['tube']
        pip = m300 if vol_composition >= 20 else m20
        tube_depth = min_depths[pip]
        mix_after = reagent['mix-after']

        num_transfers = math.ceil(vol_composition/pip.max_volume)
        vol_per_transfer = round(vol_composition/num_transfers, 1)

        pick_up_single(pip)
        for i in range(num_transfers):
            vol_mm_running += vol_per_transfer
            pip.aspirate(vol_per_transfer, tube.bottom(tube_depth))
            slow_withdraw(pip, tube)
            pip.dispense(vol_per_transfer, mm.bottom(tube_depth))
            if i == num_transfers - 1 and mix_after:
                if not m300.has_tip:
                    pick_up_single(m300)
                min_mix_volume = reagent['min-mix-volume']
                if vol_mix_fraction*(
                        vol_mm_running) <= m300.max_volume - \
                        min_mix_volume:
                    vol_mix = vol_mix_fraction*vol_mm_running
                else:
                    vol_mix = m300.max_volume - min_mix_volume
                if vol_mm_running * 0.6 < 500:
                    reps_mix = 10
                elif 500 <= vol_mm_running < 1000:
                    reps_mix = 20
                else:
                    reps_mix = 30
                m300.aspirate(min_mix_volume, mm.bottom(tube_depth))
                m300.mix(reps_mix, vol_mix, tube.bottom(5))
                m300.dispense(m300.current_volume, tube.bottom(5))
                slow_withdraw(m300, mm)
        if reagent_ind < len(mm_map) - 1:
            [pip.drop_tip() for pip in [m20, m300] if pip.has_tip]

    # transfer MM to output plate
    vol_mm_per_output = sum(reagent['volume'] for reagent in mm_map.values())
    if not m300.has_tip:
        pick_up_single(m300)
    tube_depth = min_depths[m300]
    for output in outputs_s:
        m300.aspirate(vol_mm_per_output, mm.bottom(tube_depth))
        slow_withdraw(m300, mm)
        m300.dispense(vol_mm_per_output, output.bottom(1))
        slow_withdraw(m300, output)
    m300.drop_tip()

    # transfer barcodes
    tube_depth = min_depths[m20]
    for i, output in enumerate(outputs_s):
        # check if barcodes need to be refilled
        barcode_ind = i % 16
        if i > 0 and barcode_ind == 0:
            ctx.pause('Refills barcodes 1-16 in tube block, order A3, A4, \
A5, A6, B3, B4 ... D5, D6. Resume when finished')
        barcode = barcodes[barcode_ind]
        pick_up_single(m20)
        m20.aspirate(1, barcode.bottom(tube_depth))
        m20.aspirate(5, output.bottom(1))
        m20.dispense(m20.current_volume, output.bottom(1))
        slow_withdraw(m20, output)
        m20.drop_tip()

    # transfer DNA
    pip = m20 if vol_sample <= 20 else m300
    for s, d in zip(samples_m, outputs_m):
        pip.pick_up_tip()
        pip.aspirate(vol_sample, s.bottom(1))
        slow_withdraw(pip, s)
        pip.dispense(vol_sample, d.bottom(1))
        pip.aspirate(2, d.bottom(1))
        pip.mix(10, 18, d.bottom(1))
        pip.dispense(pip.current_volume, d.bottom(1))
        slow_withdraw(pip, d)
        pip.drop_tip()

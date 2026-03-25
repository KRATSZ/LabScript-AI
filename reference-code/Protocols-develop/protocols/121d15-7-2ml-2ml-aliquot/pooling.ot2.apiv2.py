import math
import os
import json

# metadata
metadata = {
    'protocolName': 'Aliquoting - 2ml Tuberack to 2ml Tuberack',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    tip_track = True

    [input_file, tuberack1_scan, tuberack2_scan, default_transfer_vol,
     p300_mount] = get_values(  # noqa: F821
        'input_file', 'tuberack1_scan', 'tuberack2_scan',
        'default_transfer_vol', 'p300_mount')

    # load labware
    rack = ctx.load_labware('eurofins_96x2ml_tuberack', '2', 'tuberack')
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['11']]

    # pipette
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    folder_path = '/data/tip_track'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                for pip in tip_log:
                    if pip.name in data:
                        tip_log[pip]['count'] = data[pip.name]
                    else:
                        tip_log[pip]['count'] = 0
        else:
            for pip in tip_log:
                tip_log[pip]['count'] = 0
    else:
        for pip in tip_log:
            tip_log[pip]['count'] = 0

    for pip in tip_log:
        if pip.type == 'multi':
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.rows()[0]]
        else:
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.wells()]
        tip_log[pip]['max'] = len(tip_log[pip]['tips'])

    def _pick_up(pip, loc=None):
        if tip_log[pip]['count'] == tip_log[pip]['max'] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
            tip_log[pip]['count'] += 1

    # check barcode scans (tube, plate)
    tuberack1_bar, tuberack2_bar = input_file.splitlines()[3].split(',')[:2]
    if not tuberack1_scan[:len(tuberack1_scan)-4] == tuberack1_bar.strip():
        raise Exception(f'Tuberack 1 scans do not match ({tuberack1_bar}, \
{tuberack1_scan})')
    if not tuberack2_scan[:len(tuberack2_scan)-4] == tuberack2_bar.strip():
        raise Exception(f'Tuberack 2 scans do not match ({tuberack2_bar}, \
{tuberack2_bar})')

    # parse
    data = [
        [val.strip() for val in line.split(',')]
        for line in input_file.splitlines()[4:]
        if line and line.split(',')[0].strip()]

    tubes1_ordered = [
        well for col in rack.columns()
        for well in col[:8]]

    tubes2_ordered = [
        well for col in rack.columns()
        for well in col[8:]]

    prev_source = None
    for line in data:
        tube1 = tubes1_ordered[int(line[0])-1]
        tube2 = tubes2_ordered[int(line[1])-1]
        if len(line) >= 3 and line[2]:
            transfer_vol = float(line[2])
        else:
            transfer_vol = default_transfer_vol

        # tip capacity 280 with 20 uL air gap
        reps = math.ceil(transfer_vol / 280)

        vol = transfer_vol / reps

        # transfer
        if tube1 != prev_source:
            if p300.has_tip:
                p300.drop_tip()
            _pick_up(p300)

        for rep in range(reps):
            p300.move_to(tube1.top())
            p300.air_gap(20)
            p300.aspirate(vol, tube1.bottom(0.5))
            p300.dispense(vol+20, tube2.top(-5), rate=2)
            ctx.delay(seconds=1)
            p300.blow_out()

        prev_source = tube1
    p300.drop_tip()

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

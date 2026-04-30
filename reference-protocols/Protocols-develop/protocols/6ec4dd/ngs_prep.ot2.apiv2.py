import json
import os
import math

metadata = {
    'protocolName': 'NGS Library Prep Part 1: PCR Setup I',
    'author': 'Nick <protocols@opentrons.com>',
    'apiLevel': '2.10'
}


def run(ctx):

    num_samples, m20_mount, tip_track = get_values(  # noqa: F821
        'num_samples', 'm20_mount', 'tip_track')

    # labware and modules
    source_plate = ctx.load_labware('kingfisher_96_wellplate_200ul',
                                    '2', 'source plate')
    dest_plate = ctx.load_labware('biorad_96_wellplate_350ul', '3',
                                  'PCR plate')
    tipracks_20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '5')]
    reagent_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                     '6', 'reagent plate')

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks_20)

    # samples and reagents
    num_cols = math.ceil(num_samples/8)
    sources = source_plate.rows()[0][:num_cols]
    dests = dest_plate.rows()[0][:num_cols]
    mm = reagent_plate.rows()[0][0]

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

    # transfer mastermix
    _pick_up(m20)
    for d in dests:
        m20.transfer(15, mm.bottom(0.5), d.bottom(1), touch_tip=True,
                     new_tip='never')

    # transfer each corresponding sample
    for s, d in zip(sources, dests):
        if not m20.has_tip:
            _pick_up(m20)
        m20.transfer(10, s.bottom(0.5), d.bottom(1), touch_tip=True,
                     new_tip='never')
        m20.air_gap(2)  # aspirate remaining droplets to avoid contamination
        m20.drop_tip()

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

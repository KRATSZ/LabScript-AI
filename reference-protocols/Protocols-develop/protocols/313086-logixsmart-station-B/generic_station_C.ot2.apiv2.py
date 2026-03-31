import json
import os
import math

# metadata
metadata = {
    'protocolName': 'Logix Smart Nasopharyngeal/Saliva Covid-19 PCR Prep \
(Station B)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [sample_type, num_samples, p10_mount, m10_mount,
     tip_track] = get_values(  # noqa: F821
        'sample_type', 'num_samples', 'p10_mount', 'm10_mount', 'tip_track')

    # load labware
    source_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '1',
                                    '96-deepwell sample plate')
    dest_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                  '2', '96-well PCR plate')
    tuberack = ctx.load_labware('opentrons_24_tuberack_nest_2ml_screwcap',
                                '4', 'reagent tuberack')
    tipracks10s = [
        ctx.load_labware('opentrons_96_tiprack_10ul', slot,
                         '300µl tiprack')
        for slot in ['7', '8', '10', '11']]
    tipracks10m = [ctx.load_labware('opentrons_96_tiprack_10ul', slot,
                                    '10µl tiprack')
                   for slot in ['3', '5', '6', '9']]

    # load pipette
    p10 = ctx.load_instrument('p10_single', p10_mount, tip_racks=tipracks10s)
    m10 = ctx.load_instrument('p10_multi', m10_mount, tip_racks=tipracks10m)

    # setup samples and reagents
    source_multi = source_plate.rows()[0][:math.ceil((num_samples+2)/8)]
    all_dests = dest_plate.wells()[:2+num_samples]
    all_dests_multi = dest_plate.rows()[0][:math.ceil((num_samples+2)/8)]
    mm, pos_control, neg_control = tuberack.wells()[:3]

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    folder_path = '/data/B'
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

    if sample_type == 'nasopharyngeal':
        vol_mm = 5
        vol_sample = 5
    else:
        vol_mm = 10
        vol_sample = 10

    # transfer mastermix
    _pick_up(p10)
    for d in all_dests:
        if vol_mm <= 7:
            p10.aspirate(2, mm.top())
        p10.aspirate(vol_mm, mm)
        if vol_mm <= 7:
            p10.air_gap(1)
        p10.dispense(p10.current_volume, d.bottom(1))
    p10.drop_tip()

    # transfer sample
    for s, d in zip(source_multi, all_dests_multi):
        _pick_up(m10)
        if vol_mm <= 7:
            m10.aspirate(2, mm.top())
        m10.aspirate(vol_sample, mm)
        if vol_mm <= 7:
            m10.air_gap(1)
        m10.dispense(p10.current_volume, d.bottom(1))
        m10.drop_tip()

    # transfer controls
    for s, d in zip([pos_control, neg_control], dest_plate.wells()[:2]):
        _pick_up(p10)
        if vol_mm <= 7:
            p10.aspirate(2, mm.top())
        p10.aspirate(vol_sample, mm)
        if vol_mm <= 7:
            p10.air_gap(1)
        p10.dispense(p10.current_volume, d.bottom(1))
        p10.drop_tip()

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

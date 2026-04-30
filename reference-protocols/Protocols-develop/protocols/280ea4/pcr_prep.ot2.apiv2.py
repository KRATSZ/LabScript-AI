import json
import os
import math

# metadata
metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):
    [num_samples, assay, prepare_mastermix, p300_single_mount,
     p300_multi_mount, tip_track] = get_values(  # noqa: F821
        'num_samples', 'assay', 'prepare_mastermix',
        'p300_single_mount', 'p300_multi_mount', 'tip_track')

    # check source (elution) labware type
    source_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                    '1', 'DNA source plate')
    tips300s = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['5', '6', '8', '9']]
    tips300m = []
    tempdeck = ctx.load_module('Temperature Module Gen2', '7')
    pcr_plate = tempdeck.load_labware('biorad_96_aluminumblock_200ul',
                                      'PCR strips')
    tempdeck.set_temperature(4)
    tube_block = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_screwcap', '3',
        '2ml screw tube aluminum block for mastermix + reagents')

    # pipette
    p300 = ctx.load_instrument('p300_single_gen2', p300_single_mount,
                               tip_racks=tips300s)
    m300 = ctx.load_instrument('p300_multi_gen2', p300_multi_mount)

    # setup up sample sources and destinations
    sources = source_plate.wells()[:num_samples]
    sample_dests = pcr_plate.wells()[:num_samples]

    tip_log = {'count': {}}
    folder_path = '/data/C'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips300m' in data:
                    tip_log['count'][m300] = data['tips300m']
                else:
                    tip_log['count'][m300] = 0
                if 'tips300s' in data:
                    tip_log['count'][p300] = data['tips300s']
                else:
                    tip_log['count'][p300] = 0
        else:
            tip_log['count'] = {m300: 0, p300: 0}
    else:
        tip_log['count'] = {m300: 0, p300: 0}

    tip_log['tips'] = {
        m300: [tip for rack in tips300m for tip in rack.rows()[0]],
        p300: [tip for rack in tips300s for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [m300, p300]
    }

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1

    """ mastermix component maps """
    mm_tubes = tube_block.wells()[:2]
    [mmx, enzyme, primer1, primer2, primer3, primer4, primer5, primer6, probe,
     other, nfh2o] = tube_block.wells()[2:13]
    mm_map = {
        '1': {
            'sample_vol': 5,
            'mm_vol': 50,
            'components': {
                tube: vol for tube, vol in zip(
                    [mmx, enzyme, primer1, primer2, primer3, primer4, primer5,
                     primer6, nfh2o],
                    [25, 2, 2, 2, 2, 2, 2, 2, 11])
            }
        },
        '2': {
            'sample_vol': 5,
            'mm_vol': 50,
            'components': {
                tube: vol for tube, vol in zip(
                    [mmx, enzyme, primer1, primer2, nfh2o],
                    [25, 2, 1, 1, 21])
            }
        },
        '3': {
            'sample_vol': 5,
            'mm_vol': 22.5,
            'components': {
                tube: vol for tube, vol in zip(
                    [mmx, primer1, primer2, nfh2o],
                    [12.5, 1.25, 1.25, 8.5])
            }
        },
        '4': {
            'sample_vol': 5,
            'mm_vol': 17,
            'components': {
                tube: vol for tube, vol in zip(
                    [mmx, enzyme, primer1, primer2, primer3, probe, nfh2o],
                    [12.5, 1, 0.25, 0.25, 0.25, 0.25, 2.5])
            }
        },
        '5': {
            'sample_vol': 5,
            'mm_vol': 20,
            'components': {
                tube: vol for tube, vol in zip(
                    [mmx, primer1, primer2, probe, other, nfh2o],
                    [6.25, 0.1, 0.2, 0.5, 1, 11.95])
            }
        }
    }
    mm_dict = mm_map[assay]
    sample_vol = mm_dict['sample_vol']
    mm_vol = mm_dict['mm_vol']

    vol_overage = 1.2 if num_samples > 48 else 1.1
    total_mm_vol = mm_vol*(num_samples+2)*vol_overage
    # translate total mastermix volume to starting height
    r = mm_tubes[0].diameter/2
    mm_heights = {
        tube: total_mm_vol/(math.pi*(r**2)) - 5
        for tube in mm_tubes
    }

    def h_track(vol, tube):
        dh = 1.1*vol/(math.pi*(r**2))  # compensate for 10% theoretical v loss
        h = mm_heights[tube]
        h = h - dh if h - dh > 2 else 2  # stop at 2mm
        mm_heights[tube] = h
        return tube.bottom(mm_heights[tube])

    def p300_transfer(vol, source, dest):
        if vol < 20:
            p300.aspirate(20-vol, source.top())
            p300.aspirate(vol, source)
            p300.dispense(vol, dest)
            p300.dispense(p300.current_volume, dest.top())
        else:
            num_trans = math.ceil(vol/160)
            vol_per_trans = vol/num_trans
            for _ in range(num_trans):
                p300.aspirate(20, source.top())
                p300.aspirate(vol_per_trans, source)
                ctx.delay(seconds=2)
                p300.touch_tip(source)
                p300.air_gap(20)
                p300.dispense(20, dest.top())  # void air gap
                p300.dispense(vol_per_trans, dest.bottom(2))
                p300.dispense(20, dest.top())  # void pre-loaded air gap
                # p300.blow_out(mm_tube.top())
                p300.touch_tip(dest)

    if prepare_mastermix:
        p300.flow_rate.aspirate = 15
        p300.flow_rate.dispense = 30
        vol_overage = 1.2 if num_samples > 48 else 1.1
        if mm_dict['mm_vol']*num_samples*vol_overage > 1700:
            num_mm_tubes = 2
        else:
            num_mm_tubes = 1
        for i, (tube, vol) in enumerate(mm_dict['components'].items()):
            comp_vol = vol*num_samples*vol_overage/num_mm_tubes
            pick_up(p300)
            for mm_tube in mm_tubes[:num_mm_tubes]:
                p300_transfer(comp_vol, tube, mm_tube)
            if i < len(mm_dict['components'].items()) - 1:
                p300.drop_tip()
        mm_total_vol_per_tube = mm_vol*(num_samples)*vol_overage/num_mm_tubes
        if not p300.hw_pipette['has_tip']:
            pick_up(p300)
        if mm_total_vol_per_tube / 2 <= 200:
            mix_vol = mm_total_vol_per_tube / 2
        else:
            mix_vol = 100
        for tube in mm_tubes[:num_mm_tubes]:
            if num_samples > 48:
                mix_loc = mm_tube.bottom(20)
            else:
                mix_loc = mm_tube.bottom(5)
            p300.mix(7, mix_vol, mix_loc)
            # p300.blow_out(mm_tube.top())
            p300.touch_tip()

    # transfer mastermix to plate
    if num_mm_tubes == 1:
        sample_dest_sets = [sample_dests]
    else:
        split_ind = math.ceil(num_samples/2)
        sample_dest_sets = [sample_dests[:split_ind], sample_dests[split_ind:]]
    for mm_tube, dest_set in zip(mm_tubes, sample_dest_sets):
        p300.distribute(mm_dict['mm_vol'], mm_tube, dest_set,
                        new_tip='never')
    p300.drop_tip()

    # transfer samples to corresponding locations
    for s, d in zip(sources, sample_dests):
        pick_up(p300)
        p300_transfer(sample_vol, s, d)
        p300.drop_tip()

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips300m': tip_log['count'][m300],
            'tips300s': tip_log['count'][p300]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

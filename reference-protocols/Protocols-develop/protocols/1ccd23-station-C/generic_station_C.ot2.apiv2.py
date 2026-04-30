from opentrons import protocol_api
import json
import os
import math

# metadata
metadata = {
    'protocolName': 'Covid-19 qPCR Prep (Station C)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx: protocol_api.ProtocolContext):
    [num_samples, assay, strip_type, prepare_mastermix,
     tip_track] = get_values(  # noqa: F821
        'num_samples', 'assay', 'strip_type', 'prepare_mastermix', 'tip_track')

    # check source (elution) labware type
    source_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '1',
        'chilled elution plate on block from Station B')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['3', '6', '8', '9', '10', '11']
    ]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '2')]
    tempdeck = ctx.load_module('Temperature Module Gen2', '4')
    pcr_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', 'PCR plate')
    mm_strips = ctx.load_labware(strip_type, '7', 'mastermix strips')
    tempdeck.set_temperature(4)
    tube_block = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_screwcap', '5',
        '2ml screw tube aluminum block for mastermix + controls')

    # pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)

    # setup up sample sources and destinations
    num_cols = math.ceil(num_samples/8)
    sources = source_plate.rows()[0][:num_cols]
    sample_dests = pcr_plate.rows()[0][:num_cols]

    tip_log = {'count': {}}
    folder_path = '/data/C'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips20' in data:
                    tip_log['count'][m20] = data['tips20']
                else:
                    tip_log['count'][m20] = 0
                if 'tips300' in data:
                    tip_log['count'][p300] = data['tips300']
                else:
                    tip_log['count'][p300] = 0
        else:
            tip_log['count'] = {m20: 0, p300: 0}
    else:
        tip_log['count'] = {m20: 0, p300: 0}

    tip_log['tips'] = {
        m20: [tip for rack in tips20 for tip in rack.rows()[0]],
        p300: [tip for rack in tips300 for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [m20, p300]
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
    mm_tube = tube_block.wells()[0]
    mm_map = {
        'Allplex 2019-nCoV Assay': {
            'sample_vol': 8,
            'mm_vol': 17,
            'components': {
                tube: vol for tube, vol in zip(tube_block.columns()[1][:4],
                                               [5, 5, 5, 2])
            }
        },
        'Allplex SARS-CoV-2 Assay': {
            'sample_vol': 5,
            'mm_vol': 15,
            'components': {
                tube: vol for tube, vol in zip(tube_block.columns()[1][:2],
                                               [5, 5, 5])
            }
        },
        'Seegene Real-time One-step RT-PCR': {
            'sample_vol': 10,
            'mm_vol': 10,
            'components': {
                tube: vol for tube, vol in zip(tube_block.columns()[1][:2],
                                               [5, 5])
            }
        }
    }
    mm_dict = mm_map[assay]
    sample_vol = mm_dict['sample_vol']
    mm_vol = mm_dict['mm_vol']

    vol_overage = 1.2 if num_samples > 48 else 1.1
    total_mm_vol = mm_vol*(num_samples+2)*vol_overage
    # translate total mastermix volume to starting height
    r = mm_tube.diameter/2
    mm_height = total_mm_vol/(math.pi*(r**2)) - 5

    def h_track(vol):
        nonlocal mm_height
        dh = 1.1*vol/(math.pi*(r**2))  # compensate for 10% theoretical v loss
        mm_height = mm_height - dh if mm_height - dh > 2 else 2  # stop at 2mm
        return mm_tube.bottom(mm_height)

    if prepare_mastermix:
        p300.flow_rate.aspirate = 15
        p300.flow_rate.dispense = 30
        vol_overage = 1.2 if num_samples > 48 else 1.1

        for i, (tube, vol) in enumerate(mm_dict['components'].items()):
            comp_vol = vol*(num_samples)*vol_overage
            pick_up(p300)
            num_trans = math.ceil(comp_vol/160)
            vol_per_trans = comp_vol/num_trans
            for _ in range(num_trans):
                p300.aspirate(20, tube.top())
                p300.aspirate(vol_per_trans, tube)
                ctx.delay(seconds=3)
                p300.touch_tip(tube)
                p300.air_gap(20)
                p300.dispense(20, mm_tube.top())  # void air gap
                p300.dispense(vol_per_trans, mm_tube.bottom(2))
                p300.dispense(20, mm_tube.top())  # void pre-loaded air gap
                # p300.blow_out(mm_tube.top())
                p300.touch_tip(mm_tube)
            if i < len(mm_dict['components'].items()) - 1:
                p300.drop_tip()
        mm_total_vol = mm_vol*(num_samples)*vol_overage
        if not p300.hw_pipette['has_tip']:
            pick_up(p300)
        mix_vol = mm_total_vol / 2 if mm_total_vol / 2 <= 200 else 200
        mix_loc = mm_tube.bottom(20) if num_samples > 48 else mm_tube.bottom(5)
        p300.mix(7, mix_vol, mix_loc)
        # p300.blow_out(mm_tube.top())
        p300.touch_tip()

    # transfer mastermix to strips
    vol_per_strip_well = num_cols*mm_vol*((vol_overage-1)/2+1)
    mm_strip = mm_strips.columns()[0]
    if not p300.hw_pipette['has_tip']:
        pick_up(p300)
    for well in mm_strip:
        p300.transfer(vol_per_strip_well, mm_tube, well, new_tip='never')
    p300.drop_tip()

    # transfer mastermix to plate
    pick_up(m20)
    m20.transfer(mm_vol, mm_strip[0].bottom(0.5), sample_dests,
                 new_tip='never')
    m20.drop_tip()

    # transfer samples to corresponding locations
    for s, d in zip(sources, sample_dests):
        pick_up(m20)
        m20.transfer(sample_vol, s.bottom(2), d.bottom(2), new_tip='never')
        m20.mix(1, 10, d.bottom(2))
        m20.blow_out(d.top(-2))
        m20.aspirate(5, d.top(2))
        m20.drop_tip()

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips20': tip_log['count'][m20],
            'tips300': tip_log['count'][p300]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

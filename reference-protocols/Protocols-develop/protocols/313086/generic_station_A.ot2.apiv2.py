import json
import os

# metadata
metadata = {
    'protocolName': 'Logix Smart Nasopharyngeal Covid-19 Plating (Station A)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_samples, vol_sample, vol_lys_buffer, vol_elution_buffer, asp_height,
     p300_mount, p300_type, p1000_mount, p1000_type,
     tip_track] = get_values(  # noqa: F821
        'num_samples', 'vol_sample', 'vol_lys_buffer', 'vol_elution_buffer',
        'asp_height', 'p300_mount', 'p300_type', 'p1000_mount', 'p1000_type',
        'tip_track')

    # load labware
    dest_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '1', '96-deepwell sample plate')
    source_racks = [
        ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', slot,
                         'source tuberack ' + str(i+1))
        for i, slot in enumerate(['2', '3', '5', '6'])
    ]
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4',
                                 'reagent reservoir')
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                         '300µl tiprack')
        for slot in ['7', '8', '10', '11']]
    tipracks1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', slot,
                                     '1000µl tiprack')
                    for slot in ['9']]

    # load pipette
    p300 = ctx.load_instrument(p300_type, p300_mount, tip_racks=tipracks300)
    p1000 = ctx.load_instrument(p1000_type, p1000_mount,
                                tip_racks=tipracks1000)

    # setup samples and reagents
    sources = [
        well for rack in source_racks for well in rack.wells()][:num_samples]
    dests_single = dest_plate.wells()[2:2+num_samples]  # leave controls empty
    lys_buffer = reservoir.wells()[:4]
    elution_buffer = reservoir.wells()[-1]
    tip_log = {'count': {}}
    folder_path = '/data/A'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips1000' in data:
                    tip_log['count'][p1000] = data['tips1000']
                else:
                    tip_log['count'][p1000] = 0
                if 'tips300' in data:
                    tip_log['count'][p300] = data['tips300']
                else:
                    tip_log['count'][p300] = 0
    else:
        tip_log['count'] = {p1000: 0, p300: 0}

    tip_log['tips'] = {
        p1000: [tip for rack in tipracks1000 for tip in rack.wells()],
        p300: [tip for rack in tipracks300 for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p1000, p300]
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

    # transfer lysis/binding buffer
    for i, d in enumerate(dests_single):
        pick_up(p1000)
        p1000.transfer(vol_lys_buffer, lys_buffer[i//24], d.bottom(5),
                       air_gap=100, new_tip='never')
        p1000.air_gap(100)
        p1000.drop_tip()

    # transfer sample
    for s, d in zip(sources, dests_single):
        pick_up(p300)
        p300.transfer(vol_sample, s.bottom(asp_height), d.bottom(5),
                      air_gap=20, new_tip='never')
        p300.air_gap(20)
        p300.drop_tip()

    # transfer elution buffer
    for i, d in enumerate(dests_single):
        pick_up(p300)
        p300.transfer(vol_lys_buffer, elution_buffer, d.bottom(5),
                      air_gap=20, new_tip='never')
        p300.air_gap(20)
        p300.drop_tip()

    ctx.comment('Move deepwell plate (slot 4) to Station B for RNA \
extraction.')

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips1000': tip_log['count'][p1000],
            'tips300': tip_log['count'][p300]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

import os
import json
from opentrons.types import Point

# metadata
metadata = {
    'protocolName': 'Tube Filling',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.4'
}


def run(ctx):

    # num_samples, p1000_mount, input_csv = [
    #     24, 'left',
    #     'distance down tube to aspirate (in mm),aspiration speed (in ul/s),\
    #     dispense speed (in ul/s)\n20,100,100\n20,100,100\n']
    num_samples, p1000_mount, input_csv, tip_track = get_values(  # noqa: F821
        'num_samples', 'p1000_mount', 'input_csv', 'tip_track')

    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '1')]
    sample_racks = [
        ctx.load_labware('custom_6_tuberack_100ml', slot, 'Samples ' + name)
        for slot, name in zip(['5', '2', '6', '3'],
                              ['1, 2, 5, 6, 9, 10', '3, 4, 7, 8, 11, 12',
                               '13, 14, 17, 18, 21, 22',
                               '15, 16, 19, 20, 23, 24'])]
    lw_racks = [
        ctx.load_labware('custom_15_tuberack_6000ul', slot, name)
        for slot, name in zip(['10', '11'], ['LW 1-15', 'LW 16-24 (6 spare)'])]
    icp_racks = [
        ctx.load_labware('custom_15_tuberack_6000ul', slot, name)
        for slot, name in zip(['7', '8'],
                              ['ICP 1-15', 'ICP 16-24 (6 spare)'])]
    ir_rack = ctx.load_labware('custom_24_testtuberack_2ml', '4',
                               'IR tubes (1-24)')

    # pipette
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack1000)
    ctx.max_speeds['A'] = 200
    ctx.max_speeds['Z'] = 200

    # determine starting tip
    tip_log_file_path = '/data/pooling/tip_track.json'
    tip_log_folder_path = os.path.dirname(tip_log_file_path)

    tip_count = 0
    if not ctx.is_simulating() and tip_track:
        if not os.path.exists(tip_log_folder_path):
            os.makedirs(tip_log_folder_path)
        if (
                tip_track
                and os.path.isfile(tip_log_file_path)
                and os.stat(tip_log_file_path).st_size > 0):
            with open(tip_log_file_path, 'r') as tip_file:
                data = json.load(tip_file)
                if 'tips1000' in data:
                    tip_count = data['tips1000']

    tip_log = {
        p1000: {
            'tip_list': [
                tip for rack in tiprack1000 for tip in rack.wells()],
            'tip_max': len(tiprack1000) * 96,
            'tip_count': tip_count
        }
    }

    def pick_up(pip):
        if tip_log[p1000]['tip_count'] >= tip_log[p1000]['tip_max']:
            ctx.pause('Please replace 1000ul tipracks in slots 1, 6, and 9 \
before resuming.')
            tip_log[p1000]['tip_count'] = 0
        p1000.pick_up_tip(
            tip_log[p1000]['tip_list'][tip_log[p1000]['tip_count']])
        tip_log[p1000]['tip_count'] += 1

    # parse .csv file
    csv_data = [
        [val.strip() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line]
    depths, asp_rates, dispense_rates = [
        [float(line[ind]) for line in csv_data]
        for ind in range(3)]
    samples_odered = [
        well
        for i in range(2)
        for j in range(3)
        for rack in sample_racks[i*2:i*2+2]
        for well in rack.columns()[j]][:num_samples]
    lw_ordered = [
        well
        for rack in lw_racks
        for col in rack.columns()
        for well in col[::-1]][:num_samples]
    icp_ordered = [
        well
        for rack in icp_racks
        for col in rack.columns()
        for well in col[::-1]][:num_samples]
    ir_ordered = ir_rack.wells()[:num_samples]

    def touch_tip(loc, v_offset):
        [p1000.move_to(loc.top().move(
            Point(x=side*loc.geometry._diameter/2, z=v_offset)))
         for side in [-1, 1]]

    # transfers
    for asp_rate, dispense_rate, depth, s, icp, lw, ir in zip(
            asp_rates, dispense_rates, depths, samples_odered, icp_ordered,
            lw_ordered, ir_ordered):
        p1000.flow_rate.aspirate = asp_rate
        p1000.flow_rate.dispense = dispense_rate
        pick_up(p1000)
        touch_tip(s, -10)
        p1000.aspirate(1000, s.top(-1*depth))
        p1000.dispense(500, icp.top(-2))
        p1000.dispense(500, lw.top(-2))
        p1000.aspirate(1000, s.top(-1*depth))
        touch_tip(s, -10)
        p1000.dispense(500, ir.top(-2))
        p1000.drop_tip(home_after=False)

    if not ctx.is_simulating():
        with open(tip_log_file_path, 'w') as tip_file:
            data = {'tips1000': tip_log[p1000]['tip_count']}
            json.dump(data, tip_file)

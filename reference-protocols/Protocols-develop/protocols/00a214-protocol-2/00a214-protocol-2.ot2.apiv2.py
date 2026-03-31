import csv
import os

metadata = {
    'protocolName': 'DAPI Staining',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [num_plates, asp_speed,
        asp_height, disp_height] = get_values(  # noqa: F821
        'num_plates', 'asp_speed', 'asp_height', 'disp_height')

    # load labware and pipettes
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', '1')

    if num_plates > 4:
        raise Exception('This protocol can only accommodate up to 4 plates')

    plates = [
        protocol.load_labware(
            'eppendorf_96_wellplate_200ul',
            s) for s in ['2', '3', '5', '6']][:num_plates]

    res = protocol.load_labware('nest_12_reservoir_15ml', '7')
    pbs1 = res.wells()[:num_plates]
    pbs2 = res.wells()[4:4+num_plates]
    pfa = res.wells()[8:8+num_plates]

    res2 = protocol.load_labware('nest_12_reservoir_15ml', '10')
    pbsDapi = res2.wells()[:num_plates]
    pbs3 = res2.wells()[4:4+num_plates]
    pbs4 = res2.wells()[8:8+num_plates]

    waste = protocol.load_labware('nest_1_reservoir_195ml', '11',
                                  'Liquid Waste').wells()[0].top()

    p300 = protocol.load_instrument('p300_multi_gen2', 'left')

    p300.flow_rate.aspirate = asp_speed
    p300.flow_rate.dispense = asp_speed
    p300.flow_rate.blow_out = 300

    # create pick_up function for tips
    # Tip tracking between runs
    if not protocol.is_simulating():
        file_path = '/data/csv/tiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial tip count tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    tip_count_list = []
    if protocol.is_simulating():
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    tip300count = int(tip_count_list[0])

    def pick_up():
        nonlocal tip300count

        if tip300count == 12:
            for _ in range(6):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                protocol.delay(seconds=1)
            protocol.pause('Please replace tips.')
            p300.reset_tipracks()
            tip300count = 0
        p300.pick_up_tip(tips300.rows()[0][tip300count])
        tip300count += 1

    for idx, (plate, res_src) in enumerate(zip(plates, pbs1)):
        wells = plate.rows()[0]
        protocol.comment(f'Removing media from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(120, well.bottom(asp_height))
            p300.dispense(120, waste)
        protocol.comment(f'Adding PBS to plate {idx+1}...')
        for well in wells:
            p300.aspirate(140, res_src)
            p300.dispense(140, well.bottom(disp_height))
        p300.drop_tip()

    for idx, (plate, res_src) in enumerate(zip(plates, pbs2)):
        wells = plate.rows()[0]
        protocol.comment(f'Removing PBS from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(140, well.bottom(asp_height))
            p300.dispense(140, waste)
        protocol.comment(f'Adding PBS to plate {idx+1}...')
        for well in wells:
            p300.aspirate(140, res_src)
            p300.dispense(140, well.bottom(disp_height))
        p300.drop_tip()

    for idx, (plate, res_src) in enumerate(zip(plates, pfa)):
        wells = plate.rows()[0]
        protocol.comment(f'Removing PBS from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(140, well.bottom(asp_height))
            p300.dispense(140, waste)
        protocol.comment(f'Adding 2% PFA to plate {idx+1}...')
        for well in wells:
            p300.aspirate(100, res_src)
            p300.dispense(100, well.bottom(disp_height))
        p300.drop_tip()

    protocol.comment('Cells should be in PFA for at least 12 minutes...')
    protocol.pause('Click RESUME when ready')

    for idx, (plate, res_src) in enumerate(zip(plates, pbsDapi)):
        wells = plate.rows()[0]
        protocol.comment(f'Removing 2% PFA from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(100, well.bottom(asp_height))
            p300.dispense(100, waste)
        protocol.comment(f'Adding PBS+DAPI to plate {idx+1}...')
        for well in wells:
            p300.aspirate(140, res_src)
            p300.dispense(140, well.bottom(disp_height))
        p300.drop_tip()

    for idx, (plate, res_src) in enumerate(zip(plates, pbs3)):
        wells = plate.rows()[0]
        protocol.comment(f'Removing PBS+DAPI from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(140, well.bottom(asp_height))
            p300.dispense(140, waste)
        protocol.comment(f'Adding PBS to plate {idx+1}...')
        for well in wells:
            p300.aspirate(140, res_src)
            p300.dispense(140, well.bottom(disp_height))
        p300.drop_tip()

    for idx, (plate, res_src) in enumerate(zip(plates, pbs4)):
        wells = plate.rows()[0]
        protocol.comment(f'Removing PBS from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(140, well.bottom(asp_height))
            p300.dispense(140, waste)
        protocol.comment(f'Adding PBS to plate {idx+1}...')
        for well in wells:
            p300.aspirate(140, res_src)
            p300.dispense(140, well.bottom(disp_height))
        p300.drop_tip()

    # write updated tipcount to CSV
    new_tip_count = str(tip300count)+", "+str(tip_count_list[1])+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

    protocol.comment('Protocol complete!')

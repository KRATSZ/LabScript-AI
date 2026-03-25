import csv
import os

metadata = {
    'protocolName': 'Seeding Plates with Mammalian Cells',
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

    plates = [
        protocol.load_labware(
            'eppendorf_96_wellplate_200ul',
            str(s)) for s in range(2, 10)][:num_plates]

    res = protocol.load_labware('nest_12_reservoir_15ml', '10')

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

    for idx, (plate, res_src) in enumerate(zip(plates, res.wells())):
        wells = plate.rows()[0]
        protocol.comment(f'Removing gelatin from plate {idx+1}...')
        pick_up()
        for well in wells:
            p300.aspirate(50, well.bottom(asp_height))
            p300.dispense(50, waste)
        p300.drop_tip()

        protocol.comment(f'Adding solution to plate {idx+1}...')
        pick_up()
        p300.flow_rate.aspirate = 150
        p300.flow_rate.dispense = 300
        p300.mix(5, 150, res_src)
        p300.blow_out()
        p300.flow_rate.aspirate = asp_speed
        p300.flow_rate.dispense = asp_speed
        for well in wells:
            p300.aspirate(140, res_src)
            p300.dispense(140, well.bottom(disp_height))
            p300.blow_out()
        p300.drop_tip()

    # write updated tipcount to CSV
    new_tip_count = str(tip300count)+", "+str(tip_count_list[1])+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

    protocol.comment('Protocol complete!')

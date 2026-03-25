from opentrons import protocol_api
import csv
import os

metadata = {
    'protocolName': 'Cherry Picking PCR Prep with CSV File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):

    [csv_sample, transfer_vol,
        p20_mount, reset_counter] = get_values(  # noqa: F821
        "csv_sample", "transfer_vol", "p20_mount", "reset_counter")

    # Counter tracking between runs
    if not protocol.is_simulating():
        file_path = '/data/csv/tiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial well tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    counter_list = []
    if protocol.is_simulating():
        counter_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            counter_list = next(csv_reader)

    if reset_counter:
        p25ctr = 0
        p30ctr = 0

    else:
        p25ctr = int(counter_list[0])
        p30ctr = int(counter_list[1])

    # load labware
    s_plate = protocol.load_labware('life_96_aluminumblock_240ul', '1')
    plate25 = protocol.load_labware('thermoscientific_96_wellplate_200ul', '2')
    plate30 = protocol.load_labware('thermoscientific_96_wellplate_200ul', '4')
    tiprack = protocol.load_labware('opentrons_96_filtertiprack_20ul', '5')

    # load instrument
    p20 = protocol.load_instrument('p20_single_gen2', p20_mount,
                                   tip_racks=[tiprack])

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            protocol.pause("Replace all tip racks")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # csv file --> nested list
    transfer = [[val.strip().lower() for val in line.split(',')]
                for line in csv_sample.splitlines()
                if line.split(',')[0].strip()][1:]

    # distribute 2.5 ul to wells 6 columns to respective target plates
    gap = 5
    for line in transfer:
        if line[::-1][0] == 'done':
            continue

        # transferring to 25-cycle target plate
        # put 2.5 ul into wells 6 columns apart
        # aspirate extra to ensure proper distribution
        elif line[5] == '25':
            pick_up(p20)
            p20.aspirate(transfer_vol*2+2, s_plate.wells_by_name()
                         [line[4].upper().replace(':', '')])
            p20.air_gap(gap)
            p20.dispense(transfer_vol+gap, plate25.wells()[p25ctr])
            p20.air_gap(gap)
            p20.dispense(transfer_vol+gap, plate25.wells()[p25ctr+48])
            p20.air_gap(gap)
            p20.blow_out(s_plate.wells_by_name()
                         [line[4].upper().replace(':', '')])
            p20.drop_tip()
            p25ctr += 1

            if p25ctr == 48:
                protocol.pause("Replace 25-cycle target plate in Slot 2")
                p25ctr = 0

        # transferring to 30-cycle target plate
        elif line[5] == '30':
            pick_up(p20)
            p20.aspirate(transfer_vol*2+2, s_plate.wells_by_name()
                         [line[4].upper().replace(':', '')])
            p20.air_gap(gap)
            p20.dispense(transfer_vol+gap, plate30.wells()[p30ctr])
            p20.air_gap(gap)
            p20.dispense(transfer_vol+gap, plate30.wells()[p30ctr+48])
            p20.air_gap(gap)
            p20.blow_out(s_plate.wells_by_name()
                         [line[4].upper().replace(':', '')])
            p20.drop_tip()
            p30ctr += 1

            if p30ctr == 48:
                protocol.pause("Replace 30-cycle target plate in Slot 3")
                p30ctr = 0

    protocol.comment('''Source plate depleted.
Replace source plate and upload its corresponding CSV
to the protocol website.''')

    # write updated counter to CSV
    new_counter_num = str(p25ctr)+", "+str(p30ctr)+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_counter_num)

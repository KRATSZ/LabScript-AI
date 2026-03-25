metadata = {
    'protocolName': 'Cell Culture Cherry Picking with CSV File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [csv, p300_mount] = get_values(  # noqa: F821
        "csv", "p300_mount")

    # csv --> nested list
    list_of_rows = [[val.strip() for val in line.split(',')]
                    for line in csv.splitlines()
                    if line.split(',')[0].strip()][1:]

    # mapping
    source_slot = 0
    source_well = 1
    transfer_vol = 2
    dest_slot = 3
    dest_well = 4

    num_384_plates = []
    num_96_plates = []
    for row in list_of_rows:
        num_384_plates.append(int(row[source_slot]))
        num_96_plates.append(int(row[dest_slot]))
    num_384_plates = len(set(num_384_plates))

    num_96_plates = len(set(num_96_plates))

    # labware
    source_plates = [ctx.load_labware('perkinelmer_384_wellplate_110ul', slot)
                     for slot in ['1', '2', '3', '4', '5', '6'][:num_384_plates]]  # noqa: E501
    dest_plates = [ctx.load_labware('corning_96_wellplate_360ul', slot)
                   for slot in ['7', '8'][:num_96_plates]]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['10', '11']]

    # instruments
    p300 = ctx.load_instrument('p300_single_gen2',
                               p300_mount, tip_racks=tiprack200)  # noqa: E501

    airgap = 10
    for line in list_of_rows:
        source = source_plates[int(line[source_slot])-1].wells_by_name()[line[source_well]]  # noqa: E501
        dest = dest_plates[int(line[dest_slot])-1].wells_by_name()[line[dest_well]]  # noqa: E501
        p300.pick_up_tip()
        p300.mix(3, 0.80*int(line[transfer_vol]), source)
        p300.aspirate(int(line[transfer_vol]), source)
        p300.air_gap(airgap)
        p300.dispense(int(line[transfer_vol])+airgap, dest)
        p300.drop_tip()

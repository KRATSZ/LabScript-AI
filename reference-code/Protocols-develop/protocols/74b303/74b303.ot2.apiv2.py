import string

metadata = {
    'protocolName': 'Four Plate Normalization',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [mix_rate, tiprack_slot, reservoir_slot, tube_rack_slot, mix_volume,
     mix_repetitions, pooling_volume, pipette_type, pipette_mount,
     column_count, row_count, uploaded_csv] = get_values(  # noqa: F821
        "mix_rate", "tiprack_slot", "reservoir_slot", "tube_rack_slot",
        "mix_volume", "mix_repetitions", "pooling_volume", "pipette_type",
        "pipette_mount", "column_count", "row_count", "uploaded_csv")

    tiprack_map = {
        'p10_single': 'opentrons_96_filtertiprack_10ul',
        'p50_single': 'opentrons_96_filtertiprack_200ul',
        'p300_single_gen1': 'opentrons_96_filtertiprack_200ul',
        'p1000_single_gen1': 'opentrons_96_filtertiprack_1000ul',
        'p20_single_gen2': 'opentrons_96_filtertiprack_20ul',
        'p300_single_gen2': 'opentrons_96_filtertiprack_200ul',
        'p1000_single_gen2': 'opentrons_96_filtertiprack_1000ul'
    }

    if mix_rate < 1 or mix_rate > 5:
        raise Exception('Invalid mix rate (must be 1-5).')

    # row references
    rows = [*string.ascii_uppercase[:row_count]]

    # lines from uploaded csv file
    [*csv_lines] = uploaded_csv.splitlines()

    # plate count, plate order, plate names, custom volumes from csv lines
    plate_names, row_volumes = [], []
    for index, line in enumerate(csv_lines):
        if index == 0:
            plate_name_index = 0
        new_row = {}
        if not any(line.replace(",", "")):
            plate_name_index = index + 1
            continue
        if index == plate_name_index:
            plate_name = line.split(",")[column_count + 1]
            if plate_name not in plate_names:
                plate_names.append(plate_name)
            row_name_index = 0
        new_row['plate'] = plate_name
        new_row['row_name'] = rows[row_name_index]
        new_row['volumes'] = line.split(",")[:column_count]
        row_volumes.append(new_row)
        row_name_index += 1

    # tipracks
    tipracks = [ctx.load_labware(tiprack_map[pipette_type], tiprack_slot)]

    # pipette
    pip = ctx.load_instrument(pipette_type, pipette_mount, tip_racks=tipracks)

    # water
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", reservoir_slot)
    water = reservoir.wells()[0]

    # deck slots available for pcr plates
    available_deck_slots = [str(num) for num in [*range(1, 12)]]
    for slt in [tiprack_slot, reservoir_slot, tube_rack_slot]:
        available_deck_slots.pop(available_deck_slots.index(slt))

    # pcr plates
    [*plate_names] = [ctx.load_labware(
        "neptunegensci_pcrplate",
        slot, plate_name) for slot, plate_name in zip(
            available_deck_slots[:len(plate_names)],
            plate_names)]

    # pools
    tube_rack = ctx.load_labware(
      'opentrons_24_tuberack_nest_2ml_snapcap', tube_rack_slot)
    pools = ["pool" + str(i) for i in range(len(plate_names))]
    [*pools] = tube_rack.wells()[:len(plate_names)]

    # transfer csv water volumes to pcr plate row wells using one tip per plate
    for index, plate in enumerate(plate_names):
        pip.pick_up_tip()
        for item in row_volumes:
            if item["plate"] == plate.name:
                pip.transfer(
                  [float(volume) for volume in item["volumes"]], water, [
                    well for well in plate.rows_by_name()[
                      item["row_name"]]], new_tip="never")
        pip.drop_tip()

    # mix first, then pool 5 ul aliquots using one tip per plate
    for index, plate in enumerate(plate_names):
        pip.pick_up_tip()
        for well in plate.wells():
            pip.mix(mix_repetitions, mix_volume, well.bottom(), mix_rate)
            pip.aspirate(pooling_volume, well.bottom())
            pip.dispense(pooling_volume, pools[index])
        pip.drop_tip()

from opentrons import protocol_api

metadata = {
    'protocolName': 'Utility: Rearrange pipette tips for 24-well spacing',
    'author': 'Tim Fallon <tfallon@ucsd.edu>',
    'description': 'Rearranges pipette tips from their standard spacing in a \
full box, to two empty tip box putting the pipette tips in every \
other row. This allows the P300/P20-multipipette to be used for \
pipetting from 24 well plates.',
    'apiLevel': '2.13'
}


def run(protocol: protocol_api.ProtocolContext):

    tiprack_map = {
        'p10_single': {
            'standard': 'opentrons_96_tiprack_10ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p50_single': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p300_single': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        },
        'p20_single_gen2': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p300_single_gen2': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single_gen2': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        },
        'p300_multi_gen2': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_tiprack_300ul'
        }
    }

    pipette_type = 'p300_multi_gen2'
    pipette_mount = 'right'
    tip_type = 'filter'

    full_tiprack_slots = [10]
    empty_tiprack_slots = [4, 5]
    target_rows = ["A", "C", "E", "G"]
    target_cols = list(range(1, 13))
    full_tipracks = [
        protocol.load_labware(tiprack_map[pipette_type][tip_type], s)
        for s in full_tiprack_slots]
    empty_tipracks = [
        protocol.load_labware(tiprack_map[pipette_type][tip_type], s)
        for s in empty_tiprack_slots]

    pipette = protocol.load_instrument(
         pipette_type, pipette_mount, full_tipracks)

    col_index = -1
    row_index = 0
    empty_tiprack_index = 0
    for tr in full_tipracks:

        reversed_wells = list(tr.wells())
        reversed_wells.reverse()  # updates in place
        for w in reversed_wells:
            col_index += 1
            if row_index == len(target_rows)-1 and col_index == len(
                    target_cols):
                empty_tiprack_index += 1
                row_index = 0
                col_index = 0
            if col_index == len(target_cols):
                row_index += 1
                col_index = 0

            target_well = str(target_rows[row_index])+str(
                target_cols[col_index])  # I.e. like 'A1' or 'B1'
            source_location = w
            pipette.pick_up_tip(source_location)
            destination_location = empty_tipracks[empty_tiprack_index].wells(
                target_well)[0]
            pipette.drop_tip(destination_location)

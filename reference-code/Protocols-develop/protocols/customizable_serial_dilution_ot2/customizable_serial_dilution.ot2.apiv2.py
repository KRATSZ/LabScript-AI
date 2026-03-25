"""DETAILS."""
metadata = {
    'protocolName': 'Customizable Serial Dilution',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.11'
    }


def run(protocol_context):
    """PROTOCOL BODY."""
    [pipette_type, mount_side, tip_type, trough_type, plate_type,
        dilution_factor, num_of_dilutions, total_mixing_volume,
        blank_on, tip_use_strategy, air_gap_volume] = get_values(  # noqa: F821
            'pipette_type', 'mount_side', 'tip_type', 'trough_type',
            'plate_type', 'dilution_factor', 'num_of_dilutions',
            'total_mixing_volume', 'blank_on',
            'tip_use_strategy', 'air_gap_volume'
        )
    # check for bad setup here
    if not 1 <= num_of_dilutions <= 11:
        raise Exception('Enter a number of dilutions between 1 and 11')

    if num_of_dilutions == 11 and blank_on == 1:
        raise Exception(
                        'No room for blank with 11 dilutions')

    pip_range = pipette_type.split('_')[0].lower()

    tiprack_map = {
        'p10': {
            'standard': 'opentrons_96_tiprack_10ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p20': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p50': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p300': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        }
    }

    # labware
    trough = protocol_context.load_labware(
        trough_type, '2')
    plate = protocol_context.load_labware(
        plate_type, '3')
    tip_name = tiprack_map[pip_range][tip_type]
    tipracks = [
        protocol_context.load_labware(tip_name, slot)
        for slot in ['1', '4']
    ]
    print(mount_side)
    # pipette
    pipette = protocol_context.load_instrument(
        pipette_type, mount_side, tipracks)

    # reagents
    diluent = trough.wells()[0]

    transfer_volume = total_mixing_volume/dilution_factor
    diluent_volume = total_mixing_volume - transfer_volume

    if 'multi' in pipette_type:
        dilution_destination_sets = [
            [row] for row in plate.rows()[0][1:num_of_dilutions]]
        dilution_source_sets = [
            [row] for row in plate.rows()[0][:num_of_dilutions-1]]
        blank_set = [plate.rows()[0][num_of_dilutions+1]]

    else:
        dilution_destination_sets = plate.columns()[1:num_of_dilutions]
        dilution_source_sets = plate.columns()[:num_of_dilutions-1]
        blank_set = plate.columns()[num_of_dilutions+1]

    all_diluent_destinations = [
        well for set in dilution_destination_sets for well in set]

    pipette.pick_up_tip()
    for dest in all_diluent_destinations:
        # Distribute diluent across the plate to the the number of samples
        # And add diluent to one column after the number of samples for a blank
        pipette.transfer(
                diluent_volume,
                diluent,
                dest,
                air_gap=air_gap_volume,
                new_tip='never')
    pipette.drop_tip()

    # Dilution of samples across the 96-well flat bottom plate
    if tip_use_strategy == 'never':
        pipette.pick_up_tip()
    for source_set, dest_set in zip(dilution_source_sets,
                                    dilution_destination_sets):
        for s, d in zip(source_set, dest_set):
            pipette.transfer(
                    transfer_volume,
                    s,
                    d,
                    air_gap=air_gap_volume,
                    mix_after=(5, total_mixing_volume/2),
                    new_tip=tip_use_strategy)
    if tip_use_strategy == 'never':
        pipette.drop_tip()

    if blank_on:
        pipette.pick_up_tip()
        for blank_well in blank_set:
            pipette.transfer(
                    diluent_volume,
                    diluent,
                    blank_well,
                    air_gap=air_gap_volume,
                    new_tip='never')
        pipette.drop_tip()

metadata = {
    'protocolName': 'Cherrypicking (Simple)',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.7'
    }


def run(protocol):
    [volumes_csv, pip_model, pip_mount, sp_type,
     dp_type, filter_tip, tip_reuse] = get_values(  # noqa: F821
        'volumes_csv', 'pip_model', 'pip_mount', 'sp_type',
         'dp_type', 'filter_tip', 'tip_reuse')

    # create pipette and volume max
    pip_max = pip_model.split('_')[0][1:]

    pip_max = '300' if pip_max == '50' else pip_max
    tip_name = 'opentrons_96_tiprack_'+pip_max+'ul'
    if filter_tip == 'yes':
        pip_max = '200' if pip_max == '300' else pip_max
        tip_name = 'opentrons_96_filtertiprack_'+pip_max+'ul'

    tiprack_slots = ['1', '4', '7', '10']
    tips = [protocol.load_labware(tip_name, slot)
            for slot in tiprack_slots]

    pipette = protocol.load_instrument(pip_model, pip_mount, tip_racks=tips)

    # create labware
    dest_plate = protocol.load_labware(dp_type, '3', 'Destination Labware')

    data = [r.split(',') for r in volumes_csv.strip().splitlines() if r][1:]

    if len(data[0]) == 2:
        source_plate = protocol.load_labware(sp_type, '2', 'Source Labware')
        if tip_reuse == 'never':
            pipette.pick_up_tip()
        for well_idx, (source_well, vol) in enumerate(data):
            if source_well and vol:
                vol = float(vol)
                pipette.transfer(
                    vol,
                    source_plate.wells(source_well),
                    dest_plate.wells(well_idx),
                    new_tip=tip_reuse)
        if tip_reuse == 'never':
            pipette.drop_tip()
    else:
        source_plates = []
        plateno = 0
        for d in data:
            z = int(d[2])
            if z > plateno:
                plateno = z
        for i in range(plateno):
            nomenclature = 'Source Plate ' + str(i+1)
            numeral = str(i*3+2)
            source_plates.append(protocol.load_labware(
                sp_type,
                numeral,
                nomenclature
            ))
        if tip_reuse == 'never':
            pipette.pick_up_tip()
        for well_idx, (source_well, vol, plate) in enumerate(data):
            if source_well and vol and plate:
                vol = float(vol)
                source_p = source_plates[int(plate)-1]
                pipette.transfer(
                    vol,
                    source_p.wells(source_well),
                    dest_plate.wells(well_idx),
                    new_tip=tip_reuse)
        if tip_reuse == 'never':
            pipette.drop_tip()

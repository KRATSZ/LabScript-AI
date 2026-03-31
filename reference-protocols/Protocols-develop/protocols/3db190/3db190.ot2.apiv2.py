import math

metadata = {
    'protocolName': 'Lyra Direct SARS-CoV Assay Sample Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):

    [total_samples, pipette_types, pip_l, pip_r,
        tip_type] = get_values(  # noqa: F821
        "total_samples", "pipette_types", "pip_l", "pip_r", "tip_type")

    # Column Calculation for Multichannel
    total_samples = int(total_samples)
    cols = math.ceil(total_samples/8)

    tiprack_map = {
        'p20_single_gen2': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p1000_single_gen2': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        },
        'p20_multi_gen2': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p300_multi_gen2': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        }
    }

    # Load Tip Racks
    tipracks_l = [protocol.load_labware(tiprack_map[pip_l][tip_type],
                                        slot) for slot in ['7', '8']]
    tipracks_r = [protocol.load_labware(
        tiprack_map[pip_r][tip_type], slot) for slot in ['4', '5']]

    # Load Plates
    # 1 mL Deepwell Microtiter Plate
    deepwell_plate = protocol.load_labware('eppendorf_96_deepwell_1000ul', 2)
    # PCR Plate resting on top of the thermal block
    pcr_plate = protocol.load_labware('enduraplate_96_wellplate_200ul', 3)

    # Load Instruments
    pip_left = protocol.load_instrument(pip_l, 'left',
                                        tip_racks=tipracks_l)
    pip_right = protocol.load_instrument(pip_r, 'right',
                                         tip_racks=tipracks_r)

    if pipette_types == 'single':
        # Proccess Buffer (A1)
        buffer = protocol.load_labware(
            'opentrons_6_tuberack_falcon_50ml_conical', 1)['A1'].bottom(z=10)

        deep_samples = deepwell_plate.wells()[:total_samples]
        pcr_samples = pcr_plate.wells()[:total_samples]

    if pipette_types == 'multi':
        # Proccess Buffer
        # 10 mL per channel, enough for 3 columns of sample
        reservoir = protocol.load_labware('nest_12_reservoir_15ml', 1)
        buffer_wells = [well for well in reservoir.rows()[0][:cols]
                        for i in range(3)]

        # Sample Wells
        deep_samples = deepwell_plate.rows()[0][:cols]
        pcr_samples = pcr_plate.rows()[0][:cols]

    # Protocol Steps

    # Add 400 uL of Process Buffer to Required Wells in Deep Well Block
    protocol.comment(f'''Adding 400 uL of process buffer
                     sequentially to {total_samples} wells...''')
    pip = pip_left if pip_left.max_volume > 20 else pip_right
    pip.pick_up_tip()
    if pipette_types == 'single':
        for well in deep_samples:
            pip.transfer(400, buffer, well,
                         new_tip='never')
    if pipette_types == 'multi':
        for well, buffer in zip(deep_samples, buffer_wells):
            pip.transfer(400, buffer, well,
                         new_tip='never')
    pip.drop_tip()

    # PAUSE PROTOCOL #
    protocol.pause('''Pausing protocol for further specimen processing and
                   addition of 15uL of master mix to the PCR plate. Click
                   Resume when ready...''')

    # Mix and Add 5 uL from Deep Well Block to PCR Plate
    # Mix 5x with P300 set at 150 uL, (Uses new tip each time)
    # then transfer with P20 at 5 uL (Uses new tip each time)
    protocol.comment('Starting the mixing and transfer of specimen process...')
    for source, dest in zip(deep_samples, pcr_samples):
        pip = pip_left if pip_left.max_volume > 20 else pip_right
        pip.pick_up_tip()
        pip.mix(5, 150, source)
        pip.drop_tip()
        pip = pip_left if pip_left.max_volume < 300 else pip_right
        pip.transfer(5, source,
                     dest, new_tip='always')

metadata = {
    'protocolName': 'Customizable Serial Dilution',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.9'
    }


def run(ctx):
    [pipette_mount, diluent_csv, sample_csv, serial_csv,
     load_csv] = get_values(  # noqa: F821
     'pipette_mount', 'diluent_csv', 'sample_csv', 'serial_csv', 'load_csv')

    # labware
    dilution_plates = [
        ctx.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt', slot,
            'dilution plate ' + str(i+1))
        for i, slot in enumerate(['1', '3', '4', '6'])]
    sample_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '2')
    gyros_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '5', 'GyrosPCRPlate')
    diluent = ctx.load_labware(
        'nest_1_reservoir_195ml', '8', 'diluent')
    tiprack = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['7', '9', '10', '11']]

    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tiprack)

    labware_map = {
        'SamplePlate1': sample_plate,
        'GyrosDiluent': diluent,
        'GyrosPCRPlate': gyros_plate,
        'PCRPlate[001]': dilution_plates[0],
        'PCRPlate[002]': dilution_plates[1],
        'PCRPlate[003]': dilution_plates[2],
        'PCRPlate[004]': dilution_plates[3],
    }
    action_map = {
        'A': p300.aspirate,
        'D': p300.dispense,
        'W': p300.drop_tip
    }

    def csv_action(input_csv, mix=False):
        info = [
            line for line in input_csv.splitlines() if line]
        for line in info:
            vals = line.split(';')
            action = vals[0]
            if action == 'W':
                action_map[action]()
            else:
                labware = labware_map[vals[1]]
                well = labware.wells_by_name()[vals[4]]
                volume = float(vals[6])
                if not p300.has_tip:
                    p300.pick_up_tip()
                action_map[action](volume, well)
                if action == 'D' and mix:
                    p300.mix(10, 100, well)

    # diluent addition
    csv_action(diluent_csv)

    # samples
    csv_action(sample_csv)

    # serial dilution
    csv_action(serial_csv, mix=True)

    # load plate
    csv_action(load_csv)

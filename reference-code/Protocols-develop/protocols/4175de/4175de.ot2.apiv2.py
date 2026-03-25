metadata = {
    'protocolName': 'Cherrypicking PCR/qPCR prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [transfer_csv, total_samples, p20_mount, pcr_labware,
        mastermix_vol] = get_values(  # noqa: F821
        "transfer_csv", "total_samples", "p20_mount", "pcr_labware",
        "mastermix_vol")

    # Load Tip Racks
    tipracks = [protocol.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in ['1', '4', '7']]

    # Load Module
    temp_mod = protocol.load_module('temperature module gen2', 3)
    pcr_plate = temp_mod.load_labware(pcr_labware)
    mastermix = protocol.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', 2)['A6']

    # Load labware via CSV
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    for line in transfer_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[4:6]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in protocol.loaded_labwares:
                protocol.load_labware(lw.lower(), slot)

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    # Load Pipette
    p20 = protocol.load_instrument('p20_single_gen2', p20_mount,
                                   tip_racks=tipracks)

    # Activate temperature module and set temperature to 4 Celsius
    # Pauses protocol until desired temperature is reached
    protocol.comment("Setting temperature to 4C on the Temperature Module")
    temp_mod.set_temperature(4)

    # Transfer Master Mix to Variable # of wells on PCR Plate sequentially
    protocol.comment("Transferring master mix...")
    mastermix_wells = [well for row in pcr_plate.rows()
                       for well in row][:int(total_samples)]

    p20.pick_up_tip()
    for well in mastermix_wells:
        p20.transfer(float(mastermix_vol), mastermix, well,
                     new_tip='never')
    p20.drop_tip()

    # Transfer DNA from source wells to PCR Plate
    protocol.comment("Transferring DNA samples from source to destination")
    for line in transfer_info:
        _, s_slot, s_well, h, _, d_slot, d_well, vol = line[:8]
        source = protocol.loaded_labwares[int(s_slot)].wells_by_name()[
            parse_well(s_well)].bottom(float(h))
        dest = protocol.loaded_labwares[int(d_slot)].wells_by_name()[
            parse_well(d_well)]
        p20.transfer(float(vol), source, dest, new_tip='always')

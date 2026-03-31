from opentrons import protocol_api

metadata = {
    'protocolName': 'Custom CSV Transfer',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(protocol):
    [transfer_csv] = get_values(  # noqa: F821
     'transfer_csv')

    # convert CSV/multi-line string to list

    transfer_info = [
        line.split(',')
        for line in transfer_csv.splitlines() if line
    ][1:]
    source_plate_slots = []
    source_wells = []
    target_plate_slots = []
    target_wells = []
    volumes = []

    # parse for transfer information
    for line in transfer_info:
        source_plate_slots.append(line[0].strip())
        source_wells.append(line[1].strip())
        volumes.append(float(line[4].strip()))
        target_plate_slots.append(line[2].strip())
        target_wells.append(line[3].strip())

    # create dictionary based on slots found and labware
    labware_dict = {}
    labware_dict['9'] = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '9')
    labware_dict['6'] = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '6')
    labware_dict['10'] = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '10')
    labware_dict['3'] = protocol.load_labware(
        'usascientific_12_reservoir_22ml', '3')
    labware_dict['2'] = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '2')
    labware_dict['5'] = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '5')
    labware_dict['8'] = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '8')
    labware_dict['11'] = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '11')
    # tips50 = [protocol.load_labware('opentrons_96_tiprack_300ul', '1')]
    tips300 = [protocol.load_labware(
        'opentrons_96_tiprack_300ul', s) for s in ['4', '7']]

    # p50 = protocol.load_instrument('p50_single', 'right', tip_racks=tips50)
    m300 = protocol.load_instrument('p300_multi', 'left', tip_racks=tips300)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            protocol.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # perform transfers
    pick_up(m300)

    for s_slot, s_well, t_slot, t_well, vol in zip(
            source_plate_slots,
            source_wells,
            target_plate_slots,
            target_wells,
            volumes):

        m300.transfer(
            vol,
            labware_dict[s_slot][s_well],
            labware_dict[t_slot][t_well],
            new_tip='never'
        )
        mix_vol = vol
        if mix_vol > m300.max_volume:
            mix_vol = m300.max_volume
        m300.mix(10, mix_vol)
        m300.blow_out()

    m300.drop_tip()

    protocol.comment('Protocol complete!')

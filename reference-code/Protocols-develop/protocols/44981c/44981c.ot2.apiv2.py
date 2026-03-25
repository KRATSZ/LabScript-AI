from opentrons import protocol_api

metadata = {
    'protocolName': 'CSV Cherrypicking APIv2',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(protocol):
    [transfer_csv, src_labware, dest_labware,
     pipettes, tiptype] = get_values(  # noqa: F821
     'transfer_csv', 'src_labware', 'dest_labware', 'pipettes', 'tiptype')

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
    mix_vols = []
    mix_cycles = []

    # parse for transfer information
    for line in transfer_info:
        source_plate_slots.append(line[0].strip())
        source_wells.append(line[1].strip())
        volumes.append(float(line[2].strip()))
        target_plate_slots.append(line[3].strip())
        target_wells.append(line[4].strip())
        mix_vols.append(float(line[5].strip()))
        mix_cycles.append(int(line[6].strip()))

    # create dictionary based on slots found and labware
    src_slots = list(set(source_plate_slots))
    sources = {}
    for s in src_slots:
        sources[s] = protocol.load_labware(src_labware, s)
    dest_slots = list(set(target_plate_slots))
    targets = {}
    for s in dest_slots:
        targets[s] = protocol.load_labware(dest_labware, s)

    # create tip racks and pipettes based on variables
    sp_name, bp_name, sp_tip, bp_tip = pipettes.split(' ')
    if sp_tip == bp_tip:
        sp_tips = [
            protocol.load_labware(
                tiptype+sp_tip, str(s)) for s in range(7, 12)]
        bp_tips = sp_tips
    else:
        sp_tips = [
            protocol.load_labware(tiptype+sp_tip, str(s)) for s in [7, 8, 9]]
        bp_tips = [
            protocol.load_labware(tiptype+bp_tip, str(s)) for s in [10, 11]]

    small_pip = protocol.load_instrument(sp_name, 'right', tip_racks=sp_tips)
    big_pip = protocol.load_instrument(bp_name, 'left', tip_racks=bp_tips)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            protocol.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # perform transfers
    for s_slot, s_well, t_slot, t_well, vol, mix_vol, mix_n in zip(
            source_plate_slots,
            source_wells,
            target_plate_slots,
            target_wells,
            volumes,
            mix_vols,
            mix_cycles):

        if vol > 0:
            pip = small_pip if vol <= small_pip.max_volume else big_pip

            pick_up(pip)

            pip.transfer(
                vol,
                sources[s_slot][s_well],
                targets[t_slot][t_well],
                blow_out=True,
                new_tip='never'
            )
            if mix_vol > pip.max_volume:
                mix_vol = pip.max_volume
            pip.mix(mix_n, mix_vol)
            pip.blow_out()
            pip.drop_tip()

    protocol.comment('Protocol complete!')

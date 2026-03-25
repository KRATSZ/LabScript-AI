metadata = {
    'protocolName': 'Normalization',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.10'
    }


def run(ctx):
    [input_csv, pipette_type, pipette_mount,
     source_type] = get_values(  # noqa: F821
        'input_csv', 'pipette_type', 'pipette_mount', 'source_type')

    # labware
    if source_type == 'opentrons_24_tuberack_nest_1.5ml_snapcap':
        [ctx.load_labware(source_type, slot, f'tuberack {i+1}')
         for i, slot in enumerate(['4', '5', '7', '8'])]
    else:
        ctx.load_labware(source_type, '5', 'source plate')
    end_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '6', 'end plate')
    diluent_res = ctx.load_labware('nest_12_reservoir_15ml', '9',
                                   'diluent (channel 1)')

    # pipette
    pip_range = pipette_type.split('_')[0][1:]
    pip_range = '300' if pip_range == '50' else pip_range
    tiprack_def = f'opentrons_96_tiprack_{pip_range}ul'

    tipracks = [ctx.load_labware(tiprack_def, slot) for slot in ['2', '3']]
    pip = ctx.load_instrument(pipette_type, pipette_mount, tip_racks=tipracks)

    # parse data
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()
        if line and line.split(',')[0].strip()][1:]

    # transfer diluent
    dil_chan = 0
    dil_vol = 10000

    def diluent_track(vol):
        nonlocal dil_chan
        nonlocal dil_vol
        if dil_vol - vol < 100:
            if dil_chan < 11:
                dil_chan += 1
            else:
                ctx.pause('Refill diluent reservoir before resuming.')
                dil_chan = 0
            dil_vol = 10000
        dil_vol -= vol
        return diluent_res.wells(dil_chan)

    pip.pick_up_tip()
    for line in data:
        dest_well = end_plate.wells_by_name()[line[3]]
        d_vol = float(line[7])
        pip.transfer(d_vol, diluent_track(d_vol), dest_well, new_tip='never')
    pip.drop_tip()

    # transfer sample and mix
    for line in data:
        if source_type == 'nest_96_wellplate_100ul_pcr_full_skirt':
            source_slot = 5
        else:
            source_slot = int(line[1])
        source_well = ctx.loaded_labwares[source_slot].wells_by_name()[line[2]]
        dest_well = end_plate.wells_by_name()[line[3]]
        sample_vol = float(line[6])
        d_vol = float(line[7])
        total_vol = sample_vol + d_vol

        pip.pick_up_tip()
        if 0.8*total_vol < pip.max_volume:
            mix_vol = 0.8*total_vol
        else:
            mix_vol = pip.max_volume
        pip.transfer(sample_vol, source_well, dest_well,
                     mix_after=(3, mix_vol), new_tip='never')
        pip.blow_out(dest_well.top(-1))
        pip.touch_tip()
        pip.drop_tip()

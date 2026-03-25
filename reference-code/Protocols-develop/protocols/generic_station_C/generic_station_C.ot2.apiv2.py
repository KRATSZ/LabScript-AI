import math

metadata = {
    'protocolName': 'Generic qPCR Setup Protocol (Station C)',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.12'
}


def run(protocol):
    [num_samples, rm_num, mm_vol, samp_vol,
     single_pip_info, multi_pip_info] = get_values(  # noqa: F821
        'num_samples', 'rm_num', 'mm_vol', 'samp_vol',
        'single_pip_info', 'multi_pip_info')

    rm_num = int(rm_num)

    # load labware and pipettes
    sp_name, sp_tip_name = single_pip_info.split()
    mp_name, mp_tip_name = multi_pip_info.split()

    # check sample number + reaction mix number combination
    if num_samples * rm_num > 96:
        raise Exception(f'Invalid combination of number of samples \
({num_samples}) and number of reaction mixes ({rm_num}). Multiple of these \
inputs cannot exceed 96 (currently {num_samples*rm_num}).')

    sp_tips = [protocol.load_labware(sp_tip_name, s) for s in ['6', '3']]

    if mp_tip_name != "none":
        if mp_tip_name == sp_tip_name:
            mp_tips = sp_tips
        else:
            mp_tips = [protocol.load_labware(mp_tip_name, '3')]

    single_pip = protocol.load_instrument(sp_name, 'right', tip_racks=sp_tips)

    tempdeck = protocol.load_module('tempdeck', '4')
    tempplate = tempdeck.load_labware(
        'ab_96_aluminumblock')
    n_chunks = int(96/rm_num)
    mm_well_chunks = [
        tempplate.wells()[i:i + n_chunks] for i in range(0, 96, n_chunks)]

    stationBplate = protocol.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '1')

    alBlockMM = protocol.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap', '5')
    mmTubes = alBlockMM.wells()[:rm_num]
    tempdeck.set_temperature(4)

    # Distribute mastermix
    for idx, (tube, mm_wells) in enumerate(zip(mmTubes, mm_well_chunks)):
        protocol.comment(f'Distributing mastermix {idx+1}...')
        single_pip.pick_up_tip()
        mm_ctr = 8
        for well in mm_wells[:num_samples]:
            if mm_ctr == 8:
                single_pip.mix(5, single_pip.max_volume, tube)
                mm_ctr = 1
            single_pip.aspirate(mm_vol, tube)
            single_pip.dispense(mm_vol, well)
            single_pip.blow_out()
            mm_ctr += 1
        single_pip.drop_tip()

    # Add samples
    protocol.comment('Adding samples...')
    if mp_name != "none":
        pipette = protocol.load_instrument(mp_name, 'left', tip_racks=mp_tips)
        num_cols = math.ceil(num_samples/8)
        sampwells = stationBplate.rows()[0][:num_cols]
        col_chunks = int(12/rm_num)
        mm_well_chunks = [
            tempplate.rows()[0][i:i + col_chunks] for i in range(
                0, 12, col_chunks)]
    else:
        pipette = single_pip
        sampwells = stationBplate.wells()[:num_samples]

    mix_vol = samp_vol+mm_vol
    if mix_vol > pipette.max_volume:
        mix_vol = pipette.max_volume

    for tempwells in mm_well_chunks:
        for src, dest in zip(sampwells, tempwells):
            pipette.pick_up_tip()
            pipette.aspirate(samp_vol, src)
            pipette.dispense(samp_vol, dest)
            pipette.mix(3, mix_vol, dest)
            pipette.blow_out()
            pipette.drop_tip()

    protocol.comment('Protocol complete!')

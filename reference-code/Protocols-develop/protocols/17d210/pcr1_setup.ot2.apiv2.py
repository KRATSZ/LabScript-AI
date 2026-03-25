metadata = {
    'protocolName': 'Verogen ForenSeq DNA Signature Prep Kit Part 1/5: \
PCR1 Setup',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [transfer_csv, m20_mount, mm_vol, mix_after] = get_values(  # noqa: F821
        'transfer_csv', 'm20_mount', 'mm_vol', 'mix_after')
#     transfer_csv = "volume,source plate # (1-4),source column (1-12),\
# destination column(1-12)\n8,1,2,1\n8,2,3,2\n8,2,12,3"
#     m20_mount = 'left'
#     mm_vol = 7.0
#     mix_after = True

    # load labware
    mm = ctx.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul',
                          '6', 'mastermix tubes (strip column 1)').wells()[0]
    source_plates = {
        str(i+1): ctx.load_labware('amplifyt_96_wellplate_200ul', slot,
                                   f'plate {i+1}')
        for i, slot in enumerate(['11', '8', '5', '2'])
    }
    tips20m = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['3', '7']]
    dest_plate = ctx.load_labware('amplifyt_96_wellplate_200ul', '9',
                                  'destination plate')
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]

    # load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20m)

    # pre-transfer mastermix with P20-multi
    mm_dests = [
        dest_plate.columns_by_name()[line.split(',')[-1]][0]
        for line in transfer_csv.splitlines()[1:]
        if line and line.split(',')[0]]
    m20.pick_up_tip()
    for d in mm_dests:
        m20.transfer(mm_vol, mm, d.bottom(2), new_tip='never')
    m20.drop_tip()

    for line in transfer_info:
        vol, plate, s_col, d_col = line[:4]
        vol = float(vol)
        source = source_plates[plate].columns_by_name()[s_col][0]
        dest = dest_plate.columns_by_name()[d_col][0]
        m20.pick_up_tip()
        m20.transfer(vol, source, dest, new_tip='never')
        if mix_after:
            m20.mix(10, vol, dest)
        m20.drop_tip()

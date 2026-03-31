# metadata
metadata = {
    'protocolName': 'Cherrypicking from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [input_file, p20_mount, p300_mount] = get_values(  # noqa: F821
        'input_file', 'p20_mount', 'p300_mount')
    # [input_file, p20_mount, p300_mount] = [
    #     'Lable,Pos,nM,FC,Rxn,Vol,h2O,Tube\nP_F3,A1,28.9,0.8,100,10,30,\
    #     T1\nP_B3,A2,28.32,0.8,100,10,,T1\nP_FIP,A3,53.8,1.6,100,20,,\
    #     T1\nP_BIP,A4,82,1.6,100,20,,T1\nP_LF,A5,32.5,0.4,100,5,,T1',
    #     'right', 'left']

    # load labware
    plate = ctx.load_labware(
        'usascientific_96_wellplate_2.4ml_deep', '1', 'deepwell plate')
    tuberack24 = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '4',
        '4x6 rack with 2ml Eppendorf tubes'
    )
    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot, '20ul tiprack')
        for slot in ['2', '3']
    ]
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '300ul tiprack')
        for slot in ['5', '6']
    ]

    # load pipettes
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_mount, tip_racks=tipracks20)
    p300 = ctx.load_instrument(
        'p300_single_gen2', p300_mount, tip_racks=tipracks300)

    # reagent setup
    h2o = tuberack24.columns()[4][-1]
    r1 = tuberack24.columns()[5]

    tube_list = [
        well for set in [
            col if i < 4 else col[:3]
            for i, col in enumerate(tuberack24.columns()[:5])]
        for well in set
    ]

    # parse
    labels, wells, nms, final_vols, h2o_vols, tubes = [
        [line.split(',')[ind].strip() for line in input_file.splitlines()[1:]]
        for ind in [0, 1, 2, 5, 6, 7]
    ]

    """ Phase 1 """
    r1_ind = 0
    r1_vol_count = 0
    for nm, well in zip(nms, wells):
        vol = float(nm)*5
        if r1_vol_count + vol > 2000:
            r1_ind += 1
            r1_vol_count = 0
        r1_vol_count += vol
        dest = plate.wells_by_name()[well]
        p300.pick_up_tip()
        p300.transfer(vol, r1[r1_ind], dest, air_gap=20, new_tip='never')
        mix_vol = vol if vol < 250 else 250
        p300.mix(3, mix_vol, dest)
        p300.blow_out(dest.top(-2))
        p300.drop_tip()

    """ Phase 2 """
    for h2o_vol, well in zip(h2o_vols, wells):
        if h2o_vol:
            vol = float(h2o_vol)
        pip = p20 if vol <= 20 else p300
        if not pip.hw_pipette['has_tip']:
            pip.pick_up_tip()
        pip.transfer(vol, h2o, dest.top(), new_tip='never')

    """ Phase 3 """
    existing_tubes = {}
    for final_vol, well, tube in zip(final_vols, wells, tubes):
        vol = float(final_vol)
        source = plate.wells_by_name()[well]
        dest = tube_list[int(tube.split('T')[-1])-1]
        p20.pick_up_tip()
        p20.transfer(vol, source, dest, new_tip='never')
        if tube in existing_tubes:
            existing_tubes[tube] += vol
            mix = True
        else:
            existing_tubes[tube] = vol
            mix = False
        if mix:
            if existing_tubes[tube] >= 20:
                mix_vol = 15
            else:
                mix_vol = vol
            p20.mix(3, mix_vol, dest)
        p20.blow_out(dest.top(-2))
        p20.drop_tip()

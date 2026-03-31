import math

# metadata
metadata = {
    'protocolName': 'NGS Prep from .csv',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [p20_single_mount, p300_single_mount, csv_file] = get_values(  # noqa: F821
        'p20_single_mount', 'p300_single_mount', 'csv_file'
    )

    plate_a, plate_b, plate_c = [
        ctx.load_labware('biorad_96_wellplate_200ul_pcr', slot, 'plate ' + pl)
        for slot, pl in zip(['1', '2', '3'], ['A', 'B', 'C'])
    ]
    te_buffer = ctx.load_labware(
        'opentrons_15_tuberack_falcon_15ml_conical',
        '4',
        '3x5 15ml tube rack for TE buffer').wells()[0]
    micro_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '5',
        '4x6 microtube rack for mix and pool tubes (loaded empty)'
    )
    racks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['6', '7', '8']
    ]
    racks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['9', '10', '11']
    ]

    # pipettes
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_single_mount, tip_racks=racks20)
    p300 = ctx.load_instrument(
        'p300_single_gen2', p300_single_mount, tip_racks=racks300)

    # reagents
    mix_tube, final_tube = micro_rack.rows()[0][:2]

    # parse .csv file
    all_vals = [
        [float(val) for val in line.split(',')]
        for line in csv_file.splitlines() if line
    ]
    num_cols = len(all_vals[0])
    dil_b, dil_c, a_to_b, b_to_c, c_to_pool = [
        [line[col] for col in range(num_cols) for line in all_vals[i*8:i*8+8]]
        for i in range(5)
    ]

    h = 80
    r = te_buffer.diameter/2

    def h_track(vol):
        nonlocal h
        dh = vol/(math.pi*(r**2))*1.05
        h = h - dh if h - dh > 10 else 10
        return h

    # transfer diluent into plates B and C
    for dil, plate in zip([dil_b, dil_c], [plate_b, plate_c]):
        for vol, well in zip(dil, plate.wells()):
            if vol > 0:
                pip = p20 if vol <= 20 else p300
                if pip.hw_pipette['has_tip'] is False:
                    pip.pick_up_tip()
                pip.transfer(
                    vol, te_buffer.bottom(h_track(vol)), well, new_tip='never')
                pip.blow_out(well.top(-2))

    # transfer libraries from plate A to plate B and mix:
    for vol, source, dest, check in zip(
            a_to_b, plate_a.wells(), plate_b.wells(), dil_b):
        if vol > 0:
            pip = p20 if vol <= 20 else p300
            if pip.hw_pipette['has_tip'] is False:
                pip.pick_up_tip()
            pip.transfer(vol, source, dest, new_tip='never')
            if check > 0:
                pip.mix(5, vol*.8, dest)
            pip.blow_out(well.top(-2))
            pip.drop_tip()

    if p20.hw_pipette['has_tip'] is True:
        p20.drop_tip()
    if p300.hw_pipette['has_tip'] is True:
        p300.drop_tip()

    # transfer libraries from plate B to plate C and mix:
    for vol, source, dest, check in zip(
            b_to_c, plate_b.wells(), plate_c.wells(), dil_c):
        if vol > 0:
            pip = p20 if vol <= 20 else p300
            pip.pick_up_tip()
            pip.transfer(vol, source, dest, new_tip='never')
            if check > 0:
                pip.mix(5, vol*.8, dest)
            pip.blow_out(well.top(-2))
            pip.drop_tip()

    # pool final-diluted libraries
    for vol, source in zip(c_to_pool, plate_c.wells()):
        if vol > 0:
            pip = p20 if vol <= 20 else p300
            pip.pick_up_tip()
            pip.transfer(vol, source, mix_tube.bottom(5), new_tip='never')
            pip.blow_out(mix_tube.top(-2))
            pip.drop_tip()

    # mix tube and transfer
    total_vol = sum(c_to_pool)
    mix_vol = total_vol*.8 if total_vol*.8 < 270 else 270
    p300.pick_up_tip()
    p300.mix(3, mix_vol, mix_tube)
    p300.transfer(
        25, mix_tube.bottom(5), final_tube.bottom(5), new_tip='never')
    p300.blow_out(final_tube.top(-5))
    p300.drop_tip()

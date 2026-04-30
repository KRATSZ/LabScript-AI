import math

metadata = {
    'protocolName': 'Cell-Free Gene Expression (TXTL) Test',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
    }


def run(protocol):
    [mm_csv, noRep, noCe, noBlank, p20mnt, p300mnt] = get_values(  # noqa: F821
        'mm_csv', 'noRep', 'noCe', 'noBlank', 'p20mnt', 'p300mnt')

    # Sanity checks - raise exceptions, if needed
    if noRep < 1 or noRep > 3:
        raise Exception('Number of replicates should be between 1-3.')
    if noCe < 1 or noCe > 24:
        raise Exception('Number of cell extracts should be between 1-24.')
    if noBlank < 1 or noBlank > 2:
        raise Exception('Number of blanks should be 1 or 2.')
    # Definte Labware and Pipettes
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '9')]
    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', '6')]

    p20 = protocol.load_instrument('p20_single_gen2', p20mnt, tip_racks=tips20)
    p300 = protocol.load_instrument(
        'p300_single_gen2', p300mnt, tip_racks=tips300)

    plate = protocol.load_labware('brand_384_wellplate_100ul', '1')
    tr_plasmids = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '5', 'Tube Rack with Plasmids')
    tr_eb = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '2', 'Tube Rack for Extracts+Buffer')

    buffer_tubes = protocol.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        '3', 'Al Block + PCR Tubes')

    thermocycler = protocol.load_module('thermocycler')
    tc_plate = thermocycler.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')

    thermocycler.set_block_temperature(4)

    p20.flow_rate.aspirate = 10
    p20.flow_rate.dispense = 20
    p20.flow_rate.blow_out = 100
    p300.flow_rate.aspirate = 100
    p300.flow_rate.dispense = 200
    p300.flow_rate.blow_out = 300

    tipcounts = [0, 0]

    def pick_up(pip):

        if pip == p20:
            p = p20
            count = tipcounts[0]
        else:
            p = p300
            count = tipcounts[1]

        if count == 96:
            p.home()
            """for i in range(6):
                protocol.set_rails_lights(not protocol.rail_lights_on)
                protocol.delay(seconds=1)"""
            protocol.pause("Please replace tips.")
            p.reset_tipracks()
            count = 0

        p.pick_up_tip()
        if p == p20:
            tipcounts[0] = count + 1
        else:
            tipcounts[1] = count + 1

    # Step 1: Mastermix preparation (plasmid mix)

    protocol.comment('Beginning Step 1: Mastermix preparation (plasmid mix)')

    csv_data = [r.split(',') for r in mm_csv.strip().splitlines() if r][1:]

    transfer_vols = []

    for data in csv_data:
        cStock = float(data[2])*0.001/float(data[1])
        vSample = float(data[3])*(10**-9)*15/cStock
        vTotal = round((noRep*noCe+1)*vSample, 1)
        vWater = round((noRep*noCe+1)*(3.75-vSample), 1)
        transfer_vols.append([vTotal, vWater])

    source_tubes = tr_plasmids.wells()[:len(csv_data)]
    dest_tubes = tr_plasmids.wells()[8:8+len(csv_data)]
    water = tr_plasmids['A5']

    for src, dest, vols in zip(source_tubes, dest_tubes, transfer_vols):
        p_vol, w_vol = vols
        protocol.comment(
            'Adding %fuL of Plasmid and %fuL of water' % (p_vol, w_vol))
        pip = p20 if p_vol <= 20 else p300
        pick_up(pip)
        pip.transfer(p_vol, src, dest, new_tip='never')
        pip.blow_out()
        pip.drop_tip()
        pick_up(p300)
        p300.transfer(w_vol, water, dest, new_tip='never')
        p300.mix(10, round(w_vol), dest)
        p300.blow_out()
        p300.drop_tip()

    # Step 2: Distriubte Mastermixes to corresponding wells
    protocol.comment('Beginning Step 2: Distributing mastermixes to wells')

    dest_wells = []

    for i in range(len(csv_data)):
        start_no = i*noRep
        rows = plate.rows()[start_no:start_no+noRep]
        wells = [well for row in rows for well in row[:noCe]]
        dest_wells.append(wells)

    for src, d_wells in zip(dest_tubes, dest_wells):
        pick_up(p20)
        p20_vol = 0
        for well in d_wells:
            if p20_vol < 3:
                p20.dispense(p20_vol, src)
                p20.aspirate(18, src)
                p20_vol = 18
            p20.dispense(3.8, well)
            p20_vol -= 3.8
        p20.dispense(p20_vol, src)
        p20.drop_tip()

    water_rows = plate.rows()[len(csv_data)*noRep:len(csv_data)*noRep+noBlank]
    water_wells = [well for row in water_rows for well in row[:noCe]]

    pick_up(p20)
    p20_vol = 0
    for well in water_wells:
        if p20_vol < 3:
            p20.dispense(p20_vol, water)
            p20.aspirate(18, water)
            p20_vol = 18
        p20.dispense(3.8, well)
        p20_vol -= 3.8
    p20.dispense(p20_vol, water)
    p20.drop_tip()

    # Step 3: Mix cell extract (E) and buffer (B)
    protocol.comment('Beginning Step 3: Mix cell extract and buffer')

    e_b_tubes = [well for row in tr_eb.rows() for well in row][:noCe]

    num_buff = math.ceil((len(csv_data)*noRep+noBlank+0.5)*noCe*6.25/40)

    buff_cols = [buffer_tubes.columns()[i-1] for i in [1, 2, 5, 6, 9, 10, 12]]
    buffer_wells = [well for col in buff_cols for well in col][:num_buff]
    buffer_src = tr_plasmids['D5']
    protocol.comment("Adding buffer to tube")

    pick_up(p300)
    p300_vol = 0
    for well in buffer_wells:
        p300.aspirate(40, well)
        p300_vol += 40
        if p300_vol == 280:
            p300.dispense(280, buffer_src)
            p300_vol = 0
    p300.dispense(p300_vol, buffer_src)
    p300.mix(10, 250, buffer_src)

    buffer_vol = (len(csv_data)*noRep+noBlank+0.5)*6.25

    for tube in e_b_tubes:
        p300.transfer(buffer_vol, buffer_src, tube, new_tip='never')

    p300.drop_tip()

    e_src_cols = [tc_plate.columns()[i-1] for i in [1, 5, 9]]
    e_src_cols2 = [tc_plate.columns()[i-1] for i in [2, 6, 10]]
    e_src_wells = [well for col in e_src_cols for well in col][:noCe]
    e_src_wells2 = [well for col in e_src_cols2 for well in col][:noCe]

    need2 = (len(csv_data)*noRep+noBlank+0.5)*5/50
    e_vol = round((len(csv_data)*noRep+noBlank+0.5)*5)
    protocol.comment("Adding cell extracts to tubes")

    for src1, src2, dest in zip(e_src_wells, e_src_wells2, e_b_tubes):
        pick_up(p300)
        mix_vol = 40
        if need2 > 1:
            p300.transfer(50, src2, src1, new_tip='never')
            mix_vol = 80
        p300.mix(10, mix_vol, src1)
        p300.transfer(e_vol, src1, dest.top(-2), new_tip='never')
        p300.mix(15, buffer_vol, dest)
        p300.blow_out()
        p300.drop_tip()

    # Step 4: distribute E+B to corresponding wells
    protocol.comment("Step 4: Distributing E+B to corresponding wells")

    dest_cols = plate.columns()[:noCe]
    col_length = len(csv_data)*noRep+noBlank

    for src, col in zip(e_b_tubes, dest_cols):
        for dest in col[:col_length]:
            pick_up(p20)
            p20.transfer(11.3, src, dest, new_tip='never')
            p20.mix(6, 14, dest)
            p20.blow_out()
            p20.drop_tip()

    protocol.comment('Protocol complete!')

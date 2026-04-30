import math

metadata = {
    'protocolName': 'VHH Purification Protocol',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    # modules
    hs = ctx.load_module('heaterShakerModuleV1', '1')
    tempdeck = ctx.load_module('temperature module gen2', '7')
    magdeck = ctx.load_module('magnetic module gen2', '10')
    magdeck.disengage()

    # labware
    hs_plate = hs.load_labware(
        'opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep')
    temp_block = tempdeck.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap')
    mag_plate = magdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul')
    res = ctx.load_labware('nest_12_reservoir_15ml', '3')
    tipracks200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['5', '6']]

    # pipettes
    p300 = ctx.load_instrument('p300_single_gen2', 'left',
                               tip_racks=tipracks200)

    # initial positions
    vhh_lib_cultures = hs_plate.wells()[0]
    buffer_w = res.rows()[0][0]
    terrific_broth = res.rows()[0][2]
    magstrep_beads = temp_block.rows()[0][5:3:-1]
    bsa_biotin = temp_block.wells_by_name()['B6']
    samv_g1 = temp_block.wells_by_name()['C6']
    mag_height = 8.0

    tempdeck.set_temperature(10)
    hs.close_labware_latch()

    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 300

    def slow_withdraw(pip, well, delay_seconds=2):
        ctx.delay(seconds=delay_seconds)
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def separate(minutes=2.0):
        magdeck.engage(height=mag_height)
        ctx.delay(minutes=minutes)

    def remove_supernatant(vol, sources, dest, z_dest=1.5):
        p300.flow_rate.aspirate = 10
        p300.flow_rate.dispense = 50
        p300.pick_up_tip()
        for s in sources:
            p300.aspirate(vol, s.bottom(1.4))
            p300.dispense(vol, dest.bottom(z_dest))
            p300.blow_out(dest.bottom(z_dest))
            slow_withdraw(p300, dest)
        p300.drop_tip()

    bead_dests = [
        well
        for col in mag_plate.columns()[:4]
        for well in col[:3]]
    p300.pick_up_tip()
    last_source = None
    for i, d in enumerate(bead_dests):
        source = magstrep_beads[i//math.ceil(len(bead_dests)/2)]
        if source != last_source:
            p300.mix(10, 100, source)
            last_source = source
        p300.aspirate(100, source)
        p300.dispense(100, d)
        slow_withdraw(p300, d)
    p300.drop_tip()

    separate()

    supernatant_dest = temp_block.wells_by_name()['A4']
    remove_supernatant(100, bead_dests, supernatant_dest)

    magdeck.disengage()

    for _ in range(2):
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50

        p300.pick_up_tip()
        p300.distribute(90, vhh_lib_cultures,
                        [d.bottom(13) for d in bead_dests], disposal_vol=20,
                        new_tip='never')
        p300.flow_rate.dispense = 300
        for d in bead_dests:
            p300.mix(10, 50, d.bottom(1.5))
            p300.blow_out(d.bottom(1.5))
            slow_withdraw(p300, d)
        p300.drop_tip()

        separate()

        supernatant_dest = res.rows()[0][-1]
        remove_supernatant(90, bead_dests, supernatant_dest, z_dest=23)

        magdeck.disengage()

    bsa_biotin_dests = [
        well for col in mag_plate.columns()[:3:2]
        for well in col[:3]]
    g1_dests = [
        well for col in mag_plate.columns()[1:4:2]
        for well in col[:3]]

    for source, dests in zip([bsa_biotin, samv_g1],
                             [bsa_biotin_dests, g1_dests]):
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50

        p300.pick_up_tip()
        for i, d in enumerate(dests):
            if i == 0:
                p300.mix(10, 100, source.bottom(1))
            p300.aspirate(70, source.bottom(1))
            p300.dispense(70, d.bottom(13))
            p300.blow_out(d.bottom(13))
            slow_withdraw(p300, d)

        p300.flow_rate.aspirate = 300
        for d in dests:
            p300.mix(10, 50, d.bottom(1.5))
            p300.blow_out(d.bottom(1.5))
            slow_withdraw(p300, d)
        p300.drop_tip()

    for _ in range(2):
        ctx.delay(minutes=10,
                  msg='Allow binding of biotin-BSA to MagStrep beads.')

        for dests in [bsa_biotin_dests, g1_dests]:
            p300.pick_up_tip()
            p300.flow_rate.aspirate = 300
            for d in dests:
                p300.mix(10, 50, d.bottom(1.5))
                p300.blow_out(d.bottom(1.5))
                slow_withdraw(p300, d)
            p300.drop_tip()

    ctx.delay(minutes=10,
              msg='Allow binding of biotin-BSA to MagStrep beads.')

    separate()

    remove_supernatant(60, bsa_biotin_dests, temp_block.wells_by_name()['B4'])
    remove_supernatant(60, g1_dests, temp_block.wells_by_name()['C4'])

    magdeck.disengage()

    def wash(vol=100):
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50

        p300.pick_up_tip()
        for d in bead_dests:
            p300.aspirate(vol, buffer_w.bottom(1))
            slow_withdraw(p300, buffer_w)
            p300.dispense(vol, d.bottom(13))
            p300.blow_out(d.bottom(13))

        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 300

        for dests in [bsa_biotin_dests, g1_dests]:
            if not p300.has_tip:
                p300.pick_up_tip()
            for d in dests:
                p300.mix(10, 50, d.bottom(1.5))
                p300.blow_out(d.bottom(1.5))
                slow_withdraw(p300, d)
            p300.drop_tip()

        separate()

        remove_supernatant(100, bsa_biotin_dests, res.rows()[0][-1], z_dest=23)
        remove_supernatant(100, g1_dests, res.rows()[0][-1], z_dest=23)

    for _ in range(2):
        wash()

    magdeck.disengage()

    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 50

    p300.pick_up_tip()
    for d in bead_dests:
        p300.aspirate(100, buffer_w.bottom(1))
        slow_withdraw(p300, buffer_w)
        p300.dispense(100, d.bottom(13))
        p300.blow_out(d.bottom(13))
    p300.drop_tip()

    for vhh_set in range(2):
        bead_columns = [
            col[:3] for col in mag_plate.columns()[vhh_set*2:(vhh_set+1)*2]]

        bead_col = bead_columns[0]
        separate()
        remove_supernatant(100, bead_col, res.rows()[0][10], z_dest=23)
        magdeck.disengage()

        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 300
        for d in bead_col:
            p300.pick_up_tip()
            p300.mix(10, 100, vhh_lib_cultures.bottom(1))
            p300.aspirate(100, vhh_lib_cultures.bottom(1))
            slow_withdraw(p300, vhh_lib_cultures)
            p300.dispense(100, d.bottom(1.5))
            p300.mix(10, 100, d.bottom(1.5))
            p300.blow_out(d.bottom(1.5))
            slow_withdraw(p300, d)
            p300.drop_tip()

        for _ in range(2):
            ctx.delay(minutes=10,
                      msg='Binding of VHH to BSA Magbeads for \
    negative selection round 1.')
            for d in bead_col:
                p300.pick_up_tip()
                p300.mix(10, 100, d.bottom(1.5))
                p300.blow_out(d.bottom(1.5))
                slow_withdraw(p300, d)
                p300.drop_tip()

        ctx.delay(minutes=10, msg='Binding of VHH to BSA Magbeads for \
    negative selection round 1.')

        separate()
        remove_supernatant(100, bead_columns[1], res.rows()[0][10], z_dest=23)

        for s, d in zip(bead_col, bead_columns[1]):
            p300.pick_up_tip()
            p300.aspirate(100, s.bottom(1.4))
            slow_withdraw(p300, s)
            p300.dispense(100, d.bottom(1.5))
            p300.blow_out(d.bottom(1.5))
            slow_withdraw(p300, d)
            p300.drop_tip()

        magdeck.disengage()
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 300
        for d in bead_columns[1]:
            p300.pick_up_tip()
            p300.mix(10, 100, d.bottom(1.5))
            p300.blow_out(d.bottom(1.5))
            slow_withdraw(p300, d)
            p300.drop_tip()

        for _ in range(2):
            ctx.delay(minutes=10)
            for d in bead_columns[1]:
                p300.pick_up_tip()
                p300.mix(10, 100, d.bottom(1.5))
                p300.blow_out(d.bottom(1.5))
                slow_withdraw(p300, d)
                p300.drop_tip()

        ctx.delay(minutes=10)

        separate()

        p300.flow_rate.aspirate = 10
        p300.flow_rate.dispense = 50
        for d in bead_columns[1]:
            p300.pick_up_tip()
            p300.aspirate(100, d.bottom(1.4))
            slow_withdraw(p300, d)
            p300.dispense(100, temp_block.wells()[0].bottom(1.5))
            p300.blow_out(temp_block.wells()[0].bottom(1.5))
            slow_withdraw(p300, temp_block.wells()[0])
            p300.drop_tip()

        magdeck.disengage()

        for dest in temp_block.rows()[0][1:3]:
            p300.flow_rate.aspirate = 50
            p300.flow_rate.dispense = 300

            for d in bead_columns[1]:
                p300.pick_up_tip()
                p300.aspirate(100, buffer_w.bottom(1))
                slow_withdraw(p300, buffer_w)
                p300.dispense(100, d.bottom(1.5))
                p300.mix(10, 100, d.bottom(1.5))
                p300.blow_out(d.bottom(1.5))
                p300.drop_tip()

            separate()

            remove_supernatant(100, bead_col, dest, z_dest=1.5)

        magdeck.disengage()

        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50
        p300.pick_up_tip()
        for d in bead_columns[1]:
            p300.aspirate(100, buffer_w.bottom(1))
            slow_withdraw(p300, buffer_w)
            p300.dispense(100, d.bottom(13))
            p300.blow_out(d.bottom(13))
        p300.drop_tip()

        tb_dests = hs_plate.rows()[0][1:4]
        p300.pick_up_tip()
        num_trans = math.ceil(500/p300.tip_racks[0].wells()[0].max_volume)
        vol_per_trans = round(500/num_trans)
        for d in tb_dests:
            for _ in range(num_trans):
                p300.aspirate(vol_per_trans, terrific_broth.bottom(1))
                slow_withdraw(p300, terrific_broth)
                p300.dispense(vol_per_trans, d.bottom(1))
                p300.blow_out(d.bottom(1))
                slow_withdraw(p300, d)
        p300.drop_tip()

        hs.set_and_wait_for_temperature(37)
        ctx.delay(minutes=10, msg='Pause to allow TB to heat up.')

        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 300
        for s, d in zip(bead_columns[1], tb_dests):
            p300.pick_up_tip()
            p300.mix(10, 100, s.bottom(1))
            p300.aspirate(100, s.bottom(1))
            p300.dispense(100, d.bottom(1.5))
            p300.blow_out(d.bottom(1.5))
            slow_withdraw(p300, d)
            p300.drop_tip()

        p300.home()
        hs.set_and_wait_for_shake_speed(694)
        ctx.delay(minutes=120)
        if vhh_set == 0:
            hs.deactivate_shaker()

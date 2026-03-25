from opentrons import types
import math

metadata = {
    'protocolName': 'MagMAX Plant DNA Isolation Kit [2/2]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [num_samples, deep_plate, bead_add, bead_loc,
     park_tips] = get_values(  # noqa: F821
     'num_samples', 'deep_plate', 'bead_add', 'bead_loc', 'park_tips')

    # load labware and m300ette
    magdeck = protocol.load_module('magnetic module gen2', '7')
    magplate = magdeck.load_labware(deep_plate)
    magheight = {
        'omni_96_wellplate_2000ul': 8.5,
        'nest_96_wellplate_2ml_deep': 8.5,
        'usascientific_96_wellplate_2.4ml_deep': 8.5
        }

    l_waste = protocol.load_labware(
        'nest_1_reservoir_195ml', '11').wells()[0].top()
    rsvr = [protocol.load_labware('nest_12_reservoir_15ml', s) for s in [4, 5]]

    pcrplate = protocol.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '1')

    if park_tips:
        tip_racks = [
            protocol.load_labware(
                'opentrons_96_tiprack_300ul',
                x, 'Opentrons 200uL Filter Tips') for x in [
                '3',
                '6']]
        parked_tips = protocol.load_labware(
            'opentrons_96_tiprack_300ul', '2',
            'Parked Tips (200uL Filter)').rows()[0]
    else:
        tip_racks = [
            protocol.load_labware(
                'opentrons_96_tiprack_300ul',
                x, 'Opentrons 200uL Filter Tips') for x in [
                '8',
                '9',
                '6',
                '3',
                '2']]

    m300 = protocol.load_instrument('p300_multi_gen2', 'right')

    m300.flow_rate.aspirate = 100
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

    # create variables
    num_cols = math.ceil(num_samples/8)
    all_tips = [tr['A'+str(i)] for tr in tip_racks for i in range(1, 13)]

    if num_cols > 6 and not park_tips:
        [t1, t2, t3, t4, t5] = [t.rows()[0][:num_cols] for t in tip_racks]
        [t6, t7, t8, t9, t10] = [t1, t2, t3, t4, t5]
        tt_tips = False
    elif not park_tips:
        [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10] = [
            all_tips[i*num_cols:(i+1)*num_cols] for i in range(10)]
        tt_tips = False
    else:
        [t1, t2, t3, t4, t5] = tip_racks.rows()[0][:5]
        elute_tips = tip_racks.rows()[0][5:]
        ret_tips = tip_racks.rows()[0][1:]
        done_tips = tip_racks.rows()[0]

    magsamps = magplate.rows()[0][:num_cols]
    pcrsamps = pcrplate.rows()[0][:num_cols]

    etoh = [w for w in rsvr[0].wells()[1:4] for _ in range(4)][:num_cols]
    wb1 = [w for w in rsvr[0].wells()[9:] for _ in range(4)][:num_cols]
    wb2_1 = [w for w in rsvr[1].wells()[:3] for _ in range(4)][:num_cols]
    wb2_2 = [w for w in rsvr[1].wells()[3:6] for _ in range(4)][:num_cols]
    eb = [w for w in rsvr[1].wells()[10:] for _ in range(6)][:num_cols]

    def well_mix(reps, loc, v, side):
        loc1 = loc.bottom().move(types.Point(x=side, y=0, z=4))
        loc2 = loc.bottom().move(types.Point(x=side*-1, y=0, z=2))
        m300.aspirate(20, loc1)
        mvol = v-20
        for _ in range(reps-1):
            m300.aspirate(mvol, loc1)
            m300.dispense(mvol, loc2)
        m300.dispense(20, loc2)

    def remove_supernatant(vol, src, dest, side):
        m300.flow_rate.aspirate = 20
        m300.aspirate(10, src.top())
        while vol > 200:
            m300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=2.5)))
            m300.dispense(210, dest)
            m300.aspirate(10, dest)
            vol -= 200
        m300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=2.5)))
        m300.dispense(vol, dest)
        m300.dispense(10, dest)
        m300.flow_rate.aspirate = 100

    sides = [-1, 1]*6

    def wash_step(msg, src, vol, mix, t1,
                  t2, t0, tm, rpm, temp, t1_tips=False, t2_tips=False, v2=0):
        """ This is a versatile function that does a lot of the repetive tasks
            msg = message (string)
            src = source wells for reagent
            vol = volume of reagent added (and supernatant removed)*
            mix = the number of times to mix
            t1 = tips to add reagent
            t2 = tips to remove supernatant (tips will be replaced in t1)
            t0 = location to replace t1
            tm = time to mix on thermomixer
            rpm = rpm on thermomixer
            temp = temp of thermomixer
            t_tips = if True, will trash tips after adding reagent (tips1)
            v2 = the volume for supernatant removal (if different than vol)
            """
        protocol.comment(f'Adding {vol}uL of {msg} to samples...')
        for well, tip, tret, side, s in zip(magsamps, t1, t0, sides, src):
            if not m300.has_tip:
                m300.pick_up_tip(tip)
            add_vol = vol
            e_vol = 0
            while add_vol > 200:
                m300.aspirate(200, s)
                m300.dispense(200, well.top(-3))
                m300.aspirate(10, well.top(-3))
                add_vol -= 200
                e_vol += 10
            m300.aspirate(add_vol, s)
            total_vol = add_vol + e_vol
            m300.dispense(total_vol, well)
            if not park_tips:
                well_mix(mix, well, 180, side)

                m300.blow_out()

                if t1_tips:
                    m300.drop_tip()
                else:
                    m300.drop_tip(tret)
        if park_tips:
            if m300.has_tip:
                m300.drop_tip()

            for well, tip, side in zip(magsamps, parked_tips, sides):
                m300.pick_up_tip(tip)
                well_mix(mix, well, 180, side)
                m300.blow_out()
                m300.drop_tip(tip)

        for _ in range(6):
            protocol.set_rail_lights(not protocol.rail_lights_on)
            protocol.delay(seconds=1)
        protocol.pause(f'Please seal plate and place on thermomixer for {tm} \
        minutes at {rpm}rpm at {temp}. When done mixing, place plate back on \
        OT-2 and click RESUME')
        magdeck.engage(height=magheight[deep_plate])
        protocol.comment('Engaging Magdeck for 5 minutes.')
        protocol.delay(minutes=5)

        protocol.comment('Removing supernatant...')
        supernatant_volume = vol if v2 == 0 else v2
        if not park_tips:
            for well, tip, tret, side in zip(magsamps, t2, t1, sides):
                m300.pick_up_tip(tip)
                remove_supernatant(supernatant_volume, well, l_waste, side)
                m300.aspirate(10, l_waste)
                if t2_tips:
                    m300.drop_tip()
                else:
                    m300.drop_tip(tret)
        else:
            for well, tip, side in zip(magsamps, parked_tips, sides):
                m300.pick_up_tip(tip)
                remove_supernatant(supernatant_volume, well, l_waste, side)
                m300.aspirate(10, l_waste)
                m300.drop_tip(tip)

        magdeck.disengage()

    # start protocol; non-parked tips
    if not park_tips:
        if bead_add:
            if bead_loc != 'NEST_reservoir':
                bead_labware = protocol.load_labware(bead_loc, '10')
            else:
                bead_labware = rsvr[0]
            beads = bead_labware['A1']
            # add 25uL of beads, if automating
            protocol.comment('Adding 25uL of beads')
            m300.pick_up_tip(t1[0])
            for well in magsamps:
                m300.mix(3, 50, beads)
                m300.aspirate(25, beads)
                m300.dispense(25, well.top(-2))
                m300.blow_out()

        wash_step('Ethanol', etoh, 400, 5, t1, t2, t1,
                  5, 500, 'room temp', True, tt_tips, 825)
        wash_step('Wash Buffer 1', wb1, 400, 5, t3, t4, t2,
                  1, 1500, '70C', tt_tips, tt_tips)
        if num_cols > 6:
            protocol.pause('Please replace used tips with clean tips in \
            slots 8, 9, 6, and 3. When ready, click RESUME')
        wash_step('Wash Buffer 2', wb2_1, 400, 5, t5, t6, t1,
                  1, 1500, '70C', True, tt_tips)
        wash_step('Wash Buffer 2', wb2_2, 400, 5, t7, t8, t1,
                  1, 1500, '70C', True, tt_tips)

        for tip, tret, well, buff in zip(t9, t8, magsamps, eb):
            m300.pick_up_tip(tip)
            m300.aspirate(175, buff)
            m300.dispense(175, well)
            m300.mix(3, 160, well)
            m300.blow_out()
            if num_cols > 6:
                m300.drop_tip(tret)
            else:
                m300.drop_tip()

        protocol.pause('Please place plate on thermomixer for allocated time. \
        When ready to resume, replace plate on OT-2 and click RESUME')
        if num_cols > 6:
            protocol.comment('Please replace empty tips with clean tips in \
            slot 2 as well.')

        magdeck.engage(height=magheight[deep_plate])
        protocol.comment('Engaging Magdeck for 5 minutes.')
        protocol.delay(minutes=5)

        m300.flow_rate.aspirate = 30

        for tip, tret, src, dest in zip(t10, t9, magsamps, pcrsamps):
            m300.pick_up_tip(tip)
            m300.aspirate(175, src)
            m300.dispense(175, dest)
            m300.blow_out()
            if num_cols > 6:
                m300.drop_tip(tret)
            else:
                m300.drop_tip()

        magdeck.disengage()
        protocol.comment('Protocol complete!')
    else:
        # start protocol; parked tips
        if bead_add:
            if bead_loc != 'NEST_reservoir':
                bead_labware = protocol.load_labware(bead_loc, '10')
            else:
                bead_labware = rsvr[0]
            beads = bead_labware['A1']
            # add 25uL of beads, if automating
            protocol.comment('Adding 25uL of beads')
            m300.pick_up_tip(t1)
            for well in magsamps:
                m300.mix(3, 50, beads)
                m300.aspirate(25, beads)
                m300.dispense(25, well.top(-2))
                m300.blow_out()
        m300.drop_tip()
        m300.pick_up_tip(t2)
        wash_step('Ethanol', etoh, 400, 5, t1, t2, t1,
                  5, 500, 'room temp', True, tt_tips, 825)

        m300.pick_up_tip(t3)
        wash_step('Wash Buffer 1', wb1, 400, 5, t3, t4, t2,
                  1, 1500, '70C', tt_tips, tt_tips)

        m300.pick_up_tip(t4)
        wash_step('Wash Buffer 2', wb2_1, 400, 5, t5, t6, t1,
                  1, 1500, '70C', True, tt_tips)

        m300.pick_up_tip(t5)
        wash_step('Wash Buffer 2', wb2_2, 400, 5, t7, t8, t1,
                  1, 1500, '70C', True, tt_tips)

        for tip, tret, well, buff in zip(elute_tips, ret_tips, magsamps, eb):
            m300.pick_up_tip(tip)
            m300.aspirate(175, buff)
            m300.dispense(175, well)
            m300.mix(3, 160, well)
            m300.blow_out()
            m300.drop_tip(tret)

        protocol.pause('Please place plate on thermomixer for allocated time. \
        When ready to resume, replace plate on OT-2 and click RESUME')

        magdeck.engage(height=magheight[deep_plate])
        protocol.comment('Engaging Magdeck for 5 minutes.')
        protocol.delay(minutes=5)

        m300.flow_rate.aspirate = 30

        for tip, tr, src, dest in zip(ret_tips, done_tips, magsamps, pcrsamps):
            m300.pick_up_tip(tip)
            m300.aspirate(175, src)
            m300.dispense(175, dest)
            m300.blow_out()
            m300.drop_tip(tr)

        magdeck.disengage()
        protocol.comment('Protocol complete!')

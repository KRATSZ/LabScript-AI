from opentrons.types import Point
import json
import os
import math

metadata = {
    'protocolName': 'Omega Biotek Mag-Bind Viral RNA XPress Kit',
    'author': 'Nick <ndiehl@opentrons.com',
    'apiLevel': '2.11'
}


# Start protocol
def run(ctx):

    [NUM_SAMPLES, ELUTION_VOL,
        PARK, m300_mount] = get_values(  # noqa: F821
        "NUM_SAMPLES", "ELUTION_VOL", "PARK", "m300_mount")

    TIP_TRACK = False
    STARTING_VOL = 440

    # load labware and pipettes
    num_cols = math.ceil(NUM_SAMPLES/8)
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                                '200µl filtertiprack')
               for slot in ['3', '6', '8', '9', '10']]
    if PARK:
        parkingrack = ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '7',
            '200µl filtertiprack for parking')
        parking_spots = parkingrack.rows()[0][:num_cols]
    else:
        tips300.insert(0, ctx.load_labware(
                                    'opentrons_96_filtertiprack_200ul', '7',
                                    '200µl filtertiprack'))
        parking_spots = [None for none in range(12)]

    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)

    magdeck = ctx.load_module('magnetic module gen2', '4')
    magdeck.disengage()
    magheight = 6
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    tempdeck = ctx.load_module('Temperature Module Gen2', '1')
    flatplate = tempdeck.load_labware(
                'opentrons_96_aluminumblock_nest_wellplate_100ul',)
    waste = ctx.load_labware('nest_1_reservoir_195ml', '11',
                             'Liquid Waste').wells()[0].top()
    etoh = ctx.load_labware(
        'nest_1_reservoir_195ml', '2', 'EtOH reservoir').wells()[0:]
    res1 = ctx.load_labware(
        'nest_12_reservoir_15ml', '5', 'reagent reservoir 1')
    binding_buffer = res1.wells()[:3]
    wash1 = res1.wells()[3:6]
    elution_solution = res1.wells()[-1]
    lysis_buffer = res1.wells()[7:10]

    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = flatplate.rows()[0][:num_cols]

    magdeck.disengage()  # just in case
    tempdeck.set_temperature(4)

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

    folder_path = '/data/B'
    tip_file_path = folder_path + '/tip_log.json'
    tip_log = {'count': {}}
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips300' in data:
                    tip_log['count'][m300] = data['tips300']
                else:
                    tip_log['count'][m300] = 0
        else:
            tip_log['count'][m300] = 0
    else:
        tip_log['count'] = {m300: 0}

    tip_log['tips'] = {
        m300: [tip for rack in tips300 for tip in rack.rows()[0]]}
    tip_log['max'] = {m300: len(tip_log['tips'][m300])}

    def pick_up(pip, loc=None):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
            tip_log['count'][pip] += 1

    switch = True
    drop_count = 0
    drop_threshold = 240

    def drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        drop_count += 8
        if drop_count == drop_threshold:
            m300.home()
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()
            drop_count = 0

    waste_vol = 0
    waste_threshold = 185000

    def remove_supernatant(vol, park=False):
        def waste_track(vol):
            nonlocal waste_vol
            if waste_vol + vol >= waste_threshold:
                m300.home()
                ctx.pause('Please empty waste (slot 11) before resuming.')
                ctx.home()
                waste_vol = 0
            waste_vol += vol

        m300.flow_rate.aspirate = 30
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                pick_up(m300, spot)
            else:
                pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            for _ in range(num_trans):
                waste_track(vol_per_trans)
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, m.top())  # void air gap
                m300.move_to(m.center())
                m300.transfer(vol_per_trans, loc, waste, new_tip='never',
                              air_gap=20)
                m300.blow_out(waste)
                m300.air_gap(20)
            drop(m300)
        m300.flow_rate.aspirate = 150

    def bind(vol, park=True):
        # add bead binding buffer and mix samples
        for i, (well, spot, source) in enumerate(zip(mag_samples_m,
                                                     parking_spots,
                                                     binding_buffer*12)):
            if park:
                pick_up(m300, spot)
            else:
                pick_up(m300)
            for _ in range(10):
                m300.aspirate(200, source.bottom(1), rate=1.5)
                m300.dispense(200, source.bottom(5), rate=2)
            num_trans = math.ceil(vol/210)
            vol_per_trans = vol/num_trans
            for t in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, source.top())
                m300.transfer(vol_per_trans, source, well.top(), air_gap=20,
                              new_tip='never')
                if t == 0:
                    m300.air_gap(20)
            m300.mix(10, 200, well)
            m300.blow_out(well.top(-2))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                drop(m300)
        ctx.comment('\n\n\n')

        magdeck.engage(height=magheight)
        ctx.delay(minutes=2, msg='Incubating on MagDeck for 2 minutes.')

        # remove initial supernatant
        remove_supernatant(vol+STARTING_VOL, park=park)

    def wash(wash_vol, source, mix_reps=15, park=True):
        magdeck.disengage()

        num_trans = math.ceil(wash_vol/200)
        vol_per_trans = wash_vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            src = source[i//(12//len(source))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.transfer(vol_per_trans, src, m.top(), air_gap=20,
                              new_tip='never')
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(20)
            m300.mix(mix_reps, 150, loc)
            m300.blow_out(m.top())
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                drop(m300)

        magdeck.engage(height=magheight)
        ctx.delay(minutes=5, msg='Incubating on MagDeck for 5 minutes.')

        remove_supernatant(wash_vol, park=park)

    def elute(vol, park=True):
        # resuspend beads in elution
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.aspirate(vol, elution_solution)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            m300.mix(10, 0.8*vol, loc)
            m300.blow_out(m.bottom(5))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                drop(m300)

        ctx.delay(minutes=2, msg='Incubating off magnet at room temperature \
for 2 minutes')
        magdeck.engage(height=magheight)
        ctx.delay(minutes=2, msg='Incubating on magnet at room temperature \
for 2 minutes')

        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, parking_spots)):
            if park:
                pick_up(m300, spot)
            else:
                pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.transfer(40, loc, e.bottom(5), air_gap=20, new_tip='never')
            m300.blow_out(e.top(-2))
            m300.air_gap(20)
            m300.drop_tip()

    # add lysis buffer to plate
    for col, spot, buffer_well in zip(mag_samples_m,
                                      parking_spots,
                                      lysis_buffer*12):
        if PARK:
            pick_up(m300, spot)
        else:
            pick_up(m300)
        m300.transfer(240, buffer_well, col, new_tip='never')
        m300.mix(15, 200, col)
        if PARK:
            m300.drop_tip(spot)
        else:
            drop(m300)
    ctx.comment('\n\n\n')

    magdeck.engage(height=magheight)
    ctx.delay(minutes=2, msg='Incubating on MagDeck for 2 minutes.')

    bind(285, park=PARK)
    wash(350, wash1, park=PARK)
    wash(350, etoh, park=PARK)
    wash(350, etoh, park=PARK)

    ctx.delay(minutes=5, msg='Airdrying beads at room temperature for 5 \
minutes.')
    magdeck.disengage()

    elute(ELUTION_VOL, park=PARK)

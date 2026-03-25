from opentrons.types import Point, Mount
import json
import os
import math

metadata = {
    'protocolName': 'Capping Assay: Steps 3-6',
    'author': 'Nick <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE = False


def run(ctx):
    [num_samples, tip_track] = get_values(  # noqa: F821
        'num_samples', 'tip_track')

    bead_vol = 125.0
    sample_vol = 110.0
    park_tips = True
    sample_incubation_mixing = True
    mag_height = 11.5
    z_offset = 0.5
    radial_offset = 0.5
    wash1_vol = 200.0
    wash2_vol = 200.0
    elution_vol = 100.0
    air_gap_vol = 0.0
    bead_settling_time = 1.0
    temp_time = 3.0
    mix_reps = 10
    sample_mixing_time_minutes = 15.0
    mix_volume_percentage = 0.9
    sample_mixing_blowout_height_from_bottom = 10.0

    if TEST_MODE:
        [bead_settling_time, mix_reps, temp_time,
         sample_incubation_mixing] = 0.0, 1, 0.0, False

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    sample_plate = ctx.load_labware(
        'neptune_96_aluminumblock_200ul',
        '1', 'starting sample plate')
    magdeck = ctx.load_module('magnetic module gen2', '4')
    magplate = magdeck.load_labware('cytiva_96_wellplate_500ul',
                                    'deepwell plate')
    tempdeck = ctx.load_module('Temperature Module Gen2', '7')
    heatingplate = tempdeck.load_labware(
                'neptune_96_aluminumblock_200ul',
                'heating plate')
    elutionplate = ctx.load_labware(
                'neptune_96_aluminumblock_200ul', '2',
                'final elution plate')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '11',
                             'Liquid Waste').wells()[0].top()
    res = ctx.load_labware('nest_12_reservoir_15ml', '5', 'reagent reservoir')
    num_cols = math.ceil(num_samples/8)
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                                '200µl filtertiprack')
               for slot in ['3', '6', '9', '10']]
    if park_tips:
        rack = ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '8', 'tiprack for parking')
        parking_spots = rack.rows()[0][:num_cols]
    else:
        rack = ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '8', '200µl filtertiprack')
        parking_spots = [None for none in range(12)]
    tips300.insert(0, rack)

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    """
    Here is where you can define the locations of your reagents.
    """
    wash1 = res.wells()[:2]
    wash2 = res.wells()[2:5]
    beads = res.wells()[10]
    elution_solution = res.wells()[-1]

    mag_samples_m = magplate.rows()[0][:num_cols]
    starting_samples_m = sample_plate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]
    heating_samples_m = heatingplate.rows()[0][:num_cols]
    if mag_samples_m[0].width:
        radius = mag_samples_m[0].width/2
    else:
        radius = mag_samples_m[0].diameter/2

    magdeck.disengage()  # just in case
    tempdeck.set_temperature(85)

    mount = Mount.LEFT if m300.mount == 'left' else Mount.RIGHT
    ctx._hw_manager.hardware._attached_instruments[
        mount].update_config_item(
            'pick_up_current', 1)

    folder_path = '/data/B'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                for pip in tip_log:
                    if pip.name in data:
                        tip_log[pip]['count'] = data[pip.name]
                    else:
                        tip_log[pip]['count'] = 0
        else:
            for pip in tip_log:
                tip_log[pip]['count'] = 0
    else:
        for pip in tip_log:
            tip_log[pip]['count'] = 0

    for pip in tip_log:
        if pip.type == 'multi':
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.rows()[0]]
        else:
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.wells()]
        tip_log[pip]['max'] = len(tip_log[pip]['tips'])

    def slow_withdraw(pip, well, delay_seconds=2.0):
        pip.default_speed /= 16
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 16

    def _pick_up(pip=m300, loc=None):
        if tip_log[pip]['count'] == tip_log[pip]['max'] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
            tip_log[pip]['count'] += 1

    switch = True
    drop_count = 0
    # number of tips trash will accommodate before prompting user to empty
    drop_threshold = 120

    def _drop(pip=m300):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        if pip.type == 'multi':
            drop_count += 8
        else:
            drop_count += 1
        if drop_count == drop_threshold:
            # Setup for flashing lights notification to empty trash
            ctx.home()  # home before continuing with protocol
            drop_count = 0

    waste_vol = 0
    waste_threshold = 185000

    def remove_supernatant(vol, park=False, drop=True):
        """
        `remove_supernatant` will transfer supernatant from the deepwell
        extraction plate to the liquid waste reservoir.
        :param vol (float): The amount of volume to aspirate from all deepwell
                            sample wells and dispense in the liquid waste.
        :param park (boolean): Whether to pick up sample-corresponding tips
                               in the 'parking rack' or to pick up new tips.
        """

        def _waste_track(vol):
            nonlocal waste_vol
            if waste_vol + vol >= waste_threshold:
                # Setup for flashing lights notification to empty liquid waste
                ctx.home()
                ctx.pause('Please empty liquid waste (slot 11) before \
resuming.')

                waste_vol = 0
            waste_vol += vol

        m300.flow_rate.aspirate /= 2
        num_trans = math.ceil(vol/(200 - air_gap_vol))
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if not m300.has_tip:
                if park:
                    _pick_up(m300, spot)
                else:
                    _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0).move(Point(x=side*radius*radial_offset,
                                         z=z_offset))
            for _ in range(num_trans):
                _waste_track(vol_per_trans)
                if m300.current_volume > 0:
                    # void air gap if necessary
                    m300.dispense(m300.current_volume, m.top())
                m300.move_to(m.center())
                m300.aspirate(vol_per_trans, loc)
                slow_withdraw(m300, m)
                if air_gap_vol > 0:
                    m300.aspirate(air_gap_vol, m.top())
                m300.dispense(m300.current_volume, waste)
                m300.blow_out(waste)
                m300.air_gap(20)
            if drop:
                _drop(m300)
        m300.flow_rate.aspirate *= 2

    def wash(vol, source, change_tips_for_samples=True, mix_reps=mix_reps,
             park=True, resuspend=True, drop=True):
        """
        `wash` will perform bead washing for the extraction protocol.
        :param vol (float): The amount of volume to aspirate from each
                            source and dispense to each well containing beads.
        :param source (List[Well]): A list of wells from where liquid will be
                                    aspirated. If the length of the source list
                                    > 1, `wash` automatically calculates
                                    the index of the source that should be
                                    accessed.
        :param mix_reps (int): The number of repititions to mix the beads with
                               specified wash buffer (ignored if resuspend is
                               False).
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding wash buffer and removing
                               supernatant.
        :param resuspend (boolean): Whether to resuspend beads in wash buffer.
        """

        if resuspend and magdeck.status == 'engaged':
            magdeck.disengage()

        num_trans = math.ceil(vol/(200-air_gap_vol))
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if not m300.has_tip:
                _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, source.top())
                m300.aspirate(vol_per_trans, source)
                slow_withdraw(m300, source)
                z_disp = 3 if n == num_trans - 1 else m.depth - 2
                if air_gap_vol > 0:
                    m300.aspirate(air_gap_vol, source.top())
                m300.dispense(m300.current_volume, m.bottom(z_disp))
                slow_withdraw(m300, m)
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(20)
            if resuspend:
                for _ in range(mix_reps):
                    m300.aspirate(mix_volume_percentage*vol, m.bottom(0.5))
                    m300.dispense(mix_volume_percentage*vol,
                                  m.bottom().move(
                                    Point(x=side*radius*radial_offset, z=3)))
            m300.blow_out(m.top())
            m300.air_gap(20)
            if change_tips_for_samples:
                if park:
                    m300.drop_tip(spot)
                else:
                    _drop(m300)

        if magdeck.status == 'disengaged':
            magdeck.engage(mag_height)

        ctx.delay(minutes=bead_settling_time, msg='Incubating on MagDeck for \
' + str(bead_settling_time) + ' minutes.')

        remove_supernatant(vol, park=park, drop=drop)

    def elute(vol, park=True):
        """
        `elute` will perform elution from the deepwell extraction plate to the
        final clean elutions PCR plate to complete the extraction protocol.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """
        magdeck.disengage()

        # pre-heat elution buffer
        _pick_up(m300)
        for h in heating_samples_m:
            m300.aspirate(elution_vol*1.2, elution_solution)
            slow_withdraw(m300, elution_solution)
            m300.dispense(elution_vol*2, h.bottom(3))
            slow_withdraw(m300, h)
        m300.home()

        ctx.delay(minutes=temp_time, msg=f'Incubating at 85C for {temp_time} \
minutes')
        # resuspend beads in elution
        m300.flow_rate.aspirate /= 5
        m300.flow_rate.dispense /= 5
        m300.flow_rate.blow_out /= 5
        for i, (m, h, spot) in enumerate(zip(mag_samples_m, heating_samples_m,
                                             parking_spots)):
            if not m300.has_tip:
                _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset))
            m300.aspirate(vol*1.2, h)
            slow_withdraw(m300, h)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            slow_withdraw(m300, m)
            for _ in range(mix_reps):
                m300.aspirate(vol*mix_volume_percentage, m.bottom(0.5))
                m300.dispense(vol*mix_volume_percentage, m.bottom().move(Point(
                    x=side*radius*radial_offset, z=3)))
                slow_withdraw(m300, m)
            m300.aspirate(vol, m.bottom(0.5))
            slow_withdraw(m300, m)
            m300.dispense(vol, h)
            slow_withdraw(m300, h)
            m300.blow_out(h.bottom(h.depth/2))
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        ctx.delay(minutes=temp_time, msg=f'Incubating at 85C for {temp_time} \
minutes')

        for m, h, spot in zip(mag_samples_m, heating_samples_m,
                              parking_spots):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            m300.mix(5, 0.5*vol, h)
            m300.aspirate(vol, h)
            slow_withdraw(m300, h)
            m300.dispense(vol, m)
            slow_withdraw(m300, m)
            m300.blow_out(m.bottom(m.depth/2))
            _drop(m300)

        magdeck.engage(mag_height)
        ctx.delay(minutes=bead_settling_time, msg='Incubating on MagDeck for \
' + str(bead_settling_time) + ' minutes.')

        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, parking_spots)):
            _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset+2))
            m300.move_to(m.center())
            m300.aspirate(0.8*vol, loc)
            slow_withdraw(m300, m)
            if air_gap_vol > 0:
                m300.aspirate(air_gap_vol, m.top())
            m300.dispense(m300.current_volume, e.bottom(1))
            slow_withdraw(m300, e)
            m300.drop_tip()

        m300.flow_rate.aspirate *= 5
        m300.flow_rate.dispense *= 5
        m300.flow_rate.blow_out *= 5

    """
    ACTIONS
    """
    # beads
    _pick_up(m300)
    # add beads
    m300.mix(10, 150, beads)
    for m in mag_samples_m:
        m300.aspirate(bead_vol, beads)
        slow_withdraw(m300, beads)
        m300.dispense(bead_vol, m)
        slow_withdraw(m300, m)
    m300.home()

    # prewash
    magdeck.engage(mag_height)
    ctx.delay(minutes=bead_settling_time, msg=f'Beads separating for \
{bead_settling_time} minutes.')
    remove_supernatant(bead_vol, drop=False)
    # keep tips for wash

    for w in range(2):
        wash(wash1_vol, wash1[w], park=park_tips, drop=False,
             change_tips_for_samples=False)

    # add sample and mix iteratively for ~30 minutes
    magdeck.disengage()
    for s, d, p in zip(starting_samples_m, mag_samples_m, parking_spots):
        if not m300.has_tip:
            _pick_up()
        m300.transfer(sample_vol, s, d, new_tip='never')
        m300.drop_tip(p)

    m300.default_speed = 200
    # m300.flow_rate.aspirate = 46.43
    # m300.flow_rate.dispense = 92.86
    mixes_per_min = 0.5
    num_mix_cycles = int(sample_mixing_time_minutes*mixes_per_min/num_cols)
    if TEST_MODE or not sample_incubation_mixing:
        num_mix_cycles = 5
    for i in range(num_mix_cycles):
        for j, (s, p) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300, p)
            side = 1 if j % 2 == 0 else -1
            loc = s.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset-1))
            m300.move_to(s.bottom(5))
            for _ in range(mix_reps):
                m300.aspirate(sample_vol*mix_volume_percentage, loc)
                m300.dispense(sample_vol*mix_volume_percentage,
                              s.bottom().move(Point(
                                x=side*radius*radial_offset, z=7)))
                slow_withdraw(m300, s)
                m300.blow_out(
                    s.bottom(sample_mixing_blowout_height_from_bottom))
            m300.drop_tip(p)
    m300.default_speed = 400
    magdeck.engage(mag_height)
    ctx.delay(minutes=bead_settling_time)
    remove_supernatant(sample_vol, park=park_tips)

    # sample washes
    for w in range(2):
        wash(wash1_vol, wash1[w], park=park_tips)
    for w in range(3):
        wash(wash2_vol, wash2[w], park=park_tips)
    elute(elution_vol, park=park_tips)

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

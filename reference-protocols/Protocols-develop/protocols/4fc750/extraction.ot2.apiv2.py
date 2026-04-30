from opentrons.types import Point
import json
import os
import math
import contextlib
import threading
from opentrons import protocol_api

metadata = {
    'protocolName':
        'Omega Mag-Bind® Blood & Tissue DNA 96 Kit - 250μL Blood Protocol',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


"""
Here is where you can modify the magnetic module engage height:
"""


# Definitions for deck light flashing
@contextlib.contextmanager
def flashing_rail_lights(
    protocol: protocol_api.ProtocolContext, seconds_per_flash_cycle=1.0
):
    """Flash the rail lights on and off in the background.

    Source: https://github.com/Opentrons/opentrons/issues/7742

    Example usage:

        # While the robot is doing nothing for 2 minutes, flash lights quickly.
        with flashing_rail_lights(protocol, seconds_per_flash_cycle=0.25):
            protocol.delay(minutes=2)

    When the ``with`` block exits, the rail lights are restored to their
    original state.

    Exclusive control of the rail lights is assumed. For example, within the
    ``with`` block, you must not call `ProtocolContext.set_rail_lights`
    yourself, inspect `ProtocolContext.rail_lights_on`, or nest additional
    calls to `flashing_rail_lights`.
    """
    original_light_status = protocol.rail_lights_on

    stop_flashing_event = threading.Event()

    def background_loop():
        while True:
            protocol.set_rail_lights(not protocol.rail_lights_on)
            # Wait until it's time to toggle the lights for the next flash or
            # we're told to stop flashing entirely, whichever comes first.
            got_stop_flashing_event = stop_flashing_event.wait(
                timeout=seconds_per_flash_cycle/2
            )
            if got_stop_flashing_event:
                break

    background_thread = threading.Thread(
        target=background_loop, name="Background thread for flashing rail \
lights"
    )

    try:
        if not protocol.is_simulating():
            background_thread.start()
        yield

    finally:
        # The ``with`` block might be exiting normally, or it might be exiting
        # because something inside it raised an exception.
        #
        # This accounts for user-issued cancelations because currently
        # (2021-05-04), the Python Protocol API happens to implement user-
        # issued cancellations by raising an exception from internal API code.
        if not protocol.is_simulating():
            stop_flashing_event.set()
            background_thread.join()

        # This is questionable: it may issue a command to the API while the API
        # is in an inconsistent state after raising an exception.
        protocol.set_rail_lights(original_light_status)


# Start protocol
def run(ctx):
    [num_samples, deepwell_type, elution_type, res12_type, res1_type,
     magdeck_gen, p300_gen, starting_vol, binding_buffer_vol, wash1_vol,
     wash2_vol, elution_vol, air_dry_time, mix_reps, mag_height, settling_time,
     elute_on_robot, park_tips, tip_track, flash] = get_values(  # noqa: F821
        'num_samples', 'deepwell_type', 'elution_type', 'res12_type',
        'res1_type', 'magdeck_gen', 'p300_gen', 'starting_vol',
        'binding_buffer_vol', 'wash1_vol', 'wash2_vol', 'elution_vol',
        'air_dry_time', 'mix_reps', 'mag_height', 'settling_time',
        'elute_on_robot', 'park_tips', 'tip_track', 'flash')

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    magdeck = ctx.load_module(magdeck_gen, '1')
    magdeck.disengage()
    magplate = magdeck.load_labware(deepwell_type, 'deepwell plate')
    res1 = ctx.load_labware(res12_type, '2', 'reagent reservoir 1')
    res2 = ctx.load_labware(res12_type, '3', 'reagent reservoir 2')
    elutionplate = ctx.load_labware(elution_type, '4', 'elution plate')
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                                '200µl filtertiprack')
               for slot in ['5', '6', '7', '8', '9', '10']]
    waste_res = ctx.load_labware(res1_type, '11', 'Liquid Waste')
    waste = waste_res.wells()[0].top()
    num_cols = math.ceil(num_samples/8)

    # load P300M pipette
    m300 = ctx.load_instrument(p300_gen, 'left', tip_racks=tips300)

    """
    Here is where you can define the locations of your reagents.
    """
    binding_buffer = res1.wells()[:3]
    wash1 = res1.wells()[4:7]
    wash2 = res1.wells()[7:10]
    wash3 = res2.wells()[:3]
    elution_solution = res2.wells()[4]

    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]

    magdeck.disengage()  # just in case

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

    folder_path = '/data/B'
    tip_file_path = folder_path + '/tip_log.json'
    tip_log = {'count': {}}
    if tip_track and not ctx.is_simulating():
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

    parking_spots = []

    def _update_parking_spots(pip):
        nonlocal parking_spots
        count = tip_log['count'][pip]
        parking_spots = tip_log['tips'][m300][count:count+num_cols]

    def _pick_up(pip, loc=None):
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
    # number of tips trash will accommodate before prompting user to empty
    drop_threshold = 120

    def _drop(pip):
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
        if drop_count >= drop_threshold:
            # Setup for flashing lights notification to empty trash
            ctx.home()  # home before continuing with protocol
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    with flashing_rail_lights(ctx, seconds_per_flash_cycle=1):
                        ctx.pause('Please empty tips from waste before \
resuming.')
            drop_count = 0

    waste_vol = 0
    # adjust 5ml for spilling
    waste_threshold = waste_res.wells()[0].max_volume - 5000

    def remove_supernatant(vol, park=False):
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
                if flash:
                    if not ctx._hw_manager.hardware.is_simulator:
                        with flashing_rail_lights(ctx,
                                                  seconds_per_flash_cycle=1):
                            ctx.pause('Please empty liquid waste (slot 11) \
before resuming.')

                waste_vol = 0
            waste_vol += vol

        m300.flow_rate.aspirate = 30
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            for _ in range(num_trans):
                _waste_track(vol_per_trans)
                if m300.current_volume > 0:
                    # void air gap if necessary
                    m300.dispense(m300.current_volume, m.top())
                m300.move_to(m.center())
                m300.transfer(vol_per_trans, loc, waste, new_tip='never',
                              air_gap=20)
                m300.blow_out(waste)
                m300.air_gap(20)
            _drop(m300)
        m300.flow_rate.aspirate = 150

    def bind(vol, park=True):
        """
        `bind` will perform magnetic bead binding on each sample in the
        deepwell plate. Each channel of binding beads will be mixed before
        transfer, and the samples will be mixed with the binding beads after
        the transfer. The magnetic deck activates after the addition to all
        samples, and the supernatant is removed after bead bining.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """
        _update_parking_spots(m300)
        for i, (well, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
            num_trans = math.ceil(vol/200)
            vol_per_trans = vol/num_trans
            asp_per_chan = (0.95*res1.wells()[0].max_volume)//(vol_per_trans*8)
            for t in range(num_trans):
                chan_ind = int((i*num_trans + t)//asp_per_chan)
                source = binding_buffer[chan_ind]
                if m300.current_volume > 0:
                    # void air gap if necessary
                    m300.dispense(m300.current_volume, source.top())
                for _ in range(8):
                    m300.aspirate(180, source.bottom(0.5))
                    m300.dispense(180, source.bottom(5))
                m300.transfer(vol_per_trans, source, well.top(), air_gap=20,
                              new_tip='never')
                if t < num_trans - 1:
                    m300.air_gap(20)
            m300.mix(4, 200, well)
            m300.blow_out(well.top(-2))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        ctx.delay(minutes=3, msg='Incubating off MagDeck for 3 minutes.')

        # agitate after resuspension
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.mix(4, 200, loc)
            m300.blow_out(m.top(-2))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        ctx.delay(minutes=3, msg='Incubating off MagDeck for 3 minutes.')

        magdeck.engage(mag_height)
        ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

        # remove initial supernatant
        remove_supernatant(vol+starting_vol, park=park)

    def wash(vol, source, mix_reps=15, park=True, resuspend=True,
             air_dry=False):
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

        _update_parking_spots(m300)
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
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
            if resuspend:
                m300.mix(mix_reps, 150, loc)
            m300.blow_out(m.top())
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        if magdeck.status == 'disengaged':
            magdeck.engage(mag_height)

        ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

        remove_supernatant(vol, park=park)
        if air_dry:
            ctx.delay(minutes=air_dry_time, msg=f'Air drying {air_dry_time} \
minutes.')

    def elute(vol, park=True):
        """
        `elute` will perform elution from the deepwell extraciton plate to the
        final clean elutions PCR plate to complete the extraction protocol.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """

        # resuspend beads in elution
        if magdeck.status == 'enagaged':
            magdeck.disengage()

        _update_parking_spots(m300)
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.aspirate(vol, elution_solution)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            m300.mix(mix_reps, 0.8*vol, loc)
            m300.blow_out(m.bottom(5))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        ctx.delay(minutes=3, msg='Incubate at RT/65°C for 3 mins.')

        # agitate after resuspension
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.mix(mix_reps, 0.8*vol, loc)
            m300.blow_out(m.bottom(5))
            m300.air_gap(20)
            _drop(m300)

        ctx.delay(minutes=3, msg='Incubate at RT/65°C for 3 mins.')

        if elute_on_robot:
            magdeck.engage(mag_height)
            ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

            for i, (m, e, spot) in enumerate(
                    zip(mag_samples_m, elution_samples_m, parking_spots)):
                _pick_up(m300)
                side = -1 if i % 2 == 0 else 1
                loc = m.bottom(0.5).move(Point(x=side*2))
                m300.transfer(vol, loc, e.bottom(5), air_gap=20,
                              new_tip='never')
                m300.blow_out(e.top(-2))
                m300.air_gap(20)
                m300.drop_tip()
        else:
            ctx.comment('Manually transfer DNA to 1.5ml eppendrof tubes.')

    """
    Here is where you can call the methods defined above to fit your specific
    protocol. The normal sequence is:
    """
    bind(binding_buffer_vol, park=park_tips)
    wash(wash1_vol, wash1, park=park_tips)
    wash(wash1_vol, wash2, park=park_tips)
    wash(wash2_vol, wash3, park=park_tips, air_dry=True)
    elute(elution_vol, park=park_tips)

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {'tips300': tip_log['count'][m300]}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

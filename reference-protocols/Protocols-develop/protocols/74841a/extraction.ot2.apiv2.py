from opentrons.types import Point
import json
import os
import math
import contextlib
import threading
from opentrons import protocol_api

metadata = {
    'protocolName': 'Swift NormalaseTM Amplicon Panels (SNAP): Size Selection \
and Cleanup Part 1/2',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.10'
}


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
    [num_samples, mag_height, z_offset, radial_offset, starting_vol,
     binding_buffer_vol, wash1_vol, elution_vol, mix_reps,
     settling_time, park_tips, tip_track, flash] = get_values(  # noqa: F821
        'num_samples', 'mag_height', 'z_offset', 'radial_offset',
        'starting_vol', 'binding_buffer_vol', 'wash1_vol', 'elution_vol',
        'mix_reps', 'settling_time', 'park_tips', 'tip_track', 'flash')

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    magdeck = ctx.load_module('magnetic module gen2', '4')
    magdeck.disengage()
    magplate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr',
                                    'PCR plate')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '11',
                             'Liquid Waste').wells()[0].top()
    res1 = ctx.load_labware('usascientific_12_reservoir_22ml', '5',
                            'reagent reservoir')
    num_cols = math.ceil(num_samples/8)
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                                '200µl filtertiprack')
               for slot in ['2', '3', '6', '8', '9', '10']]
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                               '20µl filtertiprack') for slot in ['1']]
    if park_tips:
        rack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '7', 'tiprack for parking')
        parking_spots = rack.rows()[0][:num_cols]
    else:
        rack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '7', '200µl filtertiprack')
        parking_spots = [None for none in range(12)]
    tips300.insert(0, rack)

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    """
    Here is where you can define the locations of your reagents.
    """
    binding_buffer = res1.wells()[:1]
    etoh1 = res1.wells()[1:2]
    etoh2 = res1.wells()[2:3]
    post_pcr_te_buff = res1.wells()[3]

    mag_samples_m = magplate.rows()[0][:num_cols]
    radius = mag_samples_m[0].diameter/2

    magdeck.disengage()  # just in case

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

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

    def _pick_up(pip, loc=None):
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
        if drop_count == drop_threshold:
            # Setup for flashing lights notification to empty trash
            ctx.home()  # home before continuing with protocol
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    with flashing_rail_lights(ctx, seconds_per_flash_cycle=1):
                        ctx.pause('Please empty tips from waste before \
resuming.')
            drop_count = 0

    waste_vol = 0
    waste_threshold = 185000

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
            loc = m.bottom(0).move(Point(x=side*radius*radial_offset,
                                         z=z_offset))
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
        for i, (well, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
            source = binding_buffer[0]
            m300.aspirate(30, source.bottom(0.5))
            m300.dispense(30, source.bottom(5))
            m300.transfer(vol, source.bottom(0.5), well.bottom(0.5),
                          new_tip='never')
            ctx.delay(seconds=1)
            m300.blow_out(source.top(-1))
            m300.mix(5, starting_vol, well)
            m300.blow_out(well.top(-2))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        magdeck.engage(height=mag_height)
        ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

        # remove initial supernatant
        remove_supernatant(vol+starting_vol, park=park)

    def wash(vol, source, mix_reps=15, park=True, resuspend=True):
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

        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset))
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
            magdeck.engage(height=mag_height)

        ctx.delay(seconds=30, msg='Incubating on MagDeck for 30 seconds.')

        remove_supernatant(vol+2, park=park)

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
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m20)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset))
            m20.aspirate(vol, post_pcr_te_buff)
            m20.move_to(m.center())
            m20.dispense(vol, loc)
            m20.mix(mix_reps, 0.8*vol, loc)
            m20.blow_out(m.bottom(5))
            m20.air_gap(20)
            _drop(m20)

    """function calls"""
    bind(binding_buffer_vol, park=False)
    wash(wash1_vol, etoh1, park=park_tips, resuspend=False)
    wash(wash1_vol, etoh2, park=park_tips, resuspend=False)
    elute(elution_vol, park=park_tips)
    ctx.comment('Proceed to the Indexing PCR step.')

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

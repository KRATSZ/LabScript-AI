from opentrons.types import Point
import math

metadata = {
    'protocolName': 'SPRI 3',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.10'
}


# Start protocol
def run(ctx):
    [num_samples, m20_mount, m300_mount, mag_height, sample_vol,
     binding_buffer_vol, wash1_vol, wash2_vol, elution_vol,
     settling_time] = get_values(  # noqa: F821
        'num_samples', 'm20_mount', 'm300_mount', 'mag_height', 'sample_vol',
        'binding_buffer_vol', 'wash1_vol', 'wash2_vol', 'elution_vol',
        'settling_time')

    # num_samples = 96
    # m20_mount = 'left'
    # m300_mount = 'right'
    # mag_height = 10.5
    # sample_vol = 45.0
    # binding_buffer_vol = 45.0
    # wash1_vol = 200.0
    # wash2_vol = 200.0
    # elution_vol = 50.0
    # settling_time = 5.0
    park_tips = False
    radial_offset = 0.3
    z_offset = 0.5
    air_gap_vol = 0

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    pcr_plate = ctx.load_labware('eppendorfmetaladapter_96_wellplate_200ul',
                                 '7', 'sample plate')
    magdeck = ctx.load_module('magnetic module gen2', '10')
    magdeck.disengage()
    magplate = magdeck.load_labware('abgenemidi_96_wellplate_800ul',
                                    'deepwell wash plate')
    elutionplate = ctx.load_labware('eppendorfmetaladapter_96_wellplate_200ul',
                                    '2', 'elution plate')
    waste = ctx.loaded_labwares[12].wells()[0].top()
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '6', 'reagent reservoir')
    num_cols = math.ceil(num_samples/6)  # offset
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                                '200ul tiprack')
               for slot in ['4', '9', '11']]
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '5',
                               '20ul tiprack')]
    if park_tips:
        rack = ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '1', '200ul tiprack')
        parking_spots = rack.rows()[0][:num_cols]
    else:
        rack = ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '1', '200ul tiprack')
        parking_spots = [None for none in range(12)]
    tips300.insert(0, rack)

    # load pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2', m300_mount, tip_racks=tips300)

    m300.default_speed = 180
    m20.default_speed = 180

    """
    Here is where you can define the locations of your reagents.
    """
    binding_buffer = res1.rows()[0][:1]
    wash1 = res1.rows()[0][1:4]
    wash2 = res1.rows()[0][4:7]
    elution_solution = res1.rows()[0][-1]

    starting_samples = pcr_plate.rows()[0][:num_cols]
    starting_samples = [
        pcr_plate.columns()[col_ind][1]
        for col_ind in [2, 4][:num_cols]]
    mag_samples_m = magplate.rows()[0][10:10+num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]
    radius = mag_samples_m[0].diameter/2

    magdeck.disengage()  # just in case

    m300.flow_rate.aspirate = 20
    m300.flow_rate.dispense = 50
    m300.flow_rate.blow_out = 150

    num_channels = 3 if num_samples == 3 else 6
    pick_up_current_per_tip = 0.1

    def pick_up(pip=m20, channels=num_channels, loc=None):
        # iterate and look for required number of consecutive tips
        pick_up_current = pick_up_current_per_tip*channels
        ctx._hw_manager.hardware._attached_instruments[
          m20._implementation.get_mount()].update_config_item(
          'pick_up_current', pick_up_current)

        for rack in pip.tip_racks:
            for col in rack.columns():
                counter = 0
                for well in col[::-1]:
                    if well.has_tip:
                        counter += 1
                    else:
                        counter = 0
                    if counter == channels:
                        pip.pick_up_tip(well)
                        return

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
            drop_count = 0

    waste_vol = 0
    waste_threshold = 185000

    def remove_supernatant(vol, pip=m300, park=False):
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
                waste_vol = 0
            waste_vol += vol

        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if not m300.has_tip:
                if park:
                    pick_up(pip, spot)
                else:
                    pick_up(pip)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0).move(Point(x=side*radius*radial_offset,
                                         z=z_offset))
            _waste_track(vol)
            pip.move_to(m.center())
            # if pip == m300:
            #     air_gap_vol = 20
            # else:
            #     air_gap_vol = pip.max_volume - vol
            pip.transfer(vol, loc, waste, new_tip='never',
                         air_gap=(air_gap_vol))
            # pip.blow_out(waste)
            _drop(pip)

    def bind(vol, park=True):
        """
        `bind` will perform magnetic bead binding on each sample in the
        deepwell plate. Each channel of binding beads will be mixed before
        transfer, and the samples will be mixed with the binding beads after
        the transfer. The magnetic deck activates after the addition to all
        samples, and the supernatant is removed after bead binding.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """
        m300.flow_rate.aspirate = 30
        latest_chan = -1
        pick_up(m300)
        for i, (well, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            num_trans = math.ceil(vol/200)
            vol_per_trans = vol/num_trans
            for t in range(num_trans):
                chan_ind = 0
                source = binding_buffer[chan_ind]
                if m300.current_volume > 0:
                    # void air gap if necessary
                    m300.dispense(m300.current_volume, source.top())
                if chan_ind > latest_chan:  # mix if accessing new channel
                    for _ in range(5):
                        m300.aspirate(180, source.bottom(0.1))
                        m300.dispense(180, source.bottom(5))
                    latest_chan = chan_ind
                m300.transfer(vol_per_trans, source, well.bottom(0.1),
                              air_gap=20, new_tip='never')
                m300.blow_out(well.bottom(2))
                m300.air_gap(20)
            # m300.mix(10, 200, well)
            # m300.blow_out(well.top(-2))
        _drop(m300)

        m300.flow_rate.aspirate = 80

        # transfer samples
        for source, dest, spot in zip(starting_samples, mag_samples_m,
                                      parking_spots):
            if not m300.has_tip:
                if park:
                    pick_up(m300, loc=spot)
                else:
                    pick_up(m300)
            # _drop(m300)
            # pick_up(m300)
            m300.aspirate(sample_vol, source.bottom(0.1))
            m300.dispense(sample_vol, dest)
            m300.mix(10, sample_vol, dest)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        ctx.delay(minutes=5, msg='Incubating off magnet for 5 minutes.')
        magdeck.engage(height=mag_height)
        ctx.delay(minutes=settling_time, msg=f'Incubating on MagDeck for \
{settling_time} minutes.')

        # remove initial supernatant
        remove_supernatant(150, park=park)

    def wash(vol, source, mix_reps=15, park=True, blow_out=False,
             resuspend=False):
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
        pick_up(m300)
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            src = source[int(i//(12/len(source)))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.transfer(vol_per_trans, src, m.top(), air_gap=air_gap_vol,
                              new_tip='never')
                if blow_out:
                    m300.blow_out(m.top(-1))
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(air_gap_vol)

        if resuspend:
            for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
                if not m300.has_tip:
                    pick_up(m300)
                    side = 1 if i % 2 == 0 else -1
                    loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                                z=z_offset))
                    m300.mix(mix_reps, 150, loc)
                    m300.blow_out(m.top())
                    m300.air_gap(air_gap_vol)
                if park:
                    m300.drop_tip(spot)
                else:
                    _drop(m300)

        if magdeck.status == 'disengaged':
            magdeck.engage(height=mag_height)

        ctx.delay(seconds=60, msg='Incubating on MagDeck for 60s seconds.')
        remove_supernatant(vol, park=park)

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
        magdeck.disengage()
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset))
            m300.aspirate(vol+2.5, elution_solution)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            m300.mix(10, 0.8*vol, loc)
            m300.blow_out(m.bottom(5))
            m300.air_gap(air_gap_vol)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        magdeck.engage(height=mag_height)
        ctx.delay(minutes=settling_time, msg=f'Incubating on MagDeck for \
{settling_time} minutes.')

        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, parking_spots)):
            if park:
                pick_up(m300, loc=spot)
            else:
                pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom().move(Point(x=side*radius*radial_offset,
                                        z=z_offset))
            m300.transfer(vol, loc, e.bottom(5), air_gap=air_gap_vol,
                          new_tip='never')
            m300.blow_out(e.top(-2))
            m300.air_gap(air_gap_vol)
            m300.drop_tip()

    """
    Here is where you can call the methods defined above to fit your specific
    protocol. The normal sequence is:
    """
    bind(binding_buffer_vol, park=park_tips)
    wash(wash1_vol, wash1, park=park_tips, blow_out=True)
    wash(wash2_vol, wash2, park=park_tips)
    remove_supernatant(18, pip=m20)
    elute(elution_vol, park=park_tips)

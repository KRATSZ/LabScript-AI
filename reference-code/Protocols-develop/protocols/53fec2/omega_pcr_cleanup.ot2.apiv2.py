from opentrons.types import Point
import json
import os
import math

metadata = {
    'protocolName': 'Beckman Coulter AMPure XP PCR Cleanup and Size Selection',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


# Start protocol
def run(ctx):

    [num_samples, mag_height, sample_vol, beads_vol, wash1_vol, wash2_vol,
     elution_vol, park_tips, tip_track] = get_values(  # noqa: F821
        'num_samples', 'mag_height', 'sample_vol', 'beads_vol',
        'wash1_vol', 'wash2_vol', 'elution_vol', 'park_tips', 'tip_track')

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    num_cols = math.ceil(num_samples/8)

    etoh = [
        ctx.load_labware('epmotion_1_reservoir_100000ul', '1',
                         'EtOH').wells()[0]]
    beads = [
        ctx.load_labware('epmotion_1_reservoir_30000ul', '2',
                         'beads').wells()[0]]
    h2o = ctx.load_labware('epmotion_1_reservoir_30000ul', '3',
                           'H2O').wells()[0]
    waste_res = ctx.load_labware('epmotion_1_reservoir_100000ul', '4',
                                 'liquid waste').wells()[0]
    waste = waste_res.top()
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                                '300µl tiprack')
               for slot in ['6', '9']]
    magdeck = ctx.load_module('magnetic module gen2', '7')
    magdeck.disengage()
    magplate = magdeck.load_labware('eppendorf_96_deepwellplate_500ul',
                                    'deepwell plate')
    elutionplate = ctx.load_labware('eppendorf_96_wellplate_200ul', '8',
                                    'elution plate')
    sample_plates = [
        ctx.load_labware('eppendorf_96_wellplate_200ul', slot,
                         'sample plate ' + letter)
        for slot, letter in zip(['10', '11'], ['A', 'B'])]
    if park_tips:
        rack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '5', 'tiprack for parking')
        parking_spots = rack.rows()[0][:num_cols]
    else:
        rack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '5', '200µl filtertiprack')
        parking_spots = [None for none in range(12)]
    tips300.insert(0, rack)

    # load P300M pipette
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    """
    Here is where you can define the locations of your reagents.
    """
    sources = [plate.rows()[0][:num_cols] for plate in sample_plates]
    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]
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
        if pip.has_tip:
            pip.drop_tip(drop_loc)
            switch = not switch
            if pip.type == 'multi':
                drop_count += 8
            else:
                drop_count += 1
        if drop_count >= drop_threshold:
            # Setup for flashing lights notification to empty trash
            drop_count = 0

    waste_vol = 0
    waste_threshold = waste_res.max_volume*0.95

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
                ctx.pause('Please empty liquid waste (slot 11) before \
resuming.')

                ctx.home()  # home before continuing with protocol
                waste_vol = 0
            waste_vol += vol

        m300.flow_rate.aspirate = 30
        num_trans = math.ceil(vol/280)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0).move(Point(x=side*radius*0.8, z=0.5))
            for _ in range(num_trans):
                _waste_track(vol_per_trans*8)
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
            source = beads[0]
            _pick_up(m300)
            mix_locs = [
                source.bottom().move(Point(x=x_move, z=5))
                for x_move in [-20, 20]]
            for loc in mix_locs:
                m300.mix(10, 250, source.bottom(5))

            m300.transfer(beads_vol, source, well.top(), air_gap=20,
                          new_tip='never')
            m300.blow_out(well.top(-2))
            m300.air_gap(20)
            m300.drop_tip(spot)

    def wash(vol, source, mix_reps=15, park=True, start_park=False,
             resuspend=True):
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

        num_trans = math.ceil(vol/280)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
            src = source[i//(12//len(source))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.transfer(vol_per_trans, src, m.top(1), air_gap=20,
                              new_tip='never')
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(20)
            m300.blow_out(m.top())
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        if magdeck.status == 'disengaged':
            magdeck.engage(height=mag_height)

        ctx.delay(minutes=5, msg='Incubating on MagDeck for \
' + str(5) + ' minutes.')

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
        if magdeck.status == 'enagaged':
            magdeck.disengage()
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom().move(Point(x=side*radius*0.8, z=0.5))
            m300.aspirate(vol, h2o)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            m300.mix(10, 15, loc)
            m300.blow_out(m.bottom(5))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        magdeck.engage(height=mag_height)
        ctx.delay(minutes=3.5, msg='Incubating on MagDeck for 3.5 minutes.')

        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom().move(Point(x=side*radius*0.8, z=0.5))
            m300.transfer(vol, loc, e.bottom(5), air_gap=20, new_tip='never')
            m300.blow_out(e.top(-2))
            m300.air_gap(20)
            m300.drop_tip()

    """
    Here is where you can call the methods defined above to fit your specific
    protocol. The normal sequence is:
    """

    bind(beads_vol, park=park_tips)

    # pool sample
    for m, a, b, p in zip(mag_samples_m, sources[0], sources[1],
                          parking_spots):
        if not m300.has_tip:
            _pick_up(m300, p)
        m300.consolidate(60, [a, b], m, air_gap=5, mix_after=(10, 235),
                         new_tip='never')
        m300.air_gap(20)
        if park_tips:
            m300.drop_tip(p)
        else:
            _drop(m300)
    # iterative mixing
    for mix_rep in range(2):
        for m, p in zip(mag_samples_m, parking_spots):
            if park_tips:
                _pick_up(m300, p)
            else:
                _pick_up(m300)
            m300.mix(10, 235, m)
            m300.air_gap(20)
            if park_tips:
                m300.drop_tip(p)
            else:
                _drop(m300)
    magdeck.engage(height=mag_height)

    ctx.delay(minutes=5, msg='Incubating on MagDeck for \
' + str(5) + ' minutes.')

    remove_supernatant(vol=336, park=True)
    wash(wash1_vol, etoh, park=park_tips, resuspend=False)
    wash(wash1_vol, etoh, park=park_tips, resuspend=False)
    elute(elution_vol, park=park_tips)

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

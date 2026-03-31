from opentrons.types import Point
import json
import os
import math

metadata = {
    'protocolName': 'HP COVID-19 Assay 2 V1',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.4'
}


"""
Here is where you can modify the magnetic module engage height:
"""


# Start protocol
def run(ctx):

    num_samples, tip_track = get_values(  # noqa: F821
        'num_samples', 'tip_track')

    wash_vol = 200
    mag_height = 6.8
    elution_vol = 40
    mix_reps = 10
    settling_time = 3

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()
    magplate = magdeck.load_labware('usascientific_96_wellplate_2.4ml_deep',
                                    'deepwell plate')
    res = ctx.load_labware(
        'nest_12_reservoir_15ml', '2', 'reagent reservoir')
    tempdeck = ctx.load_module('Temperature Module Gen2', '3')
    rxn_plate = tempdeck.load_labware('biorad_96_wellplate_200ul_pcr',
                                      'reaction plate')
    source_racks = [
        ctx.load_labware('opentrons_15_tuberack_nest_15ml_conical', slot,
                         'patient samples in VTM: rack ' + str(i+1))
        for i, slot in enumerate(['5', '6'][:math.ceil(num_samples/15)])]
    elution_plate = ctx.load_labware('neo_48_wellplate_40ul', '4',
                                     'elution chips')
    # elution_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '7',
    #                                  'elution chips')
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                         '200µl filtertiprack')
        for slot in ['8', '9', '6'][:(4-math.ceil(num_samples/15))]]
    tips1000 = [
        ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot)
        for slot in ['10', '11']]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)
    p1000 = ctx.load_instrument(
        'p1000_single_gen2', 'right', tip_racks=tips1000)

    """
    Here is where you can define the locations of your reagents.
    """
    beads = res.wells()[1]
    wash1 = res.wells()[3:4]
    mm = res.wells()[4]
    waste = res.wells()[-1].top()

    sources = [
        well for rack in source_racks for well in rack.wells()][:num_samples]
    num_cols = math.ceil(num_samples/8)
    inc_tubes_m = rxn_plate.rows()[0][:num_cols]
    inc_tubes_s = rxn_plate.wells()[:num_samples]
    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = elution_plate.rows()[0][:num_cols]

    magdeck.disengage()  # just in case
    tempdeck.set_temperature(4)

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
                if 'tips1000' in data:
                    tip_log['count'][p1000] = data['tips1000']
                else:
                    tip_log['count'][m300] = 0
        else:
            tip_log['count'][m300] = 0
            tip_log['count'][p1000] = 0
    else:
        tip_log['count'] = {m300: 0, p1000: 0}

    tip_log['tips'] = {
        m300: [tip for rack in tips300 for tip in rack.rows()[0]],
        p1000: [tip for rack in tips1000 for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [m300, p1000]
    }

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
        drop_inc = 8 if pip == m300 else 1
        drop_count += drop_inc
        if drop_count >= drop_threshold:
            ctx.home()
            ctx.pause('Please empty tips from waste before resuming.')

            ctx.home()  # home before continuing with protocol

            drop_count = 0

    waste_vol = 0
    waste_threshold = 15000

    def remove_supernatant(vol):
        """
        `remove_supernatant` will transfer supernatant from the deepwell
        extraction plate to the liquid waste reservoir.
        :param vol (float): The amount of volume to aspirate from all deepwell
                            sample wells and dispense in the liquid waste.
        """

        def _waste_track(vol):
            nonlocal waste_vol
            if waste_vol + vol >= waste_threshold:
                m300.home()
                ctx.pause('Please empty liquid waste (slot 11) before \
resuming.')

                ctx.home()  # home before continuing with protocol
                waste_vol = 0
            waste_vol += vol

        m300.flow_rate.aspirate = 30
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, m in enumerate(mag_samples_m):
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

    def wash(vol, source, mix_reps=15, resuspend=True):
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
        :param resuspend (boolean): Whether to resuspend beads in wash buffer.
        """

        if resuspend and magdeck.status == 'engaged':
            magdeck.disengage()

        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, m in enumerate(mag_samples_m):
            _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*m.geometry._width))
            src = source[i//(12//len(source))]
            # m300.mix(3, 100, src)
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
            _drop(m300)

        if magdeck.status == 'disengaged':
            magdeck.engage(height=mag_height)

        ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

        remove_supernatant(vol)

    def elute(vol):
        """
        `elute` will perform elution from the deepwell extraciton plate to the
        final clean elutions PCR plate to complete the extraction protocol.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        """

        # resuspend beads in elution
        if magdeck.status == 'enagaged':
            magdeck.disengage()
        _pick_up(m300)
        m300.mix(5, 100, mm)
        for i, (m, e) in enumerate(zip(mag_samples_m, elution_samples_m)):
            if not m300.hw_pipette['has_tip']:
                _pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*m.geometry._width/2))
            m300.aspirate(vol, mm)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            m300.mix(mix_reps, 0.8*vol, loc)
            m300.transfer(vol, m.bottom(0.5), e.bottom(5), air_gap=20,
                          new_tip='never')
            m300.blow_out(e.top(-2))
            m300.air_gap(20)
            _drop(m300)

    """     REFORMATTING    """
    for s, d in zip(sources, inc_tubes_s):
        _pick_up(p1000)
        p1000.transfer(200, s, d, mix_before=(5, 100), air_gap=50,
                       new_tip='never')
        p1000.air_gap(50)
        _drop(p1000)

    # add beads
    for m in inc_tubes_m:
        _pick_up(m300)
        m300.transfer(20, beads, m, mix_before=(5, 100), mix_after=(5, 100),
                      new_tip='never')
        _drop(m300)

    # temperature incubations
    for temp in [85, 56]:
        tempdeck.set_temperature(temp)
        ctx.delay(minutes=3)
        for m in inc_tubes_m:
            _pick_up(m300)
            m300.mix(10, 100, m)
            m300.air_gap(20)
            _drop(m300)

    # transfer to magplate
    for s, d in zip(inc_tubes_m, mag_samples_m):
        _pick_up(m300)
        m300.transfer(220, s, d, mix_before=(5, 100), air_gap=20,
                      new_tip='never')
        m300.air_gap(20)
        _drop(m300)

    """     EXTRACTION     """

    ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')
    remove_supernatant(220)
    wash(wash_vol, wash1)
    elute(elution_vol)
    ctx.home()

    ctx.comment('Move NEO to GNA instrument.')

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips300': tip_log['count'][m300],
            'tips1000': tip_log['count'][p1000]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

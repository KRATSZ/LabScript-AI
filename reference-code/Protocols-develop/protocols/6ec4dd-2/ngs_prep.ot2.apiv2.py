import json
import os
import math
from opentrons.types import Point

metadata = {
    'protocolName': 'NGS Library Prep Part 1: PCR Setup I',
    'author': 'Nick <protocols@opentrons.com>',
    'apiLevel': '2.12'
}


def run(ctx):

    num_samples, m20_mount, m300_mount, tip_track = get_values(  # noqa: F821
        'num_samples', 'm20_mount', 'm300_mount', 'tip_track')

    engage_height = 10.0
    vol_initial_1 = 25.0
    vol_beads_1 = 25.0
    time_minutes_incubation_binding = 5.0
    time_minutes_mag_binding = 3.0
    time_minutes_mag_wash = 3.0
    time_minutes_airdry_wash = 2.0
    time_minutes_incubation_elution = 2.0
    time_minutes_mag_elution = 2.0
    z_offset_supernatant = 0.5
    x_offset_beads_ratio = 0.6
    z_offset_beads = 3.0
    vol_elution_buffer_1 = 60.0
    vol_elution_final_1 = 50.0
    vol_pcr_mm = 35.0

    vol_initial_2 = 10.0
    vol_beads_2 = 57.0
    vol_elution_buffer_2 = 55.0
    vol_elution_final_2 = 20.0

    # labware and modules
    elution_plate = ctx.load_labware('biorad_96_wellplate_350ul', '1',
                                     'PCR plate')
    barcode_plate = ctx.load_labware('biorad_96_wellplate_350ul', '2',
                                     'barcode plate')
    magdeck = ctx.load_module('magnetic module gen2', '4')
    mag_plate = magdeck.load_labware('biorad_96_wellplate_350ul')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5')
    tipracks_300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['3', '6', '7', '8', '9', '10']]
    tipracks_20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '11')]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks_20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks_300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    def pick_up(pip, loc=None):
        if not loc:
            if tip_log[pip]['count'] == tip_log[pip]['max']:
                ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks \
before resuming.')
                pip.reset_tipracks()
                tip_log[pip]['count'] = 0
            loc = tip_log[pip]['tips'][tip_log[pip]['count']]
            tip_log[pip]['count'] += 1
        pip.pick_up_tip(loc)
        return loc

    # samples and reagents
    num_cols = math.ceil(num_samples/8)
    mag_samples = mag_plate.rows()[0][:num_cols]
    elution_samples = elution_plate.rows()[0][:num_cols]
    barcodes = barcode_plate.rows()[0][:num_cols]

    beads = reservoir.wells()[0]
    ethanol = reservoir.wells()[1:9]
    elution_buffer = reservoir.wells()[9]
    pcr_mm = reservoir.wells()[10]
    waste = ctx.loaded_labwares[12].wells()[0].top()

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    folder_path = '/data/tip_track'
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

    def remove_supernatant(pip, vol, z_offset=z_offset_supernatant,
                           wells=mag_samples, parking_spots=None,
                           dispense_liquid=True):
        if not parking_spots:
            parking_spots = [None for _ in range(num_cols)]

        pip.flow_rate.aspirate /= 5
        for m, spot in zip(wells, parking_spots):
            if not pip.has_tip:
                pick_up(pip, spot)
            asp_loc = m.bottom(0.5)
            pip.move_to(m.center())
            pip.aspirate(vol, asp_loc)
            slow_withdraw(pip, m)
            if dispense_liquid:
                pip.dispense(vol, waste)
                pip.blow_out(waste)
                pip.air_gap(1)
            pip.drop_tip()
        pip.flow_rate.aspirate *= 5

    def slow_withdraw(pip, well):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def bind(vol_beads, vol_initial, beads=beads):
        magdeck.disengage()

        parking_set = []
        if not m300.has_tip:
            tip = pick_up(m300)
        else:
            tip = m300._last_tip_picked_up_from
        parking_set.append(tip)
        for _ in range(20):
            m300.aspirate(200, beads.bottom(2))
            m300.dispense(200, beads.bottom(10))

        for s in mag_samples:
            if not m300.has_tip:
                tip = pick_up(m300)
                parking_set.append(tip)
            m300.aspirate(vol_beads, beads)
            slow_withdraw(m300, beads)
            m300.dispense(vol_beads, s)
            m300.mix(6, vol_beads*0.8, s)
            slow_withdraw(m300, s)
            m300.drop_tip(tip)

        ctx.delay(minutes=time_minutes_incubation_binding, msg=f'Incubating \
{time_minutes_mag_wash} min')
        magdeck.engage(engage_height)
        ctx.delay(minutes=time_minutes_mag_binding, msg=f'Incubating \
{time_minutes_mag_binding} min')

        remove_supernatant(m300, vol_beads+vol_initial,
                           parking_spots=parking_set)

    def wash(wash_set, vol_wash=190, air_dry=False):
        magdeck.disengage()
        pick_up(m300)
        for i, s in enumerate(mag_samples):
            source = wash_set[i//6]
            m300.aspirate(vol_wash, source)
            slow_withdraw(m300, source)
            m300.dispense(vol_wash, s.top(-1))

        magdeck.engage(engage_height)
        ctx.delay(minutes=time_minutes_mag_wash)

        remove_supernatant(m300, vol_wash)

        if air_dry:
            ctx.delay(minutes=time_minutes_airdry_wash,
                      msg=f'Airdrying {time_minutes_airdry_wash} min')

    def elute(vol_elution_buffer, vol_elution_final):
        magdeck.disengage()

        for i, s in enumerate(mag_samples):
            side = 1 if mag_samples.index(s) % 2 == 0 else -1
            bead_loc = s.bottom().move(Point(
                x=side*s.diameter/2*x_offset_beads_ratio, z=z_offset_beads))
            pick_up(m300)
            m300.aspirate(vol_elution_buffer, elution_buffer)
            slow_withdraw(m300, elution_buffer)
            m300.dispense(vol_elution_buffer, s)
            for _ in range(6):  # mix
                m300.aspirate(vol_elution_final, s.bottom(1))
                m300.dispense(vol_elution_final, bead_loc)
            slow_withdraw(m300, s)
            m300.drop_tip()

        ctx.delay(minutes=time_minutes_mag_elution, msg=f'Incubating \
{time_minutes_mag_elution} min')
        magdeck.engage(engage_height)
        ctx.delay(minutes=time_minutes_incubation_elution, msg=f'Incubating \
{time_minutes_incubation_elution} min')

        # transfer to elution plate
        for s, e in zip(mag_samples, elution_samples):
            pick_up(m300)
            m300.flow_rate.aspirate /= 5
            m300.aspirate(vol_elution_final, s)
            m300.flow_rate.aspirate *= 5
            slow_withdraw(m300, s)
            m300.dispense(vol_elution_final, e.bottom(1))
            slow_withdraw(m300, e)
            m300.drop_tip()

    """ Cleanup 1 """
    bind(vol_beads_1, vol_initial_1)
    wash(ethanol[0:2])
    wash(ethanol[2:4], air_dry=True)
    elute(vol_elution_buffer_1, vol_elution_final_1)

    # add mastermix
    pick_up(m300)
    for s in elution_samples:
        m300.aspirate(vol_pcr_mm, pcr_mm)
        slow_withdraw(m300, pcr_mm)
        m300.dispense(vol_pcr_mm, s.top(-1))

    # elution to barcodes
    for s, b in zip(elution_samples, barcodes):
        pick_up(m20)
        m20.aspirate(5, s)
        slow_withdraw(m20, s)
        m20.dispense(5, b)
        slow_withdraw(m20, b)
        m20.drop_tip()

    ctx.pause('Remove plates and perform Index/Barcode PCR. Place PCR plate \
back on magnetic module after completed PCR. Place fresh plate 2 for final \
elution.')

    """ Cleanup 2 """
    bind(vol_beads_2, vol_initial_2)
    wash(ethanol[4:6])
    wash(ethanol[6:8], air_dry=True)
    elution_samples = [elution_plate.wells()[0]]*num_cols  # pool
    elute(vol_elution_buffer_2, vol_elution_final_2)

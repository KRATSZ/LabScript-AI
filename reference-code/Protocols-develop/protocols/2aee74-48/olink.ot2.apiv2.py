from opentrons.types import Point
import json
import os

metadata = {
    'protocolName': 'Olink Target 48 Part 1/3: Incubation',
    'author': 'Nick <ndiehl@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    p300_mount, m20_mount = get_values(  # noqa: F821
        'p300_mount', 'm20_mount')

    inc_mix = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '8',
        'tuberack for incubation mix (A1)').wells()[0]
    inc_plate = ctx.load_labware('generic_96_aluminumblock_350ul', '10',
                                 'incubation plate')
    strips = ctx.load_labware('genericstrips_96_wellplate_200ul', '11',
                              'sample and dilution strips')
    tipracks300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '9')]
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['1']]
    stationary_rack = ctx.load_labware('opentrons_96_filtertiprack_20ul', '4')

    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tipracks300)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20)

    inc_strip = strips.columns()[0]
    dilution_sample = strips.rows()[0][1:3]
    sample_strip = strips.rows()[0][3]
    control_strip = strips.rows()[0][4]
    num_cols = 6
    tip_track = True
    tip_count = 0

    folder_path = '/data/olink'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'm20' in data:
                    tip_count = data['m20']

    def m20_pick_up():
        nonlocal tip_count
        if tip_count == 12:
            ctx.pause('\n\n\n\n\nPlease refill 20ul filter tiprack on slot 6 \
before resuming.\n\n\n\n\n')
            tip_count = 0
        m20.pick_up_tip(stationary_rack.rows()[0][tip_count])
        tip_count += 1

    side = 1

    def drop(pip):
        nonlocal side
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=30*side))
        pip.drop_tip(drop_loc)
        side = -1*side

    p300.default_speed = 100
    m20.default_speed = 100

    ctx.home()
    ctx.pause(f'P20 multi transfer will begin at column {tip_count+1} of \
tiprack on slot 6.')

    # transfer incubation mix to strip with reverse pipetting
    p300.pick_up_tip()
    p300.aspirate(5, inc_mix)
    for well in inc_strip:
        p300.aspirate(23, inc_mix)
        p300.dispense(23, well)
    p300.dispense(p300.current_volume, inc_mix)
    drop(p300)

    # transfer from strip to plate
    m20_pick_up()
    m20.aspirate(5, inc_strip[0])
    for col in inc_plate.rows()[0][:num_cols]:
        m20.aspirate(3, inc_strip[0])
        m20.dispense(3, col)
    # m20.dispense(m20.current_volume, strip[0])
    drop(m20)

    # transfer samples and controls
    for s, d in zip(dilution_sample, inc_plate.rows()[0][:2]):
        m20.pick_up_tip()
        m20.transfer(1, s, d, new_tip='never')
        m20.blow_out(d.bottom(1))
        drop(m20)

    for d in inc_plate.rows()[0][2:5]:
        m20.pick_up_tip()
        m20.transfer(1, sample_strip, d, new_tip='never')
        m20.blow_out(d.bottom(1))
        drop(m20)

    m20.pick_up_tip()
    m20.transfer(1, control_strip, inc_plate.rows()[0][5], new_tip='never')
    m20.blow_out(d.bottom(1))
    drop(m20)

    ctx.comment('\n\n\n\n\nSeal the plate with an adhesive plastic film, spin \
at 400 x g, 1 min at room temperature. Incubate overnight at +4°C.\n\n\n\n\n')

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {'m20': tip_count}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

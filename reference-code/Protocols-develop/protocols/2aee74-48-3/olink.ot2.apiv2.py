from opentrons.types import Point
import json
import os

metadata = {
    'protocolName': 'Olink Target 96 Part 3/3: Detection',
    'author': 'Nick <ndiehl@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    p300_mount, m20_mount = get_values(  # noqa: F821
        'p300_mount', 'm20_mount')

    det_mix = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '9',
        'tuberack for detection mix (A3)').wells_by_name()['A3']
    inc_plate = ctx.load_labware('generic_96_aluminumblock_350ul', '5',
                                 'incubation plate')
    sample_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                    '3', 'sample plate')
    strip = ctx.load_labware(
        'genericstrips_96_wellplate_200ul', '6',
        'strip for distribution (column 7)').columns_by_name()['7']
    primer_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                    '1', 'primer plate')
    fluidigm = ctx.load_labware('fluidigm_96_wellplate_48x50ul_48x50ul', '2',
                                'Fluidigm 96.96 Dynamic Array')
    tipracks300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                  for slot in ['7', '8', '11']]
    stationary_rack = ctx.load_labware('opentrons_96_filtertiprack_20ul', '4')

    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tipracks300)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20)
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
    ctx.comment('\n\n\n\n\nPrepare and prime a 96.96 Dynamic ArrayTM \
Integrated Fluidic Circuit (IFC) according to the manufacturer’s instructions.\
 Briefly,inject one control line fluid syringe into each accumulator on the \
chip, and then prime the chip on the IFC Controller for approximately 20 \
minutes.\n\n\n\n\n')
    ctx.comment('\n\n\n\n\nThaw the Primer Plate, vortex and spin \
briefly.\n\n\n\n\n')
    ctx.pause(f'\n\n\n\n\nP20 multi transfer will begin at column \
{tip_count+1} of tiprack on slot 6.\n\n\n\n\n')

    # transfer detection mix to strip with reverse pipetting
    p300.pick_up_tip()
    p300.aspirate(5, det_mix)
    for well in strip:
        p300.aspirate(46, det_mix)
        p300.dispense(46, well)
    p300.dispense(p300.current_volume, det_mix)
    drop(p300)

    # transfer from strip to plate
    m20_pick_up()
    m20.aspirate(5, strip[0])
    for col in sample_plate.rows()[0][:num_cols]:
        m20.aspirate(7.2, strip[0])
        m20.dispense(7.2, col)
    drop(m20)

    # transfer samples
    for s, d in zip(inc_plate.rows()[0][:num_cols],
                    sample_plate.rows()[0][:num_cols]):
        m20.pick_up_tip()
        m20.transfer(2.8, s, d, new_tip='never')
        drop(m20)

    ctx.pause('\n\n\n\n\nSeal the plate with an adhesive plastic film, vortex \
and spin at 400 x g, 1 min at room temperature.\n\n\n\n\n')

    # transfer primer and sample to fluidigm plate
    sample_destinations = [
        well for row in fluidigm.rows()[:2] for well in row[3:]]
    primer_destinations = [
        well for row in fluidigm.rows()[:2] for well in row[:3]]

    for source, dest in zip(
            primer_plate.rows()[0][:num_cols] + sample_plate.rows()[0][
                :num_cols],
            primer_destinations + sample_destinations[:num_cols]):
        m20.pick_up_tip()
        m20.aspirate(7, source.bottom(0.5))
        m20.dispense(5, dest.bottom(1))
        drop(m20)

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {'m20': tip_count}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

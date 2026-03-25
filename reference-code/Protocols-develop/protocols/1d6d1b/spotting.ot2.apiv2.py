import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Slide Array Spotting',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [num_plates, num_samples, num_slides, array_pattern, blot_dwell_time,
     wash_scheme, slow_speed_up, slow_speed_down, sample_height,
     slide_dwell_time, m300_mount, tip_type] = get_values(  # noqa: F821
        'num_plates', 'num_samples', 'num_slides', 'array_pattern',
        'blot_dwell_time', 'wash_scheme', 'slow_speed_up', 'slow_speed_down',
        'sample_height', 'slide_dwell_time', 'm300_mount', 'tip_type')

    sample_plates = [
        ctx.load_labware('abgene_96_wellplate_200ul', slot,
                         'sample plate ' + str(i+1))
        for i, slot in enumerate(['1', '3', '4', '6'][:num_plates])]
    slides_mount = ctx.load_labware(
        'gracebiolabsflexwell', '2', 'slides')
    pin_wash_res = ctx.load_labware('axygen_4_reservoir_73000ul', '11',
                                    'pin wash reservoir')
    blot_res = ctx.load_labware('customblotpaper_1_reservoir_870000ul', '8',
                                'blot paper reservoir')
    tiprack300 = ctx.load_labware(tip_type, '10')
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[tiprack300])

    # setup samples
    num_cols = math.ceil(num_samples/8)
    if array_pattern == 1:
        y_space = 9/num_plates
        slide_sets = [
            [well.top().move(Point(y=move*-1*y_space)) for set in [
                slides_mount.rows()[0][i*num_cols:(i+1)*num_cols]
             for i in range(num_slides)] for well in set]
            for move in range(num_plates)]
    elif array_pattern == 2:
        slide_sets = [
            [well for i in range(num_slides)
             for col in slides_mount.columns()[i*8+3*p:i*8+3+3*p]
             for well in col[:2]]
            for p in range(num_plates)]
    else:
        slide_sets = [
            [well for s in range(num_slides)
             for row in slides_mount.rows()[p:4:2]
             for well in row[s*8+(p % 2):s*8+8:2]]
            for p in range(num_plates)]

    sample_sets = [plate.rows()[0][:num_cols] for plate in sample_plates]

    # wash and blot
    blot_locs = [
        blot_res.wells()[0].bottom().move(Point(x=shift, z=-1))
        for shift in [-30, -10, 10, 30]]

    def wash_blot():
        for wash, blot in zip(pin_wash_res.wells(), blot_locs):
            movement_locs = [
                wash.center().move(Point(z=side*5)) for side in [-1, 1]]
            m300.move_to(wash.center())
            ctx.max_speeds['X'] = 100
            if wash_scheme == 'vertical movement':
                for _ in range(5):
                    for m in movement_locs:
                        m300.move_to(m)
            else:
                ctx.delay(seconds=5)
            m300.move_to(wash.center())
            del ctx.max_speeds['X']

            ctx.max_speeds['A'] = slow_speed_down
            ctx.max_speeds['Z'] = slow_speed_down
            m300.move_to(blot.move(Point(z=10)))
            m300.move_to(blot)
            ctx.delay(seconds=blot_dwell_time)

            del ctx.max_speeds['A']
            del ctx.max_speeds['Z']

    m300.pick_up_tip()
    ctx.comment('"Ghost" aspirations to ensure all labware is calibrated.')
    for plate in sample_plates + [slides_mount, pin_wash_res, blot_res]:
        m300.aspirate(1, plate.wells()[0].top(5))
        m300.dispense(1, plate.wells()[0].top(5))

    wash_blot()

    for sample_set, slide_set in zip(sample_sets, slide_sets):
        for sample, slide_spot in zip(sample_set, slide_set):

            print(slide_spot.point)
            m300.default_speed = 40
            for _ in range(3):
                m300.move_to(sample.top(1))
                m300.move_to(sample.bottom(sample_height))
            m300.default_speed = 400
            m300.move_to(sample.top(2))
            m300.move_to(slide_spot.move(Point(z=5)))
            m300.default_speed = 40
            m300.move_to(slide_spot)
            ctx.delay(seconds=slide_dwell_time)
            m300.default_speed = 400
            m300.move_to(slide_spot.move(Point(z=5)))
            wash_blot()

    m300.move_to(tiprack300.wells()[0].top())
    ctx.pause('Protocol complete. Continue descending 20mm before dropping \
tip?\nIf yes, click \'Resume\'.\nIf no, cancel run, and remove tips/pins \
manually.')
    m300.drop_tip(tiprack300.wells()[0].top().move(Point(z=-20)))

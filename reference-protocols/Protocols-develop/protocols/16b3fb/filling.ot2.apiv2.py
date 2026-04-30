from opentrons.types import Point
import math

metadata = {
    'protocolName': 'Custom Bulb Filling - 150ul',
    'apiLevel': '2.13',
    'author': 'Nick <ndiehl@opentrons.com>'
}

num_bulbs = 432
num_racks = math.ceil(num_bulbs/48)
vol_preairgap = 0


def run(ctx):

    [vol_bulb] = get_values(  # noqa: F821
        'vol_bulb')

    buffer = ctx.load_labware('nest_1_reservoir_195ml', '10').wells()[0]
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '11')]
    bulb_racks = [
        ctx.load_labware('ag_48_tuberack_150ul', slot,
                         f'bulb rack {slot}')
        for slot in range(1, 1+num_racks)]

    p1000 = ctx.load_instrument('p1000_single_gen2', 'right',
                                tip_racks=tiprack1000)

    def slow_withdraw(pip, well, delay_s=1.0, z=0):
        pip.default_speed /= 10
        if delay_s > 0:
            ctx.delay(seconds=delay_s)
        pip.move_to(well.top().move(Point(z=z)))
        pip.default_speed *= 10

    def custom_touch(pip, well, z=-1, modulator=0.9):
        radius = well.diameter/2 if well.diameter else well.length/2
        magnitude = radius * modulator
        pip.move_to(well.top().move(Point(x=magnitude, z=z)))

    bulbs = [well for rack in bulb_racks for well in rack.wells()][:num_bulbs]

    # buffer_liquid = ctx.define_liquid(
    #     name='buffer',
    #     description='buffer',
    #     display_color='#0000FF')
    # buffer.load_liquid(buffer_liquid, 190000)

    # create distribution sets
    num_bulbs_per_asp = math.floor(
        p1000.tip_racks[0].wells()[0].max_volume/(vol_bulb+vol_preairgap))
    num_distribution_sets = math.ceil(num_bulbs/num_bulbs_per_asp)
    distribution_sets = [
        bulbs[i*num_bulbs_per_asp:(i+1)*num_bulbs_per_asp]
        if i < num_distribution_sets - 1
        else bulbs[i*num_bulbs_per_asp:]
        for i in range(num_distribution_sets)]

    p1000.pick_up_tip()
    for d_set in distribution_sets:
        p1000.blow_out(buffer.top())
        if vol_preairgap > 0:
            for _ in range(len(d_set)):
                p1000.aspirate(vol_preairgap, buffer.top())
                p1000.aspirate(vol_bulb, buffer.bottom(2))
                slow_withdraw(p1000, buffer)
        else:
            p1000.aspirate(vol_bulb*len(d_set), buffer.bottom(2))
            slow_withdraw(p1000, buffer)
        for d in d_set:
            p1000.dispense(vol_bulb+vol_preairgap, d.top(-1))
            custom_touch(p1000, d)
    p1000.drop_tip()

import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Nextera DNA Flex NGS Library Prep: Post Tagmentation \
Cleanup',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}


def run(ctx):

    [number_of_samples_to_process, p300_type,
        p300_mount] = get_values(  # noqa: F821
            'number_of_samples_to_process', 'p300_type', 'p300_mount')

    # load labware and modules
    magdeck = ctx.load_module('magdeck', '1')
    mag_plate = magdeck.load_labware(
        'biorad_96_wellplate_200ul_pcr', '1')
    res12 = ctx.load_labware(
        'usascientific_12_reservoir_22ml', '3', 'reagent reservoir')

    twb = [chan.bottom(5) for chan in res12.wells()[:2]]
    liquid_waste = [chan.top() for chan in res12.wells()[10:]]

    # check:
    if number_of_samples_to_process > 96 or number_of_samples_to_process < 1:
        raise Exception('Invalid number of samples to process (must be between \
1 and 96).')

    num_cols = math.ceil(number_of_samples_to_process/8)
    num_300_racks = math.ceil((num_cols*6)/12)
    slots300 = [str(slot) for slot in range(5, 5+num_300_racks)]
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in slots300
    ]

    # pipettes
    pip300 = ctx.load_instrument(p300_type, p300_mount, tip_racks=tips300)
    if p300_type == 'p300_multi':
        samples300 = mag_plate.rows()[0][:num_cols]
    else:
        samples300 = mag_plate.wells()[:number_of_samples_to_process]
    pip300.flow_rate.aspirate = 75
    pip300.flow_rate.dispense = 90

    magdeck.engage(height=18)
    ctx.delay(minutes=3, msg='Incubating beads on magnet for 3 minutes.')

    # remove and discard supernatant
    for s in samples300:
        pip300.pick_up_tip()
        pip300.transfer(65, s.bottom(1), liquid_waste[0], new_tip='never')
        pip300.blow_out()
        pip300.drop_tip()

    # TWB washes 3x
    count = 0
    total_twb = 96*3
    for wash in range(3):
        magdeck.disengage()

        # resuspend beads in TWB
        for i, s in enumerate(samples300):
            ind = (count*len(twb))//total_twb
            count += 1

            side = i % 2 if p300_type == 'multi' else math.floor(i/8) % 2
            angle = 1 if side == 0 else -1
            disp_loc = s.bottom().move(
                Point(x=0.85*(s.diameter/2)*angle, y=0, z=3))
            pip300.pick_up_tip()
            pip300.aspirate(100, twb[ind])
            pip300.move_to(s.center())
            pip300.dispense(100, disp_loc)
            pip300.mix(10, 80, disp_loc)
            pip300.drop_tip()

        magdeck.engage(height=18)

        if wash < 2:
            ctx.delay(
                minutes=3, msg='Incubating beads on magnet for 3 minutes')
            # remove and discard supernatant
            for s in samples300:
                pip300.pick_up_tip()
                pip300.transfer(
                    120, s.bottom(1), liquid_waste[wash], new_tip='never')
                pip300.blow_out()
                pip300.drop_tip()

    ctx.comment('Seal the plate, and keep on the magnetic module. The TWB \
remains in the wells to prevent overdrying of the beads')

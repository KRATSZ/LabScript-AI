import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Nextera DNA Flex NGS Library Prep: Cleanup Libraries',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}


def run(ctx):
    [number_of_samples_to_process, p50_type, p50_mount, p300_type,
        p300_mount] = get_values(  # noqa: F821
            'number_of_samples_to_process', 'p50_type', 'p50_mount',
            'p300_type', 'p300_mount')

    # load labware and modules
    magdeck = ctx.load_module('magdeck', '1')
    mag_plate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr')
    new_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr', '2', 'new PCR plate')
    res12 = ctx.load_labware(
        'usascientific_12_reservoir_22ml', '3', 'reagent reservoir')
    slots50 = [str(slot) for slot in range(4, 8)]
    tips50 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in slots50
    ]
    slots300 = [str(slot) for slot in range(8, 12)]
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in slots300
    ]

    # reagents
    spb = res12.wells()[0]
    nuc_free_water = res12.wells()[1].bottom(5)
    rsb = res12.wells()[2].bottom(5)
    etoh = [chan.bottom(5) for chan in res12.wells()[3:5]]
    liquid_waste = [chan.top() for chan in res12.wells()[9:12]]

    # check:
    if p50_mount == p300_mount:
        raise Exception('Input different mounts for P50 and P300 multi-channel \
pipettes')
    if number_of_samples_to_process > 96 or number_of_samples_to_process < 1:
        raise Exception('Invalid number of samples to process (must be between \
1 and 96).')

    # pipettes
    num_cols = math.ceil(number_of_samples_to_process/8)

    pip50 = ctx.load_instrument(p50_type, p50_mount, tip_racks=tips50)
    pip300 = ctx.load_instrument(p300_type, p300_mount, tip_racks=tips300)
    if p50_type == 'p50_multi':
        [mag_samples50, new_samples50] = [
            plate.rows()[0][:num_cols] for plate in [mag_plate, new_plate]]
    else:
        [mag_samples50, new_samples50] = [
            plate.wells()[:number_of_samples_to_process]
            for plate in [mag_plate, new_plate]
        ]
    if p300_type == 'p300_multi':
        [mag_samples300, new_samples300] = [
            plate.rows()[0][:num_cols] for plate in [mag_plate, new_plate]]
    else:
        [mag_samples300, new_samples300] = [
            plate.wells()[:number_of_samples_to_process]
            for plate in [mag_plate, new_plate]
        ]

    def slot_parse(slots):
        slot_str = ''
        for i, s in enumerate(slots):
            if i < len(slots)-1:
                slot_str += s + ', '
            else:
                slot_str += s
        return slot_str

    slot_str50 = slot_parse(slots50)
    slot_str300 = slot_parse(slots300)

    tip50_max = len(tips50)*12 if p50_type == 'multi' else len(tips50)*96
    tip300_max = len(tips300)*12 if p300_type == 'multi' else len(tips300)*96
    tip50_count = 0
    tip300_count = 0

    def pick_up(pip):
        nonlocal tip50_count
        nonlocal tip300_count

        if pip == 'pip50':
            if tip50_count == tip50_max:
                ctx.pause('Replace 300ul tipracks in slots \
' + slot_str50 + ' before resuming.')
                pip50.reset_tipracks()
                tip50_count = 0
            pip50.pick_up_tip()
            tip50_count += 1
        else:
            if tip300_count == tip300_max:
                ctx.pause('Replace 300ul tipracks in slots \
' + slot_str300 + ' before resuming.')
                pip300.reset_tipracks()
                tip300_count = 0
            pip300.pick_up_tip()
            tip300_count += 1

    lng = 71.88
    wid = 8.33
    h = 25

    def track_bead_height(pip, vol):
        nonlocal h
        dv = vol if pip == 'single' else vol*8
        dh = dv/(lng*wid)
        h = h - dh if h - dh > 5 else 5
        return h

    if magdeck.status == 'disengaged':
        magdeck.engage(height=18)
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes.')

    # transfer supernatant from mag plate to new plate
    for source, dest in zip(mag_samples50, new_samples50):
        pick_up('pip50')
        pip50.transfer(45, source.bottom(0.5), dest, new_tip='never')
        pip50.blow_out()
        pip50.drop_tip()

    ctx.pause('Vortex beads and add to channel 1 of the 12-channel reservoir \
in slot 3.')

    for s in new_samples300:
        pick_up('pip300')
        pip300.transfer(40, nuc_free_water, s.top(), new_tip='never')
        pip300.blow_out(s.top())
        h = track_bead_height(p300_type, 45)
        pip300.transfer(45, spb.bottom(h), s, new_tip='never')
        pip300.mix(10, 100, s)
        pip300.blow_out(s.top())
        pip300.drop_tip()

    ctx.pause('Seal PCR plate in slot 2 and incubate at room \
temperature for 5 minutes. Then discard the original plate on the magnetic \
stand and place the plate from slot 2 on the engaged magnetic deck. Place a \
new PCR plate in slot 2, and resume.')

    if p300_type == 'multi':
        pick_up('pip300')
        pip300.mix(20, 200, spb.bottom(5))
        pip300.blow_out(spb.top())
        pip300.drop_tip()
    pick_up('pip50')
    for s in new_samples50:
        h = track_bead_height(p50_type, 15)
        pip50.transfer(15, spb.bottom(h), s.top(), new_tip='never')
        pip50.blow_out(s.top())
    pip50.drop_tip()
    ctx.delay(minutes=3, msg='Incubating beads on magnet for 3 more minutes.')

    # transfer supernatant to corresponding well of new PCR plate
    for source, dest in zip(mag_samples300, new_samples300):
        pick_up('pip300')
        pip300.transfer(125, source.bottom(1), dest, new_tip='never')
        pip300.mix(10, 100, dest)
        pip300.blow_out(dest.top())
        pip300.drop_tip()
    magdeck.disengage()

    ctx.pause('Incubate for 5 minutes at room temperature before placing \
the PCR plate from slot 2 on the magnetic module in slot 1. Discard the \
original plate occupying the magnetic module. Place another fresh PCR plate \
on slot 2 for the final elution.')

    magdeck.engage(height=18)
    ctx.delay(minutes=5, msg='Incubating beads on magnet for 5 minutes.')

    # remove supernatant
    for s in mag_samples300:
        pick_up('pip300')
        pip300.transfer(150, s.bottom(1), liquid_waste[2], new_tip='never')
        pip300.drop_tip()

    # 2x EtOH wash
    for wash in range(2):
        pick_up('pip300')
        for i, s in enumerate(mag_samples300):
            pip300.transfer(190, etoh[wash], s.top(), new_tip='never')
            pip300.blow_out()
        for s in mag_samples300:
            if not pip300.hw_pipette['has_tip']:
                pick_up('pip300')
            pip300.transfer(
                200, s.bottom(1), liquid_waste[wash], new_tip='never')
            pip300.drop_tip()

    # remove residual supernatant
    for s in mag_samples50:
        pick_up('pip50')
        pip50.aspirate(20, s.bottom(0.3))
        pip50.drop_tip()

    # airdry for 5 minutes
    ctx.delay(minutes=5, msg='Airdrying for 5 minutes.')
    magdeck.disengage()

    # add RSB
    for i, s in enumerate(mag_samples50):
        side = i % 2 if p50_type == 'multi' else math.floor(i/8) % 2
        angle = 1 if side == 0 else -1
        disp_loc = s.bottom().move(
            Point(x=0.85*(s.diameter/2)*angle, y=0, z=3))

        pick_up('pip50')
        pip50.aspirate(32, rsb)
        pip50.move_to(s.center())
        pip50.dispense(32, disp_loc)
        pip50.mix(10, 20, disp_loc)
        pip50.blow_out(s.top())
        pip50.drop_tip()

    ctx.delay(minutes=2, msg='Incubating off then on magnet (2 mins each)')
    magdeck.engage(height=18)
    ctx.delay(minutes=2)

    # transfer elution to new plate
    for source, dest in zip(mag_samples50, new_samples50):
        pick_up('pip50')
        pip50.transfer(30, source.bottom(1), dest, new_tip='never')
        pip50.blow_out()
        pip50.drop_tip()

    magdeck.disengage()

    ctx.comment('If you are stopping, seal the plate with Microseal B \
adhesive or Microseal F foil seal, and store at -25°C to -15°C for up to 30 \
days.')

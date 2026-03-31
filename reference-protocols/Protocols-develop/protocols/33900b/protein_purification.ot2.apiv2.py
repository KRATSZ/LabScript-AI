from opentrons.types import Point
import math

# metadata
metadata = {
    'protocolName': 'Promega MagneHis™ Protein Purification System',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    p300_mount, sample_num = get_values(  # noqa: F821
        'p300_mount', 'sample_num')
    # p300_mount, sample_num = ['right', 96]

    # check
    if sample_num < 1 or sample_num > 96:
        raise Exception('Invalid number of samples (must be 1-96).')

    # load modules and labware
    magdeck = ctx.load_module('magdeck', '1')
    magblock = magdeck.load_labware('greinerbioone_96_wellplate_2ml_deep')
    res12 = ctx.load_labware(
        'agilent_12_reservoir_21ml', '2', '12-channel reservoir')
    res3 = ctx.load_labware(
        'agilent_3_reservoir_95ml', '3', '3-channel reservoir')
    plate = ctx.load_labware(
        'greinerbioone_96_wellplate_200ul', '4', 'PCR plate for elution')
    tipracks300 = [
        ctx.load_labware(
            'opentrons_96_tiprack_300ul', str(slot), '300µl tiprack')
        for slot in range(5, 12)
    ]

    # pipettes
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=tipracks300)

    # samples and reagent setup
    mag_samples = magblock.rows()[0][:math.ceil(sample_num/8)]
    elution_samples = plate.rows()[0][:math.ceil(sample_num/8)]
    cell_lysis = res12.wells()[0]
    benzonase_lysozyme = res12.wells()[1]
    nacl = res12.wells()[2]
    magnehis_part = res12.wells()[3]
    magnehis_eb = res12.wells()[4]
    magnehis_wash = res3.wells()[0]

    tip_count = 0
    tip_max = 12*len(tipracks300)

    def pickup():
        nonlocal tip_count
        if tip_count == tip_max:
            ctx.pause('Replace 300µl tipracks in slots 5-11 before resuming.')
            tip_count = 0
            m300.reset_tipracks()
        tip_count += 1
        m300.pick_up_tip()

    # transfer FastBreak™ Cell Lysis Reagent, Benzonase/Lysozyme, NaCl and mix
    for reagent in [cell_lysis, benzonase_lysozyme, nacl]:
        for s in mag_samples:
            pickup()
            m300.transfer(150, reagent, s, new_tip='never', mix_after=(3, 250))
            m300.blow_out(s.top(-2))
            m300.air_gap(30)
            m300.drop_tip()

    # resuspent MagneHis particles stock and transfer to mag_samples
    pickup()
    for _ in range(5):
        m300.aspirate(250, magnehis_part.bottom(1))
        m300.dispense(250, magnehis_part.bottom(20))
    m300.blow_out(magnehis_part.top(-2))
    for s in mag_samples:
        if not m300.hw_pipette['has_tip']:
            pickup()
        m300.transfer(
            50,
            magnehis_part,
            s,
            new_tip='never',
            air_gap=30,
            mix_after=(3, 250)
        )
    m300.drop_tip()

    ctx.delay(minutes=10, msg='Incubating off magnet for 10 minutes at RT.')
    magdeck.engage(height=14.94)
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes at RT.')

    # remove supernatant
    for i, s in enumerate(mag_samples):
        pickup()
        m300.transfer(
            1500, s, res12.wells()[6:8][i//6], air_gap=30, new_tip='never')
        m300.drop_tip()

    magdeck.disengage()

    # resuspend in wash buffer
    def wash(waste_set):
        for i, s in enumerate(mag_samples):
            side = 1 if i % 2 == 0 else -1
            loc = s.bottom().move(
                Point(x=side*s.geometry._width/2*0.95, y=0, z=3))
            pickup()
            m300.aspirate(300, magnehis_wash)
            m300.move_to(s.center())
            m300.dispense(300, loc)
            m300.mix(3, 150, loc)
            m300.blow_out(s.top(-2))
            m300.air_gap(30)
            m300.drop_tip()

        magdeck.engage(height=14.94)
        ctx.delay(minutes=2, msg='Incubating on magnet for 2 minutes at RT.')

        # remove supernatant
        for i, s in enumerate(mag_samples):
            pickup()
            m300.transfer(300, s, waste_set[i//6], air_gap=30, new_tip='never')
            m300.drop_tip()

        magdeck.disengage()

    wash([chan.top() for chan in res3.wells()[1:]])
    wash([chan.top() for chan in res12.wells()[8:10]])

    # resuspend in elution buffer
    for i, s in enumerate(mag_samples):
        side = 1 if i % 2 == 0 else -1
        loc = s.bottom().move(
            Point(x=side*s.geometry._width/2*0.95, y=0, z=2))
        pickup()
        m300.aspirate(150, magnehis_eb)
        m300.move_to(s.center())
        m300.dispense(150, loc)
        m300.mix(3, 120, s.bottom(1))
        m300.blow_out(s.top(-2))
        m300.air_gap(30)
        m300.drop_tip()

    magdeck.engage(height=14.94)
    ctx.delay(minutes=2, msg='Incubating on magnet for 2 minutes at RT.')

    # transfer elution to new plate
    for s, d in zip(mag_samples, elution_samples):
        pickup()
        m300.transfer(150, s, d.bottom(2), air_gap=30, new_tip='never')
        m300.blow_out(s.top(-2))
        m300.air_gap(30)
        m300.drop_tip()

    magdeck.disengage()

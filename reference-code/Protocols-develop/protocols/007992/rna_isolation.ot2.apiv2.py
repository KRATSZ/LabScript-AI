import math

metadata = {
    'protocolName': 'Viral RNA Isolation (Magnetic Beads)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(ctx):

    num_samples, m300_mount, p20_mount = get_values(  # noqa:F821
        'num_samples', 'm300_mount', 'p20_mount')

    # load labware
    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()
    isolation_plate = magdeck.load_labware(
        'usascientific_96_wellplate_2.4ml_deep', 'isolation plate')
    reagent_reservoir = ctx.load_labware(
        'usascientific_12_reservoir_22ml', '2', 'reagent reservoir')
    tempdeck = ctx.load_module('temperature module gen2', '3')
    tempdeck.set_temperature(4)
    elution_plate = tempdeck.load_labware('coleparmer_384_wellplate_50ul',
                                          'elution plate')
    tipracks200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                   for slot in ['4', '5', '7', '8', '10', '11']]
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                  for slot in ['6', '9']]

    # load pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks200)
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tipracks20)

    # setup samples and reagents
    num_cols = math.ceil(num_samples/8)
    mag_samples = isolation_plate.rows()[0][:num_cols]
    mag_samples_single = [
        well for row in isolation_plate.rows() for well in row][:num_samples]

    etoh = reagent_reservoir.wells()[:2]
    magbeads = reagent_reservoir.wells()[2]
    wash1 = reagent_reservoir.wells()[3:6]
    wash2 = reagent_reservoir.wells()[6:9]
    elution_buffer = reagent_reservoir.wells()[9]
    neg_control = reagent_reservoir.wells()[10]
    pos_control = reagent_reservoir.wells()[11]
    trash = ctx.loaded_labwares[12].wells()[0].top()

    # remove supernatant
    def remove_supernatant(vol, disengage_after=True):
        if not magdeck.status == 'engaged':
            magdeck.engage(height=3.4)
        for m in mag_samples:
            m300.pick_up_tip()
            m300.transfer(vol, m.bottom(1), trash,
                          new_tip='never')
            m300.drop_tip()
        if disengage_after:
            magdeck.disengage()

    # transfer EtOH
    m300.pick_up_tip()
    for i, m in enumerate(mag_samples):
        m300.transfer(300, etoh[i//6], m.bottom(45), new_tip='never')
    m300.drop_tip()

    # mix and transfer magnetic beads
    for m in mag_samples:
        m300.transfer(50, magbeads, m.bottom(0.5), mix_before=(10, 50),
                      mix_after=(5, 175))

    ctx.delay(minutes=5, msg='Incubating off magnet for 5 minutes')
    magdeck.engage(height=3.4)
    ctx.delay(minutes=2, msg='Incubating on magnet for 2 minutes')

    remove_supernatant(850)

    for i, (wash, vol) in enumerate(
            zip([wash1, wash2, wash2], [680, 340, 340])):
        m300.pick_up_tip()
        for i, m in enumerate(mag_samples):
            m300.transfer(vol, wash1[i//4], m.bottom(45), new_tip='never')
        m300.drop_tip()

        ctx.delay(minutes=2, msg='Incubating off magnet for 2 minutes')
        magdeck.engage(height=3.4)
        ctx.delay(minutes=2, msg='Incubating on magnet for 2 minutes')

        disengage = False if i == 2 else True
        remove_supernatant(vol, disengage)

    ctx.delay(minutes=10, msg='Air dry pre-elution')
    magdeck.disengage()

    # distribute elution buffer
    m300.distribute(25, elution_buffer, [m.bottom(45) for m in mag_samples],
                    blow_out=True)

    ctx.delay(minutes=4, msg='Incubating off magnet for 4 minutes')
    magdeck.engage(height=3.4)
    ctx.delay(minutes=2, msg='Incubating on magnet for 2 minutes')

    # setup destination
    dest_block_1 = [well for row in [row[3:9] if i == 0 else row[2:10]
                    for i, row in enumerate(elution_plate.rows()[2:8])]
                    for well in row]
    dest_block_2 = [well for row in [row[15:21] if i == 0 else row[14:22]
                    for i, row in enumerate(elution_plate.rows()[2:8])]
                    for well in row]
    for s, d in zip(mag_samples_single, dest_block_1 + dest_block_2):
        p20.transfer(4, s.bottom(1), d.bottom(0.5), mix_after=(2, 4))

    # transfer negative and positive controls
    neg_control_dests = [elution_plate.wells_by_name()[well]
                         for well in ['C3', 'C15']]
    pos_control_dests = [elution_plate.wells_by_name()[well]
                         for well in ['C10', 'C22']]
    for s, d_set in zip([neg_control, pos_control],
                        [neg_control_dests, pos_control_dests]):
        p20.distribute(4, s.bottom(1), [d.bottom(0.5) for d in d_set],
                       disposal_volume=1)

from opentrons import types

metadata = {
    'protocolName': 'Nucleic Acid Extraction Using 1.5mL Tubes',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [pipinfo, sampnum] = get_values(  # noqa: F821
     'pipinfo', 'sampnum')

    # load labware
    tips20 = [
        protocol.load_labware(
            'opentrons_96_filtertiprack_20ul', s) for s in [5, 2]]
    pipType, tipType = pipinfo.split(' ')
    tips = [
        protocol.load_labware(
            tipType, s) for s in [9, 6, 3]]

    p20 = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=tips20)
    pip = protocol.load_instrument(pipType, 'right', tip_racks=tips)

    magdeck = protocol.load_module('magnetic module gen2', '10')
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')

    tempdeck = protocol.load_module('temperature module gen2', '7')
    temprack = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap')

    tuberack = protocol.load_labware(
        'opentrons_24_tuberack_nest_1.5ml_snapcap', '4')

    alblock = protocol.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '1')

    res12 = protocol.load_labware('nest_12_reservoir_15ml', '8')
    res1 = protocol.load_labware('nest_1_reservoir_195ml', '11')

    # name variables & check parameters
    if not 1 <= sampnum <= 24:
        raise Exception('Number of Samples should be between 1 and 24.')

    samps = tuberack.wells()[:sampnum]
    magsamps = [
        well for col in magplate.columns()[:6:2] for well in col][:sampnum]
    magsamps2 = [
        well for col in magplate.columns()[6::2] for well in col][:sampnum]
    tempsamps = temprack.wells()[:sampnum]
    magbeads = alblock['A1']
    dna1 = alblock['B1']
    buff1 = [res12['A1'] for _ in range(sampnum)]
    buff2_1 = [res12[x] for x in ['A2', 'A3'] for _ in range(12)][:sampnum]
    buff2_2 = [res12[x] for x in ['A4', 'A5'] for _ in range(12)][:sampnum]
    buff2_3 = [res12[x] for x in ['A6', 'A7'] for _ in range(12)][:sampnum]
    buff3 = tuberack['A1']
    rm = tuberack['A4']
    elutes = [well for col in alblock.columns()[1:4] for well in col][:sampnum]
    rm_e = [well for col in alblock.columns()[6:] for well in col][:sampnum*2]
    waste = res1['A1'].top()

    # 1. Transfer 500uL of Buffer 1 to Tubes
    protocol.comment('\nTransferring 500uL of Buffer 1 to Tubes\n')

    for buff, samp in zip(buff1, tempsamps):
        pip.transfer(500, buff, samp)

    # 2. Transfer 500uL sample to tube
    protocol.comment('\nTransferring 500uL of Sample to Tube\n')

    for src, dest in zip(samps, tempsamps):
        pip.transfer(500, src, dest.top(-2), mix_after=(5, 200))

    # 3. Heat to 80C and hold for 10 minutes
    protocol.comment('\nHeat to 80C and hold for 10 minutes\n')

    tempdeck.set_temperature(80)
    protocol.delay(minutes=10)

    # 4. Cool to 25C and add 10uL of DNA1
    protocol.comment('\nCooling to 25C\n')

    tempdeck.set_temperature(25)

    protocol.comment('\nAdding 10uL of DNA1 to Tubes\n')

    for samp in tempsamps:
        p20.transfer(10, dna1, samp, mix_after=(5, 20))

    # 5. Add 10uL of MagBeads
    protocol.comment('\nAdding 10uL of Magnetic Beads\n')

    p20.pick_up_tip()
    p20.mix(10, 20, magbeads)

    for samp in tempsamps:
        p20.mix(2, 10, magbeads)
        p20.aspirate(10, magbeads)
        p20.dispense(10, samp.top(-2))
        p20.blow_out()

    p20.drop_tip()

    # 6. Gently agitate sample tube for 5 minutes/transfer to magplate
    protocol.comment('\nMixing samples and transferring to MagDeck\n')

    for src, dest in zip(tempsamps, magsamps):
        pip.transfer(1050, src, dest, mix_before=(5, 200))

    # 7. Collect magnetic beads on wall of tube
    protocol.comment('\nEngaging magdeck and collecting pellet\n')

    magdeck.engage()
    protocol.delay(minutes=2)

    # 8. Remove supernatant
    def supernatant_removal(vol, src, dest):
        pip.flow_rate.aspirate = 20
        pip.transfer(
            vol, src.bottom().move(types.Point(x=-1, y=0, z=0.5)),
            dest, air_gap=20, new_tip='never')
        pip.flow_rate.aspirate = round(pip.max_volume/3.25)

    protocol.comment('\nRemoving supernatant\n')

    for samp in magsamps:
        pip.pick_up_tip()
        supernatant_removal(1050, samp, waste)
        pip.drop_tip()

    magdeck.disengage()

    # 9-12. Wash with buffer 2

    buff2s = [buff2_1, buff2_2, buff2_3]
    for idx, buff in zip(range(1, 4), buff2s):
        protocol.comment(f'\nPerforming Wash {idx}\n')

        for b, samp in zip(buff, magsamps):
            pip.pick_up_tip()
            pip.transfer(1000, b, samp.top(-2), new_tip='never')
            pip.mix(10, pip.max_volume, samp)
            pip.blow_out(samp)
            pip.drop_tip()

        magdeck.engage()
        protocol.delay(minutes=2)

        for samp in magsamps:
            pip.pick_up_tip()
            supernatant_removal(1050, samp, waste)
            pip.drop_tip()

        magdeck.disengage()

    # 13. Add 25uL of Buffer 3
    protocol.pause('\nPlease make sure Buffer 3 is in A1 of the tube rack in \
        slot 4. The reaction mix should be in A4 of the same tube rack\n')

    for src, dest in zip(magsamps, tempsamps):
        p20.pick_up_tip()
        p20.transfer(25, buff3, src.top(-2), new_tip='never')
        p20.mix(10, 18, src)
        p20.blow_out(src)
        p20.transfer(35, src, dest, new_tip='never')
        p20.blow_out(dest)
        p20.drop_tip()

    # 14. Heat tube to 65 and hold for 5 minutes
    protocol.comment('\nHeating tubes to 65C and holding for 5 minutes\n')

    tempdeck.set_temperature(65)
    protocol.delay(minutes=5)

    # 15. Transfer sample back to magplate and engage magdeck
    protocol.comment('\nMoving samples back to MagDeck and engaging\n')

    for src, dest in zip(tempsamps, magsamps2):
        p20.pick_up_tip()
        p20.transfer(35, src, dest, new_tip='never')
        p20.blow_out(dest)
        p20.drop_tip()

    magdeck.engage()
    protocol.delay(minutes=1)

    # 16-18. Transfer Reaction Mix, Distribute samples, & add to RM
    protocol.comment('\nTransferring Reaction Mix to PCR Strips\n')

    p20.pick_up_tip()

    for well in rm_e:
        p20.transfer(20, rm, well, new_tip='never')
        p20.blow_out()

    p20.drop_tip()

    protocol.comment('\nTransferring elution to tubes and Reaction Mix\n')
    for src, e, d1, d2 in zip(magsamps2, elutes, rm_e[::2], rm_e[1::2]):
        p20.pick_up_tip()

        p20.transfer(
            25, src.bottom().move(types.Point(x=-1, y=0, z=0.5)),
            e, new_tip='never'
            )

        p20.aspirate(10, e)
        p20.dispense(5, d1)
        p20.dispense(5, d2)
        p20.mix(5, 15, d2)
        p20.blow_out()
        p20.mix(5, 15, d1)
        p20.blow_out()

        p20.drop_tip()

    protocol.comment('OT-2 protocol complete. Please move PCR strip containing \
    samples and reaction mix to heat at 65C for 20 minutes')

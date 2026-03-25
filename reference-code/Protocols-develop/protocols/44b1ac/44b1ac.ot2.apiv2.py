from opentrons import protocol_api, types

metadata = {
    'protocolName': ': QIAseq Targeted RNAscan Panel for Illumina Instruments',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [samples, samples_labware, p300_mount,
        p20_mount, n7_row, engage_height, bead_vol1,
        bead_vol2] = get_values(  # noqa: F821
        "samples", "samples_labware", "p300_mount", "p20_mount", "n7_row",
        "engage_height", "bead_vol1", "bead_vol2")

    if not 1 <= samples <= 12:
        raise Exception('''Invalid number of samples.
                        Sample number must be between 1-12.''')

    # Load Labware
    tipracks_200ul = ctx.load_labware('opentrons_96_filtertiprack_200ul', 9)
    tipracks_20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul', 6)
    tc_mod = ctx.load_module('thermocycler module')
    tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
                    'opentrons_96_aluminumblock_nest_wellplate_100ul')
    reagents = ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 5)
    trash = ctx.loaded_labwares[12]['A1']

    if samples_labware == 'tube':
        sample_plate = ctx.load_labware(
                        'opentrons_24_tuberack_nest_1.5ml_screwcap', 2)
    elif samples_labware == 'plate':
        sample_plate = ctx.load_labware(
                        'nest_96_wellplate_100ul_pcr_full_skirt', 2)

    # Load Pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tipracks_200ul])
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])

    # Helper Functions
    def pick_up(pip, loc=None):
        try:
            if loc:
                pip.pick_up_tip(loc)
            else:
                pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Please replace the empty tip racks!")
            pip.reset_tipracks()
            pip.pick_up_tip()

    sides = [-1 + (((n // 8) % 2) * 1*2)
             for n in range(96)]

    def getWellSide(well, plate, custom_sides=None):
        index = plate.wells().index(well)
        if custom_sides:
            return custom_sides[index]
        return sides[index]

    def remove_supernatant(vol, src, dest, side, pip=p300, mode=None):
        if mode == 'elution':
            p300.flow_rate.aspirate = 10
        else:
            p300.flow_rate.aspirate = 30
            p300.flow_rate.dispense = 30
        while vol > 200:
            p300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            p300.dispense(200, dest)
            p300.aspirate(10, dest)
            vol -= 200
        p300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        p300.dispense(vol, dest)
        if mode == 'elution':
            p300.blow_out()
        if dest == trash:
            p300.blow_out()
        p300.flow_rate.aspirate = 50

    def reset_flow_rates():
        p300.flow_rate.aspirate = 46.43
        p300.flow_rate.dispense = 46.43

    def remove_residiual_supernatant():
        for well in mag_plate_wells:
            pick_up(p20)
            p20.aspirate(10, well.bottom().move(types.Point(
                        x=getWellSide(well, mag_plate), y=0, z=0.5)))
            p20.dispense(10, trash)
            p20.drop_tip()

    # Wells
    sample_wells = sample_plate.wells()[:samples]
    temp_plate_wells = temp_plate.wells()[:samples]
    primer = reagents['A1']

    # First strand cDNA synthesis
    # Pre-Heat/Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Heating Thermocycler to 65°C')
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_block_temperature(65)
    tc_mod.set_lid_temperature(103)
    tc_mod.open_lid()
    temp_mod.await_temperature(4)
    ctx.pause('''Temperature Module has been cooled to 4°C.
              Please place your samples and reagents on the
              temperature module.''')

    # Add RNA to plate
    for src, dest in zip(sample_wells, temp_plate_wells):
        pick_up(p20)
        p20.aspirate(5, src)
        p20.dispense(5, dest)
        p20.drop_tip()

    # Add Primer
    for well in temp_plate_wells:
        pick_up(p20)
        p20.aspirate(1, primer)
        p20.dispense(1, well)
        p20.mix(7, 3)
        p20.drop_tip()

    # Pause for vortex and centrifuge
    ctx.pause('''Cover the plate with an aluminum foil seal, then briefly but
              gently vortex, and spin down briefly afterwards. Place the plate
              in the thermocycler and click continue.''')

    tc_mod.close_lid()
    tc_mod.set_block_temperature(65, hold_time_minutes=5)
    tc_mod.open_lid()

    ctx.pause('''Remove plate from thermocycler and place on temperature
              module for 2 minutes. Then briefly centrifuge and return to
              the temperature module and continue to the next step.''')

    ctx.pause('''Remove the RP Primer tube and place the first strand
              synthesis mix (Reverse transcription mix) in position A1
              of slot 5.''')

    # Reverse transcription
    # Add First Strand Synthesis Mix
    fss_mix = reagents['A1']
    for well in temp_plate_wells:
        pick_up(p20)
        p20.aspirate(4, fss_mix)
        p20.dispense(4, well)
        p20.mix(7, 5)
        p20.drop_tip()

    ctx.pause('''Cover the plate with an aluminum foil seal, then briefly but
              gently vortex, and spin down briefly afterwards. Place the plate
              in the thermocycler and click continue.''')

    tc_mod.close_lid()
    profile = [
                {'temperature': 25, 'hold_time_minutes': 10},
                {'temperature': 42, 'hold_time_minutes': 30},
                {'temperature': 70, 'hold_time_minutes': 15}]
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=10)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()

    ctx.pause('''Remove plate from thermocycler then briefly centrifuge and return to
              the temperature module and continue to the next step.''')

    # Second strand synthesis
    ctx.pause('''Remove the first strand synthesis tube and place the second strand
            synthesis mix in position A1
            of slot 5.''')

    # Reverse transcription
    # Add Second Strand Synthesis Mix
    sss_mix = reagents['A1']
    for well in temp_plate_wells:
        pick_up(p20)
        p20.aspirate(10, sss_mix)
        p20.dispense(10, well)
        p20.mix(7, 10)
        p20.drop_tip()

    ctx.pause('''Cover the plate with an aluminum foil seal, then briefly but
              gently vortex, and spin down briefly afterwards. Place the plate
              in the thermocycler and click continue.''')

    tc_mod.close_lid()
    profile = [
                {'temperature': 37, 'hold_time_minutes': 7},
                {'temperature': 65, 'hold_time_minutes': 10},
                {'temperature': 80, 'hold_time_minutes': 10}]
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=20)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()

    ctx.pause('''Remove plate from thermocycler then briefly centrifuge and return to
              the temperature module and continue to the next step.''')

    # End repair/dA tailing
    tc_mod.set_lid_temperature(70)
    tc_mod.set_block_temperature(4)
    ctx.pause('''Remove second strand synthesis mix and place the
              End repair/dA tailing mix in position A1
              of slot 5. Also place the ERA enzyme tube in position B1. ''')

    # Add End repair/dA tailing mix
    tail_mix = reagents['A1']
    era_enzyme = reagents['B1']
    for well in temp_plate_wells:
        pick_up(p20)
        p20.aspirate(20, tail_mix)
        p20.dispense(20, well)
        p20.drop_tip()

    # Add ERA Enzyme
    for well in temp_plate_wells:
        pick_up(p20)
        p20.aspirate(10, era_enzyme)
        p20.dispense(10, well)
        p20.mix(7, 20)
        p20.drop_tip()

    ctx.pause('''Cover the plate with an aluminum foil seal, then briefly but
              gently vortex, and spin down briefly afterwards. Place the plate
              in the thermocycler and click continue.''')

    profile = [
                {'temperature': 4, 'hold_time_minutes': 1},
                {'temperature': 20, 'hold_time_minutes': 30},
                {'temperature': 65, 'hold_time_minutes': 30}]

    tc_mod.close_lid()
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=40)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()

    ctx.pause('''Remove plate from thermocycler and return to
              the temperature module and continue to the next step.''')

    # Adapter Ligation
    del ctx.deck['2']
    n7_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 2)
    n7_adapters = n7_plate.rows()[n7_row]
    ligation_mix = reagents['A1']

    ctx.pause('''Remove previous reagents from Slot 5 and place the
                Ligation Mix in A1.
                Place IL-N7 plate in Slot 2, then resume.''')

    # Add IL-N7 Adapters
    for src, dest in zip(n7_adapters, temp_plate_wells):
        pick_up(p20)
        p20.aspirate(5, src)
        p20.dispense(5, dest)
        p20.mix(5, 20)
        p20.drop_tip()

    # Add Ligation Master Mix
    for well in temp_plate_wells:
        pick_up(p300)
        p300.aspirate(45, ligation_mix)
        p300.dispense(45, well)
        p300.mix(7, 50)
        p300.drop_tip()

    ctx.pause('''Place the plate in the thermocycler and click Resume.''')

    profile = [
                {'temperature': 4, 'hold_time_minutes': 1},
                {'temperature': 20, 'hold_time_minutes': 15}]

    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=100)
    tc_mod.set_block_temperature(4)

    ctx.pause('''Place the PCR plate on the temperature module.
              Click Resume to proceed to Adapter Ligation Cleanup
              (Sample Cleanup 1).''')

    # Sample Cleanup 1
    del ctx.deck['2']
    ctx.pause('''Place a NEST 96 Well Deep well plate on the Magnetic Module.
              Place a NEST 12 well reservoir containing Ethanol (A1)
              and nuclease-free water (A12) in Slot 2.
              Place QIAseq Beads in Slot 5 position A1.''')
    mag_mod = ctx.load_module('magnetic module gen2', 1)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 2)

    # Wells
    mag_plate_wells = mag_plate.wells()[:samples]
    beads = reagents['A1']
    ethanol = reservoir['A1']
    nfw = reservoir['A12']

    # Transfer 100 uL of Reaction Product to Mag Plate
    for src, dest in zip(temp_plate_wells, mag_plate_wells):
        pick_up(p300)
        p300.aspirate(100, src)
        p300.dispense(100, dest)
        p300.drop_tip()

    # Bead Wash
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(bead_vol1, beads)
        p300.dispense(bead_vol1, beads)
        p300.mix(10, (100+bead_vol1)/2)
        p300.drop_tip()

    # Incubate for 5 minutes
    ctx.delay(minutes=5, msg='Incubating at room temperature.')

    # Engage Magnetic Module
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=15, msg='Engaging Magnetic Module for 15 minutes.')

    # Remove Supernatant
    for well in mag_plate_wells:
        pick_up(p300)
        remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
        p300.drop_tip()

    # Completely Remove Residual Supernatant
    remove_residiual_supernatant()

    # 260 uL Ethanol Wash (2x)
    for _ in range(2):
        pick_up(p300)
        for well in mag_plate_wells:
            p300.aspirate(200, ethanol)
            p300.dispense(200, well.top(10))
            p300.aspirate(60, ethanol)
            p300.dispense(60, well.top(10))
        p300.drop_tip()

        ctx.delay(minutes=1, msg="Waiting for solution to clear.")

        for well in mag_plate_wells:
            pick_up(p300)
            remove_supernatant(260, well, trash, getWellSide(well, mag_plate))
            p300.drop_tip()

    mag_mod.disengage()

    # Dry Beads
    ctx.delay(minutes=10, msg='Drying Beads for 10 minutes.')

    # Add 52 uL of Nuclease-Free Water to Elute DNA
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(52, nfw)
        p300.dispense(52, well.bottom(3))
        p300.mix(10, 25, well.bottom(1))
        p300.drop_tip()

    # Engaging Magnetic Module
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=5, msg='Engaging Magnetic Module for 5 minutes.')

    ctx.pause('''Place a new empty NEST 96 Deep Well Plate in Slot 4.
               Make sure to replenish QIAseq Beads volume for
               second bead wash.''')
    intermediate_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', 4)
    intermediate_plate_wells = intermediate_plate.wells()[:samples]

    # Transfer 50 uL of sample to new intermediate plate
    for src, dest in zip(mag_plate_wells, intermediate_plate_wells):
        pick_up(p300)
        p300.aspirate(50, src)
        p300.dispense(50, dest)
        p300.drop_tip()

    # Bead Wash
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(bead_vol2, beads)
        p300.dispense(bead_vol2, beads)
        p300.mix(10, (50+bead_vol2)/2)
        p300.drop_tip()

    # Incubate for 5 minutes
    ctx.delay(minutes=5, msg='Incubating at room temperature.')

    ctx.pause('''Remove old NEST 96 Deep Well plate from Magnetic module and
              place new deep well plate from Slot 4 onto the magnetic module.
              Click Resume when completed.''')

    # Engage Magnetic Module
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=10, msg='Engaging Magnetic Module for 10 minutes.')

    # Remove Supernatant
    for well in mag_plate_wells:
        pick_up(p300)
        remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
        p300.drop_tip()

    # 200 uL Ethanol Wash (2x)
    for _ in range(2):
        pick_up(p300)
        for well in mag_plate_wells:
            p300.aspirate(200, ethanol)
            p300.dispense(200, well.top(10))
        p300.drop_tip()

        ctx.delay(minutes=1, msg="Waiting for solution to clear.")

        for well in mag_plate_wells:
            pick_up(p300)
            remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
            p300.drop_tip()

    # Completely Remove Residual Supernatant
    remove_residiual_supernatant()

    # Dry Beads
    ctx.delay(minutes=5, msg='Drying Beads for 5 minutes.')

    # Add 12.4 uL of Nuclease-Free Water to Elute DNA
    for well in mag_plate_wells:
        pick_up(p20)
        p20.aspirate(12.5, nfw)
        p20.dispense(12.5, well.bottom(3))
        p20.mix(10, 20, well.bottom(1))
        p20.drop_tip()

    ctx.pause('''Please remove the old PCR plate on the temperature module
              and place a new PCR plate. Then click Resume to continue.''')

    # Transfer 10.4 uL of supernatant to new PCR plate
    for src, dest in zip(mag_plate_wells, temp_plate_wells):
        pick_up(p20)
        p20.aspirate(10.4, src.bottom().move(types.Point(x=getWellSide(src,
                     mag_plate), y=0, z=0.5)))
        p20.dispense(10.4, dest)
        p20.drop_tip()

    # SPE Target Enrichment
    ctx.pause('''Add SPE Reaction Mix to each sample and then place the
              PCR plate in the thermocycler. Click Resume when ready.''')

    profile = [
                {'temperature': 95, 'hold_time_seconds': 15},
                {'temperature': 68, 'hold_time_minutes': 10}]

    tc_mod.deactivate_lid()
    tc_mod.close_lid()
    tc_mod.set_block_temperature(95, hold_time_minutes=15)
    tc_mod.execute_profile(steps=profile, repetitions=8)
    tc_mod.set_block_temperature(72, hold_time_minutes=5)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()

    ctx.pause('''Reaction is complete.
              Place the PCR plate on the temperature module.''')

    # Sample Cleanup 2
    ctx.pause('''Place a new deep well plate onto the magnetic module.
              Click Resume when completed.''')
    ctx.pause('''Ensure Ethanol volume and
              QIAseq bead volumes are adequate.''')

    # Add 30 uL of Nuclease-Free Water
    pick_up(p300)
    for well in temp_plate_wells:
        p300.aspirate(30, nfw)
        p300.dispense(30, well.top(-5))
    p300.drop_tip()

    # Transfer Samples to Mag Plate
    for src, dest in zip(temp_plate_wells, mag_plate_wells):
        p300.pick_up_tip()
        p300.aspirate(50, src)
        p300.dispense(50, dest)
        p300.drop_tip()

    # Bead Wash
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(bead_vol2, beads)
        p300.dispense(bead_vol2, beads)
        p300.mix(10, (50+bead_vol2)/2)
        p300.drop_tip()

    # Incubate for 5 minutes
    ctx.delay(minutes=5, msg='Incubating at room temperature.')

    # Engaging Magnetic Module
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=5, msg='Engaging Magnetic Module for 5 minutes.')

    # Remove Supernatant
    for well in mag_plate_wells:
        pick_up(p300)
        remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
        p300.drop_tip()

    # 200 uL Ethanol Wash (2x)
    for _ in range(2):
        pick_up(p300)
        for well in mag_plate_wells:
            p300.aspirate(200, ethanol)
            p300.dispense(200, well.top(10))
        p300.drop_tip()

        ctx.delay(minutes=1, msg="Waiting for solution to clear.")

        for well in mag_plate_wells:
            pick_up(p300)
            remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
            p300.drop_tip()

    # Air Dry for 5 minutes
    ctx.delay(minutes=5, msg='Air dry beads for 5 minutes.')

    # Add 15.4 uL of Nuclease-Free Water to Elute DNA
    for well in mag_plate_wells:
        pick_up(p20)
        p20.aspirate(15.4, nfw)
        p20.dispense(15.4, well.bottom(3))
        p20.mix(10, 20, well.bottom(1))
        p20.drop_tip()

    ctx.pause('Place a new PCR plate on the temperature module.')

    # Transfer Supernatant to PCR Plate
    for src, dest in zip(mag_plate_wells, temp_plate_wells):
        pick_up(p20)
        p20.transfer(13.4, src.bottom().move(types.Point(
                        x=getWellSide(well, mag_plate), y=0, z=0.5)), dest,
                     new_tip='never')
        p20.drop_tip()

    # Universal PCR amplification

    ctx.pause('''Add the Universal PCR mix to the samples on the PCR plate.
              Then place the plate in the thermocycler.
              Click Resume when complete.''')

    profile = [
                {'temperature': 95, 'hold_time_seconds': 15},
                {'temperature': 60, 'hold_time_minutes': 2}]

    tc_mod.deactivate_lid()
    tc_mod.close_lid()
    tc_mod.set_block_temperature(95, hold_time_minutes=15)
    tc_mod.execute_profile(steps=profile, repetitions=15, block_max_volume=20)
    tc_mod.set_block_temperature(72, hold_time_minutes=5)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()

    ctx.pause('''Reaction is complete.
              Place the PCR plate on the temperature module.''')

    # Sample Cleanup 3
    ctx.pause('''Place a new deep well plate onto the magnetic module.
              Click Resume when completed.''')
    ctx.pause('''Ensure Ethanol volume and
              QIAseq bead volumes are adequate.''')

    # Add 30 uL of Nuclease-Free Water
    pick_up(p300)
    for well in temp_plate_wells:
        p300.aspirate(30, nfw)
        p300.dispense(30, well.top(-5))
    p300.drop_tip()

    # Transfer Samples to Mag Plate
    for src, dest in zip(temp_plate_wells, mag_plate_wells):
        p300.pick_up_tip()
        p300.aspirate(50, src)
        p300.dispense(50, dest)
        p300.drop_tip()

    # Bead Wash
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(bead_vol2, beads)
        p300.dispense(bead_vol2, beads)
        p300.mix(10, (50+bead_vol2)/2)
        p300.drop_tip()

    # Incubate for 5 minutes
    ctx.delay(minutes=5, msg='Incubating at room temperature.')

    # Engaging Magnetic Module
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=5, msg='Engaging Magnetic Module for 5 minutes.')

    # Remove Supernatant
    for well in mag_plate_wells:
        pick_up(p300)
        remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
        p300.drop_tip()

    # 200 uL Ethanol Wash (2x)
    for _ in range(2):
        pick_up(p300)
        for well in mag_plate_wells:
            p300.aspirate(200, ethanol)
            p300.dispense(200, well.top(10))
        p300.drop_tip()

        ctx.delay(minutes=1, msg="Waiting for solution to clear.")

        for well in mag_plate_wells:
            pick_up(p300)
            remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
            p300.drop_tip()

    # Completely Remove Residual Supernatant
    remove_residiual_supernatant()

    # Air Dry for 5 minutes
    ctx.delay(minutes=5, msg='Air dry beads for 5 minutes.')

    # Add 25 uL of Nuclease-Free Water to Elute DNA
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(25, nfw)
        p300.dispense(25, well.bottom(3))
        p300.mix(10, 25, well.bottom(1))
        p300.drop_tip()

    # Delay for 5 minutes for solution to clear
    ctx.delay(minutes=5, msg='Delay for 5 minutes for solution to clear.')

    ctx.pause('Place a new PCR plate on the temperature module.')

    # Transfer Supernatant to PCR Plate
    for src, dest in zip(mag_plate_wells, temp_plate_wells):
        pick_up(p300)
        p300.transfer(21, src.bottom().move(types.Point(
                        x=getWellSide(well, mag_plate), y=0, z=0.5)), dest,
                      new_tip='never')
        p300.drop_tip()

    ctx.pause('''Protocol Completed! Proceed to library quantification.''')

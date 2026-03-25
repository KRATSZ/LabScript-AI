from opentrons import types
import json
import os
import math

metadata = {
    'protocolName': '''NEBNext Ultra II DNA Library Preparation Kit
                       for Illumina E7645S''',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [samples, m300_mount, p20_mount, initial_denaturation_cycles,
     denat_anneal_cycles, final_extension_cycles, beads_vol_1,
     elution_buff_vol, rxn_mix_vol_p3, beads_vol_2,
     p5_mix_vol] = get_values(  # noqa: F821
        "samples", "m300_mount", "p20_mount", "initial_denaturation_cycles",
        "denat_anneal_cycles", "final_extension_cycles", "beads_vol_1",
        "elution_buff_vol", "rxn_mix_vol_p3", "beads_vol_2", "p5_mix_vol")

    if samples < 1 or samples > 24:
        raise Exception('Invalid number of DNA samples (must be 1-24).')

    cols = math.ceil(samples/8)

    ctx.set_rail_lights(True)

    # Labware
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_block = temp_mod.load_labware(
                    'opentrons_24_aluminumblock_nest_2ml_screwcap')
    tc_mod = ctx.load_module('Thermocycler Module')
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    mag_mod = ctx.load_module('magnetic module gen2', 1)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    tips200ul = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                 for slot in [6, 9]]
    tips20ul = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [5]]
    pcr_block = ctx.load_labware(
                    'opentrons_96_aluminumblock_generic_pcr_strip_200ul', 2)

    # Pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips200ul)
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips20ul)

    # Wells
    enzyme_mix = temp_block['A1']
    rxn_buff = temp_block['B1']
    tc_sample_wells = tc_plate.wells()[:cols*8]
    tc_sample_cols = tc_plate.rows()[0][:cols]
    mag_plate_cols = mag_plate.rows()[0][:cols]
    trash = ctx.loaded_labwares[12]['A1']
    frag_dna_wells = pcr_block.wells()[:cols*8]
    frag_dna_cols = pcr_block.rows()[0][:cols]
    sides = [-1, 1] * (cols)
    sides = sides[:cols]

    # Helper Functions
    tip_track = True

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    folder_path = '/data/tiptracking'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                for pip in tip_log:
                    if pip.name in data:
                        tip_log[pip]['count'] = data[pip.name]
                    else:
                        tip_log[pip]['count'] = 0
        else:
            for pip in tip_log:
                tip_log[pip]['count'] = 0
    else:
        for pip in tip_log:
            tip_log[pip]['count'] = 0

    for pip in tip_log:
        if pip.type == 'multi':
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.rows()[0]]
        else:
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.wells()]
        tip_log[pip]['max'] = len(tip_log[pip]['tips'])

    def _pick_up(pip, loc=None):
        if tip_log[pip]['count'] == tip_log[pip]['max'] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
            tip_log[pip]['count'] += 1

    """ All of your protocol steps go here. Be sure to use _pick_up(pip) to
    keep track of your tips rather than the standard in
    pip.pick_up_tip() function. """

    # track final used tip
    if tip_track and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

    def remove_supernatant(vol, src, dest, side):
        m300.flow_rate.aspirate = 20
        m300.aspirate(10, src.top())
        while vol > 200:
            m300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            m300.dispense(200, dest)
            m300.aspirate(10, dest)
            vol -= 200
        m300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        m300.dispense(vol, dest)
        m300.dispense(10, dest)
        m300.flow_rate.aspirate = 50

    # I. End Preparation
    ctx.comment('Starting End Preparation')
    ctx.comment('Cooling temperature module to 4C.')
    # Set temperature to 4C (1)
    temp_mod.set_temperature(4)

    ctx.pause('''Please place reagents and libraries in the correct positions
                 on the temperature module. Click Resume to continue.''')

    # Add components to reaction mixture (2)
    for well in frag_dna_wells:
        _pick_up(p20)
        p20.transfer(3.5, rxn_buff, well, new_tip='never')
        p20.drop_tip()

        _pick_up(p20)
        p20.transfer(1.5, enzyme_mix, well, new_tip='never')
        p20.drop_tip()

    ctx.pause('''Please remove the reagents from the temperature module.''')

    # Resuspend reaction mixture 10x, 25 uL (3, 4)
    for col in frag_dna_cols:
        _pick_up(m300)
        m300.mix(10, 25, col)
        m300.drop_tip()

    # Centrifuge Plate (5)
    ctx.pause('''Please remove the reaction mixture in order to centrifuge the mixture and
              click Resume for the lid temperature to reach 75C.''')

    # Raise Lid Temperature (6)
    tc_mod.close_lid()
    tc_mod.set_lid_temperature(75)
    tc_mod.open_lid()

    # Move Reaction Mixture Plate into Thermocycler (7)
    ctx.pause('''Thermocycler lid temperature has reached 75C. Click Resume to transfer
              Reaction Mixture to Thermocycler''')

    for src, dest in zip(frag_dna_cols, tc_sample_cols):
        _pick_up(m300)
        m300.transfer(30, src, dest, new_tip='never')
        m300.drop_tip()

    tc_mod.close_lid()

    # Thermocycler Profile (8)
    profile = [
                {'temperature': 20, 'hold_time_minutes': 30},
                {'temperature': 65, 'hold_time_minutes': 30}]
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=30)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    ctx.comment('End Preparation Completed!')

    # II. Adaptor Ligation
    ctx.comment('Starting Adaptor Ligation!')
    ctx.comment('Deactivating Thermocycler Lid')
    ctx.pause('''Please place Adaptor Ligation reagents on the temperature module
              and click Resume to begin Deactivating the Thermocycler Lid.''')
    tc_mod.deactivate_lid()
    ctx.comment('Thermocycler Lid Deactivated!')

    # Reagent Wells
    illumina_adaptor = temp_block['A1']
    ligation_enhancer = temp_block['B1']
    ligation_mm = temp_block['C1']

    # Add Components to the Reaction Mixture (1)
    for well in tc_sample_wells:
        _pick_up(p20)
        p20.transfer(1.25, illumina_adaptor, well, new_tip='never')
        p20.drop_tip()

        _pick_up(p20)
        p20.transfer(0.5, ligation_enhancer, well, new_tip='never')
        p20.drop_tip()

    # Resuspend Ligation Master Mix and Add to Reaction Mixture (2, 3, 4)
    for i, well in enumerate(tc_sample_wells):
        _pick_up(p20)
        if i == 0:
            p20.mix(10, 20, ligation_mm)
        p20.transfer(15, ligation_mm, well, new_tip='never')
        p20.drop_tip()

    ctx.pause('''Please remove the reagents from the temperature module.''')

    # Resuspend reaction mixture 10x, 40 uL (5, 6)
    for col in tc_sample_cols:
        _pick_up(m300)
        m300.mix(10, 40, col)
        m300.drop_tip()

    # Centrifuge Reaction Mixture Plate (7, 8)
    ctx.pause('''Please remove the reaction mixture plate from the
              thermocycler in order to centrifuge the mixture.
              Return the plate to the thermocycler and click
              Resume once completed.''')

    # Incubate at 20C for 15 minutes (9)
    tc_mod.close_lid()
    tc_mod.set_block_temperature(20, hold_time_minutes=15)
    tc_mod.open_lid()

    ctx.pause('''Please place the USER Enzyme in A1 of the temperature module.
              Click Resume when completed.''')

    user_enzyme = temp_block['A1']

    # Add USER Enzyme to Reaction Mixture (10)
    for well in tc_sample_wells:
        _pick_up(p20)
        p20.transfer(1.5, user_enzyme, well, new_tip='never')
        p20.drop_tip()

    ctx.pause('''Please remove the USER Enzyme in A1 of the temperature module.
                Click Resume when completed.''')

    # Resuspend reaction mixture 10x, 40 uL (11, 12)
    for col in tc_sample_cols:
        _pick_up(m300)
        m300.mix(10, 40, col)
        m300.drop_tip()

    # Centrifuge Reaction Mixture Plate (13)
    ctx.pause('''Please remove the reaction mixture plate from the
              thermocycler in order to centrifuge the mixture and
              click Resume for the lid temperature to reach 47C. ''')

    # Raise Lid Temperature to 47C (14)
    tc_mod.close_lid()
    tc_mod.set_lid_temperature(47)
    tc_mod.open_lid()

    # Plate Reaction Mixture Plate into Thermocycler (15)
    ctx.pause('''Thermocycler lid temperature has reached 47C. Please put the
              reaction mixture plate into the thermocycler
              and click Resume.''')
    tc_mod.close_lid()

    # Incubate at 37C for 15 minutes (16)
    tc_mod.set_block_temperature(37, hold_time_minutes=15)
    tc_mod.open_lid()
    ctx.comment('''Adaptor Ligation Completed!
                Please setup Part 2 of the protocol.''')

    # III. Cleanup of Adaptor-Ligated DNA
    ctx.comment('Starting Cleanup of Adaptor-Ligated DNA!')
    ctx.pause('''Add the NEST 12-well reservoir with the correct reagents
              in the channels to slot 4.''')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 4)

    # Reservoir Reagents
    ethanol = reservoir['A1']
    elution_buff = reservoir['A3']
    beads = reservoir['A12']

    # Add AMPure XP Beads (1)
    for col in tc_sample_cols:
        _pick_up(m300)
        m300.transfer(beads_vol_1, beads, col, new_tip='never')
        m300.drop_tip()

    # Resuspend Reaction Mixture (2, 3)
    for col in tc_sample_cols:
        _pick_up(m300)
        m300.mix(10, 85, col)
        m300.drop_tip()

    ctx.pause('''Please remove the reaction mixture plate from the
              thermocycler in order to centrifuge the mixture. Return the plate
              on the Magnetic Module and click Resume.''')

    ctx.delay(minutes=5, msg='''Incubating reaction mixture for 5 minutes
              at Room Temperature.''')

    # Engage Magnetic Module (7)
    mag_mod.engage()
    ctx.delay(minutes=5, msg='Waiting 5 minutes for beads to pellet.')

    # Remove Supernatant (8, 9)
    for col, side in zip(mag_plate_cols, sides):
        _pick_up(m300)
        remove_supernatant(100, col, trash, side)
        m300.drop_tip()

    # Ethanol Wash (10-13)
    for _ in range(2):
        ctx.comment('Performing Ethanol Wash!')
        _pick_up(m300)
        for col in mag_plate_cols:
            m300.transfer(100, ethanol, col.top(), new_tip='never')
        m300.drop_tip()

        ctx.delay(seconds=30, msg='''Incubating reaction mixture for
                  30 seconds at room temperature''')

        for col, side in zip(mag_plate_cols, sides):
            _pick_up(m300)
            remove_supernatant(100, col, trash, side)
            m300.drop_tip()

    mag_mod.disengage()
    ctx.pause('''Magnetic Module Disengaged!
              Pausing to allow beads to dry.
              Click Resume when beads are dry.''')

    # Add Elution Buffer (15)
    ctx.comment('Adding Elution Buffer to Samples!')
    _pick_up(m300)
    for col in mag_plate_cols:
        m300.transfer(elution_buff_vol, elution_buff, col.top(),
                      new_tip='never')
    m300.drop_tip()

    # Resuspend Reaction Mixture (17)
    for col in mag_plate_cols:
        _pick_up(m300)
        m300.mix(10, 15, col)
        m300.drop_tip()

    # Incubate at Room Temp (18)
    ctx.delay(minutes=2, msg='''Incubating Reaction Mixture for
              2 minutes at Room Temperature''')

    # Engage Magnetic Module
    ctx.comment('Engaging Magnetic Module!')
    mag_mod.engage()

    ctx.delay(minutes=5, msg='Waiting 5 minutes for beads to pellet.')
    ctx.pause('''Add new PCR tubes to Almuminum Block in Slot 2.
              Tubes should start in A1 and correspond to the
              number of total samples.''')

    pcr_tube_cols = pcr_block.rows()[0][:cols]
    pcr_tube_wells = pcr_block.wells()[:cols*8]

    # Transfer Reaction Mixure to PCR Tubes
    for src, dest, side in zip(mag_plate_cols, pcr_tube_cols, sides):
        _pick_up(m300)
        remove_supernatant(rxn_mix_vol_p3, src, dest, side)
        m300.drop_tip()

    mag_mod.disengage()
    ctx.comment('Cleanup of Adaptor-Ligated DNA Completed!')

    # IV. PCR Amplification
    ctx.comment('Starting PCR Amplification!')
    ctx.pause('''Place the proper reagents in the temperature module.
    NEBNext Ultra II Q5 Master Mix in A1.
    UDI Primers in B1.''')

    # Reagent Components
    q5_mm = temp_block['A1']
    udi_primers = temp_block['B1']

    # Add Components to new PCR Tubes (1)
    # Transfer Master Mix and Primers
    for well in pcr_tube_wells:
        _pick_up(p20)
        p20.transfer(12.5, q5_mm, well, new_tip='never')
        p20.drop_tip()

        _pick_up(p20)
        p20.transfer(2.5, udi_primers, well, new_tip='never')
        p20.drop_tip()

    ctx.pause('''Remove reagents from the temperature module.''')

    # Resuspend reaction mixture 10x, 20 uL (2, 3)
    for col in pcr_tube_cols:
        _pick_up(m300)
        m300.mix(10, 20, col)
        m300.drop_tip()

    # Centrifugation (4)
    ctx.pause('''Remove reaction mixture from the deck for centrifugation.
              Return the reaction mixture and click Resume.''')
    ctx.pause('''Add a new PCR plate into the thermocycler and click Resume to begin
              transferring reaction mixture to the thermocycler.''')

    # Transfer Reaction Mixture to Thermocycler (5)
    for src, dest in zip(pcr_tube_cols, tc_sample_cols):
        _pick_up(m300)
        m300.transfer(22.5, src, dest, new_tip='never')
        m300.drop_tip()

    # Thermocycler Profile (6)
    tc_mod.close_lid()

    # Initial Denaturation
    for _ in range(initial_denaturation_cycles):
        tc_mod.set_block_temperature(98, hold_time_seconds=30)

    profile = [
            {'temperature': 98, 'hold_time_seconds': 10},
            {'temperature': 65, 'hold_time_seconds': 75}]
    tc_mod.execute_profile(steps=profile, repetitions=denat_anneal_cycles,
                           block_max_volume=25)

    # Final Extension
    for _ in range(final_extension_cycles):
        tc_mod.set_block_temperature(98, hold_time_seconds=30)

    # Hold
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    ctx.comment('PCR Amplification Completed!')

    # V. Cleanup of PCR Reaction
    ctx.pause('''Ensure reagents are in there proper place. The Cleanup of
    PCR Reactions will require Ethanol, Elution Buffer and AMPure XP Beads''')

    # Transfer Components to PCR Product Mixture (1)
    # Add Elution Buffer
    # ctx.comment('Adding Elution Buffer to PCR Product Mixtures!')
    # _pick_up(m300)
    # for col in tc_sample_cols:
    #     m300.transfer(25, elution_buff, col.top(), new_tip='never')
    # m300.drop_tip()

    # Add AMPure XP Beads
    ctx.comment('Adding AMPure XP Beads to PCR Product Mixtures!')
    for col in tc_sample_cols:
        _pick_up(m300)
        m300.transfer(beads_vol_2, beads, col, new_tip='never')
        m300.drop_tip()

    # Resuspend and Incubate at Room Temperature (2)
    for col in tc_sample_cols:
        _pick_up(m300)
        m300.mix(10, p5_mix_vol, col)
        m300.drop_tip()

    ctx.delay(minutes=5, msg='Incubating reaction mixture for 5 minutes.')

    # Move Plate to Magnetic Module (3)
    ctx.pause('''Move the PCR plate from the Thermocycler to
              the Magnetic Module and then click Resume.''')

    # Engage Magnet (4)
    mag_mod.engage()
    ctx.delay(minutes=5, msg='Engaging magnets for 5 minutes.')

    # Remove Supernatant (5, 6)
    for col, side in zip(mag_plate_cols, sides):
        _pick_up(m300)
        remove_supernatant(65, col, trash, side)
        m300.drop_tip()

    # Ethanol Wash with Delays (7-10)
    for _ in range(2):
        ctx.comment('Performing Ethanol Wash!')
        _pick_up(m300)
        for col in mag_plate_cols:
            m300.transfer(100, ethanol, col.top(), new_tip='never')
        m300.drop_tip()

        ctx.delay(seconds=30, msg='''Incubating reaction mixture for
                  30 seconds at room temperature''')

        for col, side in zip(mag_plate_cols, sides):
            _pick_up(m300)
            remove_supernatant(100, col, trash, side)
            m300.drop_tip()

    mag_mod.disengage()
    ctx.pause('''Magnetic Module Disengaged!
              Pausing to allow beads to dry.
              Click Resume when beads are dry.''')

    # Add Elution Buffer (11, 12)
    ctx.comment('Adding Elution Buffer to Reaction Mixture.')
    _pick_up(m300)
    for col in mag_plate_cols:
        m300.transfer(20, elution_buff, col.top(), new_tip='never')
    m300.drop_tip()

    # Resuspend reaction mixture 10x, 15 uL (13)
    for col in mag_plate_cols:
        _pick_up(m300)
        m300.mix(10, 15, col)
        m300.drop_tip()

    # Centrifugation (14)
    ctx.pause('''Remove reaction mixture from the magnetic module for centrifugation.
              Also add new PCR tubes starting in A1 on slot 2.
              Return the reaction mixture and click Resume.''')

    # Incubation (15)
    ctx.delay(minutes=2, msg='Incubating reaction mixture for 2 minutes.')

    # Engage Magnetic Module (16, 17)
    mag_mod.engage()
    ctx.delay(minutes=5, msg='Engaging Magnetic Module for 5 minutes.')

    # Transfer supernatant to new PCR tubes (18)
    for src, dest, side in zip(mag_plate_cols, pcr_tube_cols, sides):
        _pick_up(m300)
        remove_supernatant(30, src, dest, side)
        m300.drop_tip()

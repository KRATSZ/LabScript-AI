# flake8: noqa

from opentrons import protocol_api

from opentrons import types

import inspect

metadata = {
    'protocolName': 'Illumina DNA Prep - BMS',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.14'
}
# I removed the right() function because it is never used
# settings
# SAMPLES = '24x'         # 8x, 16x, or 24x
# YES or NO, DRYRUN = 'YES' will return tips, skip incubation times,
# shorten mix, for testing purposes
# DRYRUN = 'NO'
# YES or NO, NOMODULES = 'YES' will not require modules on the deck and will
# skip module steps, for testing purposes, if DRYRUN = 'YES', then NOMODULES
# will automatically set itself to 'NO'
# NOMODULES = 'NO'
# TIPREUSE = 'NO'
# YES or NO, Reusing tips on wash steps reduces tips needed, no tip refill
# needed, suggested only for 24x run with all steps

# YES or NO, Sets whether to use protocol specific z offsets for each tip and
# labware or no offsets aside from defaults
# OFFSET = 'YES'

# sections
# STEP_TAG = 1     # 1 is include, 0 is skip, steps with "DECK" are
# for reaction
# to take place with the on deck Thermocycler module
# This arrangement makes it possibly to set up and run only the first
# half, or to skips steps and resume if there is an Error.
# STEP_TAGDECK = 1
# If non "DECK" steps are skipped, then TIPREUSE will automatically set
# itself to 'NO' in order to keep tip order correct.
# STEP_TSB = 1
# STEP_TSBDECK = 1
# STEP_WASH = 1
# STEP_PCR = 1
# STEP_PCRDECK = 1
# STEP_POSTPCR = 1


def run(protocol: protocol_api.ProtocolContext):

    global TIPREUSE

    [SAMPLES,
     DRYRUN,
     NOMODULES,
     TIPREUSE,
     OFFSET,
     STEP_TAG,
     STEP_TAGDECK,
     STEP_TSB,
     STEP_TSBDECK,
     STEP_WASH,
     STEP_PCR,
     STEP_PCRDECK,
     STEP_POSTPCR] = get_values(  # noqa: F821
     "SAMPLES",
     "DRYRUN",
     "NOMODULES",
     "TIPREUSE",
     "OFFSET",
     "STEP_TAG",
     "STEP_TAGDECK",
     "STEP_TSB",
     "STEP_TSBDECK",
     "STEP_WASH",
     "STEP_PCR",
     "STEP_PCRDECK",
     "STEP_POSTPCR")

    STEPS = {STEP_TAG, STEP_TSB, STEP_WASH, STEP_PCR, STEP_POSTPCR}
    simulating = False
    real_temp = False
    real_incubate_time = 0.01

    if DRYRUN == 'YES':
        protocol.comment("THIS IS A DRY RUN")
    else:
        protocol.comment("THIS IS A REACTION RUN")
        NOMODULES = 'NO'

    if all(STEPS) is True:
        if TIPREUSE == 'YES':
            TIPREUSE = 'YES'
            protocol.comment("TIP REUSING")
    else:
        TIPREUSE = 'NO'
        protocol.comment("NO TIP REUSING")

    # labware
    if NOMODULES == 'YES':
        protocol.comment("THIS IS A NO MODULE RUN")
        # <--- Actually an Eppendorf 96 well, same dimensions
        mag_block = protocol.load_module('magnetic module gen2', '1')
        # <--- Actually an Eppendorf 96 well, same dimensions
        sample_plate_mag = mag_block.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
        if TIPREUSE == 'NO':
            reservoir = protocol.load_labware('nest_12_reservoir_15ml', '2')
        else:
            reservoir = protocol.load_labware(
                'nest_96_wellplate_2ml_deep', '2')

        temp_block = protocol.load_module('temperature module gen2', '3')
        reagent_plate = temp_block.load_labware(
            'armadillo_96_aluminumblock_200ul')
        tiprack_20 = protocol.load_labware(
            'opentrons_96_filtertiprack_20ul', '4')
        tiprack_200_1 = protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', '5')
        tiprack_200_2 = protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', '6')
        try:
            thermocycler = protocol.load_module('thermocyclerModuleV2')
        except:
            thermocycler = protocol.load_module('thermocycler')

        sample_plate_thermo = thermocycler.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
        tiprack_200_3 = protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', '9')
    else:
        protocol.comment("THIS IS A MODULE RUN")
        mag_block = protocol.load_module('magnetic module gen2', '1')
        # <--- Actually an Eppendorf 96 well, same dimensions
        sample_plate_mag = mag_block.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
        if TIPREUSE == 'NO':
            reservoir = protocol.load_labware('nest_12_reservoir_15ml', '2')
        else:
            reservoir = protocol.load_labware(
                'nest_96_wellplate_2ml_deep', '2')
        temp_block = protocol.load_module('temperature module gen2', '3')
        reagent_plate = temp_block.load_labware(
            'armadillo_96_aluminumblock_200ul')
        tiprack_20 = protocol.load_labware(
            'opentrons_96_filtertiprack_20ul', '4')
        tiprack_200_1 = protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', '5')
        tiprack_200_2 = protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', '6')
        try:
            thermocycler = protocol.load_module('thermocyclerModuleV2')
        except:
            thermocycler = protocol.load_module('thermocycler')
        sample_plate_thermo = thermocycler.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
        tiprack_200_3 = protocol.load_labware(
            'opentrons_96_filtertiprack_200ul', '9')

    if TIPREUSE == 'YES':
        protocol.comment("THIS PROTOCOL WILL REUSE TIPS FOR WASHES")

    # reagent - plate
    TAG = reagent_plate.wells_by_name()['A1']
    TSB = reagent_plate.wells_by_name()['A2']
    PCR = reagent_plate.wells_by_name()['A3']
    Barcodes1 = reagent_plate.wells_by_name()['A7']
    Barcodes2 = reagent_plate.wells_by_name()['A8']
    Barcodes3 = reagent_plate.wells_by_name()['A9']

    # offset
    if TIPREUSE == 'NO':
        p300_offset_Res = 2
    else:
        p300_offset_Res = 3
    p300_offset_Thermo = 1
    p300_offset_Mag = 1
    # p300_offset_Deck = 0.3
    p300_offset_Temp = 0.8
    # p300_offset_Tube = 0
    # if TIPREUSE == 'NO':
    # p20_offset_Res = 2
    # else:
    # p20_offset_Res = 2
    p20_offset_Thermo = 1
    p20_offset_Mag = 1
    # p20_offset_Deck = 0.3
    p20_offset_Temp = 1
    # p20_offset_Tube = 0

    # reagent - deepwell
    if TIPREUSE == 'NO':
        AMPure = reservoir['A1']
        water = reservoir['A2']
        EtOH_1 = reservoir['A4']
        EtOH_2 = reservoir['A4']
        EtOH_3 = reservoir['A4']
        RSB = reservoir['A6']
        TWB_1 = reservoir['A8']
        TWB_2 = reservoir['A8']
        TWB_3 = reservoir['A8']
        Liquid_trash = reservoir['A12'].bottom(p300_offset_Res)
    else:
        AMPure = reservoir['A1']
        EtOH_1 = reservoir['A4']
        EtOH_2 = reservoir['A3']
        EtOH_3 = reservoir['A2']
        RSB = reservoir['A6']
        TWB_1 = reservoir['A8']
        TWB_2 = reservoir['A9']
        TWB_3 = reservoir['A10']
        Liquid_trash = reservoir['A12'].bottom(p300_offset_Res)

    # pipette
    if NOMODULES == 'NO':
        p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[
                                        tiprack_200_1, tiprack_200_2,
                                        tiprack_200_3])
        p20 = protocol.load_instrument(
            'p20_multi_gen2', 'right', tip_racks=[tiprack_20])
    else:
        p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[
                                        tiprack_200_1, tiprack_200_2,
                                        tiprack_200_3])
        p20 = protocol.load_instrument(
            'p20_multi_gen2', 'right', tip_racks=[tiprack_20])

    def slow_tip_withdrawal(current_pipette, well_location, to_center=False):

        if to_center is False:
            current_pipette.move_to(well_location.top(), speed=10)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            protocol.pause(f"Replace empty tip racks for {pip}")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # samples
    # FIXME: This does not seem to be used
    src_file_path = inspect.getfile(lambda: None)
    protocol.comment(src_file_path)

    # tip and sample tracking
    if SAMPLES == '8x':
        protocol.comment("There are 8 Samples")
        samplecolumns = 1
        TWB_washtip_1 = tiprack_200_1['A3']
        TWB_removetip_1 = tiprack_200_1['A4']
        W1_ETOH_washtip_1 = tiprack_200_1['A10']
        W1_ETOH_removetip_1 = tiprack_200_1['A6']
    elif SAMPLES == '16x':
        protocol.comment("There are 16 Samples")
        samplecolumns = 2
        TWB_washtip_1 = tiprack_200_1['A5']
        TWB_washtip_2 = tiprack_200_1['A6']
        TWB_removetip_1 = tiprack_200_1['A7']
        TWB_removetip_2 = tiprack_200_1['A8']
        W1_ETOH_washtip_1 = tiprack_200_2['A7']
        W1_ETOH_washtip_2 = tiprack_200_2['A8']
        W1_ETOH_removetip_1 = tiprack_200_2['A9']
        W1_ETOH_removetip_2 = tiprack_200_2['A10']
    elif SAMPLES == '24x':
        protocol.comment("There are 24 Samples")
        samplecolumns = 3
        TWB_washtip_1 = tiprack_200_1['A7']
        TWB_washtip_2 = tiprack_200_1['A8']
        TWB_washtip_3 = tiprack_200_1['A9']
        TWB_removetip_1 = tiprack_200_1['A10']
        TWB_removetip_2 = tiprack_200_1['A6']
        TWB_removetip_3 = tiprack_200_1['A12']
        W1_ETOH_washtip_1 = tiprack_200_3['A4']
        W1_ETOH_washtip_2 = tiprack_200_3['A5']
        W1_ETOH_washtip_3 = tiprack_200_3['A6']
        W1_ETOH_removetip_1 = tiprack_200_3['A7']
        W1_ETOH_removetip_2 = tiprack_200_3['A8']
        W1_ETOH_removetip_3 = tiprack_200_3['A9']
    else:
        protocol.pause("ERROR?")

    # FIXME: Commented out variables are never used in the protocol
    # positions
    ##########################################################################
    #  sample_plate_thermo on the Thermocycler
    # A1_p20_bead_side = sample_plate_thermo['A1'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Thermo - 5))  # Beads to the Right
    # A1_p20_bead_top = sample_plate_thermo['A1'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Thermo + 2))  # Beads to the Right
    # A1_p20_bead_mid = sample_plate_thermo['A1'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Thermo - 2))  # Beads to the Right
    A1_p300_bead_side = sample_plate_thermo['A1'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Thermo - 7.2))  # Beads to the Right
    A1_p300_bead_top = sample_plate_thermo['A1'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Thermo - 1))  # Beads to the Right
    A1_p300_bead_mid = sample_plate_thermo['A1'].center().move(types.Point(
        x=0.80, y=0, z=p300_offset_Thermo - 4))  # Beads to the Right
    A1_p300_loc1 = sample_plate_thermo['A1'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Thermo - 4))
    # Beads to the Right
    A1_p300_loc2 = sample_plate_thermo['A1'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Thermo - 4))  # Beads to the Right
    A1_p300_loc3 = sample_plate_thermo['A1'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Thermo - 4))
    # Beads to the Right
    # A3_p20_bead_side = sample_plate_thermo['A2'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Thermo - 5))  # Beads to the Right
    # A3_p20_bead_top = sample_plate_thermo['A2'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Thermo + 2))  # Beads to the Right
    # A3_p20_bead_mid = sample_plate_thermo['A2'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Thermo - 2))  # Beads to the Right
    A3_p300_bead_side = sample_plate_thermo['A2'].center().move(types.Point(
        x=0.50, y=0, z=p300_offset_Thermo - 7.2))  # Beads to the Right
    A3_p300_bead_top = sample_plate_thermo['A2'].center().move(types.Point(
        x=-1.30, y=0, z=p300_offset_Thermo - 1))  # Beads to the Right
    A3_p300_bead_mid = sample_plate_thermo['A2'].center().move(types.Point(
        x=-0.80, y=0, z=p300_offset_Thermo - 4))  # Beads to the Right
    A3_p300_loc1 = sample_plate_thermo['A2'].center().move(types.Point(
        x=-1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Thermo - 4))
    # Beads to the Right
    A3_p300_loc2 = sample_plate_thermo['A2'].center().move(types.Point(
        x=-1.3, y=0, z=p300_offset_Thermo - 4))  # Beads to the Right
    A3_p300_loc3 = sample_plate_thermo['A2'].center().move(types.Point(
        x=-1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Thermo - 4))
    # Beads to the Right
    # A5_p20_bead_side = sample_plate_thermo['A3'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Thermo - 5))  # Beads to the Right
    # A5_p20_bead_top = sample_plate_thermo['A3'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Thermo + 2))  # Beads to the Right
    # A5_p20_bead_mid = sample_plate_thermo['A3'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Thermo - 2))  # Beads to the Right
    A5_p300_bead_side = sample_plate_thermo['A3'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Thermo - 7.2))  # Beads to the Right
    A5_p300_bead_top = sample_plate_thermo['A3'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Thermo - 1))  # Beads to the Right
    A5_p300_bead_mid = sample_plate_thermo['A3'].center().move(types.Point(
        x=0.80, y=0, z=p300_offset_Thermo - 4))  # Beads to the Right
    A5_p300_loc1 = sample_plate_thermo['A3'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Thermo - 4))
    # Beads to the Right
    A5_p300_loc2 = sample_plate_thermo['A3'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Thermo - 4))  # Beads to the Right
    A5_p300_loc3 = sample_plate_thermo['A3'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Thermo - 4))
    # Beads to the Right
    ##########################################################################

    bypass = protocol.deck.position_for(
        '11').move(types.Point(x=70, y=80, z=130))

    # commands
    if DRYRUN == 'NO':
        protocol.comment("SETTING THERMO and TEMP BLOCK Temperature")
        if real_temp:
            thermocycler.set_block_temperature(4)
            thermocycler.set_lid_temperature(100)
            temp_block.set_temperature(4)
#        temp_block.set_temperature(4)
        thermocycler.open_lid()

    if STEP_TAG == 1:
        protocol.comment('==============================================')
        protocol.comment('--> TAGMENTATION')
        protocol.comment('==============================================')

        protocol.comment('--> Adding Tagmentation Mix ')
        if DRYRUN == 'NO':
            TagVol = 20
            TagMixRep = 10
            TagMixVol = 40
        if DRYRUN == 'YES':
            TagVol = 20
            TagMixRep = 1
            TagMixVol = 40
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            pick_up(p300)
            p300.mix(3, 20, TAG.bottom(z=p300_offset_Temp), rate=0.5)
            p300.aspirate(TagVol, TAG.bottom(z=p300_offset_Temp), rate=0.25)
            p300.dispense(TagVol, sample_plate_thermo[X].bottom(
                z=p300_offset_Thermo), rate=0.25)
            p300.mix(TagMixRep, TagMixVol)
            p300.move_to(sample_plate_thermo[X].top())
            protocol.delay(seconds=2)
            p300.blow_out(sample_plate_thermo[X].top(z=-5))
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            pick_up(p300)
            p300.mix(3, 20, TAG.bottom(z=p300_offset_Temp), rate=0.5)
            p300.aspirate(TagVol, TAG.bottom(z=p300_offset_Temp), rate=0.25)
            p300.dispense(TagVol, sample_plate_thermo[X].bottom(
                z=p300_offset_Thermo), rate=0.25)
            p300.mix(TagMixRep, TagMixVol)
            p300.blow_out(sample_plate_thermo[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            pick_up(p300)
            p300.mix(3, 20, TAG.bottom(z=p300_offset_Temp), rate=0.5)
            p300.aspirate(TagVol, TAG.bottom(z=p300_offset_Temp), rate=0.25)
            p300.dispense(TagVol, sample_plate_thermo[X].bottom(
                z=p300_offset_Thermo), rate=0.25)
            p300.mix(TagMixRep, TagMixVol)
            p300.blow_out(sample_plate_thermo[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

    if STEP_TAGDECK == 1:
        if DRYRUN == 'NO':
            ###################################################################

            thermocycler.close_lid()
            profile_TAG = [
                {'temperature': 55, 'hold_time_minutes': 15}
            ]
            thermocycler.execute_profile(
                steps=profile_TAG, repetitions=1, block_max_volume=50)
            thermocycler.set_block_temperature(10)
        #######################################################################
            thermocycler.open_lid()
    else:
        protocol.pause('Seal, Run ERAT (60min)')

    thermocycler.open_lid()

    if STEP_TSB == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Adapter Ligation')
        protocol.comment('==============================================')

        protocol.comment('--> Adding Tagmentation Stop Buffer')
        if DRYRUN == 'NO':
            if NOMODULES == 'NO':
                TSBVol = 10
                TSBMixRep = 10
                TSBMixVol = 20
            else:
                TSBVol = 10
                TSBMixRep = 10
                TSBMixVol = 10
        if DRYRUN == 'YES':
            if NOMODULES == 'NO':
                TSBVol = 10
                TSBMixRep = 1
                TSBMixVol = 20
            else:
                TSBVol = 10
                TSBMixRep = 1
                TSBMixVol = 10
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            pick_up(p20)
            p20.aspirate(TSBVol, TSB.bottom(z=p20_offset_Temp))
            p20.dispense(TSBVol, sample_plate_thermo[X].bottom(
                z=p20_offset_Thermo))
            p20.mix(TSBMixRep, TSBMixVol)
            p20.blow_out(sample_plate_thermo[X].top(z=-5))
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            p20.pick_up_tip()
            p20.aspirate(TSBVol, TSB.bottom(z=p20_offset_Temp))
            p20.dispense(TSBVol, sample_plate_thermo[X].bottom(
                z=p20_offset_Thermo))
            p20.mix(TSBMixRep, TSBMixVol)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            p20.pick_up_tip()
            p20.aspirate(TSBVol, TSB.bottom(z=p20_offset_Temp))
            p20.dispense(TSBVol, sample_plate_thermo[X].bottom(
                z=p20_offset_Thermo))
            p20.mix(TSBMixRep, TSBMixVol)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()

    if STEP_TSBDECK == 1:
        if DRYRUN == 'NO':
            ###################################################################

            thermocycler.close_lid()
            profile_PTC = [
                {'temperature': 37, 'hold_time_minutes': 15}
            ]
            protocol.comment('Run PTC (15min)')
            thermocycler.execute_profile(
                steps=profile_PTC, repetitions=1, block_max_volume=60)
            thermocycler.set_block_temperature(10)
            ###################################################################
            thermocycler.open_lid()


    # FIXME: Commented out variables are never used in the protocol
    # positions
    ##########################################################################
    #  sample_plate_mag on the Mag Block
    # A1_p20_bead_side = sample_plate_mag['A1'].center().move(types.Point(
        # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A1_p20_bead_top = sample_plate_mag['A1'].center().move(types.Point(
        # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A1_p20_bead_mid = sample_plate_mag['A1'].center().move(types.Point(
        # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    A1_p300_bead_side = sample_plate_mag['A1'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    A1_p300_bead_top = sample_plate_mag['A1'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    A1_p300_bead_mid = sample_plate_mag['A1'].center().move(types.Point(
        x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A1_p300_loc1 = sample_plate_mag['A1'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    A1_p300_loc2 = sample_plate_mag['A1'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A1_p300_loc3 = sample_plate_mag['A1'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A3_p20_bead_side = sample_plate_mag['A2'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A3_p20_bead_top = sample_plate_mag['A2'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A3_p20_bead_mid = sample_plate_mag['A2'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    A3_p300_bead_side = sample_plate_mag['A2'].center().move(types.Point(
        x=1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    A3_p300_bead_top = sample_plate_mag['A2'].center().move(types.Point(
        x=-1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    A3_p300_bead_mid = sample_plate_mag['A2'].center().move(types.Point(
        x=-0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A3_p300_loc1 = sample_plate_mag['A2'].center().move(types.Point(
        x=-1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    A3_p300_loc2 = sample_plate_mag['A2'].center().move(types.Point(
        x=-1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A3_p300_loc3 = sample_plate_mag['A2'].center().move(types.Point(
        x=-1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A5_p20_bead_side = sample_plate_mag['A3'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A5_p20_bead_top = sample_plate_mag['A3'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A5_p20_bead_mid = sample_plate_mag['A3'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    A5_p300_bead_side = sample_plate_mag['A3'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    A5_p300_bead_top = sample_plate_mag['A3'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    A5_p300_bead_mid = sample_plate_mag['A3'].center().move(types.Point(
        x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A5_p300_loc1 = sample_plate_mag['A3'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    A5_p300_loc2 = sample_plate_mag['A3'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A5_p300_loc3 = sample_plate_mag['A3'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A7_p20_bead_side = sample_plate_mag['A4'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A7_p20_bead_top = sample_plate_mag['A4'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A7_p20_bead_mid = sample_plate_mag['A4'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    A7_p300_bead_side = sample_plate_mag['A4'].center().move(types.Point(
        x=1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    A7_p300_bead_top = sample_plate_mag['A4'].center().move(types.Point(
        x=-1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    # A7_p300_bead_mid = sample_plate_mag['A4'].center().move(types.Point(
    # x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A7_p300_loc1 = sample_plate_mag['A4'].center().move(types.Point(
        x=-1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    A7_p300_loc2 = sample_plate_mag['A4'].center().move(types.Point(
        x=-1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A7_p300_loc3 = sample_plate_mag['A4'].center().move(types.Point(
        x=-1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A9_p20_bead_side = sample_plate_mag['A5'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A9_p20_bead_top = sample_plate_mag['A5'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A9_p20_bead_mid = sample_plate_mag['A5'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    A9_p300_bead_side = sample_plate_mag['A5'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    A9_p300_bead_top = sample_plate_mag['A5'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    # A9_p300_bead_mid = sample_plate_mag['A5'].center().move(types.Point(
    # x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A9_p300_loc1 = sample_plate_mag['A5'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    A9_p300_loc2 = sample_plate_mag['A5'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A9_p300_loc3 = sample_plate_mag['A5'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A11_p20_bead_side = sample_plate_mag['A6'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A11_p20_bead_top = sample_plate_mag['A6'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A11_p20_bead_mid = sample_plate_mag['A6'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    A11_p300_bead_side = sample_plate_mag['A6'].center().move(types.Point(
        x=1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    A11_p300_bead_top = sample_plate_mag['A6'].center().move(types.Point(
        x=-1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    # A11_p300_bead_mid = sample_plate_mag['A6'].center().move(types.Point(
    # x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A11_p300_loc1 = sample_plate_mag['A6'].center().move(types.Point(
        x=-1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    A11_p300_loc2 = sample_plate_mag['A6'].center().move(types.Point(
        x=-1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    A11_p300_loc3 = sample_plate_mag['A6'].center().move(types.Point(
        x=-1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))






    # Beads to the Right
    # A7_p20_bead_side = sample_plate_mag['A4'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A7_p20_bead_top = sample_plate_mag['A4'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A7_p20_bead_mid = sample_plate_mag['A4'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    XA7_p300_bead_side = sample_plate_mag['A7'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    XA7_p300_bead_top = sample_plate_mag['A7'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    # A7_p300_bead_mid = sample_plate_mag['A7'].center().move(types.Point(
    # x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    XA7_p300_loc1 = sample_plate_mag['A7'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    XA7_p300_loc2 = sample_plate_mag['A7'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    XA7_p300_loc3 = sample_plate_mag['A7'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A9_p20_bead_side = sample_plate_mag['A5'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A9_p20_bead_top = sample_plate_mag['A5'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A9_p20_bead_mid = sample_plate_mag['A5'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    XA9_p300_bead_side = sample_plate_mag['A8'].center().move(types.Point(
        x=1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    XA9_p300_bead_top = sample_plate_mag['A8'].center().move(types.Point(
        x=-1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    # A9_p300_bead_mid = sample_plate_mag['A8'].center().move(types.Point(
    # x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    XA9_p300_loc1 = sample_plate_mag['A8'].center().move(types.Point(
        x=-1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    XA9_p300_loc2 = sample_plate_mag['A8'].center().move(types.Point(
        x=-1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    XA9_p300_loc3 = sample_plate_mag['A8'].center().move(types.Point(
        x=-1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    # A11_p20_bead_side = sample_plate_mag['A6'].center().move(types.Point(
    # x=-1.8 * 0.50, y=0, z=p20_offset_Mag - 5))  # Beads to the Right
    # A11_p20_bead_top = sample_plate_mag['A6'].center().move(types.Point(
    # x=1.5, y=0, z=p20_offset_Mag + 2))  # Beads to the Right
    # A11_p20_bead_mid = sample_plate_mag['A6'].center().move(types.Point(
    # x=1, y=0, z=p20_offset_Mag - 2))  # Beads to the Right
    XA11_p300_bead_side = sample_plate_mag['A9'].center().move(types.Point(
        x=-1, y=0, z=p300_offset_Mag - 7.6))  # Beads to the Right
    XA11_p300_bead_top = sample_plate_mag['A9'].center().move(types.Point(
        x=1.30, y=0, z=p300_offset_Mag - 1))  # Beads to the Right
    # A11_p300_bead_mid = sample_plate_mag['A9'].center().move(types.Point(
    # x=0.80, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    XA11_p300_loc1 = sample_plate_mag['A9'].center().move(types.Point(
        x=1.3 * 0.8, y=1.3 * 0.8, z=p300_offset_Mag - 4))  # Beads to the Right
    XA11_p300_loc2 = sample_plate_mag['A9'].center().move(types.Point(
        x=1.3, y=0, z=p300_offset_Mag - 4))  # Beads to the Right
    XA11_p300_loc3 = sample_plate_mag['A9'].center().move(types.Point(
        x=1.3 * 0.8, y=-1.3 * 0.8, z=p300_offset_Mag - 4))
    # Beads to the Right
    ##########################################################################

    if STEP_WASH == 1:
        protocol.pause("PLACE sample_plate on MAGNET")
        protocol.comment('==============================================')
        protocol.comment('--> TAGMENTATION WASH')
        protocol.comment('==============================================')

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Removing Supernatant')
        RemoveSup = 90
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 1))
            p300.aspirate(RemoveSup - 30, rate=0.05)
            p300.default_speed = 5
            if X == 'A1':
                p300.move_to(A1_p300_bead_side)
            if X == 'A2':
                p300.move_to(A3_p300_bead_side)
            if X == 'A3':
                p300.move_to(A5_p300_bead_side)
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.05)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            protocol.delay(minutes=0.1)
            p300.aspirate(10, rate=0.05)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 1))
            p300.aspirate(RemoveSup - 30, rate=0.05)
            p300.default_speed = 5
            if X == 'A1':
                p300.move_to(A1_p300_bead_side)
            if X == 'A2':
                p300.move_to(A3_p300_bead_side)
            if X == 'A3':
                p300.move_to(A5_p300_bead_side)
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.05)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            protocol.delay(minutes=0.1)
            p300.aspirate(10, rate=0.05)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 1))
            p300.aspirate(RemoveSup - 30, rate=0.05)
            p300.default_speed = 5
            if X == 'A1':
                p300.move_to(A1_p300_bead_side)
            if X == 'A2':
                p300.move_to(A3_p300_bead_side)
            if X == 'A3':
                p300.move_to(A5_p300_bead_side)
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.05)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            protocol.delay(minutes=0.1)
            p300.aspirate(10, rate=0.05)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> Repeating 3 washes')
        washreps = 3
        for wash in range(washreps):
            protocol.comment('--> TWB Wash #' + str(wash + 1))
            if DRYRUN == 'NO':
                TWBMixRep = 10
                TWBMixVol = 70
            if DRYRUN == 'YES':
                TWBMixRep = 10
                TWBMixVol = 70
            if samplecolumns >= 1:  # ----------------------------------------
                X = 'A1'
                pick_up(p300)if TIPREUSE == 'NO' else \
                    p300.pick_up_tip(TWB_washtip_1)
                p300.aspirate(100, TWB_1.bottom(z=p300_offset_Res))
                if X == 'A1':
                    p300.move_to(A1_p300_bead_top)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_top)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_top)
                p300.dispense(100, rate=0.75)
                if X == 'A1':
                    p300.move_to(A1_p300_bead_mid)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_mid)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_mid)
                p300.mix(TWBMixRep, TWBMixVol)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))

                p300.default_speed = 400
                p300.move_to(bypass)
                if TIPREUSE == 'NO':
                    p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
                else:
                    p300.return_tip()
            if samplecolumns >= 2:  # ----------------------------------------
                X = 'A2'
                pick_up(p300)if TIPREUSE == 'NO' else \
                    p300.pick_up_tip(TWB_washtip_2)
                p300.aspirate(100, TWB_2.bottom(z=p300_offset_Res))
                if X == 'A1':
                    p300.move_to(A1_p300_bead_top)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_top)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_top)
                p300.dispense(100, rate=0.75)
                if X == 'A1':
                    p300.move_to(A1_p300_bead_mid)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_mid)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_mid)
                p300.mix(TWBMixRep, TWBMixVol)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))

                p300.default_speed = 400
                p300.move_to(bypass)
                if TIPREUSE == 'NO':
                    p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
                else:
                    p300.return_tip()
            if samplecolumns >= 3:  # ----------------------------------------
                X = 'A3'
                pick_up(p300)if TIPREUSE == 'NO' else \
                    p300.pick_up_tip(TWB_washtip_3)
                p300.aspirate(100, TWB_3.bottom(z=p300_offset_Res))
                if X == 'A1':
                    p300.move_to(A1_p300_bead_top)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_top)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_top)
                p300.dispense(100, rate=0.75)
                p300.default_speed = 5
                if X == 'A1':
                    p300.move_to(A1_p300_bead_mid)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_mid)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_mid)
                p300.mix(TWBMixRep, TWBMixVol)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
                p300.default_speed = 400
                p300.move_to(bypass)
                if TIPREUSE == 'NO':
                    p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
                else:
                    p300.return_tip()

            if DRYRUN == 'NO':
                protocol.comment('MAGNET ENGAGE')
                mag_block.engage(height_from_base=8.5)
                protocol.delay(minutes=1)
                mag_block.engage(height_from_base=7)
                protocol.delay(minutes=1)
                mag_block.engage(height_from_base=5)
                protocol.delay(minutes=1)

            protocol.comment('--> Remove TWB Wash #' + str(wash + 1))
            RemoveSup = 110
            if samplecolumns >= 1:  # ----------------------------------------
                X = 'A1'
                pick_up(p300)if TIPREUSE == 'NO' else \
                    p300.pick_up_tip(TWB_removetip_1)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
                p300.aspirate(RemoveSup - 30, rate=0.05)
                p300.default_speed = 5
                if X == 'A1':
                    p300.move_to(A1_p300_bead_side)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_side)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_side)
                protocol.delay(minutes=0.1)
                p300.aspirate(20, rate=0.05)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
                protocol.delay(minutes=0.1)
                p300.aspirate(10, rate=0.05)
                p300.move_to(sample_plate_mag[X].top(z=2))
                p300.default_speed = 400
                p300.dispense(200, Liquid_trash)
                p300.move_to(bypass)
                if TIPREUSE == 'NO':
                    p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
                else:
                    p300.return_tip()
            if samplecolumns >= 2:  # ----------------------------------------
                X = 'A2'
                pick_up(p300)if TIPREUSE == 'NO' else \
                    p300.pick_up_tip(TWB_removetip_2)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
                p300.aspirate(RemoveSup - 30, rate=0.05)
                p300.default_speed = 5
                if X == 'A1':
                    p300.move_to(A1_p300_bead_side)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_side)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_side)
                protocol.delay(minutes=0.1)
                p300.aspirate(20, rate=0.05)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
                protocol.delay(minutes=0.1)
                p300.aspirate(10, rate=0.05)
                p300.move_to(sample_plate_mag[X].top(z=2))
                p300.default_speed = 400
                p300.dispense(200, Liquid_trash)
                p300.move_to(bypass)
                if TIPREUSE == 'NO':
                    p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
                else:
                    p300.return_tip()
            if samplecolumns >= 3:  # ----------------------------------------
                X = 'A3'
                pick_up(p300)if TIPREUSE == 'NO' else \
                    p300.pick_up_tip(TWB_removetip_3)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
                p300.aspirate(RemoveSup - 30, rate=0.05)
                p300.default_speed = 5
                if X == 'A1':
                    p300.move_to(A1_p300_bead_side)
                if X == 'A2':
                    p300.move_to(A3_p300_bead_side)
                if X == 'A3':
                    p300.move_to(A5_p300_bead_side)
                protocol.delay(minutes=0.1)
                p300.aspirate(20, rate=0.05)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
                protocol.delay(minutes=0.1)
                p300.aspirate(10, rate=0.05)
                p300.move_to(sample_plate_mag[X].top(z=2))
                p300.default_speed = 400
                p300.dispense(200, Liquid_trash)
                p300.move_to(bypass)
                if TIPREUSE == 'NO':
                    p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
                else:
                    p300.return_tip()

            if DRYRUN == 'NO':
                protocol.comment('MAGNET DISENGAGE')
                mag_block.disengage()

            wash += 1

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=5)

        protocol.comment('--> Removing Residual Supernatant')
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.aspirate(50, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.aspirate(50, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.aspirate(50, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            mag_block.engage(height_from_base=3)
            protocol.delay(minutes=0.5)

            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

    if STEP_PCR == 1:
        protocol.comment('==============================================')
        protocol.comment('--> AMPLIFICATION')
        protocol.comment('==============================================')

        protocol.comment('ADDING PCR')
        if DRYRUN == 'NO':
            PCRVol = 40
            PCRMixRep = 10
            PCRMixVol = 30
        if DRYRUN == 'YES':
            PCRVol = 40
            PCRMixRep = 10
            PCRMixVol = 30
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            pick_up(p300)
            p300.aspirate(PCRVol, PCR.bottom(p300_offset_Temp))
            if X == 'A1':
                p300.move_to(A1_p300_loc1)
            if X == 'A2':
                p300.move_to(A3_p300_loc1)
            if X == 'A3':
                p300.move_to(A5_p300_loc1)
            p300.dispense(PCRVol / 5, rate=0.75)
            p300.default_speed = 5
            if X == 'A1':
                p300.move_to(A1_p300_loc2)
            if X == 'A2':
                p300.move_to(A3_p300_loc2)
            if X == 'A3':
                p300.move_to(A5_p300_loc2)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc3)
            if X == 'A2':
                p300.move_to(A3_p300_loc3)
            if X == 'A3':
                p300.move_to(A5_p300_loc3)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc2)
            if X == 'A2':
                p300.move_to(A3_p300_loc2)
            if X == 'A3':
                p300.move_to(A5_p300_loc2)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc1)
            if X == 'A2':
                p300.move_to(A3_p300_loc1)
            if X == 'A3':
                p300.move_to(A5_p300_loc1)
            p300.dispense(PCRVol / 5, rate=0.75)
            reps = 1
            for x in range(reps):
                if X == 'A1':
                    p300.move_to(A1_p300_loc3)
                if X == 'A2':
                    p300.move_to(A3_p300_loc3)
                if X == 'A3':
                    p300.move_to(A5_p300_loc3)
                p300.mix(PCRMixRep, PCRMixVol)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(PCRMixRep, PCRMixVol)
            p300.move_to(sample_plate_mag[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.default_speed = 400
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            pick_up(p300)
            p300.aspirate(PCRVol, PCR.bottom(p300_offset_Temp))
            if X == 'A1':
                p300.move_to(A1_p300_loc1)
            if X == 'A2':
                p300.move_to(A3_p300_loc1)
            if X == 'A3':
                p300.move_to(A5_p300_loc1)
            p300.dispense(PCRVol / 5, rate=0.75)
            p300.default_speed = 5
            if X == 'A1':
                p300.move_to(A1_p300_loc2)
            if X == 'A2':
                p300.move_to(A3_p300_loc2)
            if X == 'A3':
                p300.move_to(A5_p300_loc2)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc3)
            if X == 'A2':
                p300.move_to(A3_p300_loc3)
            if X == 'A3':
                p300.move_to(A5_p300_loc3)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc2)
            if X == 'A2':
                p300.move_to(A3_p300_loc2)
            if X == 'A3':
                p300.move_to(A5_p300_loc2)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc1)
            if X == 'A2':
                p300.move_to(A3_p300_loc1)
            if X == 'A3':
                p300.move_to(A5_p300_loc1)
            p300.dispense(PCRVol / 5, rate=0.75)
            reps = 1
            for x in range(reps):
                if X == 'A1':
                    p300.move_to(A1_p300_loc3)
                if X == 'A2':
                    p300.move_to(A3_p300_loc3)
                if X == 'A3':
                    p300.move_to(A5_p300_loc3)
                p300.mix(PCRMixRep, PCRMixVol)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(PCRMixRep, PCRMixVol)
            p300.move_to(sample_plate_mag[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.default_speed = 400
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            pick_up(p300)
            p300.aspirate(PCRVol, PCR.bottom(p300_offset_Temp))
            if X == 'A1':
                p300.move_to(A1_p300_loc1)
            if X == 'A2':
                p300.move_to(A3_p300_loc1)
            if X == 'A3':
                p300.move_to(A5_p300_loc1)
            p300.dispense(PCRVol / 5, rate=0.75)
            p300.default_speed = 5
            if X == 'A1':
                p300.move_to(A1_p300_loc2)
            if X == 'A2':
                p300.move_to(A3_p300_loc2)
            if X == 'A3':
                p300.move_to(A5_p300_loc2)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc3)
            if X == 'A2':
                p300.move_to(A3_p300_loc3)
            if X == 'A3':
                p300.move_to(A5_p300_loc3)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc2)
            if X == 'A2':
                p300.move_to(A3_p300_loc2)
            if X == 'A3':
                p300.move_to(A5_p300_loc2)
            p300.dispense(PCRVol / 5, rate=0.75)
            if X == 'A1':
                p300.move_to(A1_p300_loc1)
            if X == 'A2':
                p300.move_to(A3_p300_loc1)
            if X == 'A3':
                p300.move_to(A5_p300_loc1)
            p300.dispense(PCRVol / 5, rate=0.75)
            reps = 1
            for x in range(reps):
                if X == 'A1':
                    p300.move_to(A1_p300_loc3)
                if X == 'A2':
                    p300.move_to(A3_p300_loc3)
                if X == 'A3':
                    p300.move_to(A5_p300_loc3)
                p300.mix(PCRMixRep, PCRMixVol)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(PCRMixRep, PCRMixVol)
            p300.move_to(sample_plate_mag[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.default_speed = 400
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> Adding Barcodes')
        BarcodeVol = 10
        BarcodeMixRep = 10
        BarcodeMixVol = 10
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            p20.pick_up_tip()
            p20.aspirate(BarcodeVol, Barcodes1.bottom(
                z=p20_offset_Temp), rate=0.25)
            p20.dispense(
                BarcodeVol, sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.mix(BarcodeMixRep, BarcodeMixVol)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            p20.pick_up_tip()
            p20.aspirate(BarcodeVol, Barcodes2.bottom(
                z=p20_offset_Temp), rate=0.25)
            p20.dispense(
                BarcodeVol, sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.mix(BarcodeMixRep, BarcodeMixVol)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            p20.pick_up_tip()
            p20.aspirate(BarcodeVol, Barcodes3.bottom(
                z=p20_offset_Temp), rate=0.25)
            p20.dispense(
                BarcodeVol, sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.mix(BarcodeMixRep, BarcodeMixVol)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()

        if DRYRUN == 'NO':
            protocol.pause("PLACE sample_plate on THERMO")

    if STEP_PCRDECK == 1:
        #######################################################################
        protocol.comment('Seal, Run PCR (25min)')

        thermocycler.close_lid()
        profile_PCR_1 = [
            {'temperature': 68, 'hold_time_minutes': 3},
            {'temperature': 98, 'hold_time_minutes': 3}
        ]
        thermocycler.execute_profile(
            steps=profile_PCR_1, repetitions=1, block_max_volume=50)
        profile_PCR_2 = [
            {'temperature': 98, 'hold_time_seconds': 45},
            {'temperature': 62, 'hold_time_seconds': 30},
            {'temperature': 68, 'hold_time_minutes': 2}
        ]
        thermocycler.execute_profile(
            steps=profile_PCR_2, repetitions=5, block_max_volume=50)
        profile_PCR_3 = [
            {'temperature': 68, 'hold_time_minutes': 1}
        ]
        thermocycler.execute_profile(
            steps=profile_PCR_3, repetitions=1, block_max_volume=50)
        thermocycler.set_block_temperature(4)
        #######################################################################
        thermocycler.open_lid()
    else:
        protocol.comment('Seal, Run PCR (60min)')

    Liquid_trash = reservoir['A11']

    if STEP_POSTPCR == 1:
        protocol.pause("PLACE sample_plate on MAGNET")
        protocol.comment('==============================================')
        protocol.comment('--> CLEANUP')
        protocol.comment('==============================================')

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Transferring Supernatant')
        TransferSup = 45
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A1'
            Y = 'A4'
            pick_up(p300)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag + 1), rate=0.05)
            protocol.delay(seconds=0.1)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag), rate=0.05)
            p300.dispense(
                TransferSup + 5, sample_plate_mag[Y].bottom(z=p300_offset_Mag))
            protocol.delay(seconds=0.1)
            p300.blow_out(sample_plate_mag[Y].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A2'
            Y = 'A5'
            pick_up(p300)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag + 1), rate=0.05)
            protocol.delay(seconds=0.1)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag), rate=0.05)
            p300.dispense(
                TransferSup + 5, sample_plate_mag[Y].bottom(z=p300_offset_Mag))
            protocol.delay(seconds=0.1)
            p300.blow_out(sample_plate_mag[Y].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A3'
            Y = 'A6'
            pick_up(p300)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag + 1), rate=0.05)
            protocol.delay(seconds=0.1)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].bottom(z=p300_offset_Mag),
                rate=0.05)
            p300.dispense(
                TransferSup + 5, sample_plate_mag[Y].bottom(z=p300_offset_Mag))
            protocol.delay(seconds=0.1)
            p300.blow_out(sample_plate_mag[Y].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> ADDING WATER')
        for column in sample_plate_mag.rows()[0][3:6][:samplecolumns]:
            pick_up(p300)
            p300.aspirate(40, water)
            p300.dispense(40, column)
            p300.mix(5, 60, column)
            p300.blow_out(column.top())
            p300.drop_tip()

        protocol.comment('--> ADDING AMPure (0.8x)')
        AMPureVol = 45
        AMPureMixRep = 20
        AMPureMixVol = 100
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A4'
            pick_up(p300)
            p300.mix(10, AMPureVol + 10, AMPure.bottom(z=p300_offset_Res))
            p300.aspirate(AMPureVol, AMPure.bottom(
                z=p300_offset_Res), rate=0.25)
            slow_tip_withdrawal(p300, AMPure)
            p300.dispense(AMPureVol, sample_plate_mag[X].bottom(
                z=p300_offset_Mag), rate=0.25)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(AMPureMixRep, AMPureMixVol)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A5'
            pick_up(p300)
            p300.mix(3, AMPureVol + 10, AMPure.bottom(z=p300_offset_Res))
            p300.aspirate(AMPureVol, AMPure.bottom(
                z=p300_offset_Res), rate=0.25)
            slow_tip_withdrawal(p300, AMPure)
            p300.dispense(AMPureVol, sample_plate_mag[X].bottom(
                z=p300_offset_Mag), rate=0.25)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(AMPureMixRep, AMPureMixVol)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A6'
            pick_up(p300)
            p300.mix(3, AMPureVol + 10, AMPure.bottom(z=p300_offset_Res))
            p300.aspirate(AMPureVol, AMPure.bottom(
                z=p300_offset_Res), rate=0.25)
            slow_tip_withdrawal(p300, AMPure)
            p300.dispense(AMPureVol, sample_plate_mag[X].bottom(
                z=p300_offset_Mag), rate=0.25)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(AMPureMixRep, AMPureMixVol)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.delay(minutes=5*real_incubate_time)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=6)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> TRANSFERRING SUPERNAT TO NEW COLUMNS 7, 8, 9')
        TransferSup = 125
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A4'
            Y = 'A7'
            pick_up(p300)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag + 1), rate=0.05)
            protocol.delay(seconds=0.1)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag), rate=0.05)
            p300.dispense(
                TransferSup + 5, sample_plate_mag[Y].bottom(z=p300_offset_Mag))
            protocol.delay(seconds=0.1)
            p300.blow_out(sample_plate_mag[Y].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A5'
            Y = 'A8'
            pick_up(p300)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag + 1), rate=0.05)
            protocol.delay(seconds=0.1)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag), rate=0.05)
            p300.dispense(
                TransferSup + 5, sample_plate_mag[Y].bottom(z=p300_offset_Mag))
            protocol.delay(seconds=0.1)
            p300.blow_out(sample_plate_mag[Y].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A6'
            Y = 'A9'
            pick_up(p300)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].
                bottom(z=p300_offset_Mag + 1), rate=0.05)
            protocol.delay(seconds=0.1)
            p300.aspirate(
                TransferSup / 2, sample_plate_mag[X].bottom(z=p300_offset_Mag),
                rate=0.05)
            p300.dispense(
                TransferSup + 5, sample_plate_mag[Y].bottom(z=p300_offset_Mag))
            protocol.delay(seconds=0.1)
            p300.blow_out(sample_plate_mag[Y].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        mag_block.disengage()

        protocol.comment('--> ADDING AMPure (0.8x)')
        AMPureVol = 15
        AMPureMixRep = 20
        AMPureMixVol = 120
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A7'
            pick_up(p300)
            p300.mix(10, 100, AMPure.bottom(z=p300_offset_Res))
            p300.aspirate(AMPureVol, AMPure.bottom(
                z=p300_offset_Res), rate=0.25)
            slow_tip_withdrawal(p300, AMPure)
            p300.dispense(AMPureVol, sample_plate_mag[X].bottom(
                z=p300_offset_Mag), rate=0.25)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(AMPureMixRep, AMPureMixVol)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A8'
            pick_up(p300)
            p300.mix(3, 100, AMPure.bottom(z=p300_offset_Res))
            p300.aspirate(AMPureVol, AMPure.bottom(
                z=p300_offset_Res), rate=0.25)
            slow_tip_withdrawal(p300, AMPure)
            p300.dispense(AMPureVol, sample_plate_mag[X].bottom(
                z=p300_offset_Mag), rate=0.25)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(AMPureMixRep, AMPureMixVol)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A9'
            pick_up(p300)
            p300.mix(3, 100, AMPure.bottom(z=p300_offset_Res))
            p300.aspirate(AMPureVol, AMPure.bottom(
                z=p300_offset_Res), rate=0.25)
            slow_tip_withdrawal(p300, AMPure)
            p300.dispense(AMPureVol, sample_plate_mag[X].bottom(
                z=p300_offset_Mag), rate=0.25)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            p300.mix(AMPureMixRep, AMPureMixVol)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.delay(minutes=5*real_incubate_time)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=6)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Removing Supernatant...')
        RemoveSup = 140
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A7'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
            p300.aspirate(RemoveSup - 30, rate=0.1)
            p300.default_speed = 5
            if X == 'A7':
                p300.move_to(XA7_p300_bead_side)
            if X == 'A8':
                p300.move_to(XA9_p300_bead_side)
            if X == 'A9':
                p300.move_to(XA11_p300_bead_side)
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.05)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            protocol.delay(minutes=0.1)
            p300.aspirate(10, rate=0.05)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A8'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
            p300.aspirate(RemoveSup - 30, rate=0.1)
            p300.default_speed = 5
            if X == 'A7':
                p300.move_to(XA7_p300_bead_side)
            if X == 'A8':
                p300.move_to(XA9_p300_bead_side)
            if X == 'A9':
                p300.move_to(XA11_p300_bead_side)
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.05)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            protocol.delay(minutes=0.1)
            p300.aspirate(10, rate=0.05)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A9'
            pick_up(p300)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
            p300.aspirate(RemoveSup - 30, rate=0.1)
            p300.default_speed = 5
            if X == 'A7':
                p300.move_to(XA7_p300_bead_side)
            if X == 'A8':
                p300.move_to(XA9_p300_bead_side)
            if X == 'A9':
                p300.move_to(XA11_p300_bead_side)
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.05)
            p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            protocol.delay(minutes=0.1)
            p300.aspirate(10, rate=0.05)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> Repeating 2 washes')
        washreps = 2
        for wash in range(washreps):
            protocol.comment('--> ETOH Wash #' + str(wash + 1))
            ETOHMaxVol = 150
            WASHNUM = 1
            if samplecolumns >= 1:  # ----------------------------------------
                X = 'A7'
                if TIPREUSE == 'NO':
                    pick_up(p300)
                elif WASHNUM == 1:
                    p300.pick_up_tip(W1_ETOH_washtip_1)
                elif WASHNUM == 2:
                    pass  # # FIXME: W2_ETOH_washtip_1 is never defined
                    # p300.pick_up_tip(W2_ETOH_washtip_1)
                p300.aspirate(ETOHMaxVol, EtOH_1.bottom(z=p300_offset_Res))
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_side)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_side)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_side)
                p300.dispense(ETOHMaxVol - 50, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(50, rate=0.5)
                p300.move_to(sample_plate_mag[X].top(z=2))
                p300.default_speed = 5
                p300.move_to(sample_plate_mag[X].top(z=-2))
                protocol.delay(minutes=0.1)
                p300.blow_out(sample_plate_mag[X].top())
                p300.default_speed = 400
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            if samplecolumns >= 2:  # ----------------------------------------
                X = 'A8'
                if TIPREUSE == 'NO':
                    pick_up(p300)
                elif WASHNUM == 1:
                    p300.pick_up_tip(W1_ETOH_washtip_2)
                elif WASHNUM == 2:
                    pass
                    # FIXME: W2_ETOH_washtip_2 is never defined
                    # p300.pick_up_tip(W2_ETOH_washtip_2)
                p300.aspirate(ETOHMaxVol, EtOH_2.bottom(z=p300_offset_Res))
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_side)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_side)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_side)
                p300.dispense(ETOHMaxVol - 50, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(50, rate=0.5)
                p300.move_to(sample_plate_mag[X].top(z=2))
                p300.default_speed = 5
                p300.move_to(sample_plate_mag[X].top(z=-2))
                protocol.delay(minutes=0.1)
                p300.blow_out(sample_plate_mag[X].top())
                p300.default_speed = 400
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            if samplecolumns >= 3:  # ----------------------------------------
                X = 'A9'
                if TIPREUSE == 'NO':
                    pick_up(p300)
                elif WASHNUM == 1:
                    p300.pick_up_tip(W1_ETOH_washtip_3)
                elif WASHNUM == 2:
                    pass
                    # FIXME: W2_ETOH_washtip_3 is undefined
                    # p300.pick_up_tip(W2_ETOH_washtip_3)
                p300.aspirate(ETOHMaxVol, EtOH_3.bottom(z=p300_offset_Res))
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_side)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_side)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_side)
                p300.dispense(ETOHMaxVol - 50, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(50, rate=0.5)
                p300.move_to(sample_plate_mag[X].top(z=2))
                p300.default_speed = 5
                p300.move_to(sample_plate_mag[X].top(z=-2))
                protocol.delay(minutes=0.1)
                p300.blow_out(sample_plate_mag[X].top())
                p300.default_speed = 400
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            protocol.delay(minutes=0.5)

            protocol.comment('--> Remove ETOH Wash #' + str(wash + 1))
            if samplecolumns >= 1:  # ----------------------------------------
                X = 'A7'
                if TIPREUSE == 'NO':
                    pick_up(p300)
                elif WASHNUM == 1:
                    p300.pick_up_tip(W1_ETOH_removetip_1)
                elif WASHNUM == 2:
                    pass
                    # FIXME: W2_ETOH_removetip_1 is never defined
                    # p300.pick_up_tip(W2_ETOH_removetip_1)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
                p300.aspirate(ETOHMaxVol, rate=0.1)
                p300.default_speed = 5
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_side)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_side)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_side)
                protocol.delay(minutes=0.1)
                p300.aspirate(200 - ETOHMaxVol, rate=0.1)
                p300.default_speed = 400
                p300.dispense(200, Liquid_trash)
                p300.move_to(Liquid_trash.top(z=5))
                protocol.delay(minutes=0.12)
                p300.blow_out()
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            if samplecolumns >= 2:  # ----------------------------------------
                X = 'A8'
                if TIPREUSE == 'NO':
                    pick_up(p300)
                elif WASHNUM == 1:
                    p300.pick_up_tip(W1_ETOH_removetip_2)
                elif WASHNUM == 2:
                    pass
                    # FIXME: W2_ETOH_removetip_2 is never defined
                    # p300.pick_up_tip(W2_ETOH_removetip_2)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
                p300.aspirate(ETOHMaxVol, rate=0.1)
                p300.default_speed = 5
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_side)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_side)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_side)
                protocol.delay(minutes=0.1)
                p300.aspirate(200 - ETOHMaxVol, rate=0.1)
                p300.default_speed = 400
                p300.dispense(200, Liquid_trash)
                p300.move_to(Liquid_trash.top(z=5))
                protocol.delay(minutes=0.12)
                p300.blow_out()
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            if samplecolumns >= 3:  # ----------------------------------------
                X = 'A9'
                if TIPREUSE == 'NO':
                    pick_up(p300)
                elif WASHNUM == 1:
                    p300.pick_up_tip(W1_ETOH_removetip_3)
                elif WASHNUM == 2:
                    pass
                    # FIXME: W2_ETOH_removetip_3 is never defined
                    # p300.pick_up_tip(W2_ETOH_removetip_3)
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag + 2))
                p300.aspirate(ETOHMaxVol, rate=0.1)
                p300.default_speed = 5
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_side)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_side)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_side)
                protocol.delay(minutes=0.1)
                p300.aspirate(200 - ETOHMaxVol, rate=0.1)
                p300.default_speed = 400
                p300.dispense(200, Liquid_trash)
                p300.move_to(Liquid_trash.top(z=5))
                protocol.delay(minutes=0.12)
                p300.blow_out()
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            wash += 1

        if DRYRUN == 'NO':
            protocol.delay(minutes=5*real_incubate_time)

        protocol.comment('--> Removing Residual ETOH')
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A7'
            p20.pick_up_tip()
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(20, rate=0.1)if NOMODULES == 'NO' else p20.aspirate(
                10, rate=0.25)
            p20.move_to(bypass)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A8'
            p20.pick_up_tip()
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(20, rate=0.1)if NOMODULES == 'NO' else p20.aspirate(
                10, rate=0.25)
            p20.move_to(bypass)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A9'
            p20.pick_up_tip()
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(20, rate=0.1)if NOMODULES == 'NO' else p20.aspirate(
                10, rate=0.25)
            p20.move_to(bypass)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()

        if DRYRUN == 'NO':
            mag_block.engage(height_from_base=6)
            protocol.comment('AIR DRY')
            protocol.delay(minutes=0.5)

            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> Adding RSB')
        RSBVol = 35
        RSBMixRep = 5
        RSBMixVol = 25
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A7'
            pick_up(p300)
            p300.aspirate(RSBVol, RSB.bottom(p300_offset_Res))
            if X == 'A7':
                p300.move_to(XA7_p300_loc1)
            if X == 'A8':
                p300.move_to(XA9_p300_loc1)
            if X == 'A9':
                p300.move_to(XA11_p300_loc1)
            p300.dispense(RSBVol / 5, rate=0.75)
            p300.default_speed = 5
            if X == 'A7':
                p300.move_to(XA7_p300_loc2)
            if X == 'A8':
                p300.move_to(XA9_p300_loc2)
            if X == 'A9':
                p300.move_to(XA11_p300_loc2)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc3)
            if X == 'A8':
                p300.move_to(XA9_p300_loc3)
            if X == 'A9':
                p300.move_to(XA11_p300_loc3)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc2)
            if X == 'A8':
                p300.move_to(XA9_p300_loc2)
            if X == 'A9':
                p300.move_to(XA11_p300_loc2)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc1)
            if X == 'A8':
                p300.move_to(XA9_p300_loc1)
            if X == 'A9':
                p300.move_to(XA11_p300_loc1)
            p300.dispense(RSBVol / 5, rate=0.75)
            reps = 5
            for x in range(reps):
                p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
                p300.aspirate(RSBVol, rate=0.5)
                if X == 'A7':
                    p300.move_to(XA7_p300_bead_top)
                if X == 'A8':
                    p300.move_to(XA9_p300_bead_top)
                if X == 'A9':
                    p300.move_to(XA11_p300_bead_top)
                p300.dispense(RSBVol, rate=1)
            reps = 3
            # for x in range(reps):
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc2)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc2)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc2)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc1)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc1)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc1)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc2)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc2)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc2)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc3)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc3)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc3)
            p300.mix(RSBMixRep, RSBMixVol, sample_plate_mag.wells_by_name()[X])
            # p300.move_to(Xsample_plate_mag.wells_by_name()
            #              [X].bottom(z=p300_offset_Mag))
            p300.mix(RSBMixRep, RSBMixVol, sample_plate_mag.wells_by_name()[X])
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            if TIPREUSE == 'NO':
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            else:
                p300.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A8'
            pick_up(p300)
            p300.aspirate(RSBVol, RSB.bottom(p300_offset_Res))
            if X == 'A7':
                p300.move_to(XA7_p300_loc1)
            if X == 'A8':
                p300.move_to(XA9_p300_loc1)
            if X == 'A9':
                p300.move_to(XA11_p300_loc1)
            p300.dispense(RSBVol / 5, rate=0.75)
            p300.default_speed = 5
            if X == 'A7':
                p300.move_to(XA7_p300_loc2)
            if X == 'A8':
                p300.move_to(XA9_p300_loc2)
            if X == 'A9':
                p300.move_to(XA11_p300_loc2)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc3)
            if X == 'A8':
                p300.move_to(XA9_p300_loc3)
            if X == 'A9':
                p300.move_to(XA11_p300_loc3)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc2)
            if X == 'A8':
                p300.move_to(XA9_p300_loc2)
            if X == 'A9':
                p300.move_to(XA11_p300_loc2)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc1)
            if X == 'A8':
                p300.move_to(XA9_p300_loc1)
            if X == 'A9':
                p300.move_to(XA11_p300_loc1)
            p300.dispense(RSBVol / 5, rate=0.75)
            reps = 5
            # for x in range(reps):
            #     p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            #     p300.aspirate(RSBVol, rate=0.5)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_bead_top)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_bead_top)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_bead_top)
            #     p300.dispense(RSBVol, rate=1)
            # reps = 3
            # for x in range(reps):
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc2)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc2)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc2)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc1)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc1)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc1)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc2)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc2)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc2)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc3)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc3)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc3)
            p300.mix(RSBMixRep, RSBMixVol, sample_plate_mag.wells_by_name()[X])
            # p300.move_to(Xsample_plate_mag.wells_by_name()
            #              [X].bottom(z=p300_offset_Mag))
            p300.mix(RSBMixRep, RSBMixVol, sample_plate_mag.wells_by_name()[X])
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            if TIPREUSE == 'NO':
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            else:
                p300.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A9'
            pick_up(p300)
            p300.aspirate(RSBVol, RSB.bottom(p300_offset_Res))
            if X == 'A7':
                p300.move_to(XA7_p300_loc1)
            if X == 'A8':
                p300.move_to(XA9_p300_loc1)
            if X == 'A9':
                p300.move_to(XA11_p300_loc1)
            p300.dispense(RSBVol / 5, rate=0.75)
            p300.default_speed = 5
            if X == 'A7':
                p300.move_to(XA7_p300_loc2)
            if X == 'A8':
                p300.move_to(XA9_p300_loc2)
            if X == 'A9':
                p300.move_to(XA11_p300_loc2)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc3)
            if X == 'A8':
                p300.move_to(XA9_p300_loc3)
            if X == 'A9':
                p300.move_to(XA11_p300_loc3)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc2)
            if X == 'A8':
                p300.move_to(XA9_p300_loc2)
            if X == 'A9':
                p300.move_to(XA11_p300_loc2)
            p300.dispense(RSBVol / 5, rate=0.75)
            if X == 'A7':
                p300.move_to(XA7_p300_loc1)
            if X == 'A8':
                p300.move_to(XA9_p300_loc1)
            if X == 'A9':
                p300.move_to(XA11_p300_loc1)
            p300.dispense(RSBVol / 5, rate=0.75)
            reps = 1
            # for x in range(reps):
            #     p300.move_to(sample_plate_mag[X].bottom(z=p300_offset_Mag))
            #     p300.aspirate(RSBVol, rate=0.5)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_bead_top)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_bead_top)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_bead_top)
            #     p300.dispense(RSBVol, rate=1)
            # reps = 1
            # for x in range(reps):
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc2)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc2)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc2)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc1)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc1)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc1)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc2)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc2)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc2)
            #     p300.mix(RSBMixRep, RSBMixVol)
            #     if X == 'A7':
            #         p300.move_to(XA7_p300_loc3)
            #     if X == 'A8':
            #         p300.move_to(XA9_p300_loc3)
            #     if X == 'A9':
            #         p300.move_to(XA11_p300_loc3)
            p300.mix(RSBMixRep, RSBMixVol, sample_plate_mag.wells_by_name()[X])
            # p300.move_to(sample_plate_mag.wells_by_name()
            #              [X].bottom(z=p300_offset_Mag))
            p300.mix(RSBMixRep, RSBMixVol, sample_plate_mag.wells_by_name()[X])
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            if TIPREUSE == 'NO':
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
            else:
                p300.return_tip()

        if DRYRUN == 'NO':
            protocol.delay(minutes=5*real_incubate_time)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=5)

            protocol.delay(minutes=4)

        protocol.comment('--> Transferring Supernatant')

        if NOMODULES == 'NO':
            TransferSup = 30
        else:
            TransferSup = 20
        if samplecolumns >= 1:  # ----------------------------------------
            X = 'A7'
            Y = 'A10'
            p20.pick_up_tip()
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(TransferSup / 2, rate=0.25)
            p20.dispense(
                TransferSup / 2, sample_plate_mag[Y].bottom(z=p20_offset_Mag))
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(TransferSup / 2, rate=0.25)
            p20.dispense(
                TransferSup / 2, sample_plate_mag[Y].bottom(z=p20_offset_Mag))
            p20.move_to(bypass)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 2:  # ----------------------------------------
            X = 'A8'
            Y = 'A11'
            p20.pick_up_tip()
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(TransferSup / 2, rate=0.25)
            p20.dispense(
                TransferSup / 2, sample_plate_mag[Y].bottom(z=p20_offset_Mag))
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(TransferSup / 2, rate=0.25)
            p20.dispense(
                TransferSup / 2, sample_plate_mag[Y].bottom(z=p20_offset_Mag))
            p20.move_to(bypass)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()
        if samplecolumns >= 3:  # ----------------------------------------
            X = 'A9'
            Y = 'A12'
            p20.pick_up_tip()
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(TransferSup / 2, rate=0.25)
            p20.dispense(
                TransferSup / 2, sample_plate_mag[Y].bottom(z=p20_offset_Mag))
            p20.move_to(sample_plate_mag[X].bottom(z=p20_offset_Mag))
            p20.aspirate(TransferSup / 2, rate=0.25)
            p20.dispense(
                TransferSup / 2, sample_plate_mag[Y].bottom(z=p20_offset_Mag))
            p20.move_to(bypass)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

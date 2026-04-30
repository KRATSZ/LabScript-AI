# flake8: noqa

from opentrons import protocol_api
from opentrons import types

metadata = {
    'protocolName': 'Illumina RNA Prep with Enrichment: Normalization',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.9'
    }

DRYRUN = 'NO'

def run(protocol: protocol_api.ProtocolContext):

    [sample_quant_csv] = get_values(  # noqa: F821
        'sample_quant_csv')

    if DRYRUN == 'YES':
        protocol.comment("THIS IS A DRY RUN")
    else:
        protocol.comment("THIS IS A REACTION RUN")


    tiprack_20      = protocol.load_labware('opentrons_96_filtertiprack_20ul', '1')
    tiprack_200     = protocol.load_labware('opentrons_96_filtertiprack_200ul', '4')
    reagent_tube    = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical','5')
    sample_plate    = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt','2')

    # reagent
    RSB               = reagent_tube.wells()[0]

    # pipette
    #p300    = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack_200])
    #p20     = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack_20])
    p300    = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack_200])
    p20     = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=[tiprack_20])

    MaxTubeVol      = 200
    RSBUsed         = 0
    RSBVol          = 0

    bypass = protocol.deck.position_for('11').move(types.Point(x=70,y=80,z=130))

    data = [r.split(',') for r in sample_quant_csv.strip().splitlines() if r][1:]

    # commands

    protocol.comment('==============================================')
    protocol.comment('Reading File')
    protocol.comment('==============================================')

    current = 0
    while current < len(data):

        CurrentWell     = str(data[current][1])
        if float(data[current][2]) > 0:
            InitialVol = float(data[current][2])
        else:
            InitialVol = 0
        if float(data[current][3]) > 0:
            InitialConc = float(data[current][3])
        else:
            InitialConc = 0
        if float(data[current][4]) > 0:
            TargetConc = float(data[current][4])
        else:
            TargetConc = 0
        TotalDNA        = float(InitialConc*InitialVol)
        if TargetConc > 0:
            TargetVol = float(TotalDNA/TargetConc)
        else:
            TargetVol = InitialVol
        if TargetVol > InitialVol:
            DilutionVol = float(TargetVol-InitialVol)
        else:
            DilutionVol = 0
        FinalVol        = float(DilutionVol+InitialVol)
        if TotalDNA > 0 and FinalVol > 0:
            FinalConc       = float(TotalDNA/FinalVol)
        else:
            FinalConc = 0

        if DilutionVol <= 1:
            protocol.comment("Sample "+CurrentWell+": Conc. Too Low, Will Skip")
        elif DilutionVol > MaxTubeVol-InitialVol:
            DilutionVol = MaxTubeVol-InitialVol
            protocol.comment("Sample "+CurrentWell+": Conc. Too High, Will add, "+str(DilutionVol)+"ul, Max = "+str(MaxTubeVol)+"ul")
            RSBVol += MaxTubeVol-InitialVol
        else:
            if DilutionVol <=20:
                protocol.comment("Sample "+CurrentWell+": Using p20, will add "+str(round(DilutionVol,1)))
            elif DilutionVol > 20:
                protocol.comment("Sample "+CurrentWell+": Using p300, will add "+str(round(DilutionVol,1)))
            RSBVol += DilutionVol
        current += 1

    if RSBVol >= 14000:
        protocol.pause("Caution, more than 15ml Required")
    else:
        protocol.comment("RSB Minimum: "+str(round(RSBVol/1000,1)+1)+"ml")

    PiR2 = 176.71
    InitialRSBVol = RSBVol
    RSBHeight = (InitialRSBVol/PiR2)+17.5

    protocol.pause("Proceed")
    protocol.comment('==============================================')
    protocol.comment('Normalizing Samples')
    protocol.comment('==============================================')

    current = 0
    while current < len(data):

        CurrentWell     = str(data[current][1])
        if float(data[current][2]) > 0:
            InitialVol = float(data[current][2])
        else:
            InitialVol = 0
        if float(data[current][3]) > 0:
            InitialConc = float(data[current][3])
        else:
            InitialConc = 0
        if float(data[current][4]) > 0:
            TargetConc = float(data[current][4])
        else:
            TargetConc = 0
        TotalDNA        = float(InitialConc*InitialVol)
        if TargetConc > 0:
            TargetVol = float(TotalDNA/TargetConc)
        else:
            TargetVol = InitialVol
        if TargetVol > InitialVol:
            DilutionVol = float(TargetVol-InitialVol)
        else:
            DilutionVol = 0
        FinalVol        = float(DilutionVol+InitialVol)
        if TotalDNA > 0 and FinalVol > 0:
            FinalConc       = float(TotalDNA/FinalVol)
        else:
            FinalConc = 0

        protocol.comment("Number "+str(data[current])+": Sample "+str(CurrentWell))
#        protocol.comment("Vol Height = "+str(round(RSBHeight,2)))
        HeightDrop = DilutionVol/PiR2
#        protocol.comment("Vol Drop = "+str(round(HeightDrop,2)))

        if DilutionVol <= 0:
        #If the No Volume
            protocol.comment("Conc. Too Low, Skipping")

        elif DilutionVol >= MaxTubeVol-InitialVol:
        #If the Required Dilution volume is >= Max Volume
            DilutionVol = MaxTubeVol-InitialVol
            protocol.comment("Conc. Too High, Will add, "+str(DilutionVol)+"ul, Max = "+str(MaxTubeVol)+"ul")
            p300.pick_up_tip()
            p300.aspirate(DilutionVol, RSB.bottom(RSBHeight-(HeightDrop)))
            RSBHeight -= HeightDrop
#            protocol.comment("New Vol Height = "+str(round(RSBHeight,2)))
            p300.dispense(DilutionVol, sample_plate.wells_by_name()[CurrentWell])
            HighVolMix = 10
            for Mix in range(HighVolMix):
                p300.move_to(sample_plate.wells_by_name()[CurrentWell].center())
                p300.aspirate(100)
                p300.move_to(sample_plate.wells_by_name()[CurrentWell].bottom())
                p300.aspirate(100)
                p300.dispense(100)
                p300.move_to(sample_plate.wells_by_name()[CurrentWell].center())
                p300.dispense(100)
                Mix += 1
            p300.move_to(sample_plate.wells_by_name()[CurrentWell].top())
            protocol.delay(seconds=3)
            p300.blow_out()
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        else:
            if DilutionVol <= 20:
        #If the Required Dilution volume is <= 20ul
                protocol.comment("Using p20 to add "+str(round(DilutionVol,1)))
                p20.pick_up_tip()
                if  round(float(data[current][3]),1) <= 20:
                    p20.aspirate(DilutionVol, RSB.bottom(RSBHeight-(HeightDrop)))
                    RSBHeight -= HeightDrop
                else:
                    p20.aspirate(20, RSB.bottom(RSBHeight-(HeightDrop)))
                    RSBHeight -= HeightDrop
                p20.dispense(DilutionVol, sample_plate.wells_by_name()[CurrentWell])
                p20.move_to(sample_plate.wells_by_name()[CurrentWell].bottom())
        # Mix volume <=20ul
                if DilutionVol+InitialVol <= 20:
                    p20.mix(10,DilutionVol+InitialVol)
                elif DilutionVol+InitialVol > 20:
                    p20.mix(10,20)
                p20.move_to(sample_plate.wells_by_name()[CurrentWell].top())
                protocol.delay(seconds=3)
                p20.blow_out()
                p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()

            elif DilutionVol > 20:
        #If the required volume is >20
                protocol.comment("Using p300 to add "+str(round(DilutionVol,1)))
                p300.pick_up_tip()
                p300.aspirate(DilutionVol, RSB.bottom(RSBHeight-(HeightDrop)))
                RSBHeight -= HeightDrop
                if DilutionVol+InitialVol >= 120:
                    HighVolMix = 10
                    for Mix in range(HighVolMix):
                        p300.move_to(sample_plate.wells_by_name()[CurrentWell].center())
                        p300.aspirate(100)
                        p300.move_to(sample_plate.wells_by_name()[CurrentWell].bottom())
                        p300.aspirate(DilutionVol+InitialVol-100)
                        p300.dispense(100)
                        p300.move_to(sample_plate.wells_by_name()[CurrentWell].center())
                        p300.dispense(DilutionVol+InitialVol-100)
                        Mix += 1
                else:
                    p300.dispense(DilutionVol, sample_plate.wells_by_name()[CurrentWell])
                    p300.move_to(sample_plate.wells_by_name()[CurrentWell].bottom())
                    p300.mix(10,DilutionVol+InitialVol)
                    p300.move_to(sample_plate.wells_by_name()[CurrentWell].top())
                protocol.delay(seconds=3)
                p300.blow_out()
                p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()
        current += 1

    protocol.comment('==============================================')
    protocol.comment('Results')
    protocol.comment('==============================================')

    current = 0
    while current < len(data):

        CurrentWell     = str(data[current][1])
        if float(data[current][2]) > 0:
            InitialVol = float(data[current][2])
        else:
            InitialVol = 0
        if float(data[current][3]) > 0:
            InitialConc = float(data[current][3])
        else:
            InitialConc = 0
        if float(data[current][4]) > 0:
            TargetConc = float(data[current][4])
        else:
            TargetConc = 0
        TotalDNA        = float(InitialConc*InitialVol)
        if TargetConc > 0:
            TargetVol = float(TotalDNA/TargetConc)
        else:
            TargetVol = InitialVol
        if TargetVol > InitialVol:
            DilutionVol = float(TargetVol-InitialVol)
        else:
            DilutionVol = 0
        if DilutionVol > MaxTubeVol-InitialVol:
            DilutionVol = MaxTubeVol-InitialVol
        FinalVol        = float(DilutionVol+InitialVol)
        if TotalDNA > 0 and FinalVol > 0:
            FinalConc       = float(TotalDNA/FinalVol)
        else:
            FinalConc = 0
        protocol.comment("Sample "+CurrentWell+": "+str(round(FinalVol,1))+" at "+str(round(FinalConc,1))+"ng/ul")

        current += 1

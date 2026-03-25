from opentrons import protocol_api

metadata = {'protocolName': 'Automated RoboZooMS Protocol',
            'author': 'Daniel Marfiewicz-Dickinson',
            'description': 'ZooMS Protocol',
            'apiLevel': '2.10'}


# string of asterisks show a pause step that is hidden for testing purposes.

def run(protocol: protocol_api.ProtocolContext):

    [sample_size,
     acid_volume,
     na_oh_volume,
     am_bic_volume,
     transfer_volume,
     trypsin_volume,
     quench_volume,
     acid_demin_yn,
     na_oh_wash_yn,
     one_rack_yn] = get_values(  # noqa: F821
                               'sample_size',
                               'acid_volume',
                               'na_oh_volume',
                               'am_bic_volume',
                               'transfer_volume',
                               'trypsin_volume',
                               'quench_volume',
                               'acid_demin_yn',
                               'na_oh_wash_yn',
                               'one_rack_yn')

    # initialize script logic
    (one_rack,
     acid_demin,
     na_oh_wash_logic) = parse_logic(acid_demin_yn,
                                     na_oh_wash_yn,
                                     one_rack_yn)

    # initialize deck positions of different labware
    ziptip_rack_location = 1
    wellplate_location = 2
    tiprack_2_location = 3
    ext_eppendorf_location = 5
    tiprack_1_location = 6
    se_eppendorf_location = 8
    falcon_tubes_location = 9
    waste_reservoir_location = 11

    # initialize labware used in protocol
    (falcon_tubes,
     tiprack_1,
     tiprack_2,
     ziptip_rack,
     ziptip_wellplate,
     tube_rack,
     ext_tube_rack,
     waste_reservoir) = load_deck(protocol,
                                  se_eppendorf_location,
                                  ext_eppendorf_location,
                                  falcon_tubes_location,
                                  tiprack_1_location,
                                  tiprack_2_location,
                                  ziptip_rack_location,
                                  waste_reservoir_location,
                                  wellplate_location)

    # initialize reagent placement in falcon tubes
    HCl = falcon_tubes.wells()[0]
    conditioning_solution = falcon_tubes.wells()[1]
    NaOH = falcon_tubes.wells()[2]
    washing_solution = falcon_tubes.wells()[3]
    AmBic = falcon_tubes.wells()[4]
    trypsin = falcon_tubes.wells()[5]

    # initialize pipettes used in protocol
    p300, p1000 = load_pipettes(protocol, tiprack_1, tiprack_2, ziptip_rack)
    p300.flow_rate.aspirate, p300.flow_rate.dispense = 10, 10

    # initialise a list of wells that are being used
    (wells_in_use,
     ext_wells_in_use,
     conditioning_wells,
     washing_wells,
     eluting_wells) = initialize_wells(ziptip_wellplate, sample_size,
                                       tube_rack, ext_tube_rack, one_rack)

    # ~~~~~~~~~~~~~~~~~~~Acid Demineralisation~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if acid_demin:  # if acid_demin true do:
        # Add acid for demineralization step
        acid_step(p1000,
                  acid_volume,
                  HCl,
                  wells_in_use)

        protocol.pause("Place samples in fridge for 24 hrs minimum (1-14 days), then centrifuge and continue. DO NOT SWITCH OFF THE ROBOT")  # noqa: E501
        # Technician would manually centrifuge and press "continue"

    # ~~~~~~~~~~~~~~~~~~~NaOH Wash~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if na_oh_wash_logic:
        # Remove acid, add NaOH, remove NaOH to remove humic acids
        na_oh_wash(protocol,
                   p1000,
                   acid_volume,
                   wells_in_use,
                   waste_reservoir,
                   na_oh_volume,
                   NaOH)

    # ~~~~~~~~~~~~~~~~~~~Gelatinisation~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # distribute AmBic into eppendorfs
    # incubate and transfer to second eppendorf rack for digestion
    gelatinize(protocol,
               p1000,
               am_bic_volume,
               AmBic,
               wells_in_use,
               transfer_volume,
               sample_size,
               ext_wells_in_use,
               waste_reservoir,
               acid_demin_yn,
               na_oh_wash_yn,
               acid_volume)

    # ~~~~~~~~~~~~~~~~~~~Trypsin digestion~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # distribute diluted trypsin into samples
    # incubate and then quench the digestion
    digestion(protocol,
              p1000,
              trypsin_volume,
              trypsin,
              ext_wells_in_use,
              quench_volume,
              washing_solution)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Zip-tipping~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # isolate the peptide using filter-tip pipettes and elute
    # ready for MALDI plate spotting
    zip_tip(p1000,
            conditioning_solution,
            conditioning_wells,
            sample_size,
            washing_solution,
            washing_wells,
            p300,
            waste_reservoir,
            ext_wells_in_use,
            eluting_wells)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Protocol End~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Initalisation Functions~~~~~~~~~~~~~~~~~~~~~~~~~


def load_pipettes(protocol, tiprack_1, tiprack_2, ziptip_rack):
    p1000 = protocol.load_instrument('p1000_single',
                                     'right',
                                     tip_racks=[tiprack_1, tiprack_2])
    p300 = protocol.load_instrument('p300_single',
                                    'left',
                                    tip_racks=[ziptip_rack])
    return p300, p1000


def load_deck(protocol,
              se_eppendorf_location,
              ext_eppendorf_location,
              falcon_tubes_location,
              tiprack_1_location,
              tiprack_2_location,
              ziptip_rack_location,
              waste_reservoir_location,
              wellplate_location):

    # list of string references to imported labware for easy changing
    eppendorf_rack_name = 'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap'  # noqa: E501
    falcon_tuberack_name = 'opentrons_6_tuberack_falcon_50ml_conical'
    tiprack_1000uL_name = 'opentrons_96_tiprack_1000ul'
    tiprack_300ul_name = 'opentrons_96_tiprack_300ul'
    waste_reservoir_name = 'nest_12_reservoir_15ml'
    wellplate_name = 'nest_96_wellplate_200ul_flat'

    tube_rack = protocol.load_labware(
                                      eppendorf_rack_name,
                                      se_eppendorf_location
                                     )

    ext_tube_rack = protocol.load_labware(
                                          eppendorf_rack_name,
                                          ext_eppendorf_location
                                         )

    # defaults: 0=HCl, 1=conditioning, 2=NaOH, 3=washing 4=AmBic, 5=trypsin.
    falcon_tubes = protocol.load_labware(
                                         falcon_tuberack_name,
                                         falcon_tubes_location
                                        )

    tiprack_1 = protocol.load_labware(
                                      tiprack_1000uL_name,
                                      tiprack_1_location
                                     )
    tiprack_2 = protocol.load_labware(
                                      tiprack_1000uL_name,
                                      tiprack_2_location
                                     )

    ziptip_rack = protocol.load_labware(
                                        tiprack_300ul_name,
                                        ziptip_rack_location
                                       )

    waste_reservoir = protocol.load_labware(
                                            waste_reservoir_name,
                                            waste_reservoir_location
                                           )

    ziptip_wellplate = protocol.load_labware(
                                             wellplate_name,
                                             wellplate_location
                                            )
    return (falcon_tubes,
            tiprack_1,
            tiprack_2,
            ziptip_rack,
            ziptip_wellplate,
            tube_rack,
            ext_tube_rack,
            waste_reservoir)


def parse_logic(acid_demin_yn, na_oh_wash_yn, one_rack_yn):
    if acid_demin_yn == 'yes':
        acid_demin = True
    else:
        acid_demin = False

    if na_oh_wash_yn == 'yes':
        na_oh_wash_logic = True
    else:
        na_oh_wash_logic = False

    if one_rack_yn == 'yes':
        one_rack = True
    else:
        one_rack = False
    return one_rack, acid_demin, na_oh_wash_logic

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Protocol Methods~~~~~~~~~~~~~~~~~~~~~~~~~~~


def initialize_wells(ziptip_wellplate,
                     sample_size,
                     tube_rack,
                     ext_tube_rack,
                     one_rack):
    wells_in_use = []
    ext_wells_in_use = []

    # initialise a list of wells that are being used in rows left to right,
    #  assuming that there is only one rack available for testing
    if one_rack:
        # create a list of well locations from rows A and B for SE eppendorfs
        print("Only using one rack")
        se_wells = [
                    well for well in (
                                      tube_rack.rows_by_name()['A']
                                      +
                                      tube_rack.rows_by_name()['B']
                                      )
                    ]
        # from the above available list, create a list of only used wells
        wells_in_use = se_wells[:sample_size]

        ext_wells = [
                     well for well in (
                                       tube_rack.rows_by_name()['C']
                                       +
                                       tube_rack.rows_by_name()['D']
                                       )
                    ]
        ext_wells_in_use = ext_wells[:sample_size]

    if not one_rack:
        print("Using two racks")
        # generate a list of wells that are being used based
        # on the amount of samples if two racks are available
        # now going by row, left to right (more intuitive)
        # this allows the use of the "distribute" function below
        # to speed up the transfer!
        se_wells = [
                    wells for wells in (
                                        tube_rack.rows_by_name()['A']
                                        +
                                        tube_rack.rows_by_name()['B']
                                        +
                                        tube_rack.rows_by_name()['C']
                                        +
                                        tube_rack.rows_by_name()['D']
                                        )
                    ]
        wells_in_use = se_wells[:sample_size]

        ext_wells = [
                     wells for wells in (
                                         ext_tube_rack.rows_by_name()['A']
                                         +
                                         ext_tube_rack.rows_by_name()['B']
                                         +
                                         ext_tube_rack.rows_by_name()['C']
                                         +
                                         ext_tube_rack.rows_by_name()['D']
                                         )
                    ]
        ext_wells_in_use = ext_wells[:sample_size]

    # c_wells = conditioning wells
    c_wells_A = [well for well in (ziptip_wellplate.rows_by_name()['A'])]
    c_wells_F = [well for well in (ziptip_wellplate.rows_by_name()['F'])]

    conditioning_wells = c_wells_A + c_wells_F

    # w_wells = washing wells
    w_wells_B = [wells for wells in (ziptip_wellplate.rows_by_name()['B'])]
    w_wells_G = [wells for wells in (ziptip_wellplate.rows_by_name()['G'])]
    washing_wells = w_wells_B + w_wells_G

    # e_wells = eluting wells
    e_wells_C = [wells for wells in (ziptip_wellplate.rows_by_name()['C'])]
    e_wells_H = [wells for wells in (ziptip_wellplate.rows_by_name()['H'])]
    eluting_wells = e_wells_C + e_wells_H

    return (wells_in_use,
            ext_wells_in_use,
            conditioning_wells,
            washing_wells,
            eluting_wells)


def reset_pipette_parameters(pipette):
    # custom method to make sure no settings carry over accidentally
    # can be called at the end of every preparative step
    pipette.well_bottom_clearance.dispense = 1
    pipette.well_bottom_clearance.aspirate = 1
    pipette.flow_rate.aspirate = 150
    pipette.flow_rate.dispense = 300


def acid_step(pipette, acid_volume, HCl, wells_in_use):
    # ~~~~~~~~~~~~~~~~~~~~~~~acidification step~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # due to dispensing clearance don't need tip changing,
    # due to not being a quantitative step exact vol of acid is
    # irrelevant so don't need to waste chemicals (disposal vol = 0)!

    # parameters for the dispensing step, can stay as hidden parameters.
    # set lots of clearance to avoid pipette touching the sample,
    # less waste and contamination.
    pipette.well_bottom_clearance.dispense = 20

    # just drawing up some acid so can afford to be quicker with it.
    pipette.flow_rate.aspirate = 1000

    pipette.pick_up_tip()
    # Add acid for demineralization step
    pipette.distribute(acid_volume,
                       HCl,
                       wells_in_use,
                       new_tip='never',
                       disposal_volume=0)
    pipette.drop_tip()

    reset_pipette_parameters(pipette)


def na_oh_wash(protocol,
               pipette,
               acid_volume,
               wells_in_use,
               waste_reservoir,
               na_oh_volume,
               NaOH):

    # remove acid from the samples to prepare for NaOH wash
    remove_acid(pipette, acid_volume, wells_in_use, waste_reservoir)

    # add NaOH to the empty eppendorf tubes, vortex 1 min then centrifuge 1 min
    dispense_naoh(pipette, na_oh_volume, NaOH, wells_in_use)
    protocol.pause("Manually vortex (1 min) and centrifuge (1 min) before next step.")  # noqa E501

    # remove NaOH wash into AqWaste
    remove_naoh(pipette, na_oh_volume, wells_in_use, waste_reservoir)

    reset_pipette_parameters(pipette)


def remove_naoh(pipette, na_oh_volume, wells_in_use, waste_reservoir):
    # remove NaOH wash into AqWast
    pipette.transfer(na_oh_volume,
                     wells_in_use,
                     waste_reservoir.wells()[0],
                     new_tip='always')


def dispense_naoh(pipette, na_oh_volume, NaOH, wells_in_use):
    # dispense basic wash to samples
    pipette.pick_up_tip()
    pipette.well_bottom_clearance.dispense = 25
    pipette.distribute(na_oh_volume,
                       NaOH,
                       wells_in_use,
                       new_tip='never')
    pipette.drop_tip()

    reset_pipette_parameters(pipette)


def remove_acid(pipette, acid_volume, wells_in_use, waste_reservoir):
    # to make sure you don't hit the samples, in mm
    pipette.well_bottom_clearance.aspirate = 7

    # remove NaOH wash into AqWaste
    pipette.transfer(acid_volume,
                     wells_in_use,
                     waste_reservoir.wells()[0],
                     new_tip='always')

    # to make sure you don't hit the samples, in mm
    pipette.well_bottom_clearance.dispense = 25


def gelatinize(protocol,
               pipette,
               am_bic_volume,
               AmBic,
               wells_in_use,
               transfer_volume,
               sample_size,
               ext_wells_in_use,
               waste_reservoir,
               acid_demin_yn,
               na_oh_wash_yn,
               acid_volume):

    # acid removal step only in NaOH wash
    # so make sure that if there is acid but no wash, acid is still removed!
    if acid_demin_yn is True and na_oh_wash_yn is False:
        remove_acid(pipette,
                    acid_volume,
                    wells_in_use,
                    waste_reservoir)

    # wash sample with ambic three times before
    # adding final ambic to gelatinise
    for i in range(3):
        distribute_am_bic(pipette, am_bic_volume, AmBic, wells_in_use)
        protocol.pause("Vortex briefly followed by 1 min of centrifuge at 130k RPM.")  # noqa: E501
        remove_am_bic(pipette, am_bic_volume, waste_reservoir, wells_in_use)

    # incubation addition of ambic
    distribute_am_bic(pipette, am_bic_volume, AmBic, wells_in_use)

    protocol.pause("1 hr incubation period @ 65degrees C, followed by centrifuge for 1 min.")  # noqa E501

    transfer_am_bic(pipette,
                    sample_size,
                    transfer_volume,
                    wells_in_use,
                    ext_wells_in_use)


def transfer_am_bic(pipette,
                    sample_size,
                    transfer_volume,
                    wells_in_use,
                    ext_wells_in_use):

    # transfer ambic extract
    # into a seperate eppendorf tube for trypsin digestion

    # some clearance to avoid collisions
    pipette.well_bottom_clearance.aspirate = 7
    for i in range(sample_size):
        pipette.transfer(transfer_volume,
                         wells_in_use[i],
                         ext_wells_in_use[i],
                         new_tip='always')

    reset_pipette_parameters(pipette)


def distribute_am_bic(pipette, am_bic_volume, AmBic, wells_in_use):
    # distribute Ammonium Bicarbonate to the samples
    pipette.well_bottom_clearance.dispense = 20
    pipette.flow_rate.aspirate = 1000

    pipette.distribute(am_bic_volume,
                       AmBic,
                       wells_in_use,
                       disposal_volume=0)

    reset_pipette_parameters(pipette)


def remove_am_bic(pipette, am_bic_volume, waste_reservoir, wells_in_use):

    # distribute Ammonium Bicarbonate to the samples
    pipette.well_bottom_clearance.dispense = 20
    pipette.flow_rate.aspirate = 1000

    pipette.transfer(am_bic_volume,
                     wells_in_use,
                     waste_reservoir.wells()[0],
                     disposal_volume=0,
                     new_tip='always')

    reset_pipette_parameters(pipette)


def digestion(protocol,
              pipette,
              trypsin_volume,
              trypsin,
              ext_wells_in_use,
              quench_volume,
              washing_solution):

    # adding trypsin to the EXT samples

    distribute_trypsin(pipette, trypsin_volume, trypsin, ext_wells_in_use)
    protocol.pause("Incubate overnight @37deg C")

    # quench trypsin digestion with a greater amount of diluted TFA
    # probably a good thing to test in lab
    quench_trypsin(pipette, quench_volume, washing_solution, ext_wells_in_use)


def quench_trypsin(pipette, quench_volume, washing_solution, ext_wells_in_use):
    pipette.transfer(quench_volume,
                     washing_solution,
                     ext_wells_in_use,
                     mix_after=(5, 100),  # instead of vortex, mix quickly
                     disposal_volume=0,
                     new_tip='always')


def distribute_trypsin(pipette, trypsin_volume, trypsin, ext_wells_in_use):
    """Protocol."""
    pipette.transfer(trypsin_volume,
                     trypsin,
                     ext_wells_in_use,
                     new_tip='always',  # avoid contamination
                     mix_after=(5, 100))  # mix the added trypsin

    reset_pipette_parameters(pipette)


def zip_tip(p1000,
            conditioning_solution,
            conditioning_wells,
            sample_size,
            washing_solution,
            washing_wells,
            p300,
            waste_reservoir,
            ext_wells_in_use,
            eluting_wells):
    """Protocol."""
    # prepare the wellplate with all of the appropriate wells
    prepare_wellplates(p1000,
                       conditioning_solution,
                       conditioning_wells,
                       sample_size,
                       washing_solution,
                       washing_wells,
                       p300)

    # do all of these steps per sample being analysed, with the same pipette
    for i in range(sample_size):

        isolate_peptides(p300,
                         conditioning_wells,
                         i,
                         washing_wells,
                         waste_reservoir,
                         ext_wells_in_use)

        # due to flat bottom well need low clearance
        # so that air is not drawn accidentally
        p300.well_bottom_clearance.dispense = 1

        # elute sample from filter into well (draw up conditioning solution
        # dispense into eluting well and mix 10 times)
        p300.transfer(100,
                      conditioning_wells[i],
                      eluting_wells[i],
                      new_tip='never',
                      mix_after=(10, 50))

        p300.drop_tip()


def isolate_peptides(p300,
                     conditioning_wells,
                     i,
                     washing_wells,
                     waste_reservoir,
                     ext_wells_in_use):
    """Protocol."""
    p300.pick_up_tip()

    # Condition the zip tip with 100 ul conditioning solution twice
    p300.mix(2, 100, conditioning_wells[i])

    # make sure that pipette tip doesn't dip into waste!
    p300.well_bottom_clearance.dispense = 20

    # wash the zip tip with 50 ul of washing solution twice
    for x in range(2):
        p300.transfer(50,
                      washing_wells[i],
                      waste_reservoir.wells()[0],
                      new_tip='never')

    # draw up sample 10 times with 100 ul to isolate peptide in the filter tip
    p300.mix(10, 100, ext_wells_in_use[i])

    # wash the zip tip with 50 ul of washing solution twice again
    for x in range(2):
        p300.transfer(50,
                      washing_wells[i],
                      waste_reservoir.wells()[0],
                      new_tip='never')


def prepare_wellplates(p1000,
                       conditioning_solution,
                       conditioning_wells,
                       sample_size,
                       washing_solution,
                       washing_wells,
                       p300):
    """Protocol."""
    # Conditioning solution added to well plate
    p1000.distribute(250,
                     conditioning_solution,
                     conditioning_wells[:sample_size],
                     disposal_volume=0)
    # washing solution added to well plate
    p1000.distribute(350,
                     washing_solution,
                     washing_wells[:sample_size],
                     disposal_volume=0)
    # make sure that pipette tip doesn't dip into waste!
    p300.well_bottom_clearance.dispense = 20

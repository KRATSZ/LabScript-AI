metadata = {
    'protocolName': 'PCR Preparation',
    'author': 'Opentrons',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(protocol):

    [number_of_DNA_samples,
        number_of_oligo_standards] = get_values(  # noqa: F821
        "number_of_DNA_samples", "number_of_oligo_standards")

    # check invalid parameters
    number_of_DNA_samples = int(number_of_DNA_samples)
    number_of_oligo_standards = int(number_of_oligo_standards)

    if number_of_DNA_samples + number_of_oligo_standards > 30:
        raise Exception('Too many samples and standards for one plate.')

    # load labware
    tips10 = protocol.load_labware('opentrons_96_tiprack_10ul', 1)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tubes = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 5)

    # modules
    temp_mod = protocol.load_module('temperature module', 4)
    temp_plate = temp_mod.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul')

    temp_mod.set_temperature(8)

    # pipettes
    p10 = protocol.load_instrument('p10_single', mount='right',
                                   tip_racks=[tips10])
    p300 = protocol.load_instrument('p300_single', mount='left',
                                    tip_racks=[tips300])

    # master mix setup
    master_mix = tubes.wells('A1')

    # DNA sample sources setup
    DNA_samples = tubes.wells()[1:(number_of_DNA_samples+1)]

    # destinations setup
    dests_triplicates = [temp_plate.rows()[start][(3*i):(3*i+3)]
                         for i in range(4) for start in range(8)]

    DNA_dests = dests_triplicates[0:number_of_DNA_samples]
    pc_dests = dests_triplicates[number_of_DNA_samples]
    NTC_dests = dests_triplicates[number_of_DNA_samples+1]
    oligo_dests = dests_triplicates[(len(dests_triplicates) -
                                    number_of_oligo_standards):
                                    len(dests_triplicates)]

    # distribute master mix to all destination wells for DNA, oligo, positive
    # control, and NTC
    mm_dests = [well
                for set in [DNA_dests, [pc_dests], [NTC_dests], oligo_dests]
                for well in set]
    for trip in mm_dests:
        p300.distribute(15, master_mix, trip)

    # transfer DNA samples to corresponding triplicate locations
    for source, dests in zip(DNA_samples, DNA_dests):
        p10.transfer(5,
                     source,
                     dests,
                     new_tip='always',
                     blow_out=True)

    protocol.pause('Please replace the master mix tube'
                   'and DNA sample tubes with '
                   'positive control, NTC and oligo standard tubes before '
                   'resuming.')

    # transfer positive control to corresponding triplicate location
    positive_control = tubes.wells('C6')
    p10.transfer(5,
                 positive_control,
                 pc_dests,
                 new_tip='always',
                 blow_out=True)

    # transfer NTC to corresponding triplicate location
    NTC = tubes.wells('D6')
    p10.transfer(5,
                 NTC,
                 NTC_dests,
                 new_tip='always',
                 blow_out=True)

    # oligo standard sources setup
    oligo_standards = tubes.wells()[:number_of_oligo_standards]

    # transfer oligo standards to corresponding triplicate locations
    for source, dests in zip(oligo_standards, oligo_dests):
        p10.transfer(5,
                     source,
                     dests,
                     new_tip='always',
                     blow_out=True)

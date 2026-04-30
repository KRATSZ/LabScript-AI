import math

metadata = {
    'protocolName': 'Illumina Nextera XT NGS Prep 3: Normalize Libraries',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.2'
    }


def run(protocol):
    [pip_type, pip_mount, no_of_samps, mixLN] = get_values(  # noqa: F821
     'pip_type', 'pip_mount', 'no_of_samps', 'mixLN')

    # labware setup
    mag_deck = protocol.load_module('magdeck', '4')
    mag_plate = mag_deck.load_labware('biorad_96_wellplate_200ul_pcr')
    in_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '5', 'Load Plate'
    )
    out_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '1', 'Final Plate (empty)'
    )
    trough = protocol.load_labware(
        'usascientific_12_reservoir_22ml', '2', 'Reservoir, 12-channel'
    )
    # reagent setup
    lna1 = trough['A1']  # Library Normalization Additives 1
    lnb1 = trough['A2']  # Library Normalization Beads 1
    lnw1 = trough['A3']  # Library Normalization Wash 1
    lns1 = trough['A4']  # Library Normalization Storage Buffer
    naoh = trough['A5']  # 0.1 N NaOH
    liquid_trash = trough['A12'].top()

    tip_no = no_of_samps * 4 + 3
    no_racks = tip_no//96 + (1 if tip_no % 96 > 0 else 0)
    tips = [
        protocol.load_labware('opentrons_96_tiprack_300ul', str(slot))
        for slot in range(6, 7+no_racks)
    ]

    pip = protocol.load_instrument(pip_type, pip_mount, tip_racks=tips)
    pipC = pip_type.split('_')[1]

    if pipC == 'multi':
        num_cols = math.ceil(no_of_samps/8)
        inputs = in_plate.rows()[0][:num_cols]
        mag = mag_plate.rows()[0][:num_cols]
        outputs = out_plate.rows()[0][:num_cols]
    else:
        inputs = [well for well in in_plate.wells()][:no_of_samps]
        mag = [well for well in mag_plate.wells()][:no_of_samps]
        outputs = [well for well in out_plate.wells()][:no_of_samps]

    # Transfer 20 uL supernatant to new plate
    pip.transfer(20, inputs, mag, new_tip='always')

    # Transfer 44 uL LNA1 per sample to trough and
    # 8 uL LNB1 per sample to trough if mixing
    if mixLN:
        lna_vol = round(no_of_samps*1.05*44)
        pip.transfer(lna_vol, lna1, trough['A6'])
        lnb_vol = round(no_of_samps*1.05*8)
        pip.pick_up_tip()
        pip.mix(5, 50, lnb1)
        pip.transfer(lnb_vol, lnb1, trough['A6'], new_tip='never')
        pip.mix(10, 50, trough['A6'])
        pip.drop_tip()

    # Transfer 45 uL combined LNA1 and LNB1 to each library
    pip.transfer(45, trough['A6'], [well.top() for well in mag])

    protocol.pause("Shake at 1800 rpm for 30 minutes. Place the plate \
    back on the MagDeck in slot 4.")

    # Turn on MagDeck for 2 minutes
    mag_deck.engage()
    protocol.delay(minutes=2)

    # Remove supernatant from each well
    for well in mag:
        pip.transfer(65, well, liquid_trash)

    # Wash beads twice with LNW1
    for cycle in range(2):
        pip.transfer(45, lnw1, [well.top() for well in mag])
        protocol.pause("Shake at 1800 rpm for 5 minutes. \
        Place the plate back on the MagDeck in slot 4.")
        protocol.delay(minutes=2)
        for well in mag:
            pip.transfer(50, well, liquid_trash)

    # Add 30 uL NaOH to each well
    mag_deck.disengage()
    pip.distribute(30, naoh, [well.top() for well in mag])

    protocol.pause("Shake at 1800 rpm for 5 minutes. Place the plate back on \
        the MagDeck in slot 4.")

    # Turn on MagDeck for 2 minutes
    mag_deck.engage()
    protocol.delay(minutes=2)

    # Add 30 uL LNS1 to each well of a new plate
    pip.distribute(30, lns1, [well.top() for well in outputs])

    # Add supernatant to new plate
    for well, dest in zip(mag, outputs):
        pip.transfer(30, well, dest)

    # Disengage MagDeck
    mag_deck.disengage()

import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Twist Library Prep || Part 3: PCR Amplification',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p20type, p300type, num, mag_gen, mag_plate,
     cold, sp, res, mm, waste] = get_values(  # noqa: F821
        'p20type', 'p300type', 'num', 'mag_gen', 'mag_plate',
        'cold', 'sp', 'res', 'mm', 'waste')

    # Variables; these are injected when downloaded from the protocol
    # Library. Listed here for ease of access.
    p20name = p20type  # should be string (ex. 'p20_multi_gen2')
    p300name = p300type  # should be string (ex. 'p300_multi')
    num_samps = num  # should be int, 1-96
    mag_version = mag_gen  # should be name of magdeck (string)
    mag_plate_type = mag_plate  # should be string (name of labware)
    cold_mod = cold  # if using module to keep samples cold
    pcr_plate_type = sp  # should be string (name of labware)
    res_type = res  # should be string (name of labware)
    mm_labware_type = mm  # should be string (name of labware)
    waste_loc = waste  # should be string (labware or 'fixed_trash')

    # Load labware and pipettes
    p20tips = [protocol.load_labware('opentrons_96_tiprack_20ul', '2')]
    p300tips = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', s) for s in ['3', '6', '9']
            ]
    p20 = protocol.load_instrument(p20name, 'left', tip_racks=p20tips)
    p300 = protocol.load_instrument(p300name, 'right', tip_racks=p300tips)

    pcr_plate = protocol.load_labware(pcr_plate_type, '1')
    rsvr = protocol.load_labware(res_type, '8')
    kapa_labware = protocol.load_labware(mm_labware_type, '5')

    if cold_mod == 'None':
        twist_udi = protocol.load_labware(
            'biorad_96_wellplate_200ul_pcr', '4', 'Twist UDI Plate')
    else:
        temp_mod = protocol.load_module(cold_mod, '4')
        twist_udi = temp_mod.load_labware(
            'biorad_96_wellplate_200ul_pcr', 'Twist UDI Plate')
        temp_mod.set_temperature(4)

    magdeck = protocol.load_module(mag_version, '10')
    magplate = magdeck.load_labware(mag_plate_type)

    if waste_loc == 'fixed_trash':
        liq_waste = protocol.fixed_trash['A1']
    else:
        liq_waste = protocol.load_labware(waste_loc, '11').wells()[0].top()

    # Create variables based on the number of samples
    num_cols = math.ceil(num_samps/8)
    pcr_wells = pcr_plate.wells()[:num_samps]
    pcr_cols = pcr_plate.rows()[0][:num_cols]
    twist_wells = twist_udi.wells()[:num_samps]
    twist_cols = twist_udi.rows()[0][:num_cols]
    mag_wells = magplate.wells()[:num_samps]
    mag_cols = magplate.rows()[0][:num_cols]
    kapa_hifi_holder = [[kapa_labware[w]]*32 for w in ['A1', 'A2', 'A3']]
    kapa_hifi = [d for dd in kapa_hifi_holder for d in dd]

    magbeads = rsvr['A1']
    if res == 'beckman_4_reservoir_38ml':
        etoh1 = [rsvr['A2'] for _ in range(num_samps)]
        etoh2 = [rsvr['A3'] for _ in range(num_samps)]
        elution = rsvr['A4']
    else:
        etoh1 = [rsvr['A3'] for _ in range(48)]+[rsvr['A4'] for _ in range(48)]
        etoh2 = [rsvr['A5'] for _ in range(48)]+[rsvr['A6'] for _ in range(48)]
        elution = rsvr['A12']

    # Assign variables to pipettes dependent on single/multi
    if p20name.split('_')[1] == 'multi':
        p20twist = twist_cols
        p20mag = mag_cols
    else:
        p20twist = twist_wells
        p20mag = mag_wells

    if p300name.split('_') == 'multi':
        p300mag = mag_cols
        p300pcr = pcr_cols
    else:
        p300mag = mag_wells
        p300pcr = pcr_wells

    # Function for picking up tips. Pauses and prompts for replacing tips
    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            protocol.pause('Please replace tips')
            pip.reset_tipracks()
            pip.pick_up_tip()

    # Function for producing comment and transfer/mix/blow
    def transfer(reagent, vol, src, dest, pip, mix_times=3):
        protocol.comment(f'Adding {vol}uL of {reagent} to each sample...')
        for s, d in zip(src, dest):
            pick_up(pip)
            pip.aspirate(vol, s)
            pip.dispense(vol, d)
            pip.mix(mix_times, pip.hw_pipette['working_volume'])
            pip.blow_out()
            pip.drop_tip()

    # Add 10uL of Twist UDI adapters to each sample in PCR plate
    transfer('Twist Adapters', 10, p20twist, p20mag, p20)

    # Add 25uL of KAPA HiFi HotStart ReadyMix to each sample
    transfer('KAPA HiFi HotStart ReadyMix', 25, kapa_hifi, p300mag, p300)

    msg1 = 'Please seal plate, spin down, & transfer to thermocycler. When \
    complete, return plate to MagDeck. Make sure magbeads are mixed and in A1 \
    of the reservoir. When ready, click RESUME.'
    protocol.pause(msg1)

    # Adding 50uL of magbeads to samples then moving to magplate
    protocol.comment('Adding 50uL of Magbeads, mixing, & transferring...')
    for well in p300mag:
        pick_up(p300)
        p300.aspirate(50, magbeads)
        p300.dispense(50, well)
        p300.mix(10, 90, well)
        p300.blow_out()
        p300.drop_tip()

    protocol.comment('Incubating for 5 minutes at room temperature...')
    protocol.delay(minutes=5)

    magdeck.engage()
    protocol.comment('Incubating with magnetic engaged for 1 minute...')
    protocol.delay(minutes=1)

    protocol.comment('Removing supernatant...')
    for well in p300mag:
        pick_up(p300)
        p300.aspirate(100, well)
        p300.dispense(100, liq_waste)
        p300.drop_tip()

    def wash(reagent):
        p300.flow_rate.dispense = 25
        p300.flow_rate.aspirate = 100
        protocol.comment('Adding ethanol...')
        for etoh, well in zip(reagent, p300mag):
            pick_up(p300)
            p300.aspirate(200, etoh)
            p300.dispense(200, well)
            p300.drop_tip()

        protocol.comment('Incubating for 1 minute...')
        protocol.delay(minutes=1)

        protocol.comment('Removing supernatant')
        p300.flow_rate.aspirate = 25
        p300.flow_rate.dispense = 100
        for well in p300mag:
            pick_up(p300)
            p300.aspirate(200, well)
            p300.dispense(200, liq_waste)
            p300.drop_tip()

    wash(etoh1)
    wash(etoh2)

    protocol.comment('Air drying for 5 minutes...')
    protocol.delay(minutes=5)
    magdeck.disengage()

    protocol.comment('Adding 22uL of elution buffer...')
    for well in p300mag:
        pick_up(p300)
        p300.aspirate(22, elution)
        p300.dispense(22, well)
        p300.mix(5, 20, well)
        p300.blow_out()
        p300.drop_tip()

    protocol.comment('Incubating for 2 minutes...')
    protocol.delay(minutes=2)

    magdeck.engage()
    protocol.comment('Incubating for 3 minutes...')
    protocol.delay(minutes=3)

    protocol.comment('Transferring 20uL of elution to PCR plate...')
    for src, dest in zip(p300mag, p300pcr):
        pick_up(p300)
        p300.aspirate(20, src)
        p300.dispense(20, dest)
        p300.blow_out()
        p300.drop_tip()

    protocol.comment('Protocol complete!')

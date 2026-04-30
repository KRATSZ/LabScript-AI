import os
import csv

metadata = {
    'protocolName': 'BP Genomics RNA Extraction',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}


def run(protocol):
    [samps, mnt20, m1k, reagent_labware] = get_values(  # noqa: F821
        'samps', 'mnt20', 'm1k', 'reagent_labware')

    # load labware and pipettes
    if samps > 16:
        raise Exception('This protocol is in review; the maximum number of \
        supported samples is: 16')
    tips1k = protocol.load_labware('opentrons_96_filtertiprack_1000ul', '6')
    # tips20 definition needs to be updated - for current version of p.library
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', '3')

    p20 = protocol.load_instrument('p20_single_gen2', mnt20)
    p1k = protocol.load_instrument('p1000_single_gen2', m1k)

    magdeck = protocol.load_module('magdeck', '4')
    magheight = 13.7
    magplate = magdeck.load_labware(
                'nest_96_wellplate_1000ul', 'NEST 1mL Deep Well Plate')
    flatplate = protocol.load_labware(
                'nest_96_wellplate_100ul_pcr_full_skirt', '1', 'Elution Plate')
    liqwaste = protocol.load_labware(
                'nest_1_reservoir_195ml', '8', 'Liquid Waste')
    waste = liqwaste['A1'].top()  # may need to change
    if reagent_labware == 'nest_12_reservoir_15ml':
        trough = protocol.load_labware(
                    reagent_labware, '2', 'Trough with Reagents')
        ie_rna = trough['A1']
        bind1 = trough['A2']
        washbuffer = trough['A5']
        washbuffer2 = trough['A7']
        ethanol = trough['A9']
        ethanol2 = trough['A9']
        water = trough['A12']
    else:
        tuberack = protocol.load_labware(
                    reagent_labware, '2',
                    'Opentrons 24 Tuberack with Reagents')
        ie_rna = tuberack['A1']
        bind1 = tuberack['A3']
        washbuffer = tuberack['A5']
        washbuffer2 = tuberack['C1']
        ethanol = tuberack['C3']
        ethanol2 = tuberack['C4']
        water = tuberack['C6']

    magsamps = magplate.wells()[:samps]
    elutes = flatplate.wells()[:samps]

    # Tip tracking between runs
    if not protocol.is_simulating():
        file_path = '/data/csv/tiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial tip count tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    tip_count_list = []
    if protocol.is_simulating():
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    p20count = int(tip_count_list[0])
    p1kcount = int(tip_count_list[1])

    def pick_up(pip):
        nonlocal p20count
        nonlocal p1kcount

        if pip == p20:
            if p20count == 96:
                p20.home()
                protocol.pause('Out of 20ul tips. Please replace in slot 3.')
                tips20.reset()
                p20count = 0

            p20.pick_up_tip(tips20.wells()[p20count])
            p20count += 1
        else:
            if p1kcount == 96:
                p1k.home()
                protocol.pause('Out of 1000ul tips. Please replace in slot 6.')
                tips1k.reset()
                p1kcount = 0

            p1k.pick_up_tip(tips1k.wells()[p1kcount])
            p1kcount += 1

    # From nCoV - Add 4ul internal extraction control RNA
    # pick_up(p20)
    p20.flow_rate.aspirate = 10
    p20.flow_rate.dispense = 20
    p20.flow_rate.blow_out = 500

    for dest in magsamps:
        pick_up(p20)
        p20.aspirate(2, ie_rna.top())
        p20.aspirate(4, ie_rna)
        p20.dispense(6, dest)
        p20.blow_out(dest.top(-2))
        p20.touch_tip()
        p20.drop_tip()

    # Step 3 - Mix bind buffer, then add to samples
    pick_up(p1k)
    p1k.aspirate(800, bind1)
    p1k.dispense(790, bind1)
    for _ in range(9):
        p1k.aspirate(790)
        p1k.dispense(790)
    p1k.dispense(10)
    p1k.blow_out(bind1.top())

    # function for mixing 800ul with p1000
    def well_mix(reps, d):
        for _ in range(reps):
            p1k.aspirate(200, d.top(-20))
            p1k.aspirate(200, d.top(-30))
            p1k.aspirate(400, d)
            p1k.dispense(800, d.top(-25))

    for dest in magsamps:
        if not p1k.hw_pipette['has_tip']:
            pick_up(p1k)
        p1k.transfer(580, bind1, dest.top(-25), new_tip='never')
        well_mix(5, dest)
        p1k.blow_out(dest.top())
        p1k.drop_tip()

    protocol.comment('Inucbating at room temp for 5 minutes.')
    protocol.delay(minutes=5)

    # Step 4 - engate magdeck for 6 minutes
    magdeck.engage(height=magheight)
    protocol.comment('Incubating on MagDeck for 6 minutes')
    protocol.delay(minutes=6)

    # Step 5 - remove supernatant
    def supernatant_removal(vol, s):
        tvol = vol-400
        pick_up(p1k)
        p1k.aspirate(200, s.top(-15))
        p1k.aspirate(200, s.top(-30))
        p1k.aspirate(tvol, s)
        p1k.dispense(vol, waste)
        p1k.drop_tip()

    for src in magsamps:
        supernatant_removal(980, src)

    magdeck.disengage()

    def wash_step(src, vol, mtimes):
        for dest in magsamps:
            pick_up(p1k)
            p1k.transfer(vol, src, dest.top(-25), new_tip='never', air_gap=50)
            well_mix(mtimes, dest)
            p1k.blow_out(dest.top())
            p1k.drop_tip()

        magdeck.engage(height=magheight)
        protocol.comment('Incubating on MagDeck for 5 minutes.')
        protocol.delay(minutes=5)

        for src in magsamps:
            supernatant_removal(vol, src)

        magdeck.disengage()

    # Step 6, 7, 8
    wash_step(washbuffer, 800, 10)

    wash_step(washbuffer2, 800, 5)

    # Step 9, 10, 11
    wash_step(ethanol, 800, 4)

    wash_step(ethanol2, 800, 4)

    # Additional wash step, if needed

    # Step 19 - allow beads to dry for 10 minutes
    protocol.comment('Allowing beads to air dry for 10 minutes.')
    protocol.delay(minutes=10)

    # Remove any extra residual liquid
    for src in magsamps:
        pick_up(p1k)
        p1k.transfer(100, src, waste, new_tip='never')
        p1k.drop_tip()

    # Step 20 - Add 40 of nuclease free water and incubate for 2 minutes
    def mix20(mtimes, d):
        p20.aspirate(20, d)
        p20.dispense(19, d)
        for _ in range(mtimes-1):
            p20.aspirate(19, d)
            p20.dispense(19, d)
        p20.dispense(1, d)
        p20.blow_out()

    for dest in magsamps:
        pick_up(p20)
        p20.transfer(20, water, dest.top(), new_tip='never')
        p20.blow_out(dest.top())
        p20.transfer(20, water, dest.top(), new_tip='never')
        p20.blow_out(dest.top())
        mix20(8, dest)
        p20.blow_out(dest.top())
        p20.drop_tip()

    protocol.comment('Incubating for 2 minutes.')
    protocol.delay(minutes=2)

    # Step 21 - Transfer elutes to clean plate
    magdeck.engage(height=magheight)
    protocol.comment('Incubating on MagDeck for 2 minutes.')
    protocol.delay(minutes=2)

    for src, dest in zip(magsamps, elutes):
        pick_up(p20)
        for _ in range(2):
            p20.transfer(20, src, dest.top(-5), new_tip='never')
            p20.blow_out(dest.top())
        p20.drop_tip()

    magdeck.disengage()

    # write updated tipcount to CSV
    new_tip_count = str(p20count)+", "+str(p1kcount)+"\n"
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)

    protocol.comment('Congratulations, the protocol is complete. You can store \
    the samples or proceed to the next protocol with the samples.')

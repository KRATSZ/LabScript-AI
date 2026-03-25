from opentrons import types
import math

metadata = {
    'protocolName': 'Zymo Research Direct-zol-96 RNA MagPrep',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [number_of_samples_to_process, p300_multi_mount,
        volume_of_beads_in_ul, bead_separation_time_in_minutes,
        mix_repetitions] = get_values(  # noqa: F821
        'number_of_samples_to_process', 'p300_multi_mount',
        'volume_of_beads_in_ul', 'bead_separation_time_in_minutes',
        'mix_repetitions')

    deep_name = 'nest_96_wellplate_2ml_deep'

    # load labware and modules
    elution_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '1', 'elution plate')
    etoh = protocol.load_labware(
        'agilent_1_reservoir_290ml', '2', 'EtOH').wells()[0]
    waste_list = [
        res.wells()[0].top()
        for res in [
            protocol.load_labware('agilent_1_reservoir_290ml', slot, 'waste')
            for slot in ['3', '6']
        ]
    ]
    magdeck = protocol.load_module('magdeck', '4')
    mag_plate = magdeck.load_labware(deep_name, 'deepwell block')
    res12 = protocol.load_labware(
        'usascientific_12_reservoir_22ml', '5', 'reagent reservoir')
    tips300 = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', str(slot)) for slot in range(7, 12)
    ]

    # reagents
    beads = res12.wells()[0]
    dnase = res12.wells()[1]
    rna_buff = res12.wells()[2:5]
    wash1 = res12.wells()[5:8]
    wash2 = res12.wells()[8:11]
    water = res12.wells(11)

    # check
    if number_of_samples_to_process > 96 or number_of_samples_to_process < 1:
        raise Exception('Invalid number of samples (must be 1-96).')

    # pipettes
    m300 = protocol.load_instrument(
        'p300_multi', p300_multi_mount, tip_racks=tips300)

    # setup
    num_cols = math.ceil(number_of_samples_to_process/8)
    mag_samples = mag_plate.rows()[0][:num_cols]
    disp_locs = []
    for i, m in enumerate(mag_samples):
        angle = -1 if i % 2 == 0 else -1
        disp_loc = m.bottom().move(types.Point(x=angle, y=0, z=1))
        disp_locs.append(disp_loc)
    elution_samples = elution_plate.rows()[0][:num_cols]

    waste_ind = 0
    waste = waste_list[waste_ind]
    waste_vol = 0

    def waste_check(vol):
        nonlocal waste_vol
        nonlocal waste_ind
        nonlocal waste
        waste_vol += vol
        if waste_vol > 270000:
            waste_vol = 0
            if waste_ind < len(waste_list-1):
                waste_ind += 1
                waste = waste_list[waste_ind]
            else:
                protocol.pause('Empty waste reservoirs in slots 3 and 6 and \
replace before resuming.')
                waste_ind = 0
                waste = waste_list[waste_ind]
        return waste

    etoh_vol = 0

    def etoh_check(vol):
        nonlocal etoh_vol
        etoh_vol -= vol
        if etoh_vol > 270000:
            protocol.pause('Refill EtOH reservoir in slot 2 before resuming.')
            etoh_vol = 0

    tip_count = 0
    tip_max = len(tips300)*12

    def pick_up(loc=None):
        nonlocal tip_count
        if tip_count == tip_max:
            protocol.pause('Replace 300ul tipracks before resuming.')
            m300.reset_tipracks()
            tip_count = 0
        if loc:
            m300.pick_up_tip(loc)
        else:
            m300.pick_up_tip()
            tip_count += 1

    def etoh_wash_3x():
        tip_locs = []
        for wash in range(3):
            magdeck.disengage()
            for t, (s, d) in enumerate(zip(mag_samples, disp_locs)):
                if wash == 0:
                    pick_up()
                    tip_locs.append(m300._last_tip_picked_up_from)
                else:
                    pick_up(tip_locs[t])
                etoh_check(500)
                m300.transfer(500, etoh, s.top(), new_tip='never')
                m300.mix(mix_repetitions, 250, d)
                m300.blow_out(s.top())
                m300.return_tip()
            magdeck.engage(height=12)
            protocol.delay(minutes=bead_separation_time_in_minutes)
            for t, s in zip(tip_locs, mag_samples):
                pick_up(t)
                w = waste_check(500)
                m300.transfer(500, s, w, new_tip='never')
                if wash < 2:
                    m300.return_tip()
                else:
                    m300.drop_tip()

    def magbead_wash(w):
        magdeck.disengage()
        tip_locs = []
        for i, (s, d) in enumerate(zip(mag_samples, disp_locs)):
            r_ind = i//5
            pick_up()
            tip_locs.append(m300._last_tip_picked_up_from)
            m300.transfer(500, w[r_ind], s.top(), new_tip='never')
            m300.mix(mix_repetitions, 250, d)
            m300.blow_out(s.top())
            m300.return_tip()
        magdeck.engage(height=12)
        protocol.delay(minutes=bead_separation_time_in_minutes)
        for t, s in zip(tip_locs, mag_samples):
            pick_up(t)
            w = waste_check(500)
            m300.transfer(550, s, w, new_tip='never')
            m300.drop_tip()

    # add beads
    pick_up()
    m300.distribute(
        volume_of_beads_in_ul,
        beads,
        [s.top() for s in mag_samples],
        new_tip='never'
    )
    m300.drop_tip()

    # add first EtOH
    tip_locs = []
    for s in mag_samples:
        pick_up()
        tip_locs.append(m300._last_tip_picked_up_from)
        etoh_check(450)
        m300.transfer(450, etoh, s, new_tip='never')
        m300.mix(mix_repetitions, 250, s)
        m300.blow_out(s.top())
        m300.return_tip()

    # iterative mixing
    for mix in range(3):
        for t, m in zip(tip_locs, mag_samples):
            protocol.comment('Incuating with iterative mixing...')
            protocol.delay(minutes=2)
            pick_up(t)
            m300.mix(mix_repetitions, 200, m)
            m300.blow_out(m.top(-2))
            if mix < 2:
                m300.return_tip()
            else:
                m300.drop_tip()

    magdeck.engage(height=12)
    protocol.comment('Beads separating for supernatant removal')
    protocol.delay(minutes=bead_separation_time_in_minutes)

    # remove supernatant
    for m in mag_samples:
        pick_up()
        w = waste_check(1000)
        m300.transfer(1000, m, waste_list[0], new_tip='never')
        m300.drop_tip()

    # first set of 3x EtOH washes
    etoh_wash_3x()
    protocol.comment('Airdrying beads for 5 minutes.')
    protocol.delay(minutes=5)

    # transfer DNAse 1
    magdeck.disengage()
    for d, s in zip(disp_locs, mag_samples):
        pick_up()
        m300.transfer(50, dnase, d, new_tip='never')
        m300.mix(mix_repetitions, 40, d)
        m300.blow_out(s.top())
        m300.drop_tip()

    protocol.comment('Incubating for 10 minutes.')
    protocol.delay(minutes=10)

    # transfer RNA buffer
    tip_locs = []
    for i, s in enumerate(mag_samples):
        r_ind = i//5
        pick_up()
        tip_locs.append(m300._last_tip_picked_up_from)
        m300.transfer(500, rna_buff[r_ind], s.top(), new_tip='never')
        m300.mix(mix_repetitions, 250, s)
        m300.blow_out(s.top())
        m300.return_tip()

    protocol.comment('Incubating off magnet for 5 minutes')
    protocol.delay(minutes=5)
    magdeck.engage(height=12)
    protocol.comment('Beads separating.')
    protocol.delay(minutes=bead_separation_time_in_minutes)

    # remove supernatant
    for t, s in zip(tip_locs, mag_samples):
        pick_up(t)
        w = waste_check(550)
        m300.transfer(550, s, w, new_tip='never')
        m300.drop_tip()

    # wash 1
    magbead_wash(wash1)

    # wash 2
    magbead_wash(wash2)

    # second set of 3x EtOH washes
    etoh_wash_3x()
    protocol.pause('Let the beads dry, ideally at 55C or let the plate seat for \
20min. Replace plate on magnetic module when finished if necessary before \
resuming.')

    # add DNAse/RNAse-free water and mix during 8 minute incubation
    magdeck.disengage()
    pick_up()
    m300.distribute(50, water, [s.top() for s in mag_samples], new_tip='never')
    tip_locs = []
    for mix_rep in range(3):
        for t, (s, d) in enumerate(zip(mag_samples, disp_locs)):
            if mix_rep == 0:
                if not m300.hw_pipette['has_tip']:
                    m300.pick_up_tip()
                tip_locs.append(m300._last_tip_picked_up_from)
            else:
                pick_up(tip_locs[t])
            m300.mix(mix_repetitions, 250, d)
            m300.blow_out(s.bottom(10))
            m300.return_tip()
        protocol.comment('Incubating before next mix...')
        protocol.delay(minutes=2)

    magdeck.engage(height=12)
    protocol.comment('Incubating on magnet for bead separation')
    protocol.delay(minutes=bead_separation_time_in_minutes)

    # transfer eluate to a new PCR plate
    for i, (t, s, e) in enumerate(zip(tip_locs, mag_samples, elution_samples)):
        angle = 1 if i % 2 == 0 else -1
        asp_loc = s.bottom().move(types.Point(x=angle, y=0, z=0.6))
        pick_up(t)
        m300.transfer(50, asp_loc, e, new_tip='never')
        m300.blow_out(e.bottom(0.5))
        m300.drop_tip()

    magdeck.disengage()

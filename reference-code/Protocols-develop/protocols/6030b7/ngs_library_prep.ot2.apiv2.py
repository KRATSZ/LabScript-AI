import math
from opentrons.types import Point

# metadata
metadata = {
    'protocolName': 'Lexogen QuantSeq 3`mRNA FWD NGS Library Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    [p20_single_mount, p300_multi_mount, magdeck_gen, tempdeck_gen,
     num_samples] = get_values(  # noqa: F821
        'p20_single_mount', 'p300_multi_mount', 'magdeck_gen', 'tempdeck_gen',
        'num_samples')

    # checks
    if num_samples > 96 or num_samples < 1:
        raise Exception('Invalid number of samples (must be 1-96).')

    # load labware
    outputplate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt',
        '1',
        'final output plate (load empty)'
    )
    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_nest_1.5ml_snapcap',
        '2',
        'reagent tuberack with 1.5ml snapcap tubes'
    )
    reservoir = ctx.load_labware(
        'nest_12_reservoir_15ml', '3', 'reagent reservoir')
    magdeck = ctx.load_module(magdeck_gen, '4')
    magplate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    sp2 = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '5', 'SP2 (load empty)')
    tips20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['6', '9']
    ]
    tempdeck = ctx.load_module(tempdeck_gen, '7')
    tubeblock = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    indexplate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '8', 'index plate')
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['10', '11']
    ]

    # reagents and samples
    fs1, fs2e1, pb, eb, ps, pcre3 = tubeblock.rows()[0]
    rs, ss1, ss2 = tuberack.rows()[0][:3]
    num_etoh_chan = 2 if num_samples <= 48 else 3
    etoh = reservoir.wells()[:num_etoh_chan]
    waste = reservoir.wells()[-1].top()
    num_cols = math.ceil(num_samples/8)
    magsamples_s = magplate.wells()[:num_samples]
    magsamples_m = magplate.rows()[0][:num_cols]
    samples2_s = sp2.wells()[:num_samples]
    indexes = indexplate.wells()[:num_samples]
    output = outputplate.wells()[:num_samples]

    # pipettes
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_single_mount, tip_racks=tips20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2', p300_multi_mount, tip_racks=tips300)

    # tip track
    tipcount20 = 0
    tipmax20 = 96*len(tips20)
    tipcount300 = 0
    tipmax300 = 12*len(tips300)

    def pickup(pip):
        nonlocal tipcount20
        nonlocal tipcount300
        if pip == p20:
            if tipcount20 == tipmax20:
                ctx.pause('Refill 20µl tipracks in slots 6 and 9 before \
resuming.')
                p20.reset_tipracks()
                tipcount20 = 0
            p20.pick_up_tip()
            tipcount20 += 1
        else:
            if tipcount300 == tipmax300:
                ctx.pause('Refill 200µl tipracks in slots 8, 10, and 11 \
before resuming.')
                m300.reset_tipracks()
                tipcount300 = 0
            m300.pick_up_tip()
            tipcount300 += 1

    def init_transfers(vol, reagent):
        for s in magsamples_s:
            pickup(p20)
            p20.transfer(vol, reagent, s, mix_after=(3, 10), new_tip='never')
            p20.blow_out(s.top())
            p20.drop_tip()

    # transfer FS1
    init_transfers(5, fs1)
    ctx.pause('Place sample plate in cycler at 85C for 3 minutes, then cool \
down to 42C. Return sample plate to OT-2 when finished.')

    # transfer FS2/E1
    init_transfers(10, fs2e1)
    ctx.pause('Place sample plate in cycler at 42C for 15 minutes. Return \
sample plate to OT-2 when finished.')

    # transfer RS
    init_transfers(5, rs)
    ctx.pause('Place sample plate in cycler at 95C for 10 minutes. Return \
sample plate to OT-2 when finished.')

    # transfer SS1
    init_transfers(10, ss1)
    ctx.pause('Place sample plate in cycler at 98C for 1 minute. Return \
sample plate to OT-2 when finished.')

    # transfer SS2
    init_transfers(5, ss2)
    ctx.pause('Place sample plate in cycler at 25C for 15 minutes. Return \
sample plate to OT-2 when finished.')

    # transfer PB
    init_transfers(16, pb)

    magdeck.engage()
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes.')

    # remove supernatant
    for m in magsamples_m:
        pickup(m300)
        m300.transfer(60, m.bottom(0.5), waste, new_tip='never')
        m300.drop_tip()

    # add 80% EtOH
    for m in magsamples_m:
        pickup(m300)
        m300.transfer(120, etoh[0], waste, new_tip='never')
        m300.drop_tip()

    ctx.delay(seconds=30, msg='Incubating on magnet for 30 seconds.')

    # remove supernatant
    for m in magsamples_m:
        pickup(m300)
        m300.transfer(130, m.bottom(0.5), waste, new_tip='never')
        m300.drop_tip()

    ctx.delay(minutes=10, msg='Drying beads for 10 minutes.')

    magdeck.disengage()

    # elute beads in EB
    for i, s in enumerate(magsamples_s):
        side = 1 if (i//8) % 2 == 0 else -1
        mix_loc = s.bottom().move(Point(x=side*s.diameter/2*0.9, y=0, z=2))
        pickup(p20)
        p20.transfer(20, eb, s.top(), new_tip='never')
        p20.aspirate(20, eb)
        p20.move_to(s.center())
        p20.dispense(20, mix_loc)
        p20.mix(5, 10, mix_loc)
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    # transfer PS
    for s in magsamples_s:
        pickup(p20)
        p20.transfer(56, ps, s.top(), new_tip='never')
        p20.mix(3, 10, s)
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    ctx.delay(minutes=5, msg='Incubating off magnet for 5 minutes.')
    magdeck.engage()
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes.')

    # transfer supernatant to SP2
    for s, d in zip(magsamples_s, samples2_s):
        pickup(p20)
        p20.transfer(17, s.bottom(0.5), d, new_tip='never')
        p20.drop_tip()

    # transfer pcre3
    pickup(p20)
    for s in samples2_s:
        p20.transfer(8, pcre3, s.top(), new_tip='never')
        p20.blow_out(s.top())

    # transfer corresponding indices
    for index, s in zip(indexes, samples2_s):
        if not p20.hw_pipette['has_tip']:
            pickup(p20)
        p20.transfer(5, index, s, mix_after=(3, 10), new_tip='never')
        p20.blow_out(s.top())
        p20.drop_tip()

    ctx.pause('Perform PCR cycling reaction, then place SP2 on the magnetic \
deck.')

    # transfer PB
    for s in magsamples_s:
        pickup(p20)
        p20.transfer(30, pb, s.top(), new_tip='never')
        p20.mix(3, 10, s)
        p20.blow_out(s.top())
        p20.drop_tip()

    ctx.delay(minutes=5, msg='Incubating off magnet for 5 minutes.')
    magdeck.engage()
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes.')

    # remove supernatant
    for m in magsamples_m:
        pickup(m300)
        m300.transfer(65, m.bottom(0.5), waste, new_tip='never')
        m300.drop_tip()

    magdeck.disengage()

    # elute beads in EB
    for i, s in enumerate(magsamples_s):
        side = 1 if (i//8) % 2 == 0 else -1
        mix_loc = s.bottom().move(Point(x=side*s.diameter/2*0.9, y=0, z=2))
        pickup(p20)
        p20.transfer(20, eb, s.top(), new_tip='never')
        p20.aspirate(10, eb)
        p20.move_to(s.center())
        p20.dispense(10, mix_loc)
        p20.mix(5, 10, mix_loc)
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    # transfer PS
    for s in magsamples_s:
        pickup(p20)
        p20.transfer(30, ps, s.top(), new_tip='never')
        p20.mix(3, 10, s)
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    ctx.delay(minutes=5, msg='Incubating off magnet for 5 minutes.')
    magdeck.engage()
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes.')

    # remove supernatant
    for m in magsamples_m:
        pickup(m300)
        m300.transfer(65, m.bottom(0.5), waste, new_tip='never')
        m300.drop_tip()

    # 2x EtOH washes
    for wash in range(2):
        # add 80% EtOH
        chan = 1 if wash == 0 else -1
        for m in magsamples_m:
            pickup(m300)
            m300.transfer(120, etoh[chan], waste, new_tip='never')
            m300.drop_tip()

        ctx.delay(seconds=30, msg='Incubating on magnet for 30 seconds.')

        # remove supernatant
        for m in magsamples_m:
            pickup(m300)
            m300.transfer(130, m.bottom(0.5), waste, new_tip='never')
            m300.drop_tip()

        ctx.delay(minutes=10, msg='Drying beads for 10 minutes.')

    magdeck.disengage()

    # elute beads in EB
    for i, s in enumerate(magsamples_s):
        side = 1 if (i//8) % 2 == 0 else -1
        mix_loc = s.bottom().move(Point(x=side*s.diameter/2*0.9, y=0, z=2))
        pickup(p20)
        p20.aspirate(20, eb)
        p20.move_to(s.center())
        p20.dispense(20, mix_loc)
        p20.mix(5, 10, mix_loc)
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    magdeck.engage()
    ctx.delay(minutes=5, msg='Incubating on magnet for 5 minutes.')

    # transfer supernatant to output plate
    for s, o in zip(magsamples_m, output):
        pickup(p20)
        p20.transfer(15, s, o, new_tip='never')
        p20.drop_tip()

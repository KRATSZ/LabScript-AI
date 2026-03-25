from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': 'Illumina GUIDE-seq NGS Prep: Cleanup',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    [num_samples, vol_sample, ratio_beads] = get_values(  # noqa: F821
        'num_samples', 'vol_sample', 'ratio_beads')

    # modules
    magdeck = ctx.load_module('magnetic module gen2', '1')
    tempdeck = ctx.load_module('temperature module gen2', '3')
    tc = ctx.load_module('thermocycler')

    # labware
    magplate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr',
                                    'cleanup plate')
    sampleplate = ctx.load_labware(
            'opentrons_96_aluminumblock_biorad_wellplate_200ul', '2',
            'sample plate')
    sampleplate = tc.load_labware('biorad_96_wellplate_200ul_pcr')
    tempplate = tempdeck.load_labware('biorad_96_wellplate_200ul_pcr',
                                      'reagent plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5',
                                 'reagent reservoir')
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['4']]
    tipracks200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['6', '9']]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', 'left',
                               tip_racks=tipracks200)
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks20)

    # calculations and reagents
    mag_height = 6.0
    num_cols = math.ceil(num_samples/8)
    samples = sampleplate.rows()[0][:num_cols]
    mag_samples = magplate.rows()[0][:num_cols]
    mm_frag = tempplate.rows()[0][0]
    mm_phos = tempplate.rows()[0][1]
    mm_lig = tempplate.rows()[0][2]
    mm_pcr1 = tempplate.rows()[0][3]
    mm_pcr2 = tempplate.rows()[0][4]
    y_xx = tempplate.rows()[0][6:8]
    i753_xx = tempplate.rows()[0][9:11]
    beads = reservoir.rows()[0][0]
    etoh = reservoir.rows()[0][3]
    rsb = reservoir.rows()[0][5]
    liquid_trash = reservoir.rows()[0][10:]

    tempdeck.set_temperature(4)
    tc.open_lid()
    tc.set_block_temperature(37)
    tc.set_lid_temperature(85)

    def pick_up(pip, tip=None):
        if not tip:
            try:
                pip.pick_up_tip()
            except protocol_api.labware.OutOfTipsError:
                msg = f'\n\n\n\nReplace the \
{pip.tip_racks[0].wells()[0].max_volume}ul tips in slot \
{", ".join([rack.parent for rack in pip.tip_racks])}'
                ctx.pause(msg)
                pip.reset_tipracks()
                pip.pick_up_tip()
        else:
            pip.pick_up_tip(tip)

    # advanced liquid handling function definitions

    def wick(well, pip, side=1):
        pip.move_to(well.bottom().move(Point(x=side*well.diameter/2*0.8, z=3)))

    def slow_withdraw(well, pip=m20):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    parked_tips = []

    def transfer_mix(vol, source, sample_set=samples, reps_mix_asp=0,
                     vol_mix_asp=0, reps_mix_dest=10, vol_mix_dest=20,
                     prompt=False, park=False):
        nonlocal parked_tips
        source_list = [source]*num_cols if not type(source) == list else source
        pip = m20 if vol <= 20 else m300
        for s, source_well in zip(sample_set, source_list):
            pick_up(pip)
            if reps_mix_asp > 0:
                pip.mix(reps_mix_asp, vol_mix_asp, source_well)
            pip.aspirate(vol, source_well)
            slow_withdraw(source_well, pip)
            if sample_set == samples:
                dispense_loc = s
            else:
                side = 1 if magplate.rows()[0].index(s) % 2 == 0 else -1
                dispense_loc = s.bottom().move(Point(x=side*s.diameter/2, z=2))
            pip.move_to(s.center())
            pip.dispense(vol, dispense_loc)
            if reps_mix_dest > 0:
                pip.mix(reps_mix_dest, vol_mix_dest, s)
            slow_withdraw(s, pip)
            if park:
                parked_tips.append(pip._last_tip_picked_up_from)
                pip.return_tip()
            else:
                pip.drop_tip()
        if prompt:
            ctx.pause('\n\n\n\nRemove thermocycler plate for thermal \
cycling. Replace when finished.\n\n\n\n')

    def remove_supernatant(vol, pip=None, dests=liquid_trash, z_asp=0.2,
                           z_disp=1.0, do_wick=False, park=False):
        nonlocal parked_tips
        if not pip:
            pip = m300 if vol >= 20 else m20
        for i, (s, d) in enumerate(zip(mag_samples, dests)):
            if not pip.has_tip:
                if park:
                    pick_up(pip, parked_tips[i])
                else:
                    pick_up(pip)
            pip.move_to(s.top())
            ctx.max_speeds['A'] = 25
            ctx.max_speeds['Z'] = 25
            # side = -1 if magplate.rows()[0].index(s) % 2 == 0 else 1
            side = 0
            pip.aspirate(vol, s.bottom().move(Point(x=side, z=z_asp)))
            pip.move_to(s.top())
            del ctx.max_speeds['A']
            del ctx.max_speeds['Z']
            pip.dispense(vol, d.bottom(z_disp))
            if do_wick:
                wick(d, pip)
            pip.drop_tip()
        parked_tips = []

    def wash(vol, source=etoh, pip=m300, time_incubation_seconds=30.0,
             vol_residual=0, dests=liquid_trash):
        pick_up(pip)
        for s in mag_samples:
            pip.aspirate(vol, source)
            slow_withdraw(source, pip)
            pip.dispense(vol, s.top())
        pip.move_to(source.top(2))

        ctx.delay(minutes=time_incubation_seconds,
                  msg='\n\n\n\nIncubating\n\n\n\n')
        remove_supernatant(vol, pip=pip, dests=dests, z_disp=dests[0].depth)

    transfer_mix(7.5, mm_frag)
    tc.close_lid()
    tc.set_block_temperature(37, hold_time_minutes=30,
                             block_max_volume=vol_sample+7.5)
    tc.set_block_temperature(4)
    tc.open_lid()
    tc.deactivate_lid()

    transfer_mix(30*ratio_beads, beads, reps_mix_asp=5, vol_mix_asp=200,
                 reps_mix_dest=10, vol_mix_dest=50, park=True)
    ctx.delay(minutes=5, msg='\n\n\n\n5 minute bead incubation.\n\n\n\n')

    total_vol = vol_sample + 7.5 + 30
    for i, (s, m) in enumerate(zip(samples, mag_samples)):
        pick_up(m300, parked_tips[i])
        m300.transfer(total_vol, s, m, new_tip='never')
        slow_withdraw(m, m300)
        m300.drop_tip(parked_tips[i])
    magdeck.engage(mag_height)
    ctx.delay(minutes=2, msg='\n\n\n\nBinding.\n\n\n\n')
    remove_supernatant(total_vol-3.0, park=True)

    wash(100)
    wash(150)

    # aspirate residual
    remove_supernatant(10, pip=m20, z_asp=0.1)
    ctx.delay(minutes=2, msg='\n\n\n\nAir dry.\n\n\n\n')
    magdeck.disengage()

    transfer_mix(10, rsb, mag_samples, reps_mix_dest=10, vol_mix_dest=8,
                 park=True)
    ctx.delay(minutes=2, msg='RSB incubation.')
    magdeck.engage(height=5)
    ctx.delay(minutes=2, msg='Binding')

    # reassign samples in plate
    samples = sampleplate.rows()[0][num_cols:num_cols*2]
    remove_supernatant(8, m20, dests=samples, z_asp=0.1, do_wick=True,
                       park=True)
    magdeck.disengage()

    transfer_mix(2, mm_phos, sample_set=samples, reps_mix_dest=10,
                 vol_mix_dest=8, prompt=False)
    tc.close_lid()
    tc.set_lid_temperature(105)
    tc.set_block_temperature(37, hold_time_minutes=30,
                             block_max_volume=10)
    tc.set_block_temperature(65, hold_time_minutes=20,
                             block_max_volume=10)
    tc.set_block_temperature(4)
    tc.open_lid()
    tc.deactivate_lid()
    ctx.pause('Fragmentated DNA denaturation, 95C for 3min and put in ice \
water immediately')

    tc.close_lid()
    tc.set_lid_temperature(50)
    tc.set_block_temperature(25, hold_time_minutes=30,
                             block_max_volume=30)
    tc.set_block_temperature(4)
    tc.open_lid()
    tc.deactivate_lid()

    transfer_mix(20, mm_lig, sample_set=samples, reps_mix_dest=10,
                 vol_mix_dest=20)

    transfer_mix(30*ratio_beads, beads, sample_set=samples, reps_mix_asp=5,
                 vol_mix_asp=200, reps_mix_dest=10, vol_mix_dest=50, park=True)

    # reassign samples in magplate
    mag_samples = magplate.rows()[0][num_cols:num_cols*2]
    for i, (s, m) in enumerate(zip(samples, mag_samples)):
        pick_up(m300, parked_tips[i])
        m300.transfer(60, s, m, new_tip='never')
        slow_withdraw(m, m300)
        m300.drop_tip(parked_tips[i])
    ctx.delay(minutes=5, msg='\n\n\n\nIncubating.\n\n\n\n')
    magdeck.engage(mag_height)
    ctx.delay(minutes=5, msg='\n\n\n\nBinding.\n\n\n\n')
    remove_supernatant(60-4.0, park=True)

    wash(100)
    wash(150)

    # aspirate residual
    remove_supernatant(20, pip=m20, z_asp=0.1)
    ctx.delay(minutes=2, msg='\n\n\n\nAir dry.\n\n\n\n')
    magdeck.disengage()

    # resuspend
    transfer_mix(21, rsb, mag_samples, reps_mix_dest=10, vol_mix_dest=8,
                 park=True)
    ctx.delay(minutes=2, msg='RSB incubation.')
    magdeck.engage(mag_height)
    ctx.delay(minutes=3, msg='Binding')

    # reassign samples in plate
    samples = sampleplate.rows()[0][num_cols*2:num_cols*3]
    remove_supernatant(20, m300, dests=samples, z_asp=0.1, do_wick=True,
                       park=True)
    magdeck.disengage()

    transfer_mix(9, mm_pcr1, sample_set=samples, reps_mix_dest=0, prompt=False)
    transfer_mix(1, y_xx, sample_set=samples, reps_mix_dest=0, prompt=True)

    transfer_mix(30*ratio_beads, beads, sample_set=samples, reps_mix_asp=5,
                 vol_mix_asp=200, reps_mix_dest=10, vol_mix_dest=50, park=True)

    # reassign samples in magplate
    mag_samples = magplate.rows()[0][num_cols*2:num_cols*3]
    for i, (s, m) in enumerate(zip(samples, mag_samples)):
        pick_up(m300, parked_tips[i])
        m300.transfer(60, s, m, new_tip='never')
        slow_withdraw(m, m300)
        m300.drop_tip(parked_tips[i])
    ctx.delay(minutes=5, msg='\n\n\n\nIncubating.\n\n\n\n')
    magdeck.engage(mag_height)
    ctx.delay(minutes=3, msg='\n\n\n\nBinding.\n\n\n\n')
    remove_supernatant(60-3.0, park=True)

    wash(100)
    wash(150)

    # aspirate residual
    remove_supernatant(20, pip=m20, z_asp=0.1)
    ctx.delay(minutes=2, msg='\n\n\n\nAir dry.\n\n\n\n')
    magdeck.disengage()

    # resuspend
    transfer_mix(16, rsb, sample_set=mag_samples, reps_mix_dest=10,
                 vol_mix_dest=13, park=True)
    ctx.delay(minutes=2, msg='RSB incubation.')
    magdeck.engage(mag_height)
    ctx.delay(minutes=3, msg='Binding')

    # reassign samples in plate
    samples = sampleplate.rows()[0][num_cols*3:num_cols*4]
    remove_supernatant(15, m20, dests=samples, z_asp=0.1, do_wick=True,
                       park=True)
    magdeck.disengage()

    transfer_mix(13.5, mm_pcr2, sample_set=samples, reps_mix_dest=0,
                 prompt=False)
    transfer_mix(0.5, y_xx, sample_set=samples, reps_mix_dest=0, prompt=False)
    transfer_mix(1, i753_xx, sample_set=samples, reps_mix_dest=0, prompt=True)

    transfer_mix(30*ratio_beads*0.7, source=beads, sample_set=samples,
                 reps_mix_asp=5, vol_mix_asp=200, reps_mix_dest=10,
                 vol_mix_dest=45, park=True)

    # reassign samples in magplate
    mag_samples = magplate.rows()[0][num_cols*3:num_cols*4]
    for i, (s, m) in enumerate(zip(samples, mag_samples)):
        pick_up(m300, parked_tips[i])
        m300.transfer(30, s, m, new_tip='never')
        slow_withdraw(m, m300)
        m300.drop_tip(parked_tips[i])
    ctx.delay(minutes=5, msg='\n\n\n\nIncubating.\n\n\n\n')
    magdeck.engage(mag_height)
    ctx.delay(minutes=3, msg='\n\n\n\nBinding.\n\n\n\n')
    remove_supernatant(30-3.0, park=True)

    wash(100)
    wash(150)

    # aspirate residual
    remove_supernatant(20, pip=m20, z_asp=0.1)
    ctx.delay(minutes=2, msg='\n\n\n\nAir dry.\n\n\n\n')
    magdeck.disengage()

    # elution
    elution_samples = magplate.rows()[0][num_cols*4:num_cols*5]
    transfer_mix(22, rsb, sample_set=mag_samples, reps_mix_dest=10,
                 vol_mix_dest=15, park=True)
    ctx.delay(minutes=2, msg='RSB incubation.')
    magdeck.engage(mag_height)
    ctx.delay(minutes=3, msg='Binding')
    remove_supernatant(20, pip=m300, dests=elution_samples, do_wick=True,
                       park=True)

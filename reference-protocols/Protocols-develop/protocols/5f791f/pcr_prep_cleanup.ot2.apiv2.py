import math
from opentrons.types import Point

metadata = {
    'protocolName': 'PCR Prep and Magnetic Bead Cleanup',
    'author': 'Nick <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    [num_samples, vol_sample, ratio_beads, vol_wash, vol_elution,
     time_settling, m20_mount, m300_mount,
     perform_steps] = get_values(  # noqa: F821
        'num_samples', 'vol_sample', 'ratio_beads', 'vol_wash', 'vol_elution',
        'time_settling', 'm20_mount', 'm300_mount', 'perform_steps')

    num_cols = math.ceil(num_samples/8)
    m20_speed_mod = 4
    supernatant_headspeed_modulator = 5
    steps = perform_steps.split(',')

    # load modules and labware
    magdeck = ctx.load_module('magnetic module gen2', '1')
    pcr_plate = magdeck.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'PCR plate')
    if 'pcr_prep' in steps:
        plate_name = 'source sample plate'
    else:
        plate_name = 'clean elution plate'
    source_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '2', plate_name)
    source_samples = source_plate.rows()[0][:num_cols]

    tipracks20 = []
    if 'pcr_prep' in steps:
        tipracks20.append(
            ctx.load_labware('opentrons_96_filtertiprack_20ul', '3'))
    vol_beads = ratio_beads * vol_sample
    if 'cleanup' in steps:
        reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4',
                                     'reagent reservoir')
        tipracks200 = [
            ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in ['5', '7', '8', '9', '10', '11']]
        beads = reservoir.wells()[0]
        etoh = reservoir.wells()[1:5]
        elution_buffer = reservoir.wells()[5]
        waste = [well.top() for well in reservoir.wells()[8:]]

        if vol_beads <= 20:
            rack = ctx.load_labware('opentrons_96_filtertiprack_20ul', '6')
            tipracks20.append(rack)
        else:
            rack = ctx.load_labware('opentrons_96_filtertiprack_200ul', '6')
            tipracks200.append(rack)

        m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                                   tip_racks=tipracks200)

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20)

    pcr_samples = pcr_plate.rows()[0][:num_cols]

    def bead_premix(reps, vol, pip):
        for _ in range(reps):
            pip.aspirate(vol, beads.bottom(1))
            pip.dispense(vol, beads.bottom(5))

    if 'pcr_prep' in steps:
        for source, dest in zip(source_samples, pcr_samples):
            m20.flow_rate.aspirate /= m20_speed_mod
            m20.flow_rate.dispense /= m20_speed_mod
            m20.pick_up_tip()
            m20.aspirate(vol_sample, source)
            m20.dispense(5, dest)
            m20.mix(1, 5, dest)
            ctx.max_speeds['A'] = 100
            ctx.max_speeds['Z'] = 100
            m20.air_gap(5)
            m20.drop_tip()
            del ctx.max_speeds['A']
            del ctx.max_speeds['Z']
            m20.flow_rate.aspirate *= m20_speed_mod
            m20.flow_rate.dispense *= m20_speed_mod

    if 'cleanup' in steps:

        ctx.pause('Run PCR on plate on magnetic module (slot 1). When \
complete, replace plate on magnetic module, and replace source sample plate \
(slot 2) with clean plate for elution.')
        elution_samples = source_plate.rows()[0][:num_cols]

        def bead_wellmix(well, pip, vol, reps=10):
            pip.move_to(well.center())
            for _ in range(reps):
                pip.aspirate(vol, well.bottom(1))
                pip.dispense(vol, well.bottom(5))

        # add beads and mix
        pip_beads = m300 if vol_beads > 20 else m20
        for i, dest in enumerate(pcr_samples):
            pip_beads.flow_rate.aspirate /= 4
            pip_beads.flow_rate.dispense /= 4
            pip_beads.pick_up_tip()
            bead_premix(5, pip_beads.tip_racks[0].wells()[0].max_volume,
                        pip_beads)
            pip_beads.aspirate(vol_beads, beads)
            pip_beads.dispense(vol_beads, dest)
            pip_beads.flow_rate.aspirate *= 2
            pip_beads.flow_rate.dispense *= 2
            bead_wellmix(dest, pip_beads, vol_beads)
            pip_beads.flow_rate.aspirate *= 2
            pip_beads.flow_rate.dispense *= 2
            pip_beads.air_gap(pip_beads.min_volume)
            pip_beads.drop_tip()

        ctx.delay(minutes=5, msg='Incubating off magnet')
        magdeck.engage()
        ctx.delay(minutes=time_settling, msg='Incubating on magnet')

        ctx.max_speeds['Z'] = 50
        ctx.max_speeds['A'] = 50
        for i, source in enumerate(pcr_samples):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip()
            m300.flow_rate.aspirate /= 10
            m300.move_to(source.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(
                vol_sample+vol_beads+5, source.bottom().move(
                    Point(x=side*2, y=0, z=0.2)))
            m300.move_to(source.top())
            m300.air_gap(20)
            m300.flow_rate.aspirate *= 10
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, waste[0])
            m300.air_gap(20)
            m300.drop_tip()

        # 3x EtOH wash
        etoh_ind = 0
        vol_counter_etoh = 0
        waste_ind = 0
        vol_counter_waste = 0
        vol_max = 13000
        for _ in range(3):
            m300.pick_up_tip()
            for dest in pcr_samples:
                if vol_counter_etoh + vol_wash*8 > vol_max:
                    vol_counter_etoh = 0
                    etoh_ind += 1
                vol_counter_etoh += vol_wash*8
                etoh_source = etoh[etoh_ind]
                m300.dispense(m300.current_volume, etoh_source.top())
                m300.move_to(etoh_source.top().move(
                    Point(x=etoh_source.length/2, z=-1)))
                m300.move_to(etoh_source.top())
                m300.aspirate(vol_wash, etoh_source)
                ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
                ctx.max_speeds['A'] /= supernatant_headspeed_modulator
                m300.move_to(etoh_source.top())
                ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
                ctx.max_speeds['A'] *= supernatant_headspeed_modulator
                m300.dispense(vol_wash, dest.top(1))
                m300.air_gap(20)
            m300.move_to(etoh_source.top())
            m300.dispense(m300.current_volume, etoh_source.top())
            ctx.delay(seconds=30)
            for i, source in enumerate(pcr_samples):
                side = -1 if i % 2 == 0 else 1
                if not m300.has_tip:
                    m300.pick_up_tip()
                m300.flow_rate.aspirate /= 15
                m300.move_to(source.top())
                ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
                ctx.max_speeds['A'] /= supernatant_headspeed_modulator
                num_aspirations = math.ceil(vol_wash/50)
                if vol_counter_waste + vol_wash*8 > vol_max:
                    vol_counter_waste = 0
                    waste_ind += 1
                for asp_ind in reversed(range(num_aspirations)):
                    asp_height = source.depth/4*asp_ind+0.5
                    m300.aspirate(50,
                                  source.bottom().move(
                                    Point(x=3*side, z=asp_height)))
                m300.aspirate(20, source.bottom().move(
                    Point(x=1.5*side, z=0.2)))
                m300.move_to(source.top())
                m300.flow_rate.aspirate *= 15
                ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
                ctx.max_speeds['A'] *= supernatant_headspeed_modulator
                m300.dispense(m300.current_volume, waste[waste_ind])
                m300.air_gap(20)
                m300.drop_tip()

        ctx.delay(minutes=5, msg='Air drying')
        magdeck.disengage()
        for i, dest in enumerate(pcr_samples):
            side = 1 if i % 2 == 0 else -1
            bead_loc = dest.bottom().move(Point(x=side*2, z=5))
            m300.pick_up_tip()
            m300.aspirate(vol_elution, elution_buffer)
            m300.move_to(dest.center())
            m300.dispense(vol_elution, bead_loc)
            m300.mix(10, 10, dest.bottom(1))
            m300.move_to(dest.bottom().move(Point(x=-2, z=3)))
            m300.air_gap(20)
            m300.drop_tip()

        ctx.delay(minutes=3, msg='Incubating off magnet')
        magdeck.engage()
        ctx.delay(minutes=time_settling, msg='Incubating on magnet')

        m300.flow_rate.aspirate /= 15
        for i, (s, d) in enumerate(zip(pcr_samples, elution_samples)):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip()
            m300.move_to(s.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol_elution-5,
                          s.bottom().move(Point(x=side*3, z=0.5)))
            m300.move_to(s.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, d.bottom(0.5))
            m300.move_to(d.bottom().move(Point(x=-2, z=3)))
            m300.air_gap(20)
            m300.drop_tip()
        m300.flow_rate.aspirate *= 15

        magdeck.disengage()

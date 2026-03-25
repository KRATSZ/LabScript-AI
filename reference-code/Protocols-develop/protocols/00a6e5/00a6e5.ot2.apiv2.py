import itertools
import math

metadata = {
    'protocolName': 'LCMS Urine Extraction',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
 }


def run(ctx):

    [num_samp, asp_height, p300_mount, p1000_mount] = get_values(  # noqa: F821
        "num_samp", "asp_height", "p300_mount", "p1000_mount")

    if not 1 <= num_samp <= 84:
        raise Exception("Enter a sample number between 1-84")

    # labware
    urine_tube_rack = [ctx.load_labware(
                    'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
                    slot, label='tuberack')
                       for slot in ['4', '5', '1', '2']]
    plate = ctx.load_labware('eppendorf_96_wellplate_2000ul', '3')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '11')
    tips1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', '7')]
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in ['8', '9']]
    reagent_rack = ctx.load_labware(
                    'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
                    '10', label='tuberack')

    # instrument
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips300)
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tips1000)

    def create_chunks(list, n):
        for i in range(0, len(list), n):
            yield list[i:i+n]

    tube_map_double_nest = [
                  [urine_tube_rack[j].rows()[i] +
                   urine_tube_rack[j+1].rows()[i]
                   for i in range(len(urine_tube_rack[0].rows()))]
                  for j in range(0, 4, 2)
                  ]

    num_samp_full = num_samp+12
    tube_map_nest = list(itertools.chain.from_iterable(tube_map_double_nest))
    full_tube_map = list(itertools.chain.from_iterable(
                         tube_map_nest))[:num_samp_full]

    # reagents
    methanol = reservoir.wells()[6:]
    buffer = reservoir.wells()[:6]
    negative_urine = full_tube_map[1:8]
    samples = full_tube_map[12:]
    spike = reagent_rack.rows()[0][:2]
    enzyme = reagent_rack.rows()[1][:5]
    water = reagent_rack.rows()[2][:3]
    plate_wells_by_row = [well
                          for row in plate.rows()[1:]
                          for well in row][:num_samp]

    buffer_vol = 340
    methanol_vol = 700
    spike_vol = 20
    water_vol = 30
    enzyme_vol = 60

    num_wells_buffer = math.ceil(buffer_vol*num_samp_full/12000)*12
    num_wells_methanol = math.ceil(methanol_vol*num_samp_full/12000)*12
    num_tubes_spike = math.ceil(spike_vol*num_samp_full/1300)
    num_tubes_water = math.ceil(water_vol*num_samp_full/1300)
    num_tubes_enzyme = math.ceil(enzyme_vol*num_samp_full/1300)

    buffer = buffer[:num_wells_buffer]
    methanol = methanol[:num_wells_methanol]
    spike = spike[:num_tubes_spike]
    enzyme = enzyme[:num_tubes_enzyme]
    water = water[:num_tubes_water]

    # add enzyme to all wells
    p300.pick_up_tip()
    p300.distribute(60, enzyme,
                    [well for well in plate.wells()[:num_samp_full]],
                    new_tip='never')
    p300.drop_tip()
    ctx.comment('\n\n\n')

    # add buffer to all wells
    p1000.pick_up_tip()
    for source, chunk in zip(buffer*num_samp,
                             create_chunks(plate.wells()[:num_samp_full], 2)):
        p1000.aspirate(660, source)
        for well in chunk:
            p1000.dispense(340, well.top())
    p1000.drop_tip()
    ctx.comment('\n\n\n')

    # add negative urine (blank)
    p300.pick_up_tip()
    p300.aspirate(300, urine_tube_rack[0].wells()[0])
    p300.dispense(300, plate.wells()[0])
    p300.drop_tip()
    ctx.comment('\n\n\n')

    # add negative urine (cals)
    for tube, well in zip(negative_urine, plate.rows()[0][1:]):
        p300.pick_up_tip()
        p300.aspirate(270, tube)
        p300.dispense(270, well)
        p300.drop_tip()
    ctx.comment('\n\n\n')

    # add samples
    for tube, well in zip(samples, plate_wells_by_row):
        p300.pick_up_tip()
        p300.aspirate(300, tube.top(z=-asp_height))
        p300.dispense(300, well)
        p300.drop_tip()
    ctx.comment('\n\n\n')

    # add methanol to samples
    p300.pick_up_tip()
    p300.distribute(30, enzyme,
                    [well.top() for well in plate_wells_by_row],
                    new_tip='never')
    p300.drop_tip()
    ctx.comment('\n\n\n')

    # add spike
    p300.pick_up_tip()
    p300.distribute(20, spike,
                    [well.top() for well in plate.wells()[:num_samp_full]],
                    new_tip='never')
    p300.drop_tip()
    ctx.comment('\n\n\n')

    # add water
    p300.pick_up_tip()
    p300.distribute(30, water,
                    [well.top() for well in plate.wells()[:num_samp_full]],
                    new_tip='never')
    p300.drop_tip()
    ctx.comment('\n\n\n')

    ctx.pause("Select `Resume` on the Opentrons app to continue.")

    # add methanol
    p300.pick_up_tip()
    p300.distribute(700, methanol,
                    [well.top() for well in plate.wells()[:num_samp_full]],
                    new_tip='never')
    p300.drop_tip()
    ctx.comment('\n\n\n')

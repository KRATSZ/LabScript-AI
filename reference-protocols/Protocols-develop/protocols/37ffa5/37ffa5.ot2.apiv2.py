import math

metadata = {
    'protocolName': '''mRNA Encapsulation''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [count_samples_rowa, count_samples_rowb, count_samples_rowc,
     count_samples_rowd] = get_values(  # noqa: F821
      'count_samples_rowa', 'count_samples_rowb', 'count_samples_rowc',
      'count_samples_rowd')

    ctx.set_rail_lights(True)

    num_samplerows = 0

    tot_count = 0

    for count in [count_samples_rowa, count_samples_rowb, count_samples_rowc,
                  count_samples_rowd]:

        if not 0 <= count <= 5:
            raise Exception('Invalid sample count (must be 1-5).')

        if count:
            num_samplerows += 1

        tot_count += count

    # helper functions

    # return liquid height in a well
    def liq_height(well, effective_diameter=None):
        if well.diameter:
            if effective_diameter:
                radius = effective_diameter / 2
            else:
                radius = well.diameter / 2
            csa = math.pi*(radius**2)
        else:
            csa = well.length*well.width
        return well.liq_vol / csa

    # yield list chunks of size n
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    # 300 and 1000 uL tips, p300 single, p1000 single

    tips1000 = [ctx.load_labware(
     "opentrons_96_tiprack_1000ul", str(slot)) for slot in [1]]

    p1000s = ctx.load_instrument(
        "p1000_single_gen2", 'left', tip_racks=tips1000)

    tips300 = [
     ctx.load_labware(
      "opentrons_96_tiprack_300ul", str(slot)) for slot in [2]]

    p300s = ctx.load_instrument(
        "p300_single_gen2", 'right', tip_racks=tips300)

    # tube rack for samples and mRNA stock
    tuberack = ctx.load_labware(
     'opentrons_24_tuberack_nest_1.5ml_snapcap', '7',
     '25 ug/mL Sample Stock and mRNA Stock')

    samps = [
     row[:count] for row, count in zip(tuberack.rows(), [
         count_samples_rowa, count_samples_rowb,
         count_samples_rowc, count_samples_rowd])]

    mrna = [row[-1] for row in tuberack.rows()]

    sample_plate = ctx.load_labware(
     'corning_96_wellplate_360ul_flat', '4', 'Sample Plate')

    tworows = []
    for index, row in enumerate(sample_plate.rows()):
        if not index % 2:
            new = row
            new.extend(sample_plate.rows()[index+1])
            tworows.append(new)

    test_plates = [
     ctx.load_labware('corning_96_wellplate_360ul_flat', str(slot),
                      'Test Plate {}'.format(
                      index+1)) for index, slot in enumerate([3, 6, 9, 5])]

    buffer_reservoir = ctx.load_labware(
     'nest_12_reservoir_15ml', '8', 'Buffer Reservoir')
    te, te_triton, pbs = [
     buffer_reservoir.wells_by_name()[name] for name in ['A1', 'A2', 'A3']]
    # deadvol_res = 3000

    # pbs.liq_vol = 13000*(tot_count / 20) + deadvol_res
    # te.liq_vol = 10400 + 6000*(tot_count / 20) + deadvol_res
    # te_triton.liq_vol = 4000 + 6000*(tot_count / 20) + deadvol_res

    # alert user to reagent volumes needed
    # ctx.comment("Ensure buffers in sufficient volume are present on deck.")
    # for volume, units, reagent, location in zip(
    # [math.ceil(rgnt.liq_vol) if rgnt.liq_vol < 1500 else math.ceil(
    # rgnt.liq_vol / 1000) for rgnt in [te, te_triton, pbs]],
    # ['mL', 'mL', 'mL'],
    # ['TE', 'TE Triton', 'PBS'],
    # [te, te_triton, pbs]):
    # ctx.comment(
    # "{0} {1} {2} in {3}".format(
    # str(volume), units, reagent.upper(), location))

    for repeat in range(num_samplerows):

        ctx.comment('\nStarting {}\n'.format(test_plates[repeat]))

        num_samps = len(samps[repeat])

        ctx.comment(
         '\nDistributing PBS to Sample Plate for {} samples\n'.format(
          num_samps))

        dests = [
         well.bottom(1) for chunk in [
          *create_chunks(tworows[repeat], 3)][:num_samps] for well in chunk]

        p1000s.distribute(
         num_samps*[210, 220, 230], pbs.bottom(1),
         dests, disposal_volume=100, blow_out=True,
         blowout_location='trash', new_tip='once')

        ctx.comment(
         '\nDistributing {} Samples to Sample Plate\n'.format(num_samps))

        for index, chunk in enumerate(
         [*create_chunks(tworows[repeat], 3)][:num_samps]):

            p300s.distribute(
             [40, 30, 20], samps[repeat][index].bottom(1),
             [well.top(2) for well in chunk],
             disposal_volume=10, blow_out=True,
             blowout_location='trash', touch_tip=True, new_tip='once')

        ctx.comment('\nDistributing TE to Test Plate\n')

        p1000s.pick_up_tip()

        for5thsample = [
         (well, well2) for well, well2 in zip(
          test_plates[repeat].rows()[4][8:11],
          test_plates[repeat].rows()[5][8:11])]

        dests = [well.bottom(1) for pair in [pair for chunk in [*create_chunks(
          [(well, well2) for well, well2 in zip(test_plates[repeat].rows()[0],
           test_plates[repeat].rows()[1])] + for5thsample, 3)
           ][:num_samps] for pair in chunk] for well in pair]

        p1000s.distribute(
         num_samps*3*[50, 50], te.bottom(1),
         dests, disposal_volume=100, blow_out=True,
         blowout_location='trash', new_tip='never')

        dests = [well.bottom(1) for pair in [
          pair for chunk in [*create_chunks(
           [(well, well2) for i, well, well2 in zip([*range(12)],
            test_plates[repeat].rows()[6],
            test_plates[repeat].rows()[7]) if (i and (not 8 <= i <= 10))], 2)
           ] for pair in chunk] for well in pair]

        p1000s.distribute(
         8*[50, 50], te.bottom(1), dests, disposal_volume=100,
         blow_out=True, blowout_location='trash',
         new_tip='never')

        dests = [well.bottom(1) for pair in [pair for chunk in [
          *create_chunks([(well, well2) for well, well2 in zip(
           test_plates[repeat].rows()[4],
           test_plates[repeat].rows()[5]) if (
           well, well2) not in for5thsample], 6)
          ] for pair in chunk] for well in pair]

        p1000s.distribute(
         9*[100, 100], te.bottom(1),
         dests, disposal_volume=100,
         blow_out=True, blowout_location='trash',
         new_tip='never')

        ctx.comment('\nDistributing TE-Triton to Test Plate\n')

        dests = [
         test_plates[repeat].rows()[rowindex][0].bottom(1) for rowindex in [
          6, 7]] + [te_triton.bottom(1)]

        p1000s.distribute(
         [100, 100, 100], te_triton.bottom(1),
         dests,
         disposal_volume=0, blow_out=False, new_tip='never')

        for5thsample = [(well, well2) for well, well2 in zip(
         test_plates[repeat].rows()[6][8:11],
         test_plates[repeat].rows()[7][8:11])]

        dests = [well.bottom(1) for pair in [pair for chunk in [*create_chunks(
          [(well, well2) for well, well2 in zip(test_plates[repeat].rows()[2],
           test_plates[repeat].rows()[3])] + for5thsample, 3)
           ][:num_samps] for pair in chunk] for well in pair
           ] + [te_triton.bottom(1)]

        vols = num_samps*3*[50, 50]

        vols = vols + [100]

        p1000s.distribute(
         vols, te_triton.bottom(1),
         dests, disposal_volume=0, blow_out=False,
         new_tip='never')

        dests = [
         well.bottom(1) for row in test_plates[repeat].rows(
         )[6:8] for i, well in zip([*range(12)], row) if (
          i and (not 8 <= i <= 10))] + [te_triton.bottom(1)]

        vols = 16*[50]

        vols = vols + [100]

        p1000s.distribute(
         vols, te_triton.bottom(1),
         dests, disposal_volume=0, blow_out=False, new_tip='never')

        p1000s.drop_tip()

        ctx.comment('\nAdding Sample to Test Plate\n')

        source = [*create_chunks(tworows[repeat], 3)][:num_samps]

        dest = [
         *create_chunks(test_plates[repeat].columns() + test_plates[
          repeat].columns()[8:11], 3)][:num_samps]

        for i, chunk, chunk2 in zip([0, 0, 0, 0, 4][:num_samps], source, dest):

            p300s.pick_up_tip()

            for well, column in zip(reversed(chunk), reversed(chunk2)):

                p300s.distribute(
                 4*[50], well.bottom(0.5),
                 [well.top(2) for well in column[i:i+4]],
                 disposal_volume=10, blow_out=True,
                 blowout_location='trash', touch_tip=True, new_tip='never')

            p300s.drop_tip()

        ctx.comment('\nSerial Dilution of mRNA in Test Plate\n')

        p1000s.distribute(
         4*[100], mrna[repeat].bottom(1),
         [row[0].top(2) for row in test_plates[repeat].rows()[4:]],
         disposal_volume=25, blow_out=True,
         blowout_location='trash', touch_tip=True, new_tip='once')

        # mix and transfer to next well
        for row in test_plates[repeat].rows()[4:]:
            p300s.pick_up_tip()
            for index, well in enumerate(row[:8]):
                dest = row[
                 index+1] if index < 7 else ctx.fixed_trash.wells()[0].top(-5)
                p300s.transfer(
                 100, well, dest, mix_before=(3, 100), new_tip='never')
            p300s.drop_tip()

        ctx.comment(
         '''\nFinished {}. Pause the robot to remove it from the deck\n
        \nResume to continue with remaining test plates.\n'''.format(
          test_plates[repeat]))

    ctx.comment("""\nProcess complete for all test plates\n""")

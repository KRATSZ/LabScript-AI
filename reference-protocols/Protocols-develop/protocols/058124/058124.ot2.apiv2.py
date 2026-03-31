import math
import csv
from datetime import datetime
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''Custom Serial Dilution for Protein Quantification''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    # get parameter values from json above
    [labware_reservoir, deadvol_reservoir,
     uploaded_csv] = get_values(  # noqa: F821
      'labware_reservoir', 'deadvol_reservoir', 'uploaded_csv')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # input csv - dilution scheme (1-6) assigned for 1-48 samples
    csvrows = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    for index, sample in enumerate(csvrows):

        if not 1 <= int(sample['dilution scheme']) <= 9:
            raise Exception('Dilution scheme must be 1-9.')

        if not index:
            if not int(sample['sample number']) == 1:
                raise Exception(
                 'Sample numbers in input csv file must start with 1.')
        else:
            if not int(
             sample['sample number']) == int(
             csvrows[index-1]['sample number']) + 1:
                raise Exception(
                 'Invalid series of sample numbers in input csv file.')
            if not 2 <= int(sample['sample number']) <= 48:
                raise Exception(
                 'Sample number in input csv file must be 1-48.')

    # filter tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [10]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [11]]
    p20s = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # yield list chunks of size n
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

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

    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # notify user to replenish tips
    def pick_up_or_refill(pip):
        try:
            pip.pick_up_tip()
        except OutOfTipsError:
            ctx.pause(
             """\n***\nPlease Refill the {} Tip Boxes
             and Empty the Tip Waste\n***\n""".format(pip))
            pip.reset_tipracks()
            pip.pick_up_tip()

    # list assigned samples for each scheme (chunks of 8, last one may be < 8)
    dilutions = {
     num+1: [*create_chunks([int(sample[
      'sample number']) for sample in csvrows if int(sample[
       'dilution scheme']) == num+1], 8)] for num in range(9)}

    # sample racks
    sample_racks = [
     ctx.load_labware(
      'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
      str(slot), 'sample rack') for slot in [
      1, 4][:math.ceil(len(csvrows) / 24)]]

    sample_positions = [
     well for rack in sample_racks for well in rack.wells()][:len(csvrows)]

    sample_cols_per_scheme = [len(dilutions[key+1]) for key in range(9)]

    for scheme in range(9):
        ctx.comment(
         """\n***\nScheme {}, preparing dilutions
         for {} columns of samples\n***\n""".format(
          str(scheme+1), sample_cols_per_scheme[scheme]))

    diluent = ctx.load_labware(labware_reservoir, '8', 'diluent').wells()[0]

    sample_cols_total = sum(sample_cols_per_scheme)

    # up to 4 dilution plates (4 consecutive columns per chunk of 8 samples)
    dilution_plates = [
     ctx.load_labware(
      'nest_96_wellplate_2ml_deep', str(slot), 'dilution plate') for slot in [
      2, 3, 5, 6][:math.ceil(sample_cols_total / 3)]]

    # to yield 4-column chunk as next dilution destination
    def thirds():

        lst = [
         chunk for plate in dilution_plates for chunk in create_chunks(
          plate.columns(), 4)]
        return lst

    dest = thirds()

    # dilution scheme parameters
    params = {
     1: {"diluent vol": [990, 450, 150],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [50, 150]},
     2: {"diluent vol": [990, 150],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [150]},
     3: {"diluent vol": [490, 450, 150],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [50, 150]},
     4: {"diluent vol": [380, 450, 100],
         "sample vol": 20,
         "mix count": 15,
         "serial vol": [50, 100]},
     5: {"diluent vol": [990, 450, 450, 100],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [50, 50, 100]},
     6: {"diluent vol": [490, 450, 450, 100],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [50, 50, 100]},
     7: {"diluent vol": [788, 150, 100],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [150, 100]},
     8: {"diluent vol": [290, 270, 190],
         "sample vol": 10,
         "mix count": 15,
         "serial vol": [30, 10]},
     9: {"diluent vol": [188, 160, 160, 160, 160, 94],
         "sample vol": 12,
         "mix count": 15,
         "serial vol": [40, 40, 40, 40, 50]}
         }

    # diluent reservoir fill volume - calculate and notify
    diluent.liq_vol = 0
    for key in params.keys():
        numsamps = 0
        for _ in dilutions[key]:
            numsamps += len(_)
        diluent.liq_vol += numsamps*sum(params[key]['diluent vol'])
    diluent.liq_vol += deadvol_reservoir
    ctx.pause(
     """\n***\nEnsure reservoir is filled with
     {} mL diluent. Resume\n***\n""".format(
      diluent.liq_vol / 1000))

    output = []  # to collect destination location for each sample

    # to yield next tip column
    def tipcolumns():

        yield from tips300[0].columns()

    tipcol = tipcolumns()

    # for each dilution scheme and all of its assigned samples
    for key, value in dilutions.items():

        # for each column of 8 samples (last column may be < 8)
        for samplenums in value:

            # construct destination for dilutions in 4-column increments
            destination = []
            numblocks = math.ceil(len(params[key]["diluent vol"]) / 4)
            for block in range(numblocks):
                destination.extend(dest[block])

            # destination wells - set current vol to 0
            for column in destination:

                column[0].liq_vol = 0

            # notify user - current scheme, assigned samples, destination
            ctx.comment(
             "\n***\nCurrent Dilution Scheme: {}\n***\n".format(key))
            ctx.comment("\n***\nAssigned Samples: {}\n***\n".format(value))
            ctx.comment("\n***\nCurrent Samples: {}\n***\n".format(samplenums))
            ctx.comment(
             "\n***\nCurrent Destination: {}\n***\n".format(destination))

            # to pick up one tip for each sample (last column may be < 8)
            tipcolindex = abs(len(samplenums)-8)

            col = next(tipcol)

            p300m.pick_up_tip(col[tipcolindex])

            # diluent transfer to destination columns
            for vol, column in zip(params[key]['diluent vol'], destination):

                diluent.liq_vol -= vol  # increment reservoir volume

                ht = liq_height(
                 diluent) - 3 if liq_height(
                 diluent) - 3 > 1 else 1

                reps = math.ceil(vol / 200)

                v = vol / reps

                for rep in range(reps):

                    p300m.aspirate(v, diluent.bottom(ht))
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p300m, diluent)

                    p300m.dispense(v, column[0].bottom(1))
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p300m, column[0])
                    p300m.touch_tip(radius=0.9, v_offset=-2, speed=10)
                    column[0].liq_vol += v  # increment current dest vol

            # sample to wells of 1st column of 4-column destination chunk
            for samplenum, d in zip(
             samplenums, [well for well in destination[0]]):

                p20s.pick_up_tip()

                sampvol = params[key]['sample vol']

                source = sample_positions[samplenum - 1]

                ht_disp = liq_height(destination[0][0])

                p20s.mix(5, sampvol, source.bottom(1))
                p20s.aspirate(sampvol, source.bottom(1))
                p20s.touch_tip(radius=0.75, v_offset=-2, speed=10)

                # dispense to top of liquid
                p20s.dispense(sampvol, d.bottom(ht_disp))
                p20s.mix(5, sampvol, d.bottom(1))
                ctx.delay(seconds=1)
                slow_tip_withdrawal(p20s, d)
                p20s.touch_tip(radius=0.85, v_offset=-2, speed=10)

                output.append((samplenum, str(d)))  # dest location for output

                p20s.drop_tip()

            # serial transfer
            tfervols = params[key]['serial vol']

            tfercount = len(tfervols)

            for i, vol, column in zip(
             [*range(tfercount)], tfervols, destination):

                # tip height - top of liquid column
                mixht = liq_height(column[0])

                # premix
                for rep in range(params[key]['mix count']):
                    p300m.aspirate(200, column[0].bottom(1))
                    p300m.dispense(200, column[0].bottom(mixht))

                if vol >= 20:
                    p300m.aspirate(vol, column[0].bottom(1))
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p300m, column[0])
                    p300m.touch_tip(radius=0.75, v_offset=-2, speed=10)

                    disploc = destination[destination.index(column)+1][0]

                    p300m.dispense(vol, disploc.bottom(1))

                else:

                    # p300 leaves well to allow p20s small vol transfer
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p300m, disploc)
                    p300m.touch_tip(radius=0.75, v_offset=-2, speed=10)

                    # p20s small volume transfer to filled wells in column
                    for j, well in enumerate(column[:len(samplenums)]):

                        p20s.pick_up_tip()

                        p20s.aspirate(vol, well.bottom(1))
                        ctx.delay(seconds=1)
                        slow_tip_withdrawal(p20s, well)
                        p20s.touch_tip(radius=0.75, v_offset=-2, speed=10)

                        disploc = destination[destination.index(column)+1][j]

                        p20s.dispense(vol, disploc.bottom(1))

                        p20s.drop_tip()

                if i == tfercount - 1:

                    # final postmix in last column
                    for rep in range(15):
                        p300m.aspirate(200, disploc.bottom(1))
                        p300m.dispense(200, disploc.bottom(mixht))
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p300m, disploc)
                    p300m.touch_tip(radius=0.75, v_offset=-2, speed=10)

            p300m.drop_tip()

    # output file - original csv content plus destination for each sample
    for row, dest in zip(csvrows, sorted(output)):

        row['destination'] = dest[1]

    """
    write output to jupyter notebook directory on OT-2 raspberry pi
    for file download via web browser [OT-2 IP address]:48888
    """

    # unique filename to avoid accidental over writing
    current = datetime.now()
    file = 'var/lib/jupyter/notebooks/outputfile{}.csv'.format(
     str(current.microsecond))

    if not ctx.is_simulating():
        with open(file, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=csvrows[0].keys())
            writer.writeheader()
            for row in csvrows:
                writer.writerow(row)

    ctx.comment("""\n***\nfinished - use the Opentrons app (click jupyter link)
    to locate and download the output csv file\n***\n""")

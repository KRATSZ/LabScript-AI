import math
from datetime import datetime
import csv


metadata = {
    'protocolName': '''Custom Normalization''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    # get parameter values from json above
    [uploaded_csv] = get_values(  # noqa: F821
      'uploaded_csv')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    csvrows = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    sample_count = len(csvrows)

    if not 1 <= sample_count <= 96:
        raise Exception('Number of samples must be 1-96.')

    for sample in csvrows:
        if not 30 <= float(sample['volume_target (ul)']) <= 100:
            raise Exception('Target volume must be 30-100 uL')
        if not 5 <= float(sample['dna_conc_target (ng/ul)']) <= 40:
            raise Exception('Target concentration must be 5-40 ng/uL')

        # convert data type
        for key in [
         'dna_conc_initial (ng/ul)',
         'dna_conc_target (ng/ul)',
         'volume_target (ul)']:
            sample[key] = float(sample[key])

        # add calculated fields
        sample['fold dilution'] = sample[
         'dna_conc_initial (ng/ul)'] / sample['dna_conc_target (ng/ul)']

        sample['sample_transfer (ul)'] = sample[
         'volume_target (ul)']*(1/sample['fold dilution'])

        sample['water_transfer (ul)'] = sample[
         'volume_target (ul)'] - sample['sample_transfer (ul)']

        sample['processed'] = 'no'

    # filter tips, p20 single, p300 single
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [7]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [10]]
    p20s = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)
    p300s = ctx.load_instrument(
        "p300_single_gen2", 'right', tip_racks=tips300)

    # source tube for water
    tentuberack = ctx.load_labware(
     'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical',
     '1', '10-Tube Rack with Water Source Tube')
    [water] = [tentuberack.wells_by_name()[well] for well in ['A4']]
    water.liq_vol = 40000  # initial volume 40 mL

    output_plate = ctx.load_labware(
     'redefinedbiorad_96_wellplate_200ul', '5', 'ouput plate')

    intermediate_plate = ctx.load_labware(
     'redefinedbiorad_96_wellplate_200ul', '8', 'intermediate plate')

    reservoir = ctx.load_labware(
     'agilent_1_reservoir_290ml', '9', 'bleach reservoir')

    input_plate = ctx.load_labware(
     'nest_96_wellplate_2ml_deep', '11', 'input plate')

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

    # apply speed limit to departing tip
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

    ctx.comment(
     "\n***\nSTEP 1 - water to output plate\n***\n")

    p20s.pick_up_tip()
    p300s.pick_up_tip()

    for index, sample, well in zip(
     [*range(sample_count)], csvrows, input_plate.wells()[:sample_count]):

        # skip and log samples that are too dilute
        if sample['sample_transfer (ul)'] > 30:

            sample['intermediate_dilution'] = 0
            sample['processed'] = 0
            ctx.comment("\n***\nSample {0} in well {1} skipped\n***\n".format(
             sample['sample_id'], well.well_name))
            continue

        # prepare 10-fold intermediate dilution if sample too concentrated
        elif sample['sample_transfer (ul)'] < 2:

            sample['intermediate_dilution'] = 1
            sample['processed'] = 1
            ctx.comment(
             """\n***\nProcessing sample {0} in well {1}
             by intermediate dilution\n***\n""".format(
              sample['sample_id'], well.well_name))

        # otherwise transfer calculated vol of water and sample to output plate
        else:

            sample['intermediate_dilution'] = 0
            sample['processed'] = 1
            ctx.comment(
             "\n***\nProcessing sample {0} in well {1}\n***\n".format(
              sample['sample_id'], well.well_name))

        # transfer less water when an intermediate dilution is required
        vol_water = sample[
         'water_transfer (ul)'] if not sample['intermediate_dilution'] else (
         sample['water_transfer (ul)'] - (9*sample['sample_transfer (ul)']))

        pipette = p20s if vol_water <= 20 else p300s

        water.liq_vol -= vol_water

        # tip height about 3 mm below surface of water
        ht = liq_height(water) - 3 if liq_height(water) - 3 > 1 else 1

        pipette.aspirate(vol_water, water.bottom(ht))
        ctx.delay(seconds=0.5)
        pipette.dispense(vol_water, output_plate.wells()[index].bottom(1))
        ctx.delay(seconds=0.5)

    p20s.return_tip()
    p20s.reset_tipracks()

    p300s.return_tip()
    p300s.reset_tipracks()

    ctx.comment(
     """\n***\nSTEP 2 - sample to output plates
     (with intermediate dilution as needed)\n***\n""")

    for index, sample, well in zip(
     [*range(sample_count)], csvrows, input_plate.wells()[:sample_count]):

        if sample['processed']:

            vol_asp = 2 if sample[
             'intermediate_dilution'] else sample['sample_transfer (ul)']

            pipette = p20s if vol_asp <= 20 else p300s

            pipette.pick_up_tip()

            # if intermediate dilution - transfer 18 uL water
            if sample['intermediate_dilution']:

                water.liq_vol -= 18

                ht = liq_height(water) - 3 if liq_height(water) - 3 > 1 else 1

                pipette.aspirate(18, water.bottom(ht))
                ctx.delay(seconds=0.5)

                pipette.dispense(
                 18, intermediate_plate.wells()[index].bottom(1))
                ctx.delay(seconds=0.5)

            pipette.aspirate(vol_asp, well.bottom(1), rate=0.5)
            ctx.delay(seconds=0.5)
            slow_tip_withdrawal(pipette, well, to_center=True)

            if not sample['intermediate_dilution']:

                pipette.dispense(
                 vol_asp, output_plate.wells()[index].bottom(1), rate=0.5)
                ctx.delay(seconds=0.5)
                slow_tip_withdrawal(pipette, output_plate.wells()[index])

            else:

                pipette.dispense(
                 vol_asp, intermediate_plate.wells()[index].bottom(1),
                 rate=0.5)
                ctx.delay(seconds=0.5)
                pipette.mix(
                 10, 16, intermediate_plate.wells()[index].bottom(1))
                pipette.aspirate(
                 10*sample['sample_transfer (ul)'],
                 intermediate_plate.wells()[index].bottom(1))
                ctx.delay(seconds=0.5)
                slow_tip_withdrawal(pipette, intermediate_plate.wells()[index])

                pipette.dispense(
                 10*sample['sample_transfer (ul)'],
                 output_plate.wells()[index].bottom(1), rate=0.5)
                ctx.delay(seconds=0.5)
                slow_tip_withdrawal(pipette, output_plate.wells()[index])

            # rinse tip in 10 percent diluted bleach
            v = 20 if pipette == p20s else 200

            pipette.aspirate(v, reservoir.wells()[0].bottom(10))
            pipette.dispense(v, reservoir.wells()[0].bottom(10))

            pipette.drop_tip()

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

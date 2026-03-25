import math

# metadata
metadata = {
    'protocolName': 'HPLC Picking',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [input_file, default_transfer_vol, p300_mount] = get_values(  # noqa: F821
        'input_file', 'default_transfer_vol', 'p300_mount')

    # load labware
    rack = ctx.load_labware('eurofins_96x2ml_tuberack', '2', 'tuberack')
    plates = [
        ctx.load_labware('irishlifesciences_96_wellplate_2200ul', slot,
                         f'plate {i+1}')
        for i, slot in enumerate(['10', '7', '4', '1'])]
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '11')]

    # pipette
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips300)

    # parse
    data = [
        line.split(',') for line in input_file.splitlines()
        if line and line.split(',')[0].strip()]

    # order
    wells_ordered = [
        well for plate in plates for row in plate.rows() for well in row]

    dest_vols = {}
    prev_dest = None
    for i, line in enumerate(data):
        source = wells_ordered[int(line[0]) - 1]
        dest = rack.wells_by_name()[line[1].upper()]
        if len(line) > 2 and line[2]:
            vol = round(float(line[2]))
        else:
            vol = default_transfer_vol

        if dest != prev_dest:
            if p300.has_tip:
                p300.drop_tip()
            p300.pick_up_tip()

        # effective tip capacity 280 with 20 uL air gap
        reps = math.ceil(vol / 280)

        v = vol / reps

        for rep in range(reps):
            p300.move_to(source.top())
            p300.air_gap(20)
            p300.aspirate(v, source.bottom(0.5))
            p300.dispense(
             v+20, dest.top(-1), rate=2)
            ctx.delay(seconds=1)
            p300.blow_out()

        prev_dest = dest

        # track volumes for final adjustment
        if dest not in dest_vols:
            dest_vols[dest] = vol
        else:
            dest_vols[dest] += vol
    p300.drop_tip()

    # final adjustment with water up to 1500ul
    ctx.pause('Replace plate 4 in slot 1 with water reservoir. Resume once \
finished.')
    water = plates[-1].wells_by_name()['D4']
    p300.pick_up_tip()
    for tube, vol in dest_vols.items():
        adjustment = 1500 - vol
        if adjustment > 0:
            # effective tip capacity 280 uL with 20 uL air gap
            reps = math.ceil(adjustment / 280)

            v = adjustment / reps

            for rep in range(reps):
                p300.move_to(water.top())
                p300.air_gap(20)
                p300.aspirate(v, water.bottom(1))
                p300.dispense(
                 v+20, tube.top(-1), rate=2)
                ctx.delay(seconds=1)
                p300.blow_out()

    p300.drop_tip()

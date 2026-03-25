import math

metadata = {
    'protocolName': '16S Library pooling',
    'author': 'Parrish Payne <parrish.payne@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}

# Step 1: Use a single channel pipettor and a new tip each time, transfer
# 2-35 uL from the 96 well PCR plate to a single 2 mL snap tube
# Step 2: Repeat across the entire plate according to the .csv file


def run(ctx):

    [input_csv, p20_mount] = get_values(  # noqa: F821
        'input_csv', 'p20_mount')

    p20_mount = 'right'

    # labware
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in [1, 4]]

    pcr_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr', 2)

    tube_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', 3)

    mag_mod = ctx.load_module('magnetic module gen2', 6)   # not used
    mag_mod.disengage()

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tips)

    # parse
    all_rows = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]][1:]

    all_samples = [
        well
        for well in pcr_plate.wells()
        ]

    for row, source in zip(all_rows, all_samples):

        volume = float(row[2])
        dest = (row[3])

        if volume > 20:
            num_transfers = math.ceil(volume/p20.max_volume)
            transfer_vol = volume/num_transfers
            for _ in range(num_transfers):

                p20.pick_up_tip()
                p20.aspirate(transfer_vol, source)
                p20.dispense(transfer_vol, tube_rack.wells_by_name()[dest])
                p20.drop_tip()
        else:
            p20.pick_up_tip()
            p20.aspirate(volume, source)
            p20.dispense(volume, tube_rack.wells_by_name()[dest])
            p20.drop_tip()

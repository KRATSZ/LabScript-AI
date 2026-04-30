metadata = {
    'protocolName': 'Sample Pooling Down Column',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [use_tuberack_A, tuberackA_tube, num_rows_A,
     use_tuberack_B, tuberackB_tube, num_rows_B,
     delay, asp_height, p300_mount] = get_values(  # noqa: F821
            "use_tuberack_A", "tuberackA_tube", "num_rows_A",
            "use_tuberack_B", "tuberackB_tube",
            "num_rows_B", "delay", "asp_height", "p300_mount")

    num_rows_A = int(num_rows_A)
    num_rows_B = int(num_rows_B)

    # load labware
    tuberack_A = ctx.load_labware(tuberackA_tube, '1',
                                  label='Tuberack A')
    tuberack_B = ctx.load_labware(tuberackB_tube, '2', label='Tuberack B')
    tiprack = ctx.load_labware('opentrons_96_filtertiprack_200ul', '4')

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2',
                               p300_mount, tip_racks=[tiprack])
    p300.well_bottom_clearance.aspirate = asp_height
    print(tuberack_B.wells())

    # protocol
    if use_tuberack_A:
        for i in range(0, num_rows_A):
            for j, well in enumerate(tuberack_A.rows()[i][:5]):
                p300.pick_up_tip()
                p300.aspirate(100, well)
                ctx.delay(seconds=delay)
                p300.dispense(100, tuberack_A.rows()[i][5])
                if j == 4:
                    p300.mix(15, 200, tuberack_A.rows()[i][5])
                p300.drop_tip()

    if use_tuberack_B:
        for i in range(0, num_rows_B):
            for j, well in enumerate(tuberack_B.rows()[i][:5]):
                p300.pick_up_tip()
                p300.aspirate(100, well)
                ctx.delay(seconds=delay)
                p300.dispense(100, tuberack_B.rows()[i][5])
                if j == 4:
                    p300.mix(15, 200, tuberack_B.rows()[i][5])
                p300.drop_tip()

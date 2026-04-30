from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Protocol 3 - Sample Plate setup',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [m300_mount, p1000_mount, samples, sample_vol, sample_asp_speed,
        tuberack_1, tuberack_2, tuberack_3,
        tuberack_4, tuberack_5, tuberack_6, tuberack_7,
        final_asp_speed, final_air_gap, tube_height, sample_plate_height,
        reservoir_height, tip_type] = get_values(  # noqa: F821
        "m300_mount", "p1000_mount", "samples", "sample_vol",
        "sample_asp_speed", "tuberack_1",
        "tuberack_2", "tuberack_3",
        "tuberack_4", "tuberack_5", "tuberack_6",
        "tuberack_7", "final_asp_speed", "final_air_gap",
        "tube_height", "sample_plate_height", "reservoir_height", "tip_type")

    final_asp_speed = float(final_asp_speed)
    final_air_gap = float(final_air_gap)
    tube_height = float(tube_height)
    sample_plate_height = float(sample_plate_height)
    reservoir_height = float(reservoir_height)

    # Get sample number
    samples = int(samples)
    if samples > 96:
        raise Exception("You cannot have greater than 96 samples")

    columns = math.ceil(samples/8)

    # Load Labware
    tiprack_300ul = ctx.load_labware(tip_type, 1)
    tiprack_1000ul = ctx.load_labware('opentrons_96_filtertiprack_1000ul', 2)
    tuberack_types = [tuberack_1, tuberack_2, tuberack_3, tuberack_4,
                      tuberack_5, tuberack_6, tuberack_7]

    tuberacks = []
    for rack, slot in zip(tuberack_types, range(5, 12)):
        tuberacks.append(ctx.load_labware(rack, slot))

    sample_plate = ctx.load_labware('kingfisher_96_deepwell_plate_2ml', 3)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 4)
    res_wells = reservoir.wells()[0:3]

    # Load Pipette
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=[tiprack_1000ul])
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[tiprack_300ul])

    # Get list of tubes across 7 racks based on sample number
    tuberack_wells = [tuberacks[i].wells() for i in range(len(tuberacks))]
    tuberack_samples = [well for wells in tuberack_wells for well in
                        wells][1:samples]

    sample_plate_wells = sample_plate.rows()[0][:columns]
    sample_plate_control = [well for well in sample_plate.wells()[:samples]
                            if well not in [sample_plate['A1'],
                            sample_plate['A12']]]

    # Aliquot 200 uL from ~7 Tube Racks
    p1000.flow_rate.aspirate = sample_asp_speed
    for tuberack_well, sample_well in zip(tuberack_samples,
                                          sample_plate_control):
        p1000.transfer(sample_vol, tuberack_well.bottom(tube_height),
                       sample_well.bottom(sample_plate_height), blow_out=True,
                       blowout_location='destination well', new_tip='always')

    ctx.pause("Add binding/beads solution to deck position 4")

    if tip_type == 'opentrons_96_filtertiprack_200ul':

        def pick_up(pip):
            try:
                pip.pick_up_tip()
            except protocol_api.labware.OutOfTipsError:
                pip.home()
                ctx.pause("Please replace the tips in slot 1!")
                pip.reset_tipracks()
                pip.pick_up_tip()

        # Aliquot 275 uL from Reservoir (Viscous Binding Solution)
        m300.flow_rate.aspirate = final_asp_speed
        for i, sample_well in enumerate(sample_plate_wells):
            for _, vol in zip(range(2), [150, 125]):
                pick_up(m300)
                m300.aspirate(vol, res_wells[i//4].bottom(reservoir_height))
                m300.air_gap(final_air_gap)
                m300.dispense(vol+final_air_gap, sample_well.center())
                m300.blow_out()
                m300.drop_tip()

    elif tip_type == 'opentrons_96_tiprack_300ul':

        m300.flow_rate.aspirate = final_asp_speed
        for i, sample_well in enumerate(sample_plate_wells):
            m300.transfer(275, res_wells[i//4].bottom(reservoir_height),
                          sample_well.center(), air_gap=final_air_gap,
                          blow_out=True, blowout_location='destination well',
                          new_tip='always')

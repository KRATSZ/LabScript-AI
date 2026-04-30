import math

metadata = {
    'protocolName': 'Protocol 1 - Washing Aliquot',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [m300_mount, samples, reservoir_height,
        plate_height] = get_values(  # noqa: F821
        "m300_mount", "samples", "reservoir_height", "plate_height")

    reservoir_height = float(reservoir_height)
    plate_height = float(plate_height)
    samples = int(samples)
    columns = math.ceil(samples/8)

    # Load Labware
    tipracks = ctx.load_labware('opentrons_96_filtertiprack_200ul', 1)
    wash_1 = ctx.load_labware('nest_12_reservoir_15ml', 7)
    wash_2 = ctx.load_labware('nest_12_reservoir_15ml', 8)
    elution = ctx.load_labware('nest_12_reservoir_15ml', 9)
    dw_plate_wash_1 = ctx.load_labware('kingfisher_96_deepwell_plate_2ml', 4)
    dw_plate_wash_2 = ctx.load_labware('kingfisher_96_deepwell_plate_2ml', 5)
    dw_plate_elution = ctx.load_labware('kingfisher_96_deepwell_plate_2ml', 6)

    # Load Pipette
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[tipracks])

    # Split Transfer Volumes
    max_vol = 200

    def split_transfer(vol, source, dest):
        while vol >= max_vol:
            m300.transfer(max_vol, source, dest, new_tip='never')
            vol -= max_vol
        else:
            if vol:
                m300.transfer(vol, source, dest, new_tip='never')

    # Aliquot 500uL of Wash 1
    m300.pick_up_tip()
    for wash_1_well, plate_1_well in zip(wash_1.wells()[:columns],
                                         dw_plate_wash_1.rows()[0][:columns]):
        split_transfer(500, wash_1_well.bottom(reservoir_height),
                       plate_1_well.bottom(plate_height))
    m300.drop_tip()

    # Aliquot 1000uL of Wash 2
    m300.pick_up_tip()
    for wash_2_well, plate_2_well in zip(wash_2.wells()[:columns],
                                         dw_plate_wash_2.rows()[0][:columns]):
        split_transfer(1000, wash_2_well.bottom(reservoir_height),
                       plate_2_well.bottom(plate_height))
    m300.drop_tip()

    # Aliquot 50uL of Elution
    m300.pick_up_tip()
    for elution_well in dw_plate_elution.rows()[0][:columns]:
        m300.transfer(50, elution.wells()[0].bottom(reservoir_height),
                      elution_well.bottom(plate_height), new_tip="never")
    m300.drop_tip()

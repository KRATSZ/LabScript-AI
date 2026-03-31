from opentrons import protocol_api

metadata = {
    'protocolName': 'SARS-COV2 (VSV) Neutralization Assay',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_plates, plate_type, serum_vol,
        lower_asp_height, m300_mount] = get_values(  # noqa: F821
        "num_plates", "plate_type", "serum_vol",
            "lower_asp_height", "m300_mount")

    # labware
    serum_res = ctx.load_labware('agilent_1_reservoir_290ml', 7)
    virus_res = ctx.load_labware('nest_12_reservoir_15ml', 8)
    source_plates = [ctx.load_labware(plate_type, slot)
                     for slot in [1, 2, 3]][:num_plates]
    dest_plates = [ctx.load_labware(plate_type, slot)
                   for slot in [4, 5, 6]][:num_plates]
    tips = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
            for slot in [9, 10, 11]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    def pick_up():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            m300.reset_tipracks()
            m300.pick_up_tip()

    def slow_tip_withdrawal(current_pipette, well_location, to_center=False):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            current_pipette.move_to(well_location.top())
        else:
            current_pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # mapping
    virus = virus_res.wells()[0]
    overlay = virus_res.wells()[1:4][:num_plates]
    serum = serum_res.wells()[0]
    trash = virus_res.wells()[11]

    # protocol
    ctx.comment('\n---------------ADDING SERUM TO PLATES----------------\n\n')
    pick_up()
    for plate in source_plates:
        m300.distribute(40, serum, plate.rows()[0][1:7], new_tip='never')
    ctx.comment('\n\n')

    for plate in source_plates:
        m300.aspirate(80, serum)
        m300.dispense(80, plate.rows()[0][7])
    ctx.comment('\n\n')

    for plate in source_plates:
        m300.aspirate(serum_vol, serum)
        m300.dispense(serum_vol, plate.rows()[0][0])

    m300.drop_tip()
    ctx.comment('\n\n')

    ctx.pause(f'''Please add {80-serum_vol}ul of media and appropriate amount
                  of sample to column 1''')

    ctx.comment('\n---------------SERIALLY DILUTING----------------\n\n')
    for plate in source_plates:
        for i in range(len(plate.rows()[0][:6])):
            pick_up()
            m300.mix(3, 40, plate.rows()[0][i].bottom(z=1-lower_asp_height))
            m300.aspirate(40, plate.rows()[0][i].bottom(z=1-lower_asp_height),
                          rate=0.4)
            if i < 5:
                m300.dispense(40, plate.rows()[0][i+1], rate=0.4)
            if i == 5:
                m300.dispense(40, trash, rate=0.4)

            m300.drop_tip()
        ctx.comment('\n')
    ctx.comment('\n\n\n\n ˚')

    ctx.comment('\n---------------ADDING VIRUS----------------\n\n')
    m300.pick_up_tip()
    for plate in source_plates:
        for col in plate.rows()[0][:7]:
            m300.mix(5, 300, virus)
            m300.aspirate(40, virus)
            m300.dispense(40, col.top())
            ctx.delay(seconds=2)
            m300.blow_out(col.top())
    m300.drop_tip()

    ctx.pause('Place plate in incubator at 37C for one hour')

    ctx.comment('\n------DISCARDING MEDIA & TRANSFER TO NEW PLATE-------\n\n')

    for s_plate, d_plate in zip(source_plates, dest_plates):
        for s, d in zip(s_plate.rows()[0][:8], d_plate.rows()[0][:8]):
            pick_up()
            m300.aspirate(100, d.bottom(z=1-lower_asp_height), rate=0.1)
            m300.dispense(100, trash)
            m300.aspirate(60, s.bottom(z=1-lower_asp_height))
            m300.dispense(60, d)
            m300.drop_tip()

    ctx.pause('Place plate in incubator at 37C for one hour')

    ctx.comment('\n------------TRANSFERRING OVERLAY-------------\n\n')
    for res_well, plate in zip(overlay, dest_plates):
        for col in plate.rows()[0][:8]:
            pick_up()
            m300.aspirate(140, res_well, rate=0.2)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(m300, col)
            m300.dispense(140, col, rate=0.2)
            slow_tip_withdrawal(m300, col)
            m300.drop_tip()
            ctx.comment('\n')

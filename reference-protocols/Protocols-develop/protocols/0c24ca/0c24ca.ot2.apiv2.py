import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Adding Transfection and Sample to Plate',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [csv_samp, number_05_plates, number_14_plates, remove_tube_vol, dest_plate,
        add_transfection_mix, trans_mix_vol,
        init_vol_50, p20_mount, p300_mount] = get_values(  # noqa: F821
        "csv_samp", "number_05_plates", "number_14_plates", "remove_tube_vol",
            "dest_plate",
            "add_transfection_mix", "trans_mix_vol",
            "init_vol_50", "p20_mount", "p300_mount")

    # labware
    source_plate_14 = [ctx.load_labware('thermofisher_96_wellplate_1400ul',
                                        slot) for slot in [1, 2, 3]][:number_14_plates]  # noqa: E501
    source_plate_05 = [ctx.load_labware('thermofisher_96_wellplate_500ul',
                                        slot) for slot in [4, 5, 6]][:number_05_plates]  # noqa: E501

    source_plate_14 = source_plate_14
    source_plate_05 = source_plate_05

    tuberack = ctx.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 7)  # noqa: E501

    dest_plate = ctx.load_labware(dest_plate, 8)
    tips200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in [10]]

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in [11]]

    csv_lines = [[val.strip() for val in line.split(',')]
                 for line in csv_samp.splitlines()
                 if line.split(',')[0].strip()][1:]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips200)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # mapping
    # liquid height tracking
    v_naught = init_vol_50*1000

    radius = tuberack.rows()[0][3].diameter/2

    h_naught = 0.85*v_naught/(math.pi*radius**2)

    h = h_naught

    def adjust_height(vol):
        nonlocal h

        dh = (vol/(math.pi*radius**2))*1.33

        h -= dh

        if h < 12:
            h = 1

    # protocol
    ctx.comment('\n---------------ADDING TUBES TO PLATES----------------\n\n')
    pip = p300 if remove_tube_vol > 20 else p20
    for line in csv_lines:
        source_well_name = line[0]
        source_slot = ctx.loaded_labwares[int(line[1])]
        source_well = source_slot.wells_by_name()[source_well_name]

        dest_well_name = line[2]
        dest_slot = ctx.loaded_labwares[8]
        dest_well = dest_slot.wells_by_name()[dest_well_name]

        pick_up(pip)
        pip.aspirate(remove_tube_vol, source_well.bottom(z=2))
        pip.dispense(remove_tube_vol, dest_well)
        if pip == p300:
            pip.blow_out()
            pip.touch_tip()
        pip.drop_tip()

    if add_transfection_mix:
        pip = p300 if trans_mix_vol > 20 else p20
        trans_mix_tube = tuberack.rows()[0][3]
        for line in csv_lines:

            dest_well_name = line[2]
            dest_slot = ctx.loaded_labwares[8]
            dest_well = dest_slot.wells_by_name()[dest_well_name]

            pick_up(pip)
            pip.aspirate(trans_mix_vol, trans_mix_tube)
            adjust_height(trans_mix_vol)
            pip.dispense(trans_mix_vol, dest_well)

            if pip == p300:
                pip.blow_out()
                pip.touch_tip()
            pip.drop_tip()

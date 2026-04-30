metadata = {
    'protocolName': 'PCR2 set up',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    ctx.set_rail_lights(True)

    # uploaded parameters
    [plate_count, choose_tip_rack, uploaded_csv] = get_values(  # noqa: F821
        "plate_count", "choose_tip_rack", "uploaded_csv")

    # sample type from manifest
    type_line = uploaded_csv.splitlines()[2]
    sample_type = type_line[type_line.find('(')+1:type_line.find(')')]

    # tips and p10 multi pipette
    tips10 = [
     ctx.load_labware(choose_tip_rack, str(slot)) for slot in [8, 11, 7, 10]]
    p10m = ctx.load_instrument(
        "p10_multi", 'right', tip_racks=tips10)

    # labware
    [pcr1_plate_1, barcode_plate_1, pcr2_plate_1, pcr2_mix_plate] = [
     ctx.load_labware(labware, slot) for labware, slot in zip(
        ["nest_96_wellplate_100ul_pcr_full_skirt",
         "nest_96_wellplate_100ul_pcr_full_skirt",
         "nest_96_wellplate_100ul_pcr_full_skirt",
         "biorad_96_wellplate_200ul_pcr"],
        [str(num) for num in [1, 2, 3, 9]])]

    # first PCR 1 plate in  slot 1
    pcr1_plates = [pcr1_plate_1]

    # first barcode plate (reverse primers) in slot 2
    barcode_plates = [barcode_plate_1]
    pcr2_plates = [pcr2_plate_1]

    # 1st PCR 2 mx, 2nd PCR 2 mx (optional), water in columns 1, 2, 3 in slot 9
    pcr2_mix_1, pcr2_mix_2, water = [pcr2_mix_plate.columns_by_name()[
     str(column)][0] for column in [1, 2, 3]]

    # optional 2nd PCR 1 plate, barcode plate, PCR 2 plate in slots 4, 5, 6
    if plate_count == 2:
        for plate_list, labware, slot in zip(
         [pcr1_plates, barcode_plates, pcr2_plates],
         ["nest_96_wellplate_100ul_pcr_full_skirt",
          "nest_96_wellplate_100ul_pcr_full_skirt",
          "nest_96_wellplate_100ul_pcr_full_skirt"], [4, 5, 6]):
            plate_list.append(ctx.load_labware(labware, str(slot)))

    # barcodes, PCR1 prod, PCR2 mx (forward primer as plate id) to pcr2 plates
    for index, plate in enumerate(pcr2_plates):
        p10m.transfer(
         2, [column[0] for column in barcode_plates[index].columns()],
         [column[0] for column in plate.columns()],
         new_tip='always', trash=False)
        if sample_type == "plasma":
            p10m.transfer(
             10, [column[0] for column in pcr1_plates[index].columns()],
             [column[0] for column in plate.columns()],
             new_tip='always', trash=False)
        else:
            for j, column in enumerate(plate.columns()):
                p10m.consolidate(
                 [8, 2], [water, pcr1_plates[index].columns()[j][0]],
                 column[0], new_tip='always', trash=False)

        ctx.set_rail_lights(False)
        ctx.pause("Please replenish the tips in slots 8 and 11. Then resume.")
        ctx.set_rail_lights(True)
        p10m.reset_tipracks()

        for column in plate.columns():
            p10m.pick_up_tip()
            p10m.transfer(
             [6.5, 6.5], pcr2_mix_plate.columns()[index][0],
             [column[0].top(), column[0].bottom()],
             new_tip='never', trash=False)
            p10m.mix(4, 10, column[0].bottom())
            p10m.return_tip()

    ctx.pause("""PCR2 set up is complete.
                 Please proceed with PCR2 thermocycling followed by the pooling
                 and clean up steps.""")

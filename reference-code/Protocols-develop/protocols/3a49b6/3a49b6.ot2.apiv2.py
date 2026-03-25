metadata = {
    'protocolName': 'Normalization',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    ctx.set_rail_lights(True)

    # uploaded csv
    [p20_side, clearance_water, mix_count, flow_rate_factor,
     uploaded_csv] = get_values(  # noqa: F821
        "p20_side", "clearance_water", "mix_count", "flow_rate_factor",
        "uploaded_csv")

    # data from csv
    header_line, *data_lines = uploaded_csv.splitlines()
    data = [
     dict(zip([item for item in header_line.split(",") if any(item)],
          [item for item in line.split(',')])) for line in data_lines]

    # tips and p20 single
    tips20 = [
     ctx.load_labware(
      "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [8, 5]]
    p20s = ctx.load_instrument(
        "p20_single_gen2", p20_side, tip_racks=tips20)

    # helper function
    def flow_rate_settings():
        if 0.5 <= flow_rate_factor <= 3:
            speed = flow_rate_factor*7.34
            p20s.flow_rate.aspirate = speed
            p20s.flow_rate.dispense = speed

    flow_rate_settings()

    # labware
    [tube_rack, dest_plate] = [
     ctx.load_labware(labware, slot) for labware, slot in zip(
        ["opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical",
         "nest_96_wellplate_100ul_pcr_full_skirt"],
        [str(num) for num in [11, 6, 9]])]

    # water in well A1 of tube rack in slot 11
    water = tube_rack.wells_by_name()['A1']

    # temperature module with pcr plate containing RNA in slot 3
    temp_mod = ctx.load_module('temperature module gen2', '3')
    rna = temp_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    temp_mod.set_temperature(4)

    # water to destination plate
    # if Vol RNA < 1 ul, set data['Vol RNA']='1'
    # if Vol H2O < 1 ul, set data['Vol H2O']='0'
    p20s.pick_up_tip()
    for item in data:
        if float(item['Vol RNA']) < 1:
            item['Vol RNA'] = '1'
        if float(item['Vol H2O']) < 1:
            item['Vol H2O'] = '0'
        p20s.transfer(
         round(float(item['Vol H2O']), 2), water.bottom(clearance_water),
         dest_plate.wells_by_name()[item['Well']],
         new_tip='never')
    p20s.drop_tip()

    # rna to destination plate
    for item in data:
        p20s.transfer(
         round(float(item['Vol RNA']), 2),
         rna.wells_by_name()[item['Well']],
         dest_plate.wells_by_name()[item['Well']],
         mix_after=(mix_count, 10), new_tip='always')

import math

metadata = {
    'protocolName': '''NEBNext Quarter Volume Library Prep Step 1:
    Enzymatic Fragmentation and End Prep''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_plates, labware_tempmod
     ] = get_values(  # noqa: F821
      'sample_count', 'labware_plates', 'labware_tempmod')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if sample_count < 48 or sample_count > 96:
        raise Exception('Number of samples must be 48-96.')

    # tips, p20 single, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [10]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module at 4 C with reagent tubes
    temp = ctx.load_module('Temperature Module', '1')
    block = temp.load_labware(
     labware_tempmod)
    [rxn_bf, enz_mx, mx_tube] = [block.wells_by_name()[name] for name in [
     'A1', 'A2', 'A3']]
    deadvol_tube = 10
    temp.set_temperature(4)

    ctx.load_module('magnetic module gen2', '9')

    reagent_plate = ctx.load_labware(labware_plates, '6', 'Reagent Plate')

    libraryprep_plate = ctx.load_labware(
     labware_plates, '3', 'Library Prep Plate')

    # reaction buffer volume 14 uL per column of samples
    rxn_bf.liq_vol = 1.1*14*num_cols + 2*deadvol_tube

    # enzyme mix volume 4 uL per column of samples
    enz_mx.liq_vol = 1.1*4*num_cols + deadvol_tube

    # alert user to reagent volumes needed
    ctx.comment(
     "\n***\nEnsure reagents in sufficient volume are present on deck\n***\n")
    for volume, reagent, location in zip(
                                    [math.ceil(rxn_bf.liq_vol),
                                     math.ceil(enz_mx.liq_vol)],
                                    ['reaction buffer', 'enzyme mix'],
                                    [rxn_bf, enz_mx]):
        ctx.comment(
         "\n***\n{0} uL {1} in {2}\n***\n".format(
          str(volume), reagent.upper(), location))

    # p300m "single channel" reaction buffer to mix tube with 10 pct overage
    p300m.pick_up_tip(tips300[0]['H12'])
    p300m.transfer(
     1.1*(14*num_cols)+(14/18)*deadvol_tube,
     rxn_bf.bottom(0.5), mx_tube, new_tip='never')
    p300m.drop_tip()

    # enzyme mix to mix tube with 10 percent overage and mix
    p300m.pick_up_tip(tips300[0]['H11'])
    p300m.transfer(
     1.1*(4*num_cols)+(4/18)*deadvol_tube,
     enz_mx.bottom(0.5), mx_tube, mix_after=(
      10, 14*num_cols), new_tip='never')

    # same tip fragmentation mix to Reagent Plate 1st column with extra 2 uL
    vol = 2.25*num_cols+2
    for well in reagent_plate.columns()[0]:
        p300m.aspirate(vol, mx_tube.bottom(0.5))
        p300m.dispense(vol, well)
    p300m.drop_tip()

    # 2.25 uL fragmentation mastermix to each sample
    p20m.transfer(
     2.25, reagent_plate.columns()[0][0].bottom(0.5),
     [column[0] for column in libraryprep_plate.columns()[:num_cols]],
     mix_after=(5, 10), new_tip='always')

    ctx.comment("\n***\nVortex, spin and incubate on PCR machine\n***\n")

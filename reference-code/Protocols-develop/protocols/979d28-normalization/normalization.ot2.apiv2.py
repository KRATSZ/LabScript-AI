import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Normalization',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.12'
}

normalization_vol = 15
mm_vol = 5


def run(ctx):

    conc_target, file_input = get_values(  # noqa: F821
        'conc_target', 'file_input')

    tempdeck = ctx.load_module('Temperature Module Gen2', '9')
    tempdeck2 = ctx.load_module('Temperature Module Gen2', '3')
    tempdeck.set_temperature(4)
    tempdeck2.set_temperature(4)
    source_plate = tempdeck.load_labware('vwr_96_aluminumblock_200ul',
                                         'source RNA plate')
    dest_plate = tempdeck2.load_labware('vwr_96_aluminumblock_200ul',
                                        'qPCR plate')
    mm = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '5', 'reaction mix (tube A1)').wells()[0]
    water = ctx.load_labware('nest_12_reservoir_15ml', '2',
                             'water (channel A1)').wells()[0]
    # parse
    data = [
        [val.strip() for val in line.split(',')]
        for line in file_input.splitlines()[1:]
        if line and line.split(',')[0].strip()]

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in ['7', '10'][:math.ceil(len(data)/48)]]
    p20 = ctx.load_instrument('p20_single_gen2', 'left', tip_racks=tips20)

    def calculate_volume(conc):
        return round(conc_target*1000/conc, 2)

    # parse
    data = [
        [val.strip() for val in line.split(',')]
        for line in file_input.splitlines()[1:]
        if line and line.split(',')[0].strip()]

    # pre-add water
    transfer_vols = []
    bad_wells = []
    p20.pick_up_tip()
    for i, line in enumerate(data):
        conc = float(line[2])
        vol_cdna = float(line[3])
        vol_water = float(line[4])
        if vol_cdna > normalization_vol:
            ctx.comment(f'Sample in well \
{source_plate.wells()[i].display_name.split(" ")[0]} cannot be normalized \
(starting concentration {conc}ng/ul requires {vol_cdna}ul transfer). Skipping')
            bad_wells.append(dest_plate.wells()[i])
            transfer_vols.append(None)
        else:
            dest = dest_plate.wells()[i]
            transfer_vols.append(vol_cdna)
            p20.aspirate(vol_water, water)
            p20.dispense(vol_water, dest.bottom(1))
            p20.move_to(dest.bottom().move(Point(x=-1.5, z=5)))

    # transfer RNA sample to normalize
    for i, vol in enumerate(transfer_vols):
        if vol:
            if not p20.has_tip:
                p20.pick_up_tip()
            source = source_plate.wells()[i]
            dest = dest_plate.wells()[i]
            p20.aspirate(vol, source)
            p20.aspirate(1, dest)
            p20.dispense(p20.current_volume)
            p20.move_to(dest.bottom().move(Point(x=-1.5, z=5)))
            p20.drop_tip()

    # transfer mastermix and mix
    for dest in dest_plate.wells()[:len(data)]:
        if dest not in bad_wells:
            p20.pick_up_tip()
            p20.transfer(mm_vol, mm, dest, mix_after=(5, 10), new_tip='never')
            p20.move_to(dest.bottom().move(Point(x=-1.5, z=5)))
            p20.drop_tip()

    bad_list = [well.display_name.split(' ')[0] for well in bad_wells]
    if len(bad_list) > 0:
        bad_msg = '\n\n'.join(bad_list)
        ctx.comment(f'The following sample wells failed: \n\n{bad_msg}')

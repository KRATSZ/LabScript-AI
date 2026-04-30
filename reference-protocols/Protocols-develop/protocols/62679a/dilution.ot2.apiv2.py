metadata = {
    'protocolName': 'Compound Dilution',
    'author': 'Nick <ndiehl@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    [file_dilution, lw_dmso, mount_p300, mount_p20,
     tipstrategy_dilution] = get_values(  # noqa: F821
     'file_dilution', 'lw_dmso', 'mount_p300', 'mount_p20',
     'tipstrategy_dilution')

    mix_reps = 5

    compound_management_plate = ctx.load_labware(
        'greinerbioone_96_wellplate_340ul', '1', 'compound management plate')
    tipracks200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['7', '8', '11']]
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['9']]
    compound_dilution_plates = {
        str(i+1): ctx.load_labware('perkinelmer_96_wellplate_450ul', slot,
                                   f'compound plate {i+1}')
        for i, slot in enumerate(['4', '5', '6', '3'])}
    dmso = ctx.load_labware(lw_dmso, '10', 'DMSO (position 1)').wells()[0]

    p300 = ctx.load_instrument('p300_single_gen2', mount_p300,
                               tip_racks=tipracks200)
    p20 = ctx.load_instrument('p20_single_gen2', mount_p20,
                              tip_racks=tipracks20)

    # parse
    data = [
        [val.strip().lower() for val in line.split(',')]
        for line in file_dilution.splitlines()[3:]
        if line and line.split(',')[8].strip()]

    def parse_well_name(name):
        return f'{name[0].upper()}{int(name[1:])}'

    def parse_column(name):
        return str(int(name[1:]))

    substance_map = {
        line[3]: compound_management_plate.wells_by_name()[
            parse_well_name(line[1])]
        for line in data if line[3]
    }

    # transfer stock to compound dilution plates
    for line in data:
        substance = line[10]
        if substance:
            p300.transfer(float(line[12]), substance_map[line[10]],
                          compound_dilution_plates[line[8]].wells_by_name()[
                            parse_well_name(line[9])],
                          mix_before=(mix_reps, 50))

    ctx.pause('Check plate/spin down to ensure there are no air bubbles.')

    # pre-transfer DMSO before dilution
    p300.pick_up_tip()
    for line in data:
        substance = line[10]
        if substance:
            p300.distribute(
                float(line[13]), dmso,
                compound_dilution_plates[
                    line[8]].columns_by_name()[parse_column(line[9])][1:],
                disposal_volume=5,
                air_gap=10,
                new_tip='never')
    p300.drop_tip()

    # dilute down each column
    for line in data:
        substance = line[10]
        if substance:
            vol = float(line[14])
            column = compound_dilution_plates[
                line[8]].columns_by_name()[parse_column(line[9])]
            [pip, mix_vol] = [p300, 50] if vol >= 20 else [p20, 20]
            sources = column[:6]
            destinations = column[1:7]
            pip.pick_up_tip()
            pip.mix(mix_reps, mix_vol, column[0])
            for s, d in zip(sources, destinations):
                if not pip.has_tip:
                    pip.pick_up_tip()
                pip.transfer(vol, s, d, mix_after=(mix_reps, mix_vol),
                             new_tip='never')
                if tipstrategy_dilution == 'always':
                    pip.air_gap(pip.min_volume)
                    pip.drop_tip()

            if tipstrategy_dilution == 'once':
                pip.air_gap(pip.min_volume)
                pip.drop_tip()

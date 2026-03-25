import math
import json

metadata = {
    'protocolName': 'Normalization',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.11'
}


def run(ctx):

    [dil_json_1, dil_json_2, dil_json_3, p1000_mount, m300_mount, final_vol
     ] = get_values(  # noqa: F821
        'dil_json_1', 'dil_json_2', 'dil_json_3', 'p1000_mount', 'm300_mount',
        'final_vol')

    # labware
    dw_plate = ctx.load_labware('thermofisherabgene_96_wellplate_2200ul', '8',
                                'deepwell plate')
    final_dilution_plates = [
        ctx.load_labware('nunc_96_wellplate_500ul', slot,
                         f'final dilution plate {i+1}')
        for i, slot in enumerate(['4', '5', '6'])]
    diluent = ctx.load_labware('thermofishernalgene_1_reservoir_300000ul',
                               '9', 'diluent').wells()[0]
    tipracks1000 = [
        ctx.load_labware('opentrons_96_tiprack_1000ul', slot)
        for slot in ['10']]
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['7']]

    # pipettes
    if p1000_mount == m300_mount:
        raise Exception('Pipette mounts cannot match.')
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tipracks1000)
    p300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks300)

    tip_data = {
        'single': {
            'count': 0,
            'tips': [
                well for rack in tipracks300[::-1]
                for col in rack.columns()[::-1]
                for well in col[::-1]]
        },
        'multi': {
            'count': 0,
            'tips': [well for rack in tipracks300 for well in rack.rows()[0]]
        }
    }

    def pickup_p300(mode='single'):
        current = 0.1 if mode == 'single' else 0.5
        ctx._implementation._hw_manager.hardware._attached_instruments[
            p300._implementation.get_mount()].update_config_item(
                'pick_up_current', current)

        p300.pick_up_tip(tip_data[mode]['tips'][tip_data[mode]['count']])
        tip_data[mode]['count'] += 1

    def extract_well_name(well_obj):
        return well_obj.display_name.split(' ')[0]

    def custom_transfer(vol, source, dest, pip=p300):
        num_trans = math.ceil(vol/pip.max_volume)
        vol_per_trans = vol/num_trans
        for n in range(num_trans):
            pip.aspirate(vol_per_trans, source)
            pip.dispense(vol_per_trans, dest)

    def determine_dil(col):
        rows = 'ABCDEFGH'
        col = dw_plate.rows()[0].index(col)
        dict = [dict1, dict2, dict3][col % 3]
        wells_to_check = [row + str(col+1) for row in rows]
        for well in wells_to_check:
            if dict[well]:
                return True
        return False

    # pre-parse `None` to `null`
    dil_json_1 = dil_json_1.replace('None', 'null')
    dil_json_2 = dil_json_2.replace('None', 'null')
    dil_json_3 = dil_json_3.replace('None', 'null')

    # read .json files as dictionaries
    dict1 = json.loads(dil_json_1)
    dict2 = json.loads(dil_json_2)
    dict3 = json.loads(dil_json_3)

    map_dil_wells = {
        well_set[0]: {
            well_set[0]: dict1[extract_well_name(well_set[0])],
            well_set[1]: dict2[extract_well_name(well_set[1])],
            well_set[2]: dict3[extract_well_name(well_set[2])]
        }
        for well_set in [
            row[i*3:(i+1)*3] for i in range(4) for row in dw_plate.rows()]
    }

    final_locations = []
    for key, dict in map_dil_wells.items():
        final_well = None
        for well, vol in dict.items():
            if vol:
                final_well = well
        final_locations.append(final_well)

    # pre-add diluent
    pickup_p300('multi')
    for col in dw_plate.rows()[0]:
        if determine_dil(col):
            for _ in range(4):  # 4x 200ul = 800ul
                p300.transfer(200, diluent, col, new_tip='never')
    p300.drop_tip()

    # prompt user to transfer neat sample
    display_wells = [
        well for well, vol in dict1.items() if vol]
    display_vols = [
        round(vol, 2) for vol in dict1.values() if vol]
    sample_str = '\n'.join([
        f'Transfer {display_vol}uL to well {display_well} of deepwell \
plate on slot 8.'
        for display_well, display_vol in zip(display_wells, display_vols)])
    ctx.pause(msg=sample_str)

    # perform dilutions
    for set in map_dil_wells.values():
        for i, (well, vol) in enumerate(set.items()):
            if i > 0 and vol:  # neat is manually added
                if vol <= 200:
                    pip = p300
                    pickup_p300('single')
                else:
                    pip = p1000
                    p1000.pick_up_tip()
                custom_transfer(vol, list(set.keys())[i-1], well, pip)
                pip.mix(5, 200, well)
                pip.drop_tip()

    # final transfer
    final_targets = [
        well for plate in final_dilution_plates for well in plate.rows()[0]]

    for source, dest in zip(final_locations, final_targets):
        if source:
            col = int(source.display_name.split(' ')[0][1:])
            if col % 3 == 1:
                pip.mix(5, 200, source)
            p1000.transfer(final_vol, source, dest)

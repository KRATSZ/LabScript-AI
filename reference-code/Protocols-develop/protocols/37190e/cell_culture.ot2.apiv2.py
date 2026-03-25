from opentrons.types import Point

metadata = {
    'protocolName': 'Cell Culture',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    num_plates, mount_p300, mount_p20 = get_values(  # noqa: F821
        'num_plates', 'mount_p300', 'mount_p20')

    plates = [
        ctx.load_labware('corning_96_wellplate_360ul_flat', f'{slot}',
                         f'plate {slot}')
        for slot in range(1, 1+num_plates)]
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '10')]
    tipracks200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '11')]
    tuberack = ctx.load_labware(
        'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', '9')

    p300 = ctx.load_instrument('p300_single_gen2', mount_p300,
                               tip_racks=tipracks200)
    p20 = ctx.load_instrument('p20_single_gen2', mount_p20,
                              tip_racks=tipracks20)

    vol_tracker = {
        well: 0.0
        for plate in plates
        for well in plate.wells()
    }

    def drop_all():
        for pip in [p300, p20]:
            if pip.has_tip:
                pip.drop_tip()

    def low_volume_dispense(vol, well, loc, pip=p20):
        pip.move_to(well.top(-1))
        ctx.max_speeds['A'] = 100
        ctx.max_speeds['X'] = 100
        ctx.max_speeds['Y'] = 100
        ctx.max_speeds['Z'] = 100

        if loc == 'bottom':
            dispense_loc = well.bottom(0.5)
            pip.dispense(vol)
            pip.blow_out()
        else:
            side = 1 if loc == 'right' else -1
            dispense_loc = well.top().move(Point(x=side*well.diameter/2, z=-1))
            pip.dispense(vol, dispense_loc)

        vol_tracker[well] += vol

        ctx.max_speeds['A'] = 400
        ctx.max_speeds['X'] = 100
        ctx.max_speeds['Y'] = 100
        ctx.max_speeds['Z'] = 400

    # transfer 1
    volumes1 = [50.00, 25.00, 12.50, 6.25, 3.13, 1.56, 50.00, 25.00, 12.50,
                6.25, 3.13]
    for plate in plates:
        for i, vol in enumerate(volumes1):
            pip = p300 if vol >= 20 else p20
            if not pip.has_tip:
                pip.pick_up_tip()
                for well in plate.columns()[i]:
                    if i == 6:
                        drop_all()
                        if not pip.has_tip:
                            pip.pick_up_tip()
                    pip.aspirate(vol, tuberack.wells_by_name()['A1'])
                    low_volume_dispense(vol, well, 'bottom', pip)
    drop_all()

    # transfer 2
    volumes2 = [50, 25, 12.5, 6.25, 3.13, 1.56, 0.78]
    for plate in plates:
        for i, vol in enumerate(volumes2):
            pip = p300 if vol >= 20 else p20
            if not pip.has_tip:
                pip.pick_up_tip()
                for well in plate.rows()[i]:
                    pip.aspirate(vol, tuberack.wells_by_name()['A2'])
                    low_volume_dispense(vol, well, 'left', pip)
    drop_all()

    # transfer 3
    vol_final = 100.0
    all_wells = [well for plate in plates for well in plate.wells()]
    for well in all_wells:
        vol = round(vol_final - vol_tracker[well], 2)
        pip = p300 if vol >= 20 else p20
        if not pip.has_tip:
            pip.pick_up_tip()
        pip.aspirate(vol, tuberack.wells_by_name()['A3'])
        low_volume_dispense(vol, well, 'right', pip)
    drop_all()

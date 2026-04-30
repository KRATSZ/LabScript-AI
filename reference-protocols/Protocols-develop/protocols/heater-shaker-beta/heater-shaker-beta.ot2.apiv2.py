import time

metadata = {
    'protocolName': '''Opentrons Heater Shaker Module beta test''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    # get parameter values from json above
    [hs_temp, hs_rpm, time_shake, every_nth_col, labware_hs, labware_source,
     labware_dest, tfer_vol, pip, pip_side] = get_values(  # noqa: F821
      'hs_temp', 'hs_rpm', 'time_shake', 'every_nth_col', 'labware_hs',
      'labware_source', 'labware_dest', 'tfer_vol', 'pip', 'pip_side')

    ctx.set_rail_lights(True)

    # selected pipette, corresponding tips in slot 11
    tipmap = {'p20_multi_gen2': 'opentrons_96_tiprack_20ul',
              'p20_single_gen2': 'opentrons_96_tiprack_20ul',
              'p300_multi_gen2': 'opentrons_96_tiprack_300ul',
              'p300_single_gen2': 'opentrons_96_tiprack_300ul',
              'p1000_single_gen2': 'opentrons_96_tiprack_1000ul'
              }

    tips = [ctx.load_labware(
     tipmap.get(pip), str(slot)) for slot in [11]]

    pipette = ctx.load_instrument(
        pip, pip_side, tip_racks=tips)

    # heater shaker module in slot 1, selected plate
    hs_mod = ctx.load_module('heaterShakerModuleV1', '1')

    hs_plate = hs_mod.load_labware(
     labware_hs, 'Heater Shaker Plate')

    # open and then close the latch
    hs_mod.open_labware_latch()
    ctx.comment(" latch status {}".format(hs_mod.labware_latch_status))
    hs_mod.close_labware_latch()
    ctx.comment(" latch status {}".format(hs_mod.labware_latch_status))

    # set target temperature and proceed without waiting
    hs_mod.set_target_temperature(celsius=hs_temp)
    ctx.comment(
     "Heater Shaker current temperature {}".format(hs_mod.current_temperature))

    # selected source labware
    source = ctx.load_labware(
     labware_source, '3', 'source')

    # selected dest labware
    dest = ctx.load_labware(
     labware_dest, '6', 'destination')

    def select_wells(selectedlabware, n, mode=pip.split('_')[1]):
        """
        Return list of wells in every nth column.

        always in row A unless mode is 'single'
        if mode is 'single', listed wells span range of rows
        """
        num_cols = len(selectedlabware.columns())
        num_rows = len(selectedlabware.columns()[0])

        # avoid labware with fewer than 8 rows with multi
        if num_rows < 8 and pip.split('_')[1] != 'single':
            # unless it is a reservoir
            if selectedlabware.wells()[0].width is not None:
                if selectedlabware.wells()[0].width < 70:
                    raise Exception(
                        '''Labware {} incompatible with
                        {}-channel pipette.'''.format(
                            selectedlabware, pip.split('_')[1]))
            else:
                raise Exception(
                        '''Labware {} incompatible with
                        {}-channel pipette.'''.format(
                            selectedlabware, pip.split('_')[1]))

        # always row A unless mode is single
        index_list = num_cols*[*range(num_rows)
                               ] if mode == 'single' else num_cols*[0]

        # every nth column
        return [column[index] for column, index in zip(
                selectedlabware.columns()[:num_cols:n],
                index_list[:num_cols:n])]

    source_wells = select_wells(source, len(source.columns()), mode='standard')

    hs_wells = select_wells(hs_plate, every_nth_col)

    # use only 1st dest column when it is a reservoir
    if dest.wells()[0].width is not None:
        if dest.wells()[0].width >= 70:
            dn = len(dest.columns())
    else:
        dn = 1

    d = len(hs_wells)*select_wells(dest, dn)
    dest_wells = d[:len(hs_wells)]

    for selection, name in zip(
     [source_wells, hs_wells, dest_wells],
     ['source', 'heater shaker', 'destination']):
        ctx.comment("Selected {0} wells {1}".format(name, selection))

    # transfer from source to heater shaker
    ctx.comment(
     "Heater Shaker current temperature {}".format(hs_mod.current_temperature))

    pipette.transfer(tfer_vol, source_wells, hs_wells, touch_tip=True)

    # shaking steps
    ctx.comment(
     "Heater Shaker current temperature {}".format(hs_mod.current_temperature))

    # wait for previously set temperature
    hs_mod.wait_for_temperature()

    ctx.comment(
     "Heater Shaker current temperature {}".format(hs_mod.current_temperature))

    # start shaking
    ctx.comment(" current speed {} ".format(hs_mod.current_speed))
    hs_mod.set_and_wait_for_shake_speed(rpm=hs_rpm)
    ctx.delay(seconds=1)
    ctx.comment(" current speed {} ".format(hs_mod.current_speed))

    # get shaking start time
    start = time.time()

    # demo pipetting steps (NOT targeting the heater shaker) during shaking
    pipette.pick_up_tip()
    pipette.mix(10, 10, dest_wells[0])
    pipette.drop_tip()

    # wait until the shake time has elapsed
    if not ctx.is_simulating():
        while time.time() - start < time_shake*60:
            continue

    # stop shaking
    hs_mod.deactivate_shaker()
    ctx.comment(" current speed {} ".format(hs_mod.current_speed))

    # transfer from heater shaker to destination
    pipette.transfer(0.8*tfer_vol, hs_wells, dest_wells, touch_tip=True)

    # deactivate heater, open latch
    hs_mod.deactivate_heater()
    hs_mod.open_labware_latch()
    ctx.comment(" latch status {}".format(hs_mod.labware_latch_status))

    ctx.comment(
     '''Process Complete.''')

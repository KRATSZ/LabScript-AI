metadata = {
    'protocolName': 'Custom Distribute Liquids Function',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    # Load Labware
    plate1 = ctx.load_labware('corning_6_wellplate_16.8ml_flat', 1, 'Plate 1')
    plate2 = ctx.load_labware('corning_24_wellplate_3.4ml_flat', 2, 'Plate 2')
    trash_plate = ctx.load_labware('agilent_1_reservoir_290ml', 3,
                                   'Trash Plate')
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', 4)
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Custom Distribute Function
    def distribute_custom(pipette, vol, source, dest, overage,
                          blowout, air_gap):

        use_vol = pipette.max_volume - overage
        num_distribute = use_vol // vol
        num_distribute = (use_vol - air_gap * num_distribute) // vol

        def well_lists(wells, n):

            for i in range(0, len(wells), n):
                yield wells[i:i + n]

        asp_vols = []

        def calc_vol(wells, vol):

            for wells in dest_wells:
                aspirate_vol = vol*len(wells) + overage
                asp_vols.append(aspirate_vol)

        dest_wells = list(well_lists(dest, num_distribute))
        calc_vol(dest_wells, vol)

        pipette.pick_up_tip()
        for wells, asp_vol in zip(dest_wells, asp_vols):
            pipette.aspirate(asp_vol, source)
            ctx.comment("Air Gap")
            pipette.move_to(source.top())
            pipette.aspirate(air_gap)

            for well in wells:
                pipette.dispense(vol+air_gap, well)
                ctx.comment("Air Gap")
                pipette.move_to(well.top())
                pipette.aspirate(air_gap)
            ctx.comment(f"Blowout at {blowout}")
            pipette.dispense(pipette.max_volume, blowout)
        pipette.drop_tip()

    distribute_custom(p300, 50, plate1['A1'], plate2.rows_by_name()['A'], 30,
                      trash_plate['A1'], 10)

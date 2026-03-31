from opentrons.types import Point

metadata = {
    'protocolName': 'Liquid Deposition on Custom Surface',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    volume, loc_csv, p20_type, p20_mount = get_values(  # noqa: F821
        'volume', 'loc_csv', 'p20_type', 'p20_mount')

    res = ctx.load_labware('usascientific_96_wellplate_2.4ml_deep', '10')
    tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '11')]
    plate = ctx.load_labware('custom_1_other_20ul', '1')
    if p20_type == 'p20_multi_gen2':
        sources = res.rows()[0][:2]
    else:
        sources = res.columns()[0]

    p20 = ctx.load_instrument(p20_type, p20_mount, tip_racks=tiprack20)
    # match mount to axis
    axis_map = {
        'right': 'A',
        'left': 'Z'
    }

    # parse .csv
    offsets = [
        [float(val) for val in line.split(',')]
        for line in loc_csv.splitlines()[1:]]

    # grid creation methods
    x_spaces = [0, 9, 13.5, 22.5]
    y_spaces = [0, -9, -18, -27]
    ref_a1 = plate.wells()[0].top().move(Point(x=0, y=0))

    def create_col(ref):
        col = [ref.move(Point(y=y_space)) for y_space in y_spaces]
        return col

    def create_grid(x_grid, y_grid):
        grid = []
        for x_start, y_start in zip([0, -4.5], [0, -4.5]):
            for x_space in x_spaces:
                ref = ref_a1.move(Point(x=x_grid+x_space+x_start,
                                        y=y_grid+y_start))
                grid.append(create_col(ref))
        return grid

    # initialize and create grids
    grids = [create_grid(0, 0)]
    for offset in offsets:
        x, y = offset
        grid = create_grid(x, y)
        grids.append(grid)

    # setup destinations depending on pipette type
    if p20_type == 'p20_multi_gen2':
        for grid in grids:
            dests = [col[0] for col in grid]
            p20.pick_up_tip()
            for i, d in enumerate(dests):
                # if i % 4 == 0:
                source = sources[i//4]
                # change tips after first 4 solutions
                if i == 4:
                    p20.move_to(tiprack20[0].wells()[-1].top().move(
                                Point(y=-20, z=30)))
                    p20.drop_tip()
                    p20.pick_up_tip()
                # shift to tips 5-8 if accessing second set of columns
                dest = d.move(Point(y=(i//4)*36))
                p20.aspirate(volume, source)
                p20.move_to(dest.move(Point(z=10)))
                ctx.max_speeds[axis_map[p20_mount]] = 10
                p20.move_to(dest)
                p20.dispense(volume, dest)
                del ctx.max_speeds[axis_map[p20_mount]]
                # if (i+1) % 4 == 0:
            p20.move_to(tiprack20[0].wells()[-1].top().move(
                        Point(y=-20, z=30)))
            p20.drop_tip()

    else:
        for grid in grids:
            dest_sets = [
                [col[well] for col in grid[set*4:(set+1)*4]]
                for set in range(2)
                for well in range(4)]
            for source, dest_set in zip(sources, dest_sets):
                p20.pick_up_tip()
                for dest in dest_set:
                    p20.aspirate(volume, source)
                    p20.move_to(dest.move(Point(z=10)))
                    ctx.max_speeds[axis_map[p20_mount]] = 10
                    p20.move_to(dest)
                    p20.dispense(volume, dest)
                    del ctx.max_speeds[axis_map[p20_mount]]
                p20.move_to(tiprack20[0].wells()[-1].top().move(
                            Point(y=-20, z=30)))
                p20.drop_tip()

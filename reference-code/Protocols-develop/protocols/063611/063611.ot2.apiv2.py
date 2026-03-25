import os
import csv
import math

metadata = {
    'title': 'Cap Filling',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [fill_volume, cap_count, rack_count, remove_empty_racks, arrange_tips,
     track_tips, change_tips, clearance_reservoir, tracking_reset,
     labware_rack] = get_values(  # noqa: F821
        "fill_volume", "cap_count", "rack_count", "remove_empty_racks",
        "arrange_tips", "track_tips", "change_tips", "clearance_reservoir",
        "tracking_reset", "labware_rack")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    """
    keep parameter value selections within acceptable range
    """

    if fill_volume < 215 or fill_volume > 250:
        raise Exception('Fill volume must be in range 215-250.')

    if cap_count < 1 or cap_count > 96:
        raise Exception('Cap count must be in range 1-96.')

    if rack_count < 1 or rack_count > 4:
        raise Exception('Rack count must be in range 1-4.')

    if rack_count < math.ceil(cap_count / 24):
        raise Exception('Rack count must be at least {}'.format(
         str(math.ceil(cap_count / 24))))

    if clearance_reservoir < 1:
        raise Exception('Reservoir bottom clearance must be at least 1 mm.')

    if remove_empty_racks:
        rack_count = math.ceil(cap_count / 24)

    # p300 multi, tips
    tip_slots = [10, 11]
    tips300 = [ctx.load_labware(
     'opentrons_96_tiprack_300ul', str(slot)) for slot in tip_slots]
    p300m = ctx.load_instrument("p300_multi_gen2", 'right', tip_racks=tips300)

    """
    prepare custom tip arrangement
    """

    if arrange_tips:
        ctx.pause("""Important. Please make sure the tip box in slot 10 is
        completely full and the tip box in slot 11 is completely empty before
        clicking resume.""")

        empty300 = tips300.pop(1)

        for full, empty in zip(tips300, [empty300]):
            for index, column in enumerate(full.columns()):
                p300m.pick_up_tip(column[4])
                p300m.drop_tip(empty.columns()[index][0])

        for box in tips300+[empty300]:
            for column in box.columns():
                for s in range(1, 6, 2):
                    p300m.pick_up_tip(column[s])
                    p300m.drop_tip(column[s+1])

        p300m.reset_tipracks()

        tips300.append(empty300)

    """
    get starting tip based on previous run
    """
    if track_tips:
        # if ctx.is_simulating():  # reversed logic for simulation
        if not ctx.is_simulating():
            file_path = '/data/temporary/tiptracking.csv'
            file_dir = os.path.dirname(file_path)
            # check for file directory
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            # check for file; if not there, create initial csv
            if (not os.path.isfile(file_path) or tracking_reset):
                with open(file_path, 'w') as outfile:
                    outfile.write(",".join([
                     "0", "\n"]))

        current_data = []
        # if not ctx.is_simulating():  # reversed logic for simulation
        if ctx.is_simulating():
            current_data = ["0"]
        else:
            with open(file_path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                current_data = next(csv_reader)

        current_starting_tip = current_data[0]

    else:
        current_starting_tip = 0

    # yield currently available tips
    tip_list = tips300[0].rows()[0]+tips300[1].rows()[0]

    def tip_loc():
        unused_list = tip_list[int(current_starting_tip):]
        yield from unused_list

    use_tip = tip_loc()

    # custom racks
    rack_slots = [4, 1, 5, 2]
    [*racks] = [ctx.load_labware(
     labware_rack, str(
      slot), 'Rack') for slot in rack_slots[:rack_count]]

    # reservoir
    reservoir = ctx.load_labware('nest_1_reservoir_195ml', '3', 'Reservoir')

    def pick_up():
        if track_tips:
            try:
                nonlocal use_tip
                p300m.pick_up_tip(next(use_tip))
            except StopIteration:
                ctx.pause("Please add full tipracks to slots 10 and 11")
                current_starting_tip = 0
                # to satisfy the linter
                ctx.comment("current starting tip reset to {}".format(
                 current_starting_tip))
                use_tip = tip_loc()
                p300m.pick_up_tip(next(use_tip))
        else:
            p300m.pick_up_tip()

    """
    process steps to fill caps
    """
    for index, rack in enumerate(racks[:math.ceil(cap_count / 24)]):
        remaining = cap_count - (index*24)
        num_cols = math.ceil(remaining / 4) if (index == (len(racks[
         :math.ceil(cap_count / 24)])-1)) else 6
        for column in rack.columns()[:num_cols]:
            if not p300m.has_tip:
                pick_up()
            p300m.aspirate(
             fill_volume, reservoir['A1'].bottom(clearance_reservoir))
            p300m.air_gap(25)
            p300m.dispense(fill_volume+25, column[0].top(-2))
            p300m.blow_out()
            p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
            if change_tips:
                p300m.drop_tip()
        if p300m.has_tip:
            p300m.drop_tip()

    """
    keep track of starting tip for the next run
    """
    if track_tips:
        try:
            future_tip = tip_list.index(next(use_tip))
        except StopIteration:
            ctx.pause("Please add full tipracks to slots 10 and 11")
            current_starting_tip = 0
            use_tip = tip_loc()
            future_tip = tip_list.index(next(use_tip))

        # write future starting tip to csv
        new_data = ",".join([str(future_tip), '\n'])
        # if ctx.is_simulating():  # reversed logic for simulation
        if not ctx.is_simulating():
            with open(file_path, 'w') as outfile:
                outfile.write(new_data)
                ctx.comment(" new_data {}".format(new_data))

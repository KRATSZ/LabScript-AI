metadata = {
    'protocolName': 'Cherrypicking',
    'author': 'Nick <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


def run(ctx):

    p50_mount, input_csv, air_gap = get_values(  # noqa: F821
        'p50_mount', 'input_csv', 'air_gap')

    # parse csv
    data = [
        [val.strip() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]]
    occupied_slots = [int(line[ind]) for line in data for ind in [0, 2]]
    for slot in occupied_slots:
        if slot not in ctx.loaded_labwares:
            ctx.load_labware('biorad_96_wellplate_200ul_pcr', str(slot))

    tipracks = []
    for slot in range(1, 12):
        if slot not in ctx.loaded_labwares:
            tipracks.append(
                ctx.load_labware('opentrons_96_tiprack_300ul', str(slot),
                                 '300ul tiprack'))

    p50 = ctx.load_instrument('p50_single', p50_mount, tip_racks=tipracks)

    tip_max = len(tipracks)*96
    tip_count = 0

    def pick_up():
        nonlocal tip_count
        if tip_count == tip_max:
            ctx.pause('Refill tipracks before resuming.')
            p50.reset_tipracks()
            tip_count = 0
        tip_count += 1
        p50.pick_up_tip()

    for line in data:
        s_slot, s_well, d_slot, d_well, vol = line[:5]
        source = ctx.loaded_labwares[int(s_slot)].wells_by_name()[s_well]
        dest = ctx.loaded_labwares[int(d_slot)].wells_by_name()[d_well]
        pick_up()
        p50.transfer(float(vol), source, dest, air_gap=air_gap,
                     new_tip='never')
        p50.air_gap(5)
        p50.drop_tip()

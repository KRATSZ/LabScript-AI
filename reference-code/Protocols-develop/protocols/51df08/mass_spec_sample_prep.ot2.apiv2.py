from opentrons.types import Point

metadata = {
    'protocolName': 'Mass Spec Sample Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [process, num_antibodies, num_samples, y_offset, p20_mount,
     p300_mount] = get_values(  # noqa: F821
            'process', 'num_antibodies', 'num_samples', 'y_offset',
            'p20_mount', 'p300_mount')

    # load labware
    reagent_rack = ctx.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '1',
        '50ml reagent tuberack')
    num_slides = 2 if num_antibodies > 3 else 1
    slide_mounts = [ctx.load_labware(
        'custom_72_other_24x330ul_24x330ul_24x330ul', slot, 'slides ' + inds)
        for slot, inds in zip(['5', '2'], ['1-3', '4-5'])][:num_slides]
    # slide_mounts = [ctx.load_labware(
    #     'biorad_96_wellplate_200ul_pcr', slot, 'slides ' + inds)
    #     for slot, inds in zip(['5', '2'], ['1-3', '4-5'])][:num_slides]
    sample_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '3',
        '1.5ml Eppendorf tuberacks for samples')
    waste = ctx.load_labware(
        'nest_1_reservoir_195ml', '4',
        'waste reservoir (calibrate to top center)').wells()[0].top()
    ab_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '6',
        '1.5ml Eppendorf tuberacks for antibodies')
    tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '7')]
    tiprack300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['8', '9', '10', '11']]

    # load pipettes
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_mount, tip_racks=tiprack20)
    p300 = ctx.load_instrument(
        'p300_single_gen2', p300_mount, tip_racks=tiprack300)

    # define wells
    if num_antibodies > 3:
        slide_inds = [3, num_antibodies % 3]
    else:
        slide_inds = [num_antibodies]
    slides_split = [[slide_mount.columns()[i*3:i*3+3] for i in range(ind)]
                    for slide_mount, ind in zip(slide_mounts, slide_inds)]
    slides = [slide for slide_split in slides_split for slide in slide_split]
    slides_cols_reordered = [[col[1:] if i % 2 == 0 else col[:0:-1]
                             for i, col in enumerate(slide)]
                             for slide in slides]
    slides_wells_reordered = [[well for col in slide for well in col]
                              for slide in slides_cols_reordered]
    detergent_wash_buffer = reagent_rack.wells()[0].bottom(5)
    bsa_blocking_buffer = reagent_rack.wells()[1].bottom(5)
    pbs = [tube.bottom(2) for tube in reagent_rack.wells()[2:4]]
    water = [tube.bottom(2) for tube in reagent_rack.wells()[4:6]]

    samples = sample_rack.wells()[:num_samples]
    antibodies = ab_rack.wells()[:num_antibodies]

    # calculate offset for spots
    # y_offset = slide_mounts[0].wells()[0].width/3/2
    ab_spot_sets = [
        [[well.bottom().move(Point(y=side*y_offset/2)) for side in [1, -1]]
         for well in slide]
        for slide in slides_wells_reordered]

    tip_track = {
        p300: {
            'max': len(tiprack300)*96,
            'count': 0
        },
        p20: {
            'max': len(tiprack20)*96,
            'count': 0
        }
    }

    def pick_up(pip):
        nonlocal tip_track
        if tip_track[pip]['count'] == tip_track[pip]['max']:
            ctx.pause('Replace ' + str(pip.max_volume) + 'ul tipracks before \
resuming.')
            tip_track[pip]['count'] = 0
            pip.reset_tipracks()
        tip_track[pip]['count'] += 1
        pip.pick_up_tip()

    def add_reagent(vol, source, drop=True):
        pick_up(p300)
        for slide_wells in slides_wells_reordered:
            for well in slide_wells:
                p300.transfer(vol, source, well.top(), air_gap=20,
                              new_tip='never')
        if drop:
            p300.drop_tip()

    def discard_liquid(vol, new_tip=False):
        if not p300.hw_pipette['has_tip']:
            pick_up(p300)
        for slide_wells in slides_wells_reordered:
            for well in slide_wells:
                if not p300.hw_pipette['has_tip']:
                    pick_up(p300)
                p300.transfer(
                    vol, well.bottom(0.2), waste, air_gap=20, new_tip='never')
                p300.drop_tip()
            if p300.hw_pipette['has_tip']:
                p300.drop_tip()

    def wash(vol, source):
        add_reagent(vol, source)
        discard_liquid(vol)

    if 'antibody' in process:
        # transfer antibodies to slide wells 2x
        for ab, slide in zip(antibodies, ab_spot_sets):
            pick_up(p20)
            for set in slide:
                for well in set:
                    p20.transfer(1.5, ab, well, new_tip='never')
            p20.drop_tip()

        ctx.home()
        ctx.pause('Remove well module from OT-2 and incubate in humidity \
chamber overnight at 4C to allow antibodies to adhere to slides. After \
overnight incubation, remove the slides from the humidity chamber and place \
in desiccator to dry. Once dry, place slides with attached well module back \
into OT-2')

        wash(250, detergent_wash_buffer)

        add_reagent(250, bsa_blocking_buffer)

        ctx.home()
        ctx.pause('Remove slide from OT-2 and place on benchtop shaker to \
    incubate in humidity chamber for 1 hour at room temperature')

        for _ in range(2):
            wash(250, pbs[0])

        wash(250, water[0])

    ctx.home()
    ctx.pause('Remove slide from OT-2 and desiccate dry. Prepare serum \
samples in Eppendorf tubes')

    if 'sample' in process:
        # add samples
        sample_duplicates = [[slide[i*2+1:i*2+3] for i in range(num_samples)]
                             for slide in slides_wells_reordered]
        for slide in sample_duplicates:
            for sample, set in zip(samples, slide):
                pick_up(p300)
                p300.distribute(100, sample, [d.top(-1) for d in set],
                                air_gap=20, new_tip='never')
                p300.air_gap(20)
                p300.drop_tip()

        ctx.home()
        ctx.pause('Remove slide from OT-2 and incubate on benchtop shaker in \
    humidity box for 2 hours at room temperature')

        discard_liquid(100, new_tip=True)

        for _ in range(2):
            wash(250, pbs[1])

        for _ in range(2):
            wash(250, water[1])

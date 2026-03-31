import math

metadata = {
    'protocolName': 'KingFisher Flex Plate Set Up',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json
    [num_cols, labware_processing_plate, labware_reservoir_12well,
     labware_reservoir_1well,
        m300_mount, m20_mount] = get_values(  # noqa: F821
      "num_cols", "labware_processing_plate", "labware_reservoir_12well",
      "labware_reservoir_1well", "m300_mount", "m20_mount")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=5)
    if not 1 <= num_cols <= 12:
        raise Exception('Invalid number of columns (must be 1-12).')

    # tips, p300 and p20 multi
    tips300 = [ctx.load_labware(
     "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [11]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", m300_mount, tip_racks=tips300)

    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [10]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", m20_mount, tip_racks=tips20)

    # yield list chunks of size n
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    # return liquid height in a well
    def liq_height(well, effective_diameter=None):
        if well.diameter:
            if effective_diameter:
                radius = effective_diameter / 2
            else:
                radius = well.diameter / 2
            csa = math.pi*(radius**2)
        else:
            csa = well.length*well.width
        return well.liq_vol / csa

    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'

        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # to extend aspirate
    def extended1(func):
        """
        Extend aspirate method.

        For viscous liquids.
        Half default flow rate.
        Delay after aspiration.
        Slow departure of tip.
        """
        def wrapper(*args, **kwargs):
            func(*args, **kwargs, rate=0.5)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(func.__self__, [*args][1].labware.object)
        return wrapper

    # to extend aspirate
    def extended2(func):
        """
        Extend aspirate method.

        For volatile liquids.
        Post-aspirate air gap.
        """
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            func.__self__.air_gap(20)
        return wrapper

    # to extend dispense
    def extended3(func):
        """
        Extend dispense method.

        For viscous liquids.
        Half default flow rate.
        Delay after dispense.
        Blow out at top of well.
        Touch tip.
        """
        def wrapper(*args, **kwargs):
            func(*args, **kwargs, rate=0.5)
            ctx.delay(seconds=1)
            # func.__self__.blow_out([*args][1].labware.object.top())
            func.__self__.touch_tip()
        return wrapper

    # to extend dispense
    def extended4(func):
        """
        Extend dispense method.

        For volatile liquids.
        Delayed blow out at top of well.
        Touch tip.
        """
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            func.__self__.move_to([*args][1].labware.object.top())
            ctx.delay(seconds=0.5)
            # func.__self__.blow_out([*args][1].labware.object.top())
            func.__self__.touch_tip()
        return wrapper

    # to extend dispense
    def extended5(func):
        """
        Extend dispense method.

        For aqueous liquids.
        Blow out at top of well.
        Touch tip.
        """
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            func.__self__.blow_out([*args][1].labware.object.top())
            func.__self__.touch_tip()
        return wrapper

    washreservoir = ctx.load_labware(
     labware_reservoir_1well, '8', 'Wash Buffer')

    etohreservoir = ctx.load_labware(
     labware_reservoir_1well, '9', '80 Percent EtOH')

    twelvewellreservoir = ctx.load_labware(
        labware_reservoir_12well, '7', '12-Well Reservoir')

    source_dict = {
     'Proteinase K Solution': twelvewellreservoir.wells_by_name()['A1'],
     'Wash Buffer': washreservoir.wells()[0],
     '80 Percent EtOH': etohreservoir.wells()[0],
     'Elution Solution': twelvewellreservoir.wells_by_name()['A12']}

    processingplates = [
     ctx.load_labware(
      labware_processing_plate, str(slot+1), name) for name, slot in zip(
      ['Sample Plate',
       'Wash Plate 1',
       'Wash Plate 2',
       'Wash Plate 3',
       'Elution Plate 4'],
      [*range(5)])]

    for source, lc, tfervol in zip(
     [value for value in source_dict.values()],
     ['aqueous', 'viscous', 'volatile', 'aqueous'],
     [10, 1000, 1500, 100]):

        source.liq_class = lc
        source.liq_vol = 1.1*(tfervol*8*num_cols)

    for source, transfervolume, plate in zip(
        [source_dict[reagent] for reagent in [
         'Proteinase K Solution',
         'Wash Buffer',
         '80 Percent EtOH',
         '80 Percent EtOH',
         'Elution Solution']],
        [10, 1000, 1000, 500, 100],
            processingplates):

        pip = p20m if transfervolume <= 20 else p300m

        # python dict to store and dispatch extended aspirate
        pip_aspirate = {'viscous': extended1(pip.aspirate),
                        'volatile': extended2(pip.aspirate),
                        'aqueous': pip.aspirate}

        # python dict to store and dispatch extended dispense
        pip_dispense = {'viscous': extended3(pip.dispense),
                        'volatile': extended4(pip.dispense),
                        'aqueous': extended5(pip.dispense)}

        vol_airgap = 20 if source.liq_class == 'volatile' else 0

        reps = math.ceil(
         transfervolume / (
          pip.tip_racks[0].wells()[0].max_volume - vol_airgap))

        v = transfervolume / reps

        pip.pick_up_tip()

        for column in plate.columns()[:num_cols]:

            dest = column[0].top(
            ) if v > 50 else column[0].bottom(1)

            for rep in range(reps):

                source.liq_vol -= v*pip.channels

                tipheight = liq_height(
                 source) - 3 if liq_height(source) - 3 > 1 else 1

                pip_aspirate[source.liq_class](v, source.bottom(tipheight))

                pip_dispense[source.liq_class](v+vol_airgap, dest)

        pip.drop_tip()

    ctx.comment("Finished set up of five processing plates")

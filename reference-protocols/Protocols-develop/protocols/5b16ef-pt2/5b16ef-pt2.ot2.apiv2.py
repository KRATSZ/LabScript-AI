from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': '',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_col, csv, index_start_col,
        m20_mount, m300_mount] = get_values(  # noqa: F821
        "num_col", "csv", "index_start_col",
            "m20_mount", "m300_mount")

    if not 1 <= num_col <= 6:
        raise Exception("Enter a column number between 1-6")

    index_start_col = int(index_start_col)
    num_index_start_cols_left = 12 - index_start_col

    if not num_index_start_cols_left >= num_col:
        raise Exception(f"Not enough index columns to process {num_col} sample columns")  # noqa: E501
    index_start_col -= 1

    # load module
    mag_mod = ctx.load_module('magnetic module gen2', 10)
    mag_plate = mag_mod.load_labware('biorad_96_wellplate_200ul_pcr')

    # load labware
    sample_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 5)
    mmx_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 2)
    final_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 4)
    index_plate = ctx.load_labware('indexplate_96_wellplate_200ul', 1)
    reagent_res = ctx.load_labware('nest_12_reservoir_15ml', 3)
    reagent_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', 8)
    waste_res = ctx.load_labware('nest_12_reservoir_15ml', 11)

    # load tipracks
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [9]]

    tipracks300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                   for slot in [6, 7]]

    # load pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)
    m300 = ctx.load_instrument('p300_multi_gen2',
                               m300_mount, tip_racks=tipracks300)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tipracks")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # mapping
    water = reagent_res.wells()[0]
    twb = reagent_res.wells()[1]
    ethanol = reagent_res.wells()[10:12 if num_col > 4 else 11]

    pcr_mmx = reagent_plate.rows()[0][0]
    spb = reagent_plate.rows()[0][1]
    rsb = reagent_plate.rows()[0][2]

    tagment_mmx = mmx_plate.rows()[0][0]
    tsb = mmx_plate.rows()[0][11]

    samples = final_plate.rows()[0][:num_col*2:2]
    waste = waste_res.wells()[0]

    # csv --> nested list
    list_of_rows = [[val.strip() for val in line.split(',')]
                    for line in csv.splitlines()
                    if line.split(',')[0].strip()][1:]

    num_channels_per_pickup = 1
    tips_ordered = [
        tip
        for row in tipracks[0].rows()[
         len(tipracks[0].rows())-num_channels_per_pickup::-1*num_channels_per_pickup]  # noqa: E501
        for tip in row]

    tip_count = 0

    def pick_up_less_channels():
        nonlocal tip_count
        m20.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    ctx.comment('\n\nMOVING WATER TO PLATE VIA CSV\n')
    pick_up_less_channels()
    for row in list_of_rows:
        dna_vol = int(row[1])
        water_vol = 30 - dna_vol
        well = final_plate.wells_by_name()[row[0]]
        if water_vol > m20.max_volume:
            water_vol /= 2
            for _ in range(2):
                m20.aspirate(water_vol, water)
                m20.dispense(water_vol, well.top())
        else:
            m20.aspirate(water_vol, water)
            m20.dispense(water_vol, well.top())
            m20.blow_out()
    m20.drop_tip()

    ctx.comment('\n\nMOVING DNA TO PLATE\n')

    for row in list_of_rows:

        dna_vol = int(row[1])
        source = sample_plate.wells_by_name()[row[0]]
        dest = final_plate.wells_by_name()[row[0]]

        pick_up_less_channels()
        if dna_vol > m20.max_volume:
            dna_vol /= 2
            for _ in range(2):
                m20.aspirate(dna_vol, source)
                m20.dispense(dna_vol, dest)
                m20.blow_out()
        else:
            m20.aspirate(dna_vol, source)
            m20.dispense(dna_vol, dest)
            m20.blow_out()
        m20.drop_tip()

    ctx.comment('\n\nMOVING TAGMENT MMX TO SAMPLES\n')
    for col in samples:
        pick_up(m20)
        m20.mix(3, 20, tagment_mmx)
        m20.aspirate(20, tagment_mmx)
        m20.dispense(20, col)
        m20.mix(3, 20, col)
        m20.blow_out()
        m20.touch_tip()
        m20.drop_tip()

    ctx.pause("""
    Seal plate with Microseal B.
    Using a thermal cycler with lid heated to 100C, incubate plate at 55C
    for 15 minutes, followed by 10C hold (step 11 of section 8.4.2 of protocol)
    Program "Flex Tag" on the thermal cycler. Afterwards, place plate back on
    slot 4 of the deck and select "Resume" on the Opentrons app for
    Post Tagmentation Cleanup. Empty trash if needed.
    """)

    ctx.comment('\n\nMOVING TSB TO SAMPLES\n')
    for col in samples:
        pick_up(m20)
        m20.mix(3, 10, tsb)
        m20.aspirate(10, tsb)
        m20.dispense(10, col)
        m20.mix(3, 10, col)
        m20.blow_out()
        m20.touch_tip()
        m20.drop_tip()

    ctx.pause("""
    Seal plate with Microseal A.
    Using a thermal cycler with lid heated to 100C, incubate plate at 37C
    for 15 minutes, followed by 10C hold (step 5 of section 8.4.3 of protocol)
    Program "Flex Post" on the thermal cycler. Afterwards, spin the plate,
    and place plate back on MAGNETIC MODULE and select "Resume" on the
    Opentrons app for washing. Empty trash if needed.
    """)

    samples = mag_plate.rows()[0][:num_col*2:2]
    mag_mod.engage()
    ctx.delay(minutes=3)

    ctx.comment('\n\nREMOVING 60ul SUPERNATANT\n')
    for col in samples:
        aspirate_loc = col.bottom(z=1.5).move(
                Point(x=(col.diameter/2-2)*-1))
        pick_up(m300)
        m300.aspirate(60, aspirate_loc, rate=0.5)
        m300.dispense(60, waste)
        m300.blow_out()
        m300.drop_tip()

    mag_mod.disengage()
    ctx.comment('\n\n3 WASHES\n')
    for i in range(3):
        ctx.comment('\n\nADDING TWB\n')
        for col in samples:
            pick_up(m300)
            m300.aspirate(100, twb)
            m300.dispense(100, col)
            m300.mix(3, 100, col)
            m300.blow_out()
            m300.touch_tip()
            m300.drop_tip()

        mag_mod.engage()
        ctx.delay(minutes=3)

        if i < 2:

            ctx.comment('\n\nREMOVING 100ul SUPERNATANT\n')
            for col in samples:
                aspirate_loc = col.bottom(z=1.5).move(
                        Point(x=(col.diameter/2-2)*-1))
                pick_up(m300)
                m300.aspirate(100, aspirate_loc, rate=0.5)
                m300.dispense(100, waste)
                m300.blow_out()
                m300.touch_tip()
                m300.drop_tip()
            mag_mod.disengage()

    ctx.pause("""
    Ensure PCR mastermix is loaded onto the deck.
    Select "Resume" on the Opentron App.
    Empty trash if needed.
    """)

    ctx.comment('\n\nREMOVING 100ul SUPERNATANT\n')
    for col in samples:
        aspirate_loc = col.bottom(z=1.5).move(
                Point(x=(col.diameter/2-2)*-1))
        pick_up(m300)
        m300.aspirate(100, aspirate_loc, rate=0.5)
        m300.dispense(100, waste)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip()
    mag_mod.disengage()

    ctx.comment('\n\nADDING PCR MASTERMIX\n')
    for col in samples:
        pick_up(m300)
        m300.aspirate(40, pcr_mmx)
        m300.dispense(40, col)
        m300.mix(3, 30, col, rate=0.5)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip()

    ctx.comment('\n\nADDING INDEX MASTERMIX\n')
    for index_col, col in zip(index_plate.rows()[0][index_start_col:],
                              samples):
        pick_up(m300)
        m300.move_to(index_col.top(z=-3))
        m300.drop_tip()
        pick_up(m300)
        m300.aspirate(10, index_col)
        m300.dispense(10, col)
        m300.mix(10, 40, col)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip()

    ctx.pause("""
    Seal the plate with Microseal A.
    Run the following preprogrammed settings on the thermal cycler
    with a headed lid (100C). Program "Flex Amp" on the thermal cycler.
    Ensure a fresh 96 well bio-rad plate is in slot 4 of the deck.
    Select "Resume" on the Opentron App.
    Empty trash if needed.
    """)

    mag_mod.engage()
    ctx.delay(minutes=5)

    ctx.comment('\n\nREMOVING SUPERNATANT TO FINAL PLATE ON 4\n')
    for source, dest in zip(samples, final_plate.rows()[0][:num_col*2:2]):
        aspirate_loc = source.bottom(z=1.5).move(
                Point(x=(source.diameter/2-2)*-1))
        pick_up(m300)
        m300.aspirate(45, aspirate_loc, rate=0.5)
        m300.dispense(45, dest)
        m300.blow_out()
        m300.drop_tip()
    mag_mod.disengage()

    ctx.pause("""
    Discard plate on magnetic module, and move plate from slot 4 to the
    magnetic module.
    Select "Resume" on the Opentron App.
    Empty trash if needed.
    """)

    for col in samples:
        pick_up(m300)
        m300.aspirate(81, spb, rate=0.5)
        ctx.delay(seconds=3)
        m300.dispense(81, col)
        m300.mix(10, 100, col)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip()

    ctx.delay(minutes=5, msg="Incubating at room temperature for 5 minutes")

    ctx.comment('\n\n2 ETHANOL WASHES\n')
    mag_mod.engage()
    for i in range(2):
        ctx.comment('\n\nADDING ETHANOL\n')
        for eth, col in zip(ethanol*num_col*8, samples):
            dispense_loc = col.bottom(z=1.5).move(
                    Point(x=(col.diameter/2-2)*-1))
            pick_up(m300)
            m300.aspirate(200, eth)
            m300.dispense(200, dispense_loc, rate=0.5)
            m300.blow_out()
            m300.touch_tip()
            m300.drop_tip()

        ctx.delay(seconds=30)

        ctx.comment('\n\nREMOVING 200ul SUPERNATANT\n')
        for col in samples:
            aspirate_loc = col.bottom(z=1.5).move(
                    Point(x=(col.diameter/2-2)*-1))
            pick_up(m300)
            m300.aspirate(200, aspirate_loc, rate=0.5)
            m300.dispense(200, waste)
            m300.blow_out()
            m300.touch_tip()
            m300.drop_tip()

    ctx.delay(minutes=5, msg="Letting beads air dry for 3 minutes")

    mag_mod.disengage()
    ctx.comment('\n\nADDING RSB\n')
    pick_up(m300)
    for col in samples:
        m300.aspirate(32, rsb)
        m300.dispense(32, col.top())
        m300.blow_out()
    m300.drop_tip()

    ctx.delay(minutes=3, msg="Incubating with RSB for 2 minutes")
    mag_mod.engage()
    ctx.delay(minutes=3.5)

    ctx.pause("""
    Ensure a fresh 96 well bio-rad plate is in slot 4 of the deck.
    Select "Resume" on the Opentron App.
    Empty trash if needed.
    """)

    ctx.comment('\n\nREMOVING SUPERNATANT TO FINAL PLATE ON 4\n')
    for source, dest in zip(samples, final_plate.rows()[0][:num_col*2:2]):
        aspirate_loc = source.bottom(z=1.5).move(
                Point(x=(source.diameter/2-2)*-1))
        pick_up(m300)
        m300.aspirate(30, aspirate_loc, rate=0.5)
        m300.dispense(30, dest)
        m300.blow_out()
        m300.drop_tip()
    mag_mod.disengage()

    ctx.comment('\n\nPOOLING TO H12 ON REAGENT DEEPWELL PLATE ON 8\n')
    final_wells = [well for col in final_plate.columns()[:num_col*2:2]
                   for well in col]
    pool = reagent_plate.wells()[-1]

    for row, well in zip(list_of_rows, final_wells):
        pick_up_less_channels()
        pool_vol = int(row[2])
        m20.aspirate(pool_vol, well)
        m20.dispense(pool_vol, pool)
        m20.blow_out()
        m20.drop_tip()

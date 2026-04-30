import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Simplified Fe Quantification Assay',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [aliquot_vol, use_single_source,
        num_samp, digestion_temp, digestion_time, sample_vol,
        p20_mount, p300_mount,
        transfer_to_storage, test_mode] = get_values(  # noqa: F821
        "aliquot_vol", "use_single_source", "num_samp",
            "digestion_temp", "digestion_time",
        "sample_vol",
        "p20_mount", "p300_mount",
            "transfer_to_storage", "test_mode")

    if not 1 <= num_samp <= 24:
        raise Exception("Enter a sample number between 1-24")

    # labware
    temp_mod = ctx.load_module('temperature module gen2', 4)
    digestion_plate = temp_mod.load_labware('zinsser_96_wellplate_1898ul')
    analysis_plate = ctx.load_labware('hellma_96_wellplate_300ul', 2)  # noqa: E501
    sample_block = ctx.load_labware('rrlcustom_40_wellplate_1500ul', 3)
    reagent_block = ctx.load_labware('nest_12_reservoir_15ml', 1)
    acid_block = ctx.load_labware('rrl_1_wellplate_180000ul', 5)
    storage_block = ctx.load_labware('corning_96_wellplate_200ul', 6)  # noqa: E501
    tips20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
              for slot in [10, 11]]
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in [7, 8, 9]]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tips300)

    def pick_up():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks.")
            m300.reset_tipracks()
            pick_up()

    # mapping
    samples = [well for row in sample_block.rows()[:3]
               for well in row][:num_samp]
    cal_standards = [well
                     for well in sample_block.rows()[-1]][:7]
    water = reagent_block.wells()[0]
    reag_A = reagent_block.wells()[1]
    reag_B = reagent_block.wells()[2]
    reag_C = reagent_block.wells()[3]
    acid = acid_block.wells()[0]

    # protocol
    ctx.comment('\n-----------ADDING WATER TO DIGESTION PLATE------------\n\n')
    p20.pick_up_tip()
    for well in digestion_plate.wells()[:3]:
        p20.aspirate(aliquot_vol, water)
        p20.dispense(aliquot_vol, well)
        p20.blow_out()
    p20.drop_tip()
    ctx.comment('\n\n\n')

    ctx.comment('\n----ADDING SAMPLE IN TRIPLICATE TO DIGESTION PLATE----\n\n')
    sample_wells = digestion_plate.wells()[3:3+num_samp*3]
    sample_chunks = [sample_wells[i:i+3]
                     for i in range(0, len(sample_wells), 3)]

    well_ctr = 0

    for s_well, chunk in zip(samples, sample_chunks):
        p20.pick_up_tip()
        for d_well in chunk:
            p20.aspirate(aliquot_vol,
                         s_well if not use_single_source else sample_block.wells()[0])  # noqa: E501
            p20.dispense(aliquot_vol, d_well)
            p20.blow_out()
            well_ctr += 1
        p20.drop_tip()
        ctx.comment('\n')

    ctx.comment('\n-----------ADDING ACID AND MIXING------------\n\n')
    well_ctr += 3
    num_col = math.ceil(well_ctr/8)
    pick_up()
    for col in digestion_plate.rows()[0][:num_col]:
        m300.transfer(1200, acid, col.top(),
                      new_tip='never', blow_out=True,
                      blowout_location='destination well')
    m300.drop_tip()

    for col in digestion_plate.rows()[0][:num_col]:
        m300.pick_up_tip()
        m300.mix(15, 200, col.bottom(2))
        m300.drop_tip()
    ctx.comment('\n\n\n')

    if not test_mode:
        ctx.pause('''Cover the digestion plate.
                     Temperature block will go to 95C for 12 hours.''')
        temp_mod.set_temperature(digestion_temp)
        ctx.delay(minutes=digestion_time)
        temp_mod.set_temperature(25)
        ctx.delay(minutes=60)

        ctx.pause('''Remove cover from digestion plate.
                     Place reagent block and analysis plate on deck''')

    ctx.comment('\n----ADDING CALIBRATION STANDARDS IN TRIPLICATE----\n\n')
    dispense_chunks = [analysis_plate.wells()[i:i+3]
                       for i in range(0, len(analysis_plate.wells()), 3)]

    for s, chunk in zip(cal_standards, dispense_chunks):
        p20.pick_up_tip()
        for d in chunk:
            p20.aspirate(10, s)
            p20.dispense(10, d)
            p20.blow_out()
        p20.drop_tip()
        ctx.comment('\n')

    ctx.comment('\n---------MIXING DIGESTION PLATE----------\n\n')

    for col in digestion_plate.rows()[0][:num_col]:

        m300.pick_up_tip()
        m300.mix(15, 200, col.bottom(2))
        m300.drop_tip()

    ctx.comment('\n----TRANSFERRING SAMPLE TO ANALYSIS PLATE----\n\n')

    for s, d in zip(digestion_plate.wells()[:3+3*num_samp],
                    analysis_plate.wells()[21:]):

        p20.pick_up_tip()
        p20.aspirate(sample_vol, s)
        p20.dispense(sample_vol, d)
        p20.blow_out()
        p20.drop_tip()

    if not test_mode:
        ctx.pause('''Move analysis plate on slot 2 to slot 4 temp. module''')
        temp_mod.set_temperature(95)
        ctx.delay(minutes=60)
        temp_mod.set_temperature(25)
        ctx.delay(minutes=60)

        ctx.pause('''Remove analysis plate and move back to slot 2.
                     Put digestion plate back on temp. mod on slot 4.''')

    ctx.comment('\n----TRANSFERRING WATER TO ANALYSIS PLATE----\n\n')
    num_wells = num_samp*3+3+21  # + water wells + cal wells
    num_col = math.ceil(num_wells/8)
    pick_up()
    for col in analysis_plate.rows()[0][:num_col]:
        m300.aspirate(46, water)
        m300.dispense(46, col.top())
        m300.blow_out()
    m300.drop_tip()

    ctx.comment('\n----TRANSFERRING REAG A TO ANALYSIS PLATE----\n\n')

    for col in analysis_plate.rows()[0][:num_col]:
        pick_up()
        m300.aspirate(30, reag_A)
        m300.dispense(30, col)
        m300.mix(10, 45, col.bottom(2))
        m300.blow_out()
        m300.drop_tip()

    if not test_mode:
        ctx.delay(minutes=60)

    ctx.comment('\n----TRANSFERRING REAG B TO ANALYSIS PLATE----\n\n')
    pick_up()
    for col in analysis_plate.rows()[0][:num_col]:
        m300.aspirate(49, reag_B)
        m300.dispense(49, col.top())
        m300.blow_out()
    m300.drop_tip()

    ctx.comment('\n----TRANSFERRING REAG C TO ANALYSIS PLATE----\n\n')

    for col in analysis_plate.rows()[0][:num_col]:
        pick_up()
        m300.aspirate(75, reag_C)
        m300.dispense(75, col)
        m300.mix(10, 150, col.bottom(2))
        m300.blow_out()
        m300.drop_tip()

    if transfer_to_storage:
        ctx.comment('\n----TRANSFERRING TO STORAGE BLOCK----\n\n')

        for s, d in zip(digestion_plate.rows()[0][:num_col],
                        storage_block.rows()[0]):
            pick_up()
            m300.aspirate(200, s)
            m300.dispense(200, d)
            m300.blow_out()
            m300.drop_tip()

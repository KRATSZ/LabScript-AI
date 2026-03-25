metadata = {
    'protocolName': 'nCoV-2019 Lo Cost protocol',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_col, m20_mount, park, m300_mount] = get_values(  # noqa: F821
        "num_col", "m20_mount", "park", "m300_mount")

    num_col = int(num_col)

    # load labware
    temp_mod = ctx.load_module('temperature module gen2', '10')
    temp_plate = temp_mod.load_labware(
                    'opentrons_96_aluminumblock_nest_wellplate_100ul')
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['7', '8']]
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['9', '11']]
    amp_pt1 = ctx.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt', '1')
    amp_pt2 = ctx.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt', '2')
    final_plate = ctx.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt', '3')
    res = ctx.load_labware('nest_12_reservoir_15ml', '6')
    reagent_plate = ctx.load_labware(
                'nest_96_wellplate_100ul_pcr_full_skirt', '4')
    barcode_plate = ctx.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt', '5')

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2',
                               m300_mount, tip_racks=tiprack300)
    tips = [tip_col for rack in tiprack20 for tip_col in rack.rows()[0]]

    tip_counter = 0

    def pick_up():
        nonlocal tip_counter
        if tip_counter == 24:
            ctx.home()
            ctx.pause('Replace all 20ul tip racks')
            m20.reset_tipracks()
            tip_counter = 0
            pick_up()
        else:
            m20.pick_up_tip(tips[tip_counter])
            tip_counter += 1

    def create_chunks(list, n):
        for i in range(0, len(list), n):
            yield list[i:i+n]

    # load reagents
    water = res.wells()[0]
    end_prep_mmx = reagent_plate.rows()[0][0]
    barcode_mmx = reagent_plate.rows()[0][1]
    pool_col = reagent_plate.rows()[0][2]

    # PROTOCOL
    ctx.comment('~~~~~~~~Adding Amp Product from Plate 1 to Plate 2~~~~~~~~~')
    for source, dest in zip(amp_pt1.rows()[0][:num_col], amp_pt2.rows()[0]):
        m300.pick_up_tip()
        m300.aspirate(25, source)
        m300.dispense(25, dest)
        m300.mix(5, 35, dest)
        m300.touch_tip(radius=0.6)
        m300.drop_tip()
    ctx.comment('\n\n\n\n')

    ctx.comment('~~~~~~~~Adding Water to Final Plate~~~~~~~~~')
    m300.pick_up_tip()
    m300.distribute(45,
                    water,
                    [col for col in final_plate.rows()[0][:num_col]],
                    new_tip='never',
                    blow_out=True,
                    blowout_location='source well')
    m300.drop_tip()
    ctx.comment('\n\n\n\n')

    ctx.comment('~~~~~~~~Adding Amp Product from Plate 2 to Water~~~~~~~~~')
    for source, dest in zip(amp_pt2.rows()[0][:num_col],
                            final_plate.rows()[0]):
        pick_up()
        m20.aspirate(5, source)
        m20.dispense(5, dest)

        for _ in range(10):
            m20.aspirate(20, dest)
            m20.dispense(20, dest.top(z=-5))
        m20.touch_tip(radius=0.6)
        if park:
            m20.return_tip()
        else:
            m20.drop_tip()

    ctx.comment('\n\n\n\n')

    ctx.comment('~~~~~~~~Adding Mastermix to Temp Plate~~~~~~~~~')
    pick_up()
    for chunk in create_chunks(final_plate.rows()[0][:num_col], 2):
        m20.aspirate(15, end_prep_mmx)
        for well in chunk:
            m20.dispense(6.7, well)
        m20.dispense(m20.current_volume, end_prep_mmx)
    m20.drop_tip()
    ctx.comment('\n\n\n\n')

    ctx.comment('~~~~~~~~Adding Diluted PCR Product~~~~~~~~~')
    if park:
        tip_counter = 0
    for source, dest in zip(final_plate.rows()[0][:num_col],
                            temp_plate.rows()[0]):
        pick_up()
        m20.aspirate(3.3, source)
        m20.dispense(3.3, dest)
        m20.mix(10, 7.5, dest, rate=0.85)
        m20.blow_out(dest.top())
        m20.touch_tip(radius=0.6)
        m20.drop_tip()
    ctx.comment('\n\n\n\n')

    ctx.delay(minutes=15, msg='INCUBATING AT ROOM TEMPERATURE')
    temp_mod.set_temperature(65)
    ctx.delay(minutes=15, msg='INCUBATING AT 65C')
    temp_mod.set_temperature(25)

    ctx.pause('''
    Temperature module is at room temperature.
    Initial incubation steps complete. Put on ice for 1 minute.
    Please take the 96 block off of the temperature
    module and place it in slot 1 by replacing the plate already there.
    Place a new NEST 100ul 96 well plate on the magnetic module,
    and then select "Resume" on the Opentrons App.
    ''')

    ctx.comment('~~~~~~~~Adding Barcode Mastermix~~~~~~~~~')
    tip_counter += 1
    pick_up()
    for chunk in create_chunks(temp_plate.rows()[0][:num_col], 2):
        m20.aspirate(18, barcode_mmx)
        for well in chunk:
            m20.dispense(7.75, well)
        m20.dispense(2.5, barcode_mmx)
    m20.drop_tip()
    ctx.comment('\n\n\n\n')

    ctx.comment('~~~~~~~~Adding Barcode~~~~~~~~~')
    for s_col, d_col in zip(barcode_plate.rows()[0][:num_col],
                            temp_plate.rows()[0]):
        pick_up()
        m20.aspirate(1.25, s_col)
        m20.dispense(1.25, d_col)
        m20.touch_tip(radius=0.6)
        m20.drop_tip()
    ctx.comment('\n\n\n\n')

    # switch nomenclature for discarded plate and and prep plate
    end_prep_plate = amp_pt1
    ctx.comment('~~~~~~~~Adding Endprep Reaction and Mixing~~~~~~~~~')
    for source, dest in zip(end_prep_plate.rows()[0][:num_col],
                            temp_plate.rows()[0]):
        pick_up()
        m20.aspirate(1, source, rate=0.5)
        m20.dispense(1, dest, rate=0.5)
        m20.mix(10, 7.5, dest)
        m20.touch_tip(radius=0.75, v_offset=-12)
        m20.drop_tip()

    ctx.delay(minutes=30, msg='INCUBATING AT ROOM TEMPERATURE')
    temp_mod.set_temperature(65)
    ctx.delay(minutes=10, msg='INCUBATING AT 65C')
    temp_mod.set_temperature(25)

    ctx.pause('Put aluminum block on ice for 1 minute.')

    ctx.comment('~~~~~~~~Pooling Samples~~~~~~~~~')
    pick_up()
    for chunk in create_chunks(temp_plate.rows()[0][:num_col], 7):
        for well in chunk:
            m20.aspirate(2.5, well)
        m20.dispense(m20.current_volume, pool_col)
        m20.blow_out()
    m20.drop_tip()

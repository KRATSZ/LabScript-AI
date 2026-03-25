import math
from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'Swift Rapid NGS Part 3 - Extension, SPRI, and Ligation',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_samp, tip_type, overage_percent, bead_dry_time,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_type", "overage_percent", "bead_dry_time",
        "p20_mount", "p300_mount")

    # keep user in range
    num_samp = int(num_samp)
    if not 0.0 <= overage_percent <= 10.0:
        raise Exception("Enter a an overage percent between 5-10%")
    overage_percent = 1+overage_percent/100
    num_cols = math.ceil(int(num_samp/8))

    # load labware
    thermocycler = ctx.load_module('thermocycler')
    samp_plate = thermocycler.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
    temperature_mod = ctx.load_module('temperature module gen2', '3')
    alum_tuberack = temperature_mod.load_labware(
                        'opentrons_24_aluminumblock_generic_2ml_screwcap')
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_mod.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2')
    tiprack20 = [ctx.load_labware(tip_type, '9')]
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['4', '5', '6']]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=tiprack300)

    def pick_up(pipette):
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    # extraction function for step 5
    def extraction(mag_bead_vol, te_vol, te_tip,
                   transfer_vol, ethanol_well, trash_well, supernat_vol):
        ethanol_well = ethanol_well-1
        trash_well = trash_well-1
        if te_tip == 'p20':
            pip = p20
            samples = mag_plate.wells()[32:32+num_samp]
            dest = mag_plate.wells()[32:]

        elif te_tip == 'm300':
            pip = m300
            samples = sample_cols
            dest = mag_plate.rows()[0][8:]

        beads = reservoir.wells()[1]
        ethanol = reservoir.wells()[ethanol_well]
        trash = reservoir.wells()[trash_well]
        te = reservoir.wells()[0]

        # adding magbeads
        ctx.comment('\nAdding magbeads\n')
        m300.pick_up_tip()
        m300.distribute(mag_bead_vol, beads,
                        [col.top() for col in sample_cols],
                        mix_before=(5, 200),
                        new_tip='never')
        m300.drop_tip()

        # mix solution, cut flow rate to avoid bubbles
        m300.flow_rate.aspirate = 7.56  # same flow rate as p20
        m300.flow_rate.dispense = 7.56
        for col in sample_cols:
            m300.pick_up_tip()
            m300.mix(15, mag_bead_vol, col)
            m300.touch_tip()
            m300.drop_tip()
        m300.flow_rate.aspirate = 150  # set flow rate back to default
        m300.flow_rate.dispense = 300

        # 7.5 minute incubation
        ctx.delay(minutes=7.5)
        ctx.pause('''Remove magnetic plate from deck, seal and spin down -
                     If needed, please empty trash.''')
        ctx.comment('\nEngaging magnetic module in extraction step\n')
        mag_mod.engage()
        ctx.delay(minutes=5)

        # remove supernatant before ethanol wash
        for i, col in enumerate(sample_cols):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip()
            m300.move_to(col.center())
            m300.aspirate(supernat_vol, col.bottom().move(
                    Point(x=(col.diameter/2-1)*side)))
            m300.dispense(supernat_vol, trash.top())
            m300.drop_tip()

        # 2x ethanol washes
        for i in range(2):
            # add ethanol to beads and incubate
            m300.pick_up_tip()
            for col in sample_cols:
                m300.aspirate(200, ethanol)
                m300.dispense(200, col.top())
            m300.drop_tip()
            ctx.delay(seconds=30)

            # trash ethanol
            for col in sample_cols:
                side = -1 if i % 2 == 0 else 1
                m300.pick_up_tip()
                m300.move_to(col.center())
                m300.aspirate(50, col.top(z=-(col.depth-col.depth/4)).move(
                        Point(x=(col.diameter/2-1)*side)))
                m300.aspirate(50, col.top(z=-(col.depth-2*col.depth/4)).move(
                        Point(x=(col.diameter/2-1)*side)))
                m300.aspirate(50, col.top(z=-(col.depth-3*col.depth/4)).move(
                        Point(x=(col.diameter/2-1)*side)))
                m300.aspirate(50, col.bottom().move(
                        Point(x=(col.diameter/2-1)*side)))
                m300.dispense(200, trash.top())
                m300.drop_tip()
                ctx.comment('\n\n')
        mag_mod.disengage()
        ctx.pause('''Seal and spin down sample plate -
                     after, place sample plate back on magnetic module. ''')
        ctx.delay(minutes=bead_dry_time)

        # add te and mix
        pick_up(pip)
        for dest in samples:
            pip.aspirate(te_vol, te)
            pip.dispense(te_vol, dest.top())
        pip.drop_tip()

        m300.flow_rate.aspirate = 7.56  # same flow rate as p20
        m300.flow_rate.dispense = 7.56
        for dest in sample_cols:
            pick_up(m300)
            m300.mix(20, te_vol, dest)
            m300.blow_out()
            m300.touch_tip()
            m300.drop_tip()
        m300.flow_rate.aspirate = 150  # set flow rate back to default
        m300.flow_rate.dispense = 300

        # incubate for 4 minutes at RT
        ctx.delay(minutes=4)
        mag_mod.disengage()
        ctx.pause('''Seal and spin down sample plate -
                 remove seal, then place back on magnet.
                 If needed, empty tip rack.''')
        mag_mod.engage()
        ctx.delay(minutes=3)

        # move supernatant to new wells - columns 9, 10, and 11
        if te_tip == 'm300':
            for i, (s, d) in enumerate(zip(sample_cols,
                                           mag_plate.rows()[0][8:])):
                side = -1 if i % 2 == 0 else 1
                pick_up(pip)
                pip.aspirate(transfer_vol, s.bottom().move(
                        Point(x=(s.diameter/2-1)*side)))
                pip.dispense(transfer_vol, d)
                pip.drop_tip()
                ctx.comment('\n\n')

        elif te_tip == 'p20':
            for i, (s, d) in enumerate(zip(mag_plate.wells()[32:32+num_samp],
                                           mag_plate.wells()[64:])):
                side = -1 if i % 2 == 0 else 1
                pick_up(pip)
                pip.aspirate(transfer_vol, s.bottom().move(
                        Point(x=(s.diameter/2-1)*side)))
                pip.dispense(transfer_vol, d)
                pip.drop_tip()
                ctx.comment('\n\n')
        ctx.comment('\n\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n\n')

    # METHOD 1 - ASSEMBLE EXTENSION MASTERMIX
    # reagents
    temperature_mod.set_temperature(4)
    rna_reagent = alum_tuberack.rows()[0][0]
    pcr_mastermix = alum_tuberack.rows()[0][1]
    ext_mastermix = alum_tuberack.rows()[0][2]
    num_cols = math.ceil(int(num_samp/8))

    # assemble extension mastermix
    p20.pick_up_tip()
    p20.transfer(num_samp*overage_percent, rna_reagent, ext_mastermix.top(),
                 new_tip='never')
    p20.drop_tip()
    p20.pick_up_tip()
    p20.transfer(num_samp*23*overage_percent, pcr_mastermix,
                 ext_mastermix.top(), new_tip='never')
    p20.drop_tip()
    ctx.pause('''Mix extension mastermix and pulse spin to collect contents.
    After, put the mastermix back in tube well A3 on the aluminum block.''')

    # distribute mastermix
    for well in samp_plate.wells()[32:32+num_samp]:
        p20.pick_up_tip()
        p20.transfer(23*overage_percent, ext_mastermix, well.top(),
                     new_tip='never')
        p20.drop_tip()

    # thermocycler
    if thermocycler.lid_position != 'open':
        thermocycler.open_lid()
    ctx.pause('''Thermocycler heated. Place sample plate on thermocycler.''')
    profile = [
        {'temperature': 98, 'hold_time_minutes': 1},
        {'temperature': 63, 'hold_time_minutes': 2},
        {'temperature': 72, 'hold_time_minutes': 5},
    ]
    thermocycler.close_lid()
    thermocycler.execute_profile(steps=profile,
                                 repetitions=1,
                                 block_max_volume=43.5)
    thermocycler.set_block_temperature(4, block_max_volume=43.5)
    thermocycler.open_lid()
    ctx.pause('Place sample plate on magnetic module')

    # step 5 - extraction
    ctx.comment('\n\nSPRI-Cleaning\n\n')
    sample_cols = mag_plate.rows()[0][4:4+num_cols]
    extraction(52.5, 52, 'm300', 50, 11, 5, 91)
    extraction(60, 17, 'p20', 15, 12, 6, 55)
    ctx.pause('Place sample plate back on thermocycler')

    # step 6 - ligation
    # reagents
    rna_buffer_L1 = alum_tuberack.rows()[1][0]
    rna_buffer_L2 = alum_tuberack.rows()[1][1]
    rna_buffer_L3 = alum_tuberack.rows()[1][2]
    ligation_mastermix = alum_tuberack.rows()[1][3]

    # assemble ligation mastermix
    p20.pick_up_tip()
    p20.transfer(num_samp*3*overage_percent, rna_buffer_L1,
                 ligation_mastermix.top(), new_tip='never')
    p20.drop_tip()
    p20.pick_up_tip()
    p20.transfer(num_samp*10*overage_percent, rna_buffer_L2,
                 ligation_mastermix.top(), new_tip='never')
    p20.drop_tip()
    p20.pick_up_tip()
    p20.transfer(num_samp*2*overage_percent, rna_buffer_L3,
                 ligation_mastermix.top(), new_tip='never')
    p20.drop_tip()
    thermocycler.set_lid_temperature(35)
    ctx.pause('''Seal and spin down plate for next thermocycler profile''')

    # distribute ligation mastermix to wells
    p20.pick_up_tip()
    for dest in mag_plate.wells()[64:64+num_samp]:
        p20.transfer(15, ligation_mastermix, dest.top(), new_tip='never')
    p20.drop_tip()
    ctx.pause("Place sample plate on magnetic module")

    # thermocycler profile
    profile = [
        {'temperature': 25, 'hold_time_minutes': 15},
    ]
    thermocycler.close_lid()
    thermocycler.execute_profile(steps=profile,
                                 repetitions=1,
                                 block_max_volume=30)
    thermocycler.set_block_temperature(4, block_max_volume=30)
    thermocycler.open_lid()

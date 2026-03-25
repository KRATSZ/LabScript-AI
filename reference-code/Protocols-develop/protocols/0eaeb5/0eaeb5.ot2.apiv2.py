import math
from opentrons import protocol_api
from opentrons import types

metadata = {
    'protocolName': 'CleanPlex NGS Library Preparation',
    'author': 'Songnian Liu <Songnian.liu@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, DRYRUN, TEST_MODE_BEADS, water_rate,
     buffer_mmx_primer_rate, sample_rate, beads_rate,
     ethanol_rate, beads_mix_reps, beads_mix_rate, magdeck_engage_height,
     ethnaol_dis_zoffset, incubation_time, beads_engaging_time, airdry_time,
     ethanol_wash_time, p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samples", "DRYRUN", "TEST_MODE_BEADS",
        "water_rate",
         "buffer_mmx_primer_rate", "sample_rate", "beads_rate",
         "ethanol_rate", "beads_mix_reps", "beads_mix_rate",
         "magdeck_engage_height",
         "ethnaol_dis_zoffset", "incubation_time", "beads_engaging_time",
         "airdry_time",
         "ethanol_wash_time", "p20_mount", "p300_mount")

    # DO NOT TOUCH BELOW
    sample_cols = math.ceil(num_samples/8)
    if sample_cols > 12:
        raise ValueError('Not enough wells for specified number of samples')

    # modules & tips
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_mod.disengage()
    temp_mod = ctx.load_module('temperature module gen2', '3')
    temp_mod.set_temperature(celsius=4)
    # tips
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in ['4', '7', '6']]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['9', '8', '5']]
    # pipettes
    p20m = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tips20)
    p300m = ctx.load_instrument('p300_multi_gen2', p300_mount,
                                tip_racks=tips300)
    # #customized functions

    def pause_attention(msg):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=1)
        ctx.set_rail_lights(True)
        ctx.delay(seconds=1)
        ctx.set_rail_lights(False)
        ctx.delay(seconds=1)
        ctx.set_rail_lights(True)
        ctx.delay(seconds=1)
        ctx.set_rail_lights(False)
        ctx.delay(seconds=1)
        ctx.set_rail_lights(True)
        ctx.pause(msg)

    def pick_up(pipette):
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pause_attention(msg='\n\nReplace empty tipracks before resuming.')
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    # def replace_labware(slot_number, new_labware, name):
    #     del ctx.deck[str(slot_number)]
    #     return ctx.load_labware(new_labware, str(slot_number), name)

    def aspirate_with_delay(pipette, volume, src,
                            asp_rate, asp_delay_seconds):
        pipette.aspirate(volume, src, rate=asp_rate)
        if asp_delay_seconds > 0:
            ctx.delay(seconds=asp_delay_seconds)

    def dispense_with_delay(pipette, volume, dest,
                            dis_rate, dis_delay_seconds):
        pipette.dispense(volume, dest, rate=dis_rate)
        if dis_delay_seconds > 0:
            ctx.delay(seconds=dis_delay_seconds)

    def mix(pipette, volume, mix_loc, mix_rep, mix_rate):
        for _ in range(mix_rep):
            aspirate_with_delay(pipette, volume, mix_loc, mix_rate, 0)
            dispense_with_delay(pipette, volume, mix_loc, mix_rate, 0)

    def slow_tip_withdrawal(pipette, well, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well.top(-3))
        else:
            pipette.move_to(well.center())
        ctx.max_speeds[axis] = None

    def beads_mix(pipette, volume, mix_loc, mix_rep,
                  z_low, z_high,
                  asp_rate, dis_rate, blowout=True):
        for _ in range(mix_rep):
            aspirate_with_delay(pipette, volume, mix_loc.bottom(z_low),
                                asp_rate, 0)
            dispense_with_delay(pipette, volume, mix_loc.bottom(z_high),
                                dis_rate, 0)
        if blowout:
            pipette.flow_rate.blow_out /= 5
            pipette.blow_out(mix_loc.bottom(z_high+1))
            pipette.flow_rate.blow_out *= 5  # blowout 1st for beads_mix
            slow_tip_withdrawal(pipette, mix_loc, to_center=False)

    def transfer_combo(pipette, volume, src, dest,
                       asp_rate, dis_rate,
                       delay_mode=False,
                       asp_zoffset=1, dis_zoffset=1, blowout_zoffset=-2,
                       prewet=False, slow_withdrawl_asp=False,
                       postmix=False, postmix_vol=0,
                       postmix_rep=0, postmix_rate=0,
                       slow_withdrawl_dis=False, blowout_mode=False):
        if prewet:
            # if 0.8 * volume <= 2:
            #     premix_vol = 2
            # elif 0.8 * volume <= 200:
            premix_vol = round((0.8 * volume), 1)
            # else:
            #     premix_vol = 200
            mix(pipette, premix_vol, src.bottom(asp_zoffset+1),
                mix_rep=1, mix_rate=0.8)
        aspirate_with_delay(pipette, volume, src.bottom(asp_zoffset),
                            asp_rate, asp_delay_seconds=1 if delay_mode else 0)
        if slow_withdrawl_asp:
            slow_tip_withdrawal(pipette, src, to_center=False)
        dispense_with_delay(pipette, volume, dest.bottom(dis_zoffset),
                            dis_rate, dis_delay_seconds=1 if delay_mode else 0)
        if postmix:
            mix(pipette, postmix_vol, dest.bottom(dis_zoffset+1),
                postmix_rep, postmix_rate)
        if slow_withdrawl_dis:
            slow_tip_withdrawal(pipette, dest, to_center=False)
        if blowout_mode == 'default':
            pipette.flow_rate.blow_out /= 2
            pipette.blow_out(dest.top(blowout_zoffset))
            pipette.flow_rate.blow_out *= 2
        elif blowout_mode == 'viscous':
            pipette.flow_rate.blow_out /= 5
            pipette.blow_out(dest.top(blowout_zoffset))
            pipette.flow_rate.blow_out *= 5

    def incubation_airdry(time):
        if TEST_MODE_BEADS is False:
            ctx.delay(minutes=time)
        else:
            ctx.delay(seconds=time)

    def mag_engage(height, minutes):
        mag_mod.engage(height_from_base=height)
        if TEST_MODE_BEADS is False:
            ctx.delay(minutes=minutes)
        else:
            ctx.delay(seconds=minutes)

    xloc_index = 0

    def tip_disposal(pipette):
        nonlocal xloc_index
        xloc = [30, 0, -30]
        if DRYRUN or TEST_MODE_BEADS:
            pipette.return_tip()
        elif pipette.has_tip:
            drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
                types.Point(x=xloc[xloc_index]))
            pipette.drop_tip(drop_loc)
            xloc_index = (xloc_index + 1) % len(xloc)

    def add_reagent(pipette, reagent_well, dest, reagent_volume,
                    liq_class=False, mix_vol_sum=None):
        ctx.comment(f'--- Sample location: {str(dest)}')
        if liq_class == 'water_or_emptywell':
            transfer_combo(pipette, reagent_volume, reagent_well, dest,
                           asp_rate=water_rate, dis_rate=water_rate,
                           delay_mode=False,
                           asp_zoffset=2, dis_zoffset=1, blowout_zoffset=-2,
                           prewet=False, slow_withdrawl_asp=False,
                           postmix=False, postmix_vol=0,
                           postmix_rep=0, postmix_rate=0,
                           slow_withdrawl_dis=False, blowout_mode='default')
        elif liq_class == 'buffer_mmx_primer':
            # delay and prewet to avoid bubbles
            # slow withdrawl both true for asp and dis
            # postmix for buffer_mmx_primer is true
            transfer_combo(pipette, reagent_volume, reagent_well, dest,
                           asp_rate=buffer_mmx_primer_rate,
                           dis_rate=buffer_mmx_primer_rate,
                           delay_mode=True,
                           asp_zoffset=1, dis_zoffset=1, blowout_zoffset=-2,
                           prewet=True, slow_withdrawl_asp=True,
                           postmix=True, postmix_vol=0.8*mix_vol_sum,
                           postmix_rep=3, postmix_rate=1,
                           slow_withdrawl_dis=True, blowout_mode='viscous')
        elif liq_class == 'sample':
            # sample transfer usually does not require postmix
            # parameter can be used for elution
            transfer_combo(pipette, reagent_volume, reagent_well, dest,
                           asp_rate=sample_rate,
                           dis_rate=sample_rate,
                           delay_mode=False,
                           asp_zoffset=1, dis_zoffset=1, blowout_zoffset=-2,
                           prewet=False, slow_withdrawl_asp=False,
                           postmix=False, postmix_vol=0,
                           postmix_rep=0, postmix_rate=0,
                           slow_withdrawl_dis=True, blowout_mode='viscous')
        elif liq_class == 'bead':
            # use beads_mix to substitube prewet/postmix and blowout
            transfer_combo(pipette, reagent_volume, reagent_well, dest,
                           asp_rate=beads_rate,
                           dis_rate=beads_mix_rate,
                           delay_mode=True,
                           asp_zoffset=1, dis_zoffset=1, blowout_zoffset=0,
                           prewet=False, slow_withdrawl_asp=True,
                           postmix=False, postmix_vol=0,
                           postmix_rep=0, postmix_rate=0,
                           slow_withdrawl_dis=False, blowout_mode=False)

    def removal_liquids(liquid_volume, mag_sources, dest_list, mode=False):
        if mode == 'supernantant':
            ctx. comment('\n--------------Removing Supernatant-------------')
            for i, (mag_well, dest) in enumerate(zip(mag_sources, dest_list)):
                side = -1 if i % 2 == 0 else 1
                pick_up(p300m)
                p300m.aspirate(liquid_volume, mag_well.bottom().move(
                    types.Point(x=side, y=0, z=1)),
                    rate=0.1)
                p300m.aspirate(10, mag_well.bottom().move(
                    types.Point(x=0.5*side, y=0, z=0.7)),
                    rate=0.1)
                p300m.aspirate(10, mag_well.bottom().move(
                    types.Point(x=0.5*side, y=0, z=0.4)),
                    rate=0.1)
                p300m.dispense((liquid_volume+20), dest)
                p300m.blow_out()
                tip_disposal(p300m)
                ctx. comment('\n--------')
        if mode == 'elution':
            ctx. comment('\n------------------Removing Elution---------------')
            p20m.flow_rate.blow_out /= 2
            for i, (mag_well, dest) in enumerate(zip(mag_sources, dest_list)):
                side = -1 if i % 2 == 0 else 1
                pick_up(p20m)
                p20m.aspirate(liquid_volume, mag_well.bottom().move(
                    types.Point(x=side, y=0, z=1)),
                    rate=0.5)
                p20m.aspirate(2, mag_well.bottom().move(
                    types.Point(x=0.5*side, y=0, z=0.7)),
                    rate=0.5)
                p20m.aspirate(2, mag_well.bottom().move(
                    types.Point(x=0.5*side, y=0, z=0.4)),
                    rate=0.5)
                p20m.dispense((liquid_volume+4), dest)
                p20m.blow_out()
                tip_disposal(p20m)
                ctx. comment('\n--------')
            p20m.flow_rate.blow_out *= 2

    def ethanol_wash_airdry(wash_volume, wash_list, wash_reps):
        for _ in range(wash_reps):
            ctx. comment('\n------------------adding ethanol-----------------')
            pick_up(p300m)
            for i, wash_well in enumerate(wash_list):
                side = -1 if i % 2 == 0 else 1
                p300m.aspirate(wash_volume, ethanol.bottom(2),
                               rate=ethanol_rate)
                p300m.dispense(wash_volume, wash_well.top().move(
                    types.Point(x=side, y=0, z=ethnaol_dis_zoffset)),
                               rate=ethanol_rate)
                p300m.blow_out()
            tip_disposal(p300m)
            incubation_airdry(ethanol_wash_time)
            ctx. comment('\n------------------removing ethanol--------------')
            removal_liquids(wash_volume,
                            mag_sources=wash_list,
                            dest_list=trash,
                            mode='supernantant')
        ctx. comment('\n------------------Airdry-----------------')
        incubation_airdry(airdry_time)

    # labwares
    mag_plate = mag_mod.load_labware(
        'biorad_96_wellplate_200ul_pcr', 'mag_plate')
    reagent_plate = temp_mod.load_labware(
        'biorad_96_wellplate_200ul_pcr', 'reagent_plate')
    sample_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr', '2', 'sample_plate')
    # index_plate = ctx.load_labware(
    # 'biorad_96_wellplate_200ul_pcr', '5', 'index_plate')
    reagent_res = ctx.load_labware(
        'nest_12_reservoir_15ml', '10', 'reagent_reservoir')
    trash_res = ctx.load_labware(
        'nest_12_reservoir_15ml', '11', 'trash_reservoir')
    # reagent for deck layout 1
    water = reagent_res.wells()[0]                # A1 :water
    TE = reagent_res.wells()[1]                   # A2 ：TE
    beads = reagent_res.wells()[2]                # A3 : beads
    ethanol = reagent_res.wells()[3]              # A4 : ethanol
    trash = trash_res.wells()[::-1]           # collect all beads trash
    mPCR_mix_5x = reagent_plate.rows()[0][0]      # Column1 A1
    mPCR_primers = reagent_plate.rows()[0][1]     # Column2 A2
    stop = reagent_plate.rows()[0][2]             # Column3 A3
    digest_mmx = reagent_plate.rows()[0][3]       # Column4 A4
    second_PCR_mmx = reagent_plate.rows()[0][4]   # Column5 A5
    index_primers = reagent_plate.rows()[0][5]    # reserved position A6
    # # Plate mapping on the modules
    sample_list = sample_plate.rows()[0][:sample_cols]
    mag_sample_list = mag_plate.rows()[0][:sample_cols]
    # Protocl starts here
    pause_attention(msg='''Set up for CleanPlex NGS library preparation:\
    1. Double check all labwares/modules/reagents are loaded correctly\
    2. Please set up a timer\
    3. Remember to be back to transfer the 96-well plate for mPCR reaction''')
    ctx. comment('\n------------Multiplex PCR (mPCR) Reaction--------------')
    ctx. comment('\n-------------1A.1: adding 6 ul of water-----------')
    pick_up(p20m)
    for well in sample_list:
        add_reagent(p20m, water, well, reagent_volume=6,
                    liq_class='water_or_emptywell')
    tip_disposal(p20m)
    ctx.comment('\n')

    ctx. comment('\n----------1A.1: adding 2 ul of mPCR mix--------------')
    for well in sample_list:
        pick_up(p20m)
        add_reagent(p20m, mPCR_mix_5x, well, reagent_volume=2,
                    liq_class='buffer_mmx_primer', mix_vol_sum=8)
        tip_disposal(p20m)
        ctx.comment('\n')

    ctx. comment('\n---------------1A.1: adding 2 ul of mPCR primers-------')
    for well in sample_list:
        pick_up(p20m)
        add_reagent(p20m, mPCR_primers, well, reagent_volume=2,
                    liq_class='buffer_mmx_primer', mix_vol_sum=10)
        tip_disposal(p20m)
        ctx.comment('\n')

    pause_attention(msg='''1. mPCR reaction pre is compelte\
    2. Transfer the sample plate from deck slot 2 to thermocycler\
    3. Set up a timer\
    4. Please refill the 20ul filter tipracks and dump the trash bin\
    5. Transfer sample plate to the magnetic module after
    reaction&centrifugation''')
    p20m.reset_tipracks()

    ctx. comment('\n------------------Post-mPCR Purification-----------------')
    ctx. comment('\n------------------1A.4: adding 2 ul of STOP solution-----')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, stop, well, reagent_volume=2,
                    liq_class='buffer_mmx_primer', mix_vol_sum=12)
        tip_disposal(p20m)
        ctx.comment('\n')

    ctx. comment('\n----------------1B.1: adding 10 ul of TE-----------------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, TE, well, reagent_volume=10,
                    liq_class='buffer_mmx_primer', mix_vol_sum=20)
        tip_disposal(p20m)
        ctx.comment('\n')

    ctx. comment('\n---------------1B.2: adding 29 ul of beads-----------')
    for well in mag_sample_list:
        pick_up(p300m)
        beads_mix(p300m, 100, beads, mix_rep=beads_mix_reps,
                  z_low=1, z_high=5,
                  asp_rate=beads_mix_rate, dis_rate=beads_mix_rate,
                  blowout=False)
        add_reagent(p300m, beads, well, reagent_volume=29, liq_class='bead')
        beads_mix(p300m, 40, well, mix_rep=beads_mix_reps,
                  z_low=1, z_high=5,
                  asp_rate=beads_mix_rate, dis_rate=beads_mix_rate)
        tip_disposal(p300m)
        ctx.comment('\n')

    ctx. comment('\n---1B.3: 5 minutes incubation for DNA binding------')
    incubation_airdry(time=incubation_time)

    ctx. comment('\n------------------1B.4: Magnet Engage-----------------')
    mag_engage(height=magdeck_engage_height, minutes=beads_engaging_time)

    ctx. comment('\n--------1B.5: Remove supernantant---------------------')
    removal_liquids(liquid_volume=51,
                    mag_sources=mag_sample_list,
                    dest_list=trash,
                    mode='supernantant')

    ctx. comment('\n--------1B.6 + 1B.7: Ethanol wash x2 + airdry------')
    ethanol_wash_airdry(
        wash_volume=180, wash_list=mag_sample_list, wash_reps=2)
    mag_mod.disengage()
    p20m.reset_tipracks()

    ctx. comment('\n--------------1B.9: adding 10 ul of TE------------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, TE, well, reagent_volume=10,
                    liq_class='buffer_mmx_primer', mix_vol_sum=10)
        tip_disposal(p20m)
        ctx.comment('\n')

    # ctx. comment('\n-----1B.9: 5 minutes incubation for DNA binding------')
    # incubation_airdry(time=incubation_time)

    # ctx. comment('\n------------------1B.9: Magnet Engage-----------------')
    # mag_engage(height=magdeck_engage_height, minutes=beads_engaging_time)
    #

    # ctx. comment('\n--------1B.9: Remove Elution---------------------')
    # removal_liquids(liquid_volume=10,
    #                 mag_sources=mag_sample_list,
    #                 dest_list=sample_list,
    #                 mode='elution')
    # mag_mod.disengage()

    ctx. comment('\n----------------Digestion Reaction-----------------')
    ctx. comment('\n--------------2A.1: adding 10 ul of digestion_mmx-------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, digest_mmx, well, reagent_volume=10,
                    liq_class='buffer_mmx_primer', mix_vol_sum=20)
        tip_disposal(p20m)
        ctx.comment('\n')

    pause_attention(msg='''1. Ready for 37C digestion for 10 min\
    2. Transfer the sample plate from the magnetic module to thermocycler\
    3. Set up a timer\
    4. Please refill both filter tipracks and dump the trash bin\
    5. Move the sample plate to the magnetic module after
    digestion&centrifugation''')
    p20m.reset_tipracks()
    p300m.reset_tipracks()

    ctx. comment('\n-------------2A.4: adding 2 ul of STOP solution----------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, stop, well, reagent_volume=2,
                    liq_class='buffer_mmx_primer', mix_vol_sum=22)
        tip_disposal(p20m)
        ctx.comment('\n')

    ctx. comment('\n----------2B.1: adding 29 ul of beads-------------')
    for well in mag_sample_list:
        pick_up(p300m)
        beads_mix(p300m, 100, beads, mix_rep=beads_mix_reps,
                  z_low=1, z_high=5,
                  asp_rate=beads_mix_rate, dis_rate=beads_mix_rate,
                  blowout=False)
        add_reagent(p300m, beads, well, reagent_volume=29, liq_class='bead')
        beads_mix(p300m, 40, well, mix_rep=beads_mix_reps,
                  z_low=1, z_high=5,
                  asp_rate=beads_mix_rate, dis_rate=beads_mix_rate)
        tip_disposal(p300m)
        ctx.comment('\n')

    ctx. comment('\n---------2B.2: 5 minutes incubation for DNA binding----')
    incubation_airdry(time=incubation_time)

    ctx. comment('\n------------------2B.3: Magnet Engage-----------------')
    mag_engage(height=magdeck_engage_height, minutes=beads_engaging_time)

    ctx. comment('\n--------2B.3: Remove supernantant---------------------')
    removal_liquids(liquid_volume=51,
                    mag_sources=mag_sample_list,
                    dest_list=trash,
                    mode='supernantant')

    ctx. comment('\n--------2B.5 + 2B.6: Ethanol wash x2 + airdry------')
    ethanol_wash_airdry(
        wash_volume=180, wash_list=mag_sample_list, wash_reps=2)
    mag_mod.disengage()

    p20m.reset_tipracks()
    ctx. comment('\n--------------2B.8: adding 10 ul of TE------------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, TE, well, reagent_volume=10,
                    liq_class='buffer_mmx_primer', mix_vol_sum=10)
        tip_disposal(p20m)
        ctx.comment('\n')

    # ctx. comment('\n-----2B.8: 5 minutes incubation for DNA binding------')
    # incubation_airdry(time=incubation_time)

    # ctx. comment('\n------------------2B.8: Magnet Engage-----------------')
    # mag_engage(height=magdeck_engage_height, minutes=beads_engaging_time)

    # ctx. comment('\n--------2B.8: Remove Elution---------------------')
    # removal_liquids(liquid_volume=10,
    #                 mag_sources=mag_sample_list,
    #                 dest_list=sample_list,
    #                 mode='elution')
    # mag_mod.disengage()

    ctx. comment('\n----------------Second PCR Reaction-----------------')
    ctx. comment('\n--------------3A.1: adding 26 ul of second_PCR_mmx-------')
    for well in mag_sample_list:
        pick_up(p300m)
        add_reagent(p300m, second_PCR_mmx, well, reagent_volume=26,
                    liq_class='buffer_mmx_primer', mix_vol_sum=36)
        tip_disposal(p300m)
        ctx.comment('\n')

    ctx. comment('\n------------3A.1: adding 4 ul of index primers---')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, index_primers, well, reagent_volume=4,
                    liq_class='buffer_mmx_primer', mix_vol_sum=20)
        tip_disposal(p20m)
        ctx.comment('\n')

    pause_attention(msg='1. Ready for second PCR reaction\
    2. Transfer the sample plate from the magnetic module to thermocycler\
    3. Set up a min timer\
    4. Refill both 20ul and 200ul filter tipracks and dump the trash bin\
    5. Move the sample plate from TC to the magnetic module after PCR')
    p20m.reset_tipracks()
    p300m.reset_tipracks()

    ctx. comment('\n-------------3A.4: adding 2 ul of STOP solution----------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, stop, well, reagent_volume=2,
                    liq_class='buffer_mmx_primer', mix_vol_sum=22)
        tip_disposal(p20m)
        ctx.comment('\n')

    ctx. comment('\n----------3B.1: adding 40 ul of beads-------------')
    for well in mag_sample_list:
        pick_up(p300m)
        beads_mix(p300m, 100, beads, mix_rep=beads_mix_reps,
                  z_low=1, z_high=5,
                  asp_rate=beads_mix_rate, dis_rate=beads_mix_rate,
                  blowout=False)
        add_reagent(p300m, beads, well, reagent_volume=40, liq_class='bead')
        beads_mix(p300m, 48, well, mix_rep=beads_mix_reps,
                  z_low=1, z_high=5,
                  asp_rate=beads_mix_rate, dis_rate=beads_mix_rate)
        tip_disposal(p300m)
        ctx.comment('\n')

    ctx. comment('\n---------3B.2: 5 minutes incubation for DNA binding----')
    incubation_airdry(time=incubation_time)

    ctx. comment('\n------------------3B.3: Magnet Engage-----------------')
    mag_engage(height=magdeck_engage_height, minutes=beads_engaging_time)

    ctx. comment('\n--------3B.3: Remove supernantant---------------------')
    removal_liquids(liquid_volume=62,
                    mag_sources=mag_sample_list,
                    dest_list=trash,
                    mode='supernantant')

    ctx. comment('\n--------3B.5 + 3B.6: Ethanol wash x2 + airdry------')
    ethanol_wash_airdry(
        wash_volume=180, wash_list=mag_sample_list, wash_reps=2)
    mag_mod.disengage()

    p20m.reset_tipracks()
    ctx. comment('\n--------------3B.8: adding 10 ul of TE------------')
    for well in mag_sample_list:
        pick_up(p20m)
        add_reagent(p20m, TE, well, reagent_volume=10,
                    liq_class='buffer_mmx_primer', mix_vol_sum=10)
        tip_disposal(p20m)
        ctx.comment('\n')

    # ctx. comment('\n-----3B.8: 5 minutes incubation for DNA binding------')
    # incubation_airdry(time=incubation_time)

    # ctx. comment('\n------------------3B.8: Magnet Engage-----------------')
    # mag_engage(height=magdeck_engage_height, minutes=beads_engaging_time)

    # ctx. comment('\n--------3B.8: Remove Elution---------------------')
    # removal_liquids(liquid_volume=10,
    #                 mag_sources=mag_sample_list,
    #                 dest_list=sample_list,
    #                 mode='elution')
    # mag_mod.disengage()

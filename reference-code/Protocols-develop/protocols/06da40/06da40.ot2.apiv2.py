from opentrons import protocol_api
import math

# metadata
metadata = {
    'protocolName': 'Normalization and ddPCR Setup',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'description': 'This protocol performs Normalization before ddPCR Setup',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):
    [_input_csv, _reaction_mix, _replicates] = get_values(  # noqa: F821
        '_input_csv', '_reaction_mix', '_replicates')

    # variables
    input_csv = _input_csv  # CSV: Well, Sample Vol, Dilutent Vol
    reaction_mix = _reaction_mix  # Bool - create reaction mix on deck or not
    replicates = _replicates  # number of replicates

    # labware
    tips = [
        ctx.load_labware('opentrons_96_tiprack_20ul', s) for s in range(7, 11)]
    all_20_tips = [well for rack in tips for well in rack.wells()]
    tip_20_ctr = 0
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', 11)]
    dest_plates = [
        ctx.load_labware(
            'thermofishermicroamp_96_aluminumblock_200ul',
            s) for s in [1, 2, 3]]
    src_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 4)
    norm_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 5)
    tube_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 6)

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', 'left', tip_racks=tips)
    p300 = ctx.load_instrument('p300_single_gen2', 'right', tip_racks=tips300)

    # Helper Functions
    def pick_up(pip):
        nonlocal tip_20_ctr
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Replace the tips")
            pip.reset_tipracks()
            if pip == p20:
                tip_20_ctr = 0
            pip.pick_up_tip()

    def drop_tip(pip):
        nonlocal tip_20_ctr
        """Function that can will drop used p20 tips in empty tip racks
        (saving space in waste bin)"""
        if pip == p300:
            pip.drop_tip()
        else:
            tip_20_ctr += 1
            if tip_20_ctr < 96:
                pip.drop_tip()
            else:
                pip.drop_tip(all_20_tips[tip_20_ctr-96])

    def custom_mix(pip, well, mix_num, vol):
        """Custom function for mixing"""
        loc1 = well.bottom(1)
        ht = 3
        loc2 = well.bottom(ht)
        for _ in range(mix_num):
            pip.aspirate(vol, loc1)
            pip.dispense(vol, loc2)

    # parse CSV
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]]
    num_samps = len(data)
    reaction_mixes = tube_rack.columns()[0]

    # perform calculations and comment to user how much volume is needed
    # dilutent
    total_dil = 0
    for line in data:
        total_dil += float(line[2])
    dil_h20 = tube_rack.columns()[-1]
    for well in dil_h20:
        if total_dil <= 1500:
            well.liq_vol = total_dil
            total_dil -= total_dil
        else:
            well.liq_vol = 1500
            total_dil -= 1500
        if well.liq_vol > 1500:
            raise Exception("There aren't enough wells to accomodate this \
            volume of dilutent.")
        if well.liq_vol > 0:
            ctx.comment(
                f"Please ensure there is {well.liq_vol}uL of dilutent in \
                {well}\n")

    # reaction mix
    samp_chunks = [0]
    for i in range(num_samps):
        if samp_chunks[-1] == 24:
            samp_chunks.append(0)
        samp_chunks[-1] += 1

    for chunk, tube in zip(samp_chunks, reaction_mixes):
        if reaction_mix:
            num_ddpcr_tubes = math.ceil((3*11*num_samps*1.15)/1200)
            ctx.comment(f"Please ensure that there is {num_ddpcr_tubes} tubes \
            of 2x ddPCR Supermix column 4, all with at least \
            1200ul of 2x ddPCR\n")  # FIX COMMENT
        else:
            total_vol = 18 * round(((chunk+1) * 3.15), 0)
            ctx.comment(f"Please ensure that there is {total_vol}uL of \
            Reaction Mix in {tube}\n")  # FIX COMMENT
            tube.liq_vol = total_vol

    if reaction_mix:
        vol_reagents = 1.1
        vol_water = 0.4
        components = {
            'RPL32 Forward': tube_rack['A2'],
            'RPL32 Reverse': tube_rack['B2'],
            'RPL32 Probe': tube_rack['C2'],
            'RRE Forward': tube_rack['A3'],
            'RRE Reverse': tube_rack['B3'],
            'RRE Probe': tube_rack['C3']
        }

        # water_tube = vol_water * round((num_samps) * 3)
        water_src = tube_rack['D2']

    # perform normalization
    dil_iter = iter(dil_h20)

    # pre-transfer diluent
    dil_src = next(dil_iter)
    for line in data:
        loc, dil_vol = line[0], line[2]

        if not dil_vol or dil_vol == 0:
            pass
        else:
            dil_vol = float(dil_vol)
            pip = p20 if dil_vol <= 20 else p300
            if dil_src.liq_vol < dil_vol + 20:
                dil_src = next(dil_iter)
            dil_src.liq_vol -= dil_vol
            dest = norm_plate[loc]
            if not pip.has_tip:
                pip.pick_up_tip()
            dest.liq_vol = dil_vol
            pip.transfer(dil_vol, dil_src.bottom(1), dest, new_tip='never')

    for pip in [p20, p300]:
        if pip.has_tip:
            drop_tip(pip)

    # perform normalization
    for line in data:
        loc, samp_vol = line[:2]
        samp_vol = float(samp_vol)

        src = src_plate[loc]
        dest = norm_plate[loc]
        pip = p20 if samp_vol <= 20 else p300

        # transfer sample
        pip.pick_up_tip()
        pip.mix(2, samp_vol, src)
        pip.aspirate(samp_vol, src)
        pip.dispense(samp_vol, dest)
        dest.liq_vol = samp_vol
        custom_mix(pip, dest, 3, samp_vol)
        drop_tip(pip)

    # create reaction mix
    if reaction_mix:
        ctx.comment('Creating Reaction Mix')
        tube_vols = [0]
        for i in range(num_samps):
            if tube_vols[-1] == 24:
                tube_vols.append(0)
            tube_vols[-1] += 1

        for tube, tube_v in zip(reaction_mixes, tube_vols):
            transfer_vol = round(vol_reagents * round((tube_v) * 3), 1)
            transfer_vol *= 1.15
            pip = p20 if transfer_vol <= 20 else p300
            for label, src in components.items():
                ctx.comment(f"\nTransferring {transfer_vol}uL of {label} \
                from {src} to {tube}.")
                pip.pick_up_tip()
                # custom pip.mix()
                pip.aspirate(transfer_vol, src)
                pip.dispense(transfer_vol, tube)
                # custom pip.mix()
                drop_tip(pip)
            water_vol = vol_water * round((tube_v) * 3)
            water_vol *= 1.15
            pip = p20 if water_vol <= 20 else p300
            ctx.comment(f"\nTransferring {water_vol}uL of water from \
            {water_src} to {tube}.")
            pip.pick_up_tip()
            # custom pip.mix()
            pip.aspirate(water_vol, src)
            pip.dispense(water_vol, tube)
            # custom pip.mix()
            drop_tip(pip)

            pick_up(p300)
            ddpcr_vol = 3*11*num_samps*1.15
            ctx.comment(f"\nTransferring {ddpcr_vol}uL of ddpcr from \
            column 4 to A1.")

            num_transfers = math.ceil(ddpcr_vol/300)
            starting_tube_vol = 1200
            tube_ctr = 0

            for _ in range(num_transfers):
                transfer_vol = 300 if ddpcr_vol >= 300 else ddpcr_vol
                if starting_tube_vol < transfer_vol:
                    tube_ctr += 1
                    starting_tube_vol = 1200
                p300.aspirate(transfer_vol,
                              tube_rack.columns()[3][tube_ctr])
                p300.dispense(transfer_vol,
                              tube_rack.wells()[0].top())
                starting_tube_vol -= transfer_vol
                ddpcr_vol -= transfer_vol

            p300.mix(25, 300, tube_rack.wells()[0])
            drop_tip(p300)

    # transfer reaction mix
    ctx.comment(f"Transferring Reaction Mix to {num_samps*replicates} wells")
    dest_wells = [well for plate in dest_plates for well in plate.wells()]
    for idx, dest in enumerate(dest_wells[:num_samps*replicates]):
        src = reaction_mixes[idx//(24*replicates)]
        if not p20.has_tip:
            p20.pick_up_tip()
        p20.aspirate(18, src.bottom(1))
        p20.dispense(18, dest)
        if idx % (24*replicates) == (24 * replicates - 1):
            drop_tip(p20)

    if p20.has_tip:
        drop_tip(p20)
    # transfer samples + mix
    ctx.comment("Transferring normalized samples to destination plate(s).")
    ctr = 0
    for idx, dest in enumerate(dest_wells[:num_samps*replicates]):
        src = norm_plate.wells()[idx//replicates]
        pick_up(p20)
        custom_mix(p20, src, 2, 10)
        p20.aspirate(4, src)
        p20.dispense(4, dest)
        dest.liq_vol = 22
        custom_mix(p20, dest, 3, 15)
        drop_tip(p20)
        ctr += 1

    leftover = ctr % 8
    ctx.comment('\n\n\n\n\n')

    pick_up(p300)
    for well in dest_wells[ctr:ctr+leftover]:
        p300.aspirate(22, water_src)
        p300.dispense(22, well)
    drop_tip(p300)

    ctx.comment("Protocol complete.")

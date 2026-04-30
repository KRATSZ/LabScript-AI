from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Oncomine Focus Assay - Pt 4: Purify Library + Elution',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):
    [
     _samp_cols,  # column numbers containing samples
     _m300_mount  # mount for p300-Multi
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        '_samp_cols',
        '_m300_mount')

    # custom variables
    if type(_samp_cols) is int:
        samp_cols = [_samp_cols]
    else:
        samp_cols = _samp_cols.split(",")
    m300_mount = _m300_mount

    # load modules
    mag_deck = ctx.load_module('magnetic module gen2', '1')

    # load labware
    mag_plate = mag_deck.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt',
        'Sample Plate on MagDeck')

    elution_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '3',
        'Elution Plate')

    res12 = ctx.load_labware(
        'nest_12_reservoir_15ml', '2', '12-Well Reservoir with Reagents')

    # load tipracks
    tips = [ctx.load_labware(
        'opentrons_96_filtertiprack_200ul', s) for s in ['5', '6']]

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    # helper functions
    # to take vol and return estimated liq height
    def liq_height(well):
        if well.diameter is not None:
            radius = well.diameter / 2
            cse = math.pi*(radius**2)
        elif well.length is not None:
            cse = well.length*well.width
        else:
            cse = None
        if cse:
            return well.liq_vol / cse
        else:
            raise Exception("""Labware definition must
                supply well radius or well length and width.""")

    def incubate(min):
        ctx.comment(f'\nIncubating for {min} minutes\n')
        ctx.delay(minutes=min)

    def remove_supernatant(vol):
        ctx.comment(f'\nTransferring {vol}uL from wells to liquid waste\n')
        m300.flow_rate.aspirate = 15
        for col in samp_cols:
            m300.pick_up_tip()
            m300.aspirate(vol, mag_plate['A'+str(col).strip()])
            m300.dispense(vol, waste)
            m300.drop_tip()
        m300.flow_rate.aspirate = 94

    # reagents
    beads = res12['A1']
    beads.liq_vol = 45 * len(samp_cols) * 1.05
    etoh = res12['A3']
    etoh.liq_vol = 350 * len(samp_cols)
    te = res12['A5']
    te.liq_vol = 50 * len(samp_cols) * 1.05
    waste = res12['A11'].top(-2)

    # protocol
    # Transfer Bead Solution Transfer
    ctx.comment(f'\nTransferring 45uL Bead Solution \
    to samples in columns {samp_cols}\n')
    for col in samp_cols:
        m300.pick_up_tip()
        beads.liq_vol -= 45
        bead_ht = liq_height(beads) - 2 if liq_height(beads) - 2 > 1 else 1
        m300.mix(3, 40, beads.bottom(bead_ht))
        m300.aspirate(45, beads.bottom(bead_ht))
        m300.dispense(45, mag_plate['A'+str(col).strip()])
        m300.mix(5, 60, mag_plate['A'+str(col).strip()])
        ctx.delay(seconds=1)
        m300.drop_tip()

    # Incubate for 5 minutes, engage magnet, incubate for 2 minutes
    incubate(5)
    mag_deck.engage()
    incubate(2)

    # remove supernatant
    remove_supernatant(75)
    mag_deck.disengage()

    # Perform 2 ethanol washes
    for i in range(2):
        ctx.comment(f'\nPerforming EtOH Wash {i+1}\n')
        for col in samp_cols:
            m300.pick_up_tip()
            etoh.liq_vol -= 150
            et_ht = liq_height(etoh) - 2 if liq_height(etoh) - 2 > 1 else 1
            m300.aspirate(150, etoh.bottom(et_ht))
            m300.dispense(150, mag_plate['A'+str(col).strip()])
            m300.mix(5, 100, mag_plate['A'+str(col).strip()])
            ctx.delay(seconds=1)
            m300.blow_out()
            m300.drop_tip()

        mag_deck.engage()
        incubate(2)

        remove_supernatant(150)
        mag_deck.disengage()

    incubate(2)

    # Transfer elution buffer and elutes
    ctx.comment(f'\nTransferring 50uL Low TE \
    to samples in columns {samp_cols}\n')
    for col in samp_cols:
        m300.pick_up_tip()
        te.liq_vol -= 50
        te_ht = liq_height(te) - 2 if liq_height(te) - 2 > 1 else 1
        m300.aspirate(50, te.bottom(te_ht))
        m300.dispense(50, mag_plate['A'+str(col).strip()])
        m300.mix(5, 25, mag_plate['A'+str(col).strip()])
        ctx.delay(seconds=1)
        m300.drop_tip()

    incubate(2)
    mag_deck.engage()
    incubate(2)

    ctx.comment('\nTransferring samples to Elution Plate\n')
    m300.flow_rate.aspirate = 30
    for col, dest in zip(samp_cols, elution_plate.rows()[0]):
        m300.pick_up_tip()
        m300.aspirate(50, mag_plate['A'+str(col).strip()])
        m300.dispense(50, dest)
        m300.drop_tip()

    ctx.comment('\nProtocol complete!')

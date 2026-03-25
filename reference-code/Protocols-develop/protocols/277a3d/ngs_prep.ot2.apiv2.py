metadata = {
    'protocolName': 'Oxford Nanopore Technologies 16S Barcoding NGS Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    num_samples, mount_p20, mount_p300 = get_values(  # noqa: F821
        'num_samples', 'mount_p20', 'mount_p300')

    if not 1 <= num_samples <= 24:
        raise Exception(f'Invalid sample number: {num_samples}')
    if mount_p20 == mount_p300:
        raise Exception(f'Pipette mounts cannot match: both {mount_p20}')

    # labware
    sample_plate = ctx.load_labware('thermofishermicroamp_96_wellplate_200ul',
                                    '2', 'sample plate')
    mag_rack = ctx.load_labware('permagen_24_tuberack_1500ul', '3',
                                'magnetic rack')
    tempdeck = ctx.load_module('temperature module gen2', '4')
    reagent_rack = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_snapcap', 'reagent tubes')
    tempdeck.set_temperature(4)
    barcode_rack = ctx.load_labware(
        'opentrons_24_tuberack_500ul', '5', 'barcode rack')
    etoh_res = ctx.load_labware('nest_1_reservoir_195ml', '6',
                                'EtOH reservoir')
    tipracks_20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['7', '10']]
    tipracks_300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['8', '11']]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', mount_p20,
                              tip_racks=tipracks_20)
    p300 = ctx.load_instrument('p300_single_gen2', mount_p300,
                               tip_racks=tipracks_300)

    # reagents
    water = reagent_rack.wells()[0]
    longamp_taq = reagent_rack.wells()[1]
    etoh = etoh_res.wells()[0]
    samples_plate = sample_plate.wells()[:num_samples]
    samples_tubes = mag_rack.wells()[:num_samples]
    barcodes = barcode_rack.wells()[:num_samples]

    p20.pick_up_tip()
    for s in samples_plate:
        p20.transfer(14, water, s.top(-1), new_tip='never')
        p20.blow_out(s.top(-1))
    p20.drop_tip()

    p300.pick_up_tip()
    for s in samples_plate:
        p300.transfer(25, longamp_taq, s.top(-1), new_tip='never')
        p300.blow_out(s.top(-1))
    p300.drop_tip()

    for barcode, s in zip(barcodes, samples_plate):
        p20.pick_up_tip()
        p20.move_to(barcode.top())
        # slow pipette head for accessing barcodes
        ctx.max_speeds['A'] = 100
        ctx.max_speeds['Z'] = 100
        p20.aspirate(1, barcode)
        p20.touch_tip(barcode)
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']
        p20.dispense(1, s.bottom(2))
        p20.touch_tip(s)
        p20.drop_tip()

    msg = """Step 4) Thermocycle\n
    Step 5) Take off thermocycler and transfer all samples to 1.5ml tubes\n
    Step 6) Add Ampure Beads\n
    Step 7) Incubate on a Hula mixer (rotator mixer) for 5 minutes at RT.\n
    Step 8) Place tube on Magnetics tube holder in OT-2\n"""

    ctx.pause(msg)

    for _ in range(2):
        for tube in samples_tubes:
            p300.pick_up_tip()
            p300.transfer(200, etoh, tube, new_tip='never')
            p300.aspirate(200, tube)
            p300.drop_tip()

    ctx.comment('Remove tubes for final elution')

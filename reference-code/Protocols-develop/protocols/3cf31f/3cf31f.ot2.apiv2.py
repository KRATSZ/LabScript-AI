from opentrons import protocol_api

metadata = {
    'protocolName': 'BioFluid Mix and Transfer - Part 1/2 - APIv2',
    'author': 'Opentrons',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [p300_mount] = get_values(  # noqa: F821
        "p300_mount")

    # Load labware/tiprack/modules
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', '11',
                               'Tiprack 50/300ul')

    cryovials = ctx.load_labware('custom_nanosep_tube_container', '3')
    centtubes = ctx.load_labware('custom_centrifuge_tube_container', '2')
    ultratubes = ctx.load_labware('custom_nanosep_tube_container', '1')

    tempdeck = ctx.load_module('tempdeck', '10')
    temprack = tempdeck.load_labware(
                'opentrons_24_aluminumblock_nest_1.5ml_snapcap')

    # Load pipettes
    p300 = ctx.load_instrument('p300_single', p300_mount, tip_racks=[tiprack])

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause('Replace 50/300ul tiprack in slot 11. \
                When ready, click RESUME.')
            pip.reset_tipracks()
            pip.pick_up_tip()

    tempdeck.set_temperature(4)

    # Step 1 - mix bio-fluid and transfer 50uL
    # change to 48 wells.
    """
    The code below creates a new list of wells that is based on 48 wells.
    The 'centtubes' and 'ultratubes' are converted into lists that span rows
    A, C, E, G, I, and K (how the rows are named in this orientation).
    """
    cryovials48 = [well for wells in cryovials.rows()[::2] for well in wells]
    centtubes48 = [well for wells in centtubes.rows()[::2] for well in wells]
    ultratubes48 = [well for wells in ultratubes.rows()[::2] for well in wells]

    for source, dest in zip(cryovials48, centtubes48):
        pick_up(p300)
        p300.transfer(50, source, dest, new_tip='never')
        p300.drop_tip()

    # Step 2 - transfer 40ul aliquot of solution

    for dest in centtubes48:
        pick_up(p300)
        p300.transfer(40, temprack.wells()[0], dest,
                      new_tip='never')
        p300.mix(3, 35, dest)
        p300.blow_out(dest.top())
        p300.drop_tip()

    # Step 3 + 4 transfer 110ul solution then transfer 200 to nanosep tubes

    for k, cent, ultra in zip(range(48), centtubes48, ultratubes48):
        m = (k//10) + 1
        pick_up(p300)
        p300.transfer(110, temprack.wells(m), cent,
                      new_tip='never')
        p300.mix(3, 150, cent)
        p300.blow_out(cent.top())
        p300.transfer(200, cent, ultra,
                      new_tip='never')
        p300.blow_out(ultra.top())
        p300.drop_tip()

    ctx.comment("Part 1 is now complete. Please remove samples from OT-2 for\
    centrifugation. After centrifugation, replace samples on the deck and run\
    Part 2. Be sure to replace the cryovials in slots 3/6/9 with sample\
    vials. Lastly, replace the tiprack in slot 11 with a full rack.")

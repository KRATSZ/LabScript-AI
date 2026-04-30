import math

metadata = {
    'protocolName': 'Olink Target 96 Part 2/3: Extension',
    'author': 'Nick <ndiehl@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    num_samples, plate_type, m300_mount = get_values(  # noqa: F821
        'num_samples', 'plate_type', 'm300_mount')

    if not 1 <= num_samples <= 96:
        raise Exception('Invalid number of samples (1-96)')

    ext_mix = ctx.load_labware(
        'nest_12_reservoir_15ml', '5',
        'reservoir for extension mix (channel 1)').wells()[0]
    inc_plate = ctx.load_labware(plate_type, '2', 'incubation plate')
    tipracks300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '6')]

    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks300)

    num_cols = math.ceil(num_samples/8)

    ctx.comment('Bring the Incubation Plate to room temperature, spin at 400 x \
g for 1 min. Preheat the PCR machine.')
    ctx.comment('Vortex the Extension mix and pour into a multi-channel \
pipette reservoir.')

    m300.pick_up_tip()
    m300.aspirate(20, ext_mix)
    for col in inc_plate.rows()[0][:num_cols]:
        m300.aspirate(96, ext_mix)
        m300.dispense(96, col.top(-1))
    m300.drop_tip()

    ctx.comment('Seal the plate with an adhesive plastic film, vortex \
thoroughly ensuring that all wells are mixed, and spin down.')
    ctx.comment('Place the Incubation Plate in the thermal cycler, and start \
the PEA program (50°C 20 min, 95°C 5 min (95°C 30s, 54°C 1 min, 60°C 1 min) \
x17, 10°C hold).')

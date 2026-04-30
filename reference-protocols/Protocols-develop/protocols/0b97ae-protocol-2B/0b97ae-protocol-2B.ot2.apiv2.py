import math

metadata = {
    'protocolName': 'QIAseq FastSelect Fragmentation',
    'author': 'Trevor <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    # Variables
    [num_samples, vol_dna, p300_used] = get_values(  # noqa: F821
        "num_samples", "vol_dna", "p300_used")
    num_samples = int(num_samples)
    num_cols = math.ceil(num_samples/8)
    Water_Vol = 15-(vol_dna+2.5)

    # load tips
    tips = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
            for slot in [3, 5]]
    if p300_used == 'yes':
        tips3 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                 for slot in [8]]

    # load modules
    tempdeck_1 = ctx.load_module('temperature module gen2', '10')
    tempdeck_2 = ctx.load_module('temperature module gen2', '7')
    Mag_mod = ctx.load_module('magnetic module', '4')
    Mag_mod = Mag_mod

    # load labware
    water_res = ctx.load_labware('perkinelmer_12_reservoir_21000ul', 2,
                                 'Water reservoir')
    Mastermix_plate = tempdeck_1.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul',  # noqa: E501
                                              'MasterMix plate')
    Diluted_plate = tempdeck_2.load_labware('appliedbiosystemsenduraplate_96_aluminumblock_220ul',  # noqa: E501
                                            'Diluted RNA plate')

    # mapping
    water = water_res.rows()[0][0]
    mm = Mastermix_plate.rows()[0][0]

    # Turn on Temp Mods
    # tempdeck_1.set_temperature(4)
    tempdeck_2.set_temperature(4)

    # pipettes
    p20 = ctx.load_instrument('p20_multi_gen2', 'left',
                              tip_racks=tips)
    if p300_used == 'yes':
        p300 = ctx.load_instrument('p300_multi_gen2', 'right',
                                   tip_racks=tips3)

    # Plating Water
    for well in Diluted_plate.rows()[0][:num_cols]:
        if Water_Vol > 20:
            p300.transfer(Water_Vol, water, well, new_tip='always')
        else:
            p20.transfer(Water_Vol, water, well, new_tip='always')

    # Plating MasterMix
    for i, col in enumerate(Diluted_plate.rows()[0][:num_cols]):
        p20.transfer(2.5, mm, col, new_tip='always', mix_after=(5, 10))

    ctx.pause('Click continue when ready to turn the cooling plates off')
    tempdeck_1.deactivate()
    tempdeck_2.deactivate()
    ctx.comment(
     '''
        Process Complete. Remove Plate from Position 7 and incubate according
        to FastSelect 5/16/23S, Table 3
    ''')

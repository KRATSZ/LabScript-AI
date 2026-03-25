from opentrons.types import Point
import math

metadata = {
    'protocolName': 'IVT Aliquots',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.14'
}


def run(ctx):

    [input_csv] = get_values(  # noqa: F821
        'input_csv')

    # parse data
    data = [
        [val.strip() for val in line.split(',')]
        for line in input_csv.splitlines()
    ]
    rxn_vol = float(data[9][5])
    num_rxns = int(data[10][5])
    total_vol_with_overage = float(data[11][5])
    factor_overage = total_vol_with_overage/(rxn_vol*num_rxns)

    # labware
    rack1 = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '4', 'component rack 1')
    rack2 = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '7', 'component rack 2')
    rack15 = ctx.load_labware(
        'opentrons_15_tuberack_5000ul', '8', 'mix tube')
    aliquot_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '5', 'aliquot rack')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '6', 'reservoir')
    tiprack_20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '1')]
    tiprack_300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '2')]

    template_volumes = []
    for line in data[31:]:
        if not line[0] or 'rxn' in line[0].lower():  # look for templates end
            break
        template_volumes.append(float(line[6]))
    num_temp = len(template_volumes)
    if not num_temp == num_rxns:
        ctx.pause(f'# templates {num_temp} != # rxns {num_rxns}. Continue?')

    mix_volumes = [
        float(line[5]) for line in data[14:24]
    ]
    mix_map = {
        well: vol
        for well, vol in zip(rack1.wells()[:len(mix_volumes)], mix_volumes)
    }

    template_map = {
        well: vol
        for well, vol in zip(rack2.wells()[:len(template_volumes)],
                             template_volumes)
    }
    enzyme_volumes = [
        float(line[5]) for line in data[25:27]]
    enzyme_map = {
        well: vol
        for well, vol in zip(
            rack2.wells()[len(template_volumes):
                          len(template_volumes)+len(enzyme_volumes)],
            enzyme_volumes)
    }

    colors = [
        '#5b3811',
        '#ddb4ca',
        '#4f3e24',
        '#584582',
        '#860916',
        '#1f6f7e',
        '#95bb6d',
        '#f5ea87',
        '#539a51',
        '#992d16',
        '#5f50cf',
        '#159668',
        '#897f77',
        '#2bad24',
        '#3bbac0',
        '#44971e',
        '#d11e7f',
        '#4cfe77',
        '#ee06d2',
        '#9ffd59']

    try:
        for letter, (well, vol) in zip('ABCDEFGHIJ', mix_map.items()):

            temp = ctx.define_liquid(
                name=letter,
                description='',
                display_color=colors.pop()
            )
            well.load_liquid(temp, vol)

        template_color = colors.pop()
        for i, (well, vol) in enumerate(template_map.items()):

            temp = ctx.define_liquid(
                name=f'DNA template {i+1}',
                description='',
                display_color=template_color
            )
            well.load_liquid(temp, vol*factor_overage)

        for letter, (well, vol) in zip(
                ['P (1:100 dilution)', 'TP'], enzyme_map.items()):

            temp = ctx.define_liquid(
                name=letter,
                description='',
                display_color=colors.pop()
            )
            well.load_liquid(temp, vol)
    except AttributeError:
        pass

    mix_tube = rack15.wells()[0]
    enzyme_mix_tube = rack2.rows()[0][-1]
    dn = rack2.wells()[len(template_volumes)+len(enzyme_volumes)]
    cac = rack2.wells()[len(template_volumes)+len(enzyme_volumes)+1]
    rxns = aliquot_rack.wells()[:num_rxns]
    water = reservoir.wells()[0]
    licl_h2o = reservoir.wells()[1]

    # find vols DN and CaC
    vol_dn = vol_cac = None
    for line in data[45:]:  # start looking lower
        if line[0].lower().strip() == 'dn':
            vol_dn = float(line[5])
        if line[0].lower().strip() == 'cac':
            vol_cac = float(line[5])

    try:
        mix_tube_liq = ctx.define_liquid(
                name='mix tube',
                description='non-enzyme mix components',
                display_color=colors.pop()
        )
        enzyme_mix_tube_liq = ctx.define_liquid(
                name='enzyme mix tube',
                description='enzyme mix components',
                display_color=colors.pop()
        )
        water_liq = ctx.define_liquid(
                name='water',
                description='',
                display_color=colors.pop()
        )
        licl_h2o_liq = ctx.define_liquid(
                name='LiCl + H2O',
                description='1:1 ratio of LiCl and H2O',
                display_color=colors.pop()
        )

        mix_tube.load_liquid(mix_tube_liq, 0)
        enzyme_mix_tube.load_liquid(enzyme_mix_tube_liq, 0)

        dn_liq = ctx.define_liquid(
            name='DN',
            description='',
            display_color=colors.pop()
        )
        dn.load_liquid(dn_liq, vol_dn)

        cac_liq = ctx.define_liquid(
            name='CaC',
            description='',
            display_color=colors.pop()
        )
        cac.load_liquid(cac_liq, vol_cac)
    except AttributeError:
        pass

    vols_water = [
        rxn_vol - (sum(mix_volumes)/num_rxns/factor_overage +
                   sum(enzyme_volumes)/num_rxns/factor_overage +
                   template_vol)
        for template_vol in template_volumes]
    vol_licl_h2o = (rxn_vol + sum([vol_dn, vol_cac])/factor_overage)*2

    try:
        water.load_liquid(water_liq, sum(vols_water))
        licl_h2o.load_liquid(licl_h2o_liq, vol_licl_h2o)
    except AttributeError:
        pass

    # pipettes
    p300 = ctx.load_instrument(
        'p300_single_gen2', 'left', tip_racks=tiprack_300)
    p20 = ctx.load_instrument(
        'p20_single_gen2', 'right', tip_racks=tiprack_20)

    def wick(pip, well, side=1):
        pip.default_speed /= 5
        radius = well.diameter/2 if well.diameter else well.length/2
        pip.move_to(well.bottom().move(Point(x=side*radius*0.5, z=3)))
        pip.default_speed *= 5

    def slow_withdraw(pip, well, delay_seconds=1.0):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 10

    vol_pre_airgap_p300 = 20.0
    vol_pre_airgap_p20 = 2.0

    # initial mix
    for i, (well, transfer_vol) in enumerate(mix_map.items()):
        if transfer_vol > 20:
            pip, vol_pre_airgap = p300, vol_pre_airgap_p300
        else:
            pip, vol_pre_airgap = p20, vol_pre_airgap_p20
        num_trans = math.ceil(
            transfer_vol/(
                pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
        vol_per_trans = round(transfer_vol/num_trans, 2)
        pip.pick_up_tip()
        for n in range(num_trans):
            depth = 0.5 if transfer_vol <= 10 else 3
            pip.aspirate(vol_pre_airgap, well.top())
            pip.aspirate(vol_per_trans, well.bottom(depth))
            slow_withdraw(pip, well)
            if n < num_trans - 1:
                pip.dispense(pip.current_volume, mix_tube.top())
            else:
                pip.dispense(pip.current_volume, mix_tube.bottom(2))
                slow_withdraw(pip, mix_tube)
            slow_withdraw(pip, mix_tube)
        if i == len(mix_map.items()) - 1:
            if not pip == p300:
                pip.drop_tip()
                p300.pick_up_tip()
            p300.mix(5, pip.max_volume*0.8, mix_tube, rate=0.5)
            slow_withdraw(pip, mix_tube)
        [pip.drop_tip() for pip in [p300, p20] if pip.has_tip]

    # water addition
    for vol_water, d in zip(vols_water,
                            aliquot_rack.wells()[:len(template_volumes)]):
        if vol_water > 20:
            pip, vol_pre_airgap = p300, vol_pre_airgap_p300
        else:
            pip, vol_pre_airgap = p20, vol_pre_airgap_p20
        num_trans = math.ceil(
            vol_water/(
                pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
        vol_per_trans = round(vol_water/num_trans, 2)
        if not pip.has_tip:
            pip.pick_up_tip()
        for _ in range(num_trans):
            pip.aspirate(vol_pre_airgap, water.top())
            pip.aspirate(vol_per_trans, water)
            slow_withdraw(pip, water)
            pip.dispense(pip.current_volume, d.bottom(2))
            slow_withdraw(pip, d)
    for pip in [p20, p300]:
        if pip.has_tip:
            pip.drop_tip()

    # mix addition
    vol_mix = sum(mix_volumes)/(num_rxns*factor_overage)
    if vol_mix > 20:
        pip, vol_pre_airgap = p300, vol_pre_airgap_p300
    else:
        pip, vol_pre_airgap = p20, vol_pre_airgap_p20
    num_trans = math.ceil(
        vol_mix/(
            pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
    vol_per_trans = round(vol_mix/num_trans, 2)
    for d in rxns:
        pip.pick_up_tip()
        for _ in range(num_trans):
            pip.aspirate(vol_pre_airgap, mix_tube.top())
            pip.aspirate(vol_per_trans, mix_tube)
            slow_withdraw(pip, mix_tube)
            pip.dispense(pip.current_volume, d.bottom(2))
            slow_withdraw(pip, d)
        pip.drop_tip()

    # DNA template addition
    for (template, vol), d in zip(
            template_map.items(),
            aliquot_rack.wells()[:len(template_volumes)]):
        if vol > 20:
            pip, vol_pre_airgap = p300, vol_pre_airgap_p300
        else:
            pip, vol_pre_airgap = p20, vol_pre_airgap_p20
        num_trans = math.ceil(
            vol/(
                pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
        num_trans = math.ceil(vol/pip.tip_racks[0].wells()[0].max_volume)
        vol_per_trans = round(vol/num_trans, 2)
        pip.pick_up_tip()
        depth = 0.5 if vol_per_trans <= 10 else 3
        for n in range(num_trans):
            pip.aspirate(vol_pre_airgap, template.top())
            pip.aspirate(vol_per_trans, template.bottom(depth))
            slow_withdraw(pip, template)
            pip.dispense(pip.current_volume, d.bottom(3))
            if n == num_trans - 1:
                pip.mix(5, pip.max_volume*0.8, d.bottom(3), rate=0.5)
            slow_withdraw(pip, d)
        pip.drop_tip()

    ctx.pause('Place enzymes in tuberack.')

    # enzyme mix
    for i, (well, transfer_vol) in enumerate(enzyme_map.items()):
        if transfer_vol > 20:
            pip, vol_pre_airgap = p300, vol_pre_airgap_p300
        else:
            pip, vol_pre_airgap = p20, vol_pre_airgap_p20
        num_trans = math.ceil(
            transfer_vol/(
                pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
        vol_per_trans = round(transfer_vol/num_trans, 2)
        pip.pick_up_tip()
        depth = 0.5 if vol_per_trans <= 10 else 3
        for _ in range(num_trans):
            pip.aspirate(vol_pre_airgap, well.top())
            pip.aspirate(vol_per_trans, well.bottom(depth))
            slow_withdraw(pip, well)
            pip.dispense(pip.current_volume, enzyme_mix_tube.bottom(1.5))
            if i == 0:
                wick(pip, enzyme_mix_tube)
            slow_withdraw(pip, enzyme_mix_tube)
        if i == len(enzyme_map.items()) - 1:
            pip.mix(5, sum(enzyme_volumes)*0.8,
                    enzyme_mix_tube.bottom(2), rate=0.5)
            slow_withdraw(pip, enzyme_mix_tube)
        pip.drop_tip()

    # enzyme mix addition
    vol_enzyme_mix = sum(enzyme_volumes)/(num_rxns*factor_overage)
    if vol_enzyme_mix > 20:
        pip, vol_pre_airgap = p300, vol_pre_airgap_p300
    else:
        pip, vol_pre_airgap = p20, vol_pre_airgap_p20
    num_trans = math.ceil(
        vol_enzyme_mix/(
            pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
    vol_per_trans = round(vol_enzyme_mix/num_trans, 2)
    for d in rxns:
        pip.pick_up_tip()
        for _ in range(num_trans):
            pip.aspirate(vol_per_trans, enzyme_mix_tube.bottom(1.5))
            slow_withdraw(pip, enzyme_mix_tube)
            pip.dispense(pip.current_volume, d.bottom(2))
            slow_withdraw(pip, d)
        pip.mix(
            5,
            pip.tip_racks[0].wells()[0].max_volume*0.8,
            d.bottom(2),
            rate=0.5)
        pip.drop_tip()

    ctx.pause('INCUBATION')

    # DN and CaC
    for vol, reagent in zip([vol_dn, vol_cac], [dn, cac]):
        pip = p20 if vol < 20 else p300
        for d in rxns:
            pip.pick_up_tip()
            pip.aspirate(vol, reagent)
            slow_withdraw(pip, reagent)
            pip.dispense(vol, d.bottom(3))
            pip.mix(5, pip.max_volume*0.8, d.bottom(2), rate=5)
            slow_withdraw(pip, d)
            pip.drop_tip()

    ctx.pause('INCUBATION')

    # LiCl and H2O
    if vol_licl_h2o > 20:
        pip, vol_pre_airgap = p300, vol_pre_airgap_p300
    else:
        pip, vol_pre_airgap = p20, vol_pre_airgap_p20
    num_trans = math.ceil(
        vol_licl_h2o/(
            pip.tip_racks[0].wells()[0].max_volume-vol_pre_airgap))
    vol_per_trans = round(vol_licl_h2o/num_trans, 2)
    for d in rxns:
        pip.pick_up_tip()
        for i in range(num_trans):
            pip.aspirate(vol_pre_airgap, licl_h2o.top())
            pip.aspirate(vol_per_trans, licl_h2o)
            slow_withdraw(pip, licl_h2o)
            if i < num_trans - 1:
                pip.dispense(pip.current_volume, d.top(-1))
                pip.blow_out()
                ctx.delay(seconds=2.0)
            else:
                pip.dispense(pip.current_volume, d.bottom(2))
                slow_withdraw(pip, d)
        pip.drop_tip()

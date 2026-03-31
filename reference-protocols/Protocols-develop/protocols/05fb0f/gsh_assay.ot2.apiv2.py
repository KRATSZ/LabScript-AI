import time
import math
from opentrons import protocol_api
from opentrons.types import Point

metadata = {
    'protocolName': 'GSH Assay',
    'author': 'Nick <ndiehl@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.14'
}


def run(ctx):

    [num_samples, temp_set_reservoir, mount_m20,
     mount_m300] = get_values(  # noqa: F821
        'num_samples', 'temp_set_reservoir', 'mount_m20', 'mount_m300')

    # modules
    tempdeck = ctx.load_module('temperatureModuleV2', '9')
    hs = ctx.load_module('heaterShakerModuleV1', '10')

    # labware
    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['1']]
    pcr_plates = [
        ctx.load_labware('framestarpcr_96_wellplate_200ul', slot,
                         f'PCR plate {i+1}')
        for i, slot in enumerate(['2', '3'])
    ]
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['4']]
    reservoir = ctx.load_labware('thermo_1_reservoir_300ul', '6')
    res4 = ctx.load_labware('axygen_4_reservoir_70ul', '8')
    temp_reservoir = tempdeck.load_labware('thermo_1_reservoir_300ul')
    hs_plate = hs.load_labware('tecan_96_wellplate_1300ul')
    # hs_plate = ctx.load_labware('tecan_96_wellplate_1300ul', '10')
    deep_plate = ctx.load_labware('eppendorfdeepwell_96_wellplate_1200ul',
                                  '5')

    num_cols = math.ceil(num_samples/8)

    # liquids
    liq_1 = ctx.define_liquid(
        name='',
        description='',
        display_color='#0000FF')
    liq_2 = ctx.define_liquid(
        name='',
        description='',
        display_color='#00FF00')
    liq_3 = ctx.define_liquid(
        name='',
        description='',
        display_color='#FF0000')
    liq_4 = ctx.define_liquid(
        name='',
        description='',
        display_color='#ff9900')

    res4.wells()[0].load_liquid(liq_1, volume=450*num_samples)
    res4.wells()[1].load_liquid(liq_2, volume=50*num_samples)
    reservoir.wells()[0].load_liquid(liq_3, volume=98)
    temp_reservoir.wells()[0].load_liquid(liq_4, volume=450*num_samples)

    reagent1, reagent2 = res4.wells()[:2]
    reagent3 = reservoir.wells()[0]
    reagent4 = temp_reservoir.wells()[0]

    # pipettes
    m20 = ctx.load_instrument(
        'p20_multi_gen2', mount_m20, tip_racks=tipracks20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount_m300, tip_racks=tipracks300)

    def wick(pip, well, side=1):
        radius = well.diameter/2 if well.diameter else well.width/2
        pip.move_to(well.bottom().move(Point(x=side*radius*0.7, z=3)))

    def slow_withdraw(pip, well, delay_s=2.0):
        pip.default_speed = 25
        if delay_s > 0:
            ctx.delay(seconds=delay_s)
        pip.move_to(well.top())
        pip.default_speed = 400

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    tempdeck.set_temperature(temp_set_reservoir)
    hs.close_labware_latch()

    vol_1 = 450.0
    num_transfers = math.ceil(vol_1/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_transfer = round(vol_1/num_transfers, 2)
    pick_up(m300)
    for d in hs_plate.rows()[0][:num_cols]:
        for _ in range(num_transfers):
            m300.aspirate(vol_per_transfer, reagent1)
            slow_withdraw(m300, reagent1)
            m300.dispense(vol_per_transfer, d.bottom(2))
            slow_withdraw(m300, d)
    m300.drop_tip()

    for s, d in zip(pcr_plates[0].rows()[0][:num_cols],
                    hs_plate.rows()[0][:num_cols]):
        pick_up(m20)
        m20.aspirate(1, s.bottom(1))
        slow_withdraw(m20, s)
        m20.dispense(1, d.bottom(2))
        m20.mix(5, 20, d.bottom(2))
        slow_withdraw(m20, d)
        m20.drop_tip()

    ctx.comment('Preincubation')
    hs.set_and_wait_for_temperature(37)
    hs.set_and_wait_for_shake_speed(1000)
    time_preincubation = 10.0*60  # seconds
    start_time = time.monotonic()

    vol_2 = 98
    pick_up(m300)
    for d in pcr_plates[1].rows()[0][:num_cols]:
        m300.aspirate(vol_2, reagent3)
        slow_withdraw(m300, reagent3)
        m300.dispense(vol_2, d.bottom())
        slow_withdraw(m300, d)

    vol_3 = 380.0
    num_transfers = math.ceil(vol_3/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_transfer = round(vol_3/num_transfers, 2)
    for d in deep_plate.rows()[0][:num_cols]:
        for _ in range(num_transfers):
            m300.aspirate(vol_per_transfer, reagent3)
            slow_withdraw(m300, reagent3)
            m300.dispense(vol_per_transfer, d.bottom(2))
            slow_withdraw(m300, d)
    m300.drop_tip()

    for s, d in zip(pcr_plates[0].rows()[0][:num_cols],
                    pcr_plates[1].rows()[0][:num_cols]):
        pick_up(m20)
        m20.aspirate(2, s.bottom(1))
        slow_withdraw(m20, s)
        m20.dispense(2, d.bottom(2))
        slow_withdraw(m20, d)
        m20.drop_tip()

    ctx.delay(max(0, start_time+time_preincubation - time.monotonic()))

    hs.deactivate_shaker()

    pick_up(m300)
    for d in deep_plate.rows()[0][:num_cols]:
        m300.aspirate(20, reagent2.top())  # pre-airgap
        m300.aspirate(50, reagent2)
        slow_withdraw(m300, reagent2)
        m300.dispense(m300.current_volume, d.top(-1))
        ctx.delay(seconds=1)
    m300.drop_tip()

    hs.set_and_wait_for_shake_speed(1000)
    ctx.delay(minutes=60)
    hs.deactivate_shaker()

    vol_4 = 450.0
    num_transfers = math.ceil(vol_4/m300.tip_racks[0].wells()[0].max_volume-20)
    vol_per_transfer = round(vol_4/num_transfers, 2)
    pick_up(m300)
    for d in hs_plate.rows()[0][:num_cols]:
        for _ in range(num_transfers):
            m300.aspirate(20, reagent4.top())
            m300.aspirate(vol_per_transfer, reagent4)
            slow_withdraw(m300, reagent4)
            m300.dispense(m300.current_volume, d.top(-1))
            slow_withdraw(m300, d)
    m300.drop_tip()

    hs.open_labware_latch()

    ctx.pause('Remove Slot 10) Heater Shaker & Tecan 96 Well Plate 1200 ul \
and centrifuge, and remove Slot 11) Eppendorf 96 DWP 1200ul and seal. Place \
a new Slot 11) Eppendorf 96 DWP 1200ul and place Tecan 96 Well Plate 1200 \
ul back on the Slot 10) Heater Shaker')

    hs.close_labware_latch()

    vol_final = 400.0
    num_transfers = math.ceil(
        vol_final/m300.tip_racks[0].wells()[0].max_volume)
    vol_per_transfer = round(vol_final/num_transfers, 2)
    for s, d in zip(hs_plate.rows()[0][:num_cols],
                    deep_plate.rows()[0][:num_cols]):
        pick_up(m300)
        for _ in range(num_transfers):
            m300.aspirate(vol_per_transfer, s.bottom(1))
            slow_withdraw(m300, s)
            m300.dispense(vol_per_transfer, d.bottom(1))
            slow_withdraw(m300, d)
        m300.drop_tip()

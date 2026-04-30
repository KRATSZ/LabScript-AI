import math
from opentrons.protocol_api.labware import Well

metadata = {
    'protocolName': 'Plate Filling',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, m300_mount, p1000_mount] = get_values(  # noqa: F821
        'num_samples', 'm300_mount', 'p1000_mount')

    vol_wash_buffer_1 = 500
    vol_wash_buffer_2 = 500
    vol_elution_buffer = 100
    vol_air_gap = 20

    # labware

    wash_plates = [
        ctx.load_labware('nest_96_wellplate_2ml_deep', slot,
                         f'wash plate {i+1}')
        for i, slot in enumerate(['1', '2'])]
    elution_plate = ctx.load_labware('kingfisher_96_wellplate_200ul', '3',
                                     'elution plate')
    reservoir = ctx.load_labware('usascientific_12_reservoir_22ml', '4',
                                 'reservoir')
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '5')]
    tiprack1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', '6')]

    # pipettes

    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack200)
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack1000)

    class WellH(Well):
        def __init__(self, well, height=5, min_height=3,
                     comp_coeff=1.15, current_volume=0, min_vol=1000):
            super().__init__(well._impl)
            self.well = well
            self.height = height
            self.min_height = min_height
            self.comp_coeff = comp_coeff
            self.x = self.width
            self.y = self.length
            self.current_volume = current_volume
            self.min_vol = min_vol

        def height_dec(self, vol, num_channels=1):
            vol_actual = vol*num_channels
            dh = (vol_actual/(self.x*self.y))*self.comp_coeff
            if self.height - dh > self.min_height:
                self.height = self.height - dh
            else:
                self.height = self.min_height
            if self.current_volume - vol_actual > 0:
                self.current_volume = self.current_volume - vol_actual
            else:
                self.current_volume = 0
            return(self.well.bottom(self.height))

        def height_inc(self, vol, num_channels=1):
            vol_actual = vol*num_channels
            dh = (vol_actual/(self.x*self.y))*self.comp_coeff
            if self.height + dh < self.depth:
                self.height = self.height + dh
            else:
                self.height = self.depth
            self.current_volume += vol_actual
            return(self.well.bottom(self.height + 20))

    def slow_withdraw(well, pip):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # reagents

    num_cols = math.ceil(num_samples/8)
    wash_buffer_1 = [
        WellH(well, height=2, min_height=2, comp_coeff=1, current_volume=14000,
              min_vol=800)
        for well in reservoir.rows()[0][:4]]
    wash_buffer_2 = [
        WellH(well, height=2, min_height=2, comp_coeff=1, current_volume=14000,
              min_vol=800)
        for well in reservoir.rows()[0][4:8]]
    elution_buffer = reservoir.rows()[0][8]

    iterator_wash_buffer_1 = iter(wash_buffer_1)
    current_wash_buffer_1 = next(iterator_wash_buffer_1)
    iterator_wash_buffer_2 = iter(wash_buffer_2)
    current_wash_buffer_2 = next(iterator_wash_buffer_2)

    def check_wash_1(vol):
        nonlocal current_wash_buffer_1

        if current_wash_buffer_1.current_volume - vol < \
                current_wash_buffer_1.min_vol:
            current_wash_buffer_1 = next(iterator_wash_buffer_1)
        return current_wash_buffer_1

    def check_wash_2(vol):
        nonlocal current_wash_buffer_2

        if current_wash_buffer_2.current_volume - vol < \
                current_wash_buffer_2.min_vol:
            current_wash_buffer_2 = next(iterator_wash_buffer_2)
        return current_wash_buffer_2

    num_wash_buffer_1_transfers = math.ceil(
        vol_wash_buffer_1/(
            m300.tip_racks[0].wells()[0].max_volume-vol_air_gap))
    vol_per_wash_buffer_1_transfer = round(
        vol_wash_buffer_1/num_wash_buffer_1_transfers, 1)
    list_wash_buffer_1_transfers = [
        vol_per_wash_buffer_1_transfer]*num_wash_buffer_1_transfers
    num_wash_buffer_2_transfers = math.ceil(
        vol_wash_buffer_2/(
            m300.tip_racks[0].wells()[0].max_volume-vol_air_gap))
    vol_per_wash_buffer_2_transfer = round(
        vol_wash_buffer_2/num_wash_buffer_2_transfers, 1)
    list_wash_buffer_2_transfers = [
        vol_per_wash_buffer_2_transfer]*num_wash_buffer_2_transfers

    # transfer wash buffers
    for wash_vol_list, current_wash_buffer, check_func, plate in zip(
            [list_wash_buffer_1_transfers, list_wash_buffer_2_transfers],
            [current_wash_buffer_1, current_wash_buffer_2],
            [check_wash_1, check_wash_2],
            wash_plates):
        m300.pick_up_tip()
        for dest in plate.rows()[0][:num_cols]:
            for vol in wash_vol_list:
                current_buffer = check_func(vol*8)
                m300.aspirate(
                    vol,
                    current_buffer.height_dec(vol, num_channels=8))
                slow_withdraw(current_buffer, m300)
                m300.aspirate(vol_air_gap,
                              current_buffer.top())  # air gap
                m300.dispense(m300.current_volume, dest.bottom(2))
                slow_withdraw(dest, m300)
        m300.drop_tip()

    # transfer elution buffer
    num_elution_buffer_aspirations = math.ceil(vol_elution_buffer*num_samples/(
        p1000.tip_racks[0].wells()[0].max_volume))
    dests_per_aspiration = math.ceil(
        num_samples/num_elution_buffer_aspirations)
    elution_dest_sets = [
        elution_plate.wells()[
            i*dests_per_aspiration:(i+1)*dests_per_aspiration]
        if i < num_elution_buffer_aspirations - 1
        else elution_plate.wells()[i*dests_per_aspiration:]
        for i in range(num_elution_buffer_aspirations)
    ]
    p1000.pick_up_tip()
    for dest_set in elution_dest_sets:
        p1000.aspirate(vol_elution_buffer*len(dest_set), elution_buffer)
        slow_withdraw(elution_buffer, p1000)
        for d in dest_set:
            p1000.dispense(vol_elution_buffer, d)
            slow_withdraw(d, p1000)
    p1000.drop_tip()

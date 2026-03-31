from opentrons import protocol_api
from opentrons.protocol_api.labware import Well
from opentrons.types import Point
from typing import List
import math

# metadata
metadata = {
    'protocolName': 'Thermal Proteome Profiling (TPP)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_drug_plates, vol_h_lysate, temp_lysate, mount_m300,
     mount_m20] = get_values(  # noqa: F821
        'num_drug_plates', 'vol_h_lysate', 'temp_lysate', 'mount_m300',
        'mount_m20')

    # modules
    tc = ctx.load_module('thermocycler')
    tempdeck = ctx.load_module('temperature module gen2', '1')
    tempdeck2 = ctx.load_module('temperature module gen2', '9')
    res_h_lysate = tempdeck2.load_labware('nest_12_reservoir_15ml')

    # labware
    tc_plate = tc.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'heating plate')
    drug_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                  '5', 'drug plate')
    filter_plate = ctx.load_labware(
        'pall_96_wellplate_350ul', '4', 'filter plate')
    res_lysate = tempdeck.load_labware(
            'opentrons_96_aluminumblock_nest_wellplate_100ul',
            'lysate reservoir')
    tiprack200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['2', '3']]
    tiprack20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['6']]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', mount_m300,
                               tip_racks=tiprack200)
    m20 = ctx.load_instrument('p20_multi_gen2', mount_m20, tip_racks=tiprack20)

    # reagents and variables
    l_lysate = res_lysate.rows()[0][:6]
    h_lysate = res_h_lysate.rows()[0][:1]

    vol_l_lysate = 70
    reps_mix = 5
    vol_mix = vol_l_lysate*0.8
    vol_filter = 5.15
    hold_time_minutes = 3.0

    # module setup
    tempdeck.set_temperature(temp_lysate)
    tempdeck2.set_temperature(temp_lysate)
    tc.open_lid()
    temp_block_start = 37.0
    temp_lid_start = temp_block_start + 2.0
    temp_block_end = 67.0
    temp_range = temp_block_end - temp_block_start
    num_increments = 12
    d_temp = temp_range/num_increments
    temps_incubation_block = [
        temp_block_start + i*d_temp
        for i in range(num_increments+1)  # inclusive range
    ]
    temps_incubation_lid = [
        temp + 2.0 for temp in temps_incubation_block]
    tc.set_block_temperature(temp_block_start)
    tc.set_lid_temperature(temp_lid_start)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(f'\n\n\n\nReplace \
{pip.tip_racks[0].wells()[0].max_volume}ul tipracks \
(slot \',\'.join{[rack.parent for rack in pip.tip_racks]}) before resuming.')
            pip.reset_tipracks()
            pip.pick_up_tip()

    def wick(pip, well, side=1):
        pip.move_to(well.bottom().move(Point(x=side*well.diameter/2*0.8, z=3)))

    def slow_withdraw(pip, well):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def custom_distribute(pip,
                          vol: float,
                          source: List[Well],
                          destinations: list,
                          pre_airgap_vol: float = 0,
                          destination_height: float = 0.5,
                          wick_after: bool = True,
                          pick_up_tip: bool = True,
                          drop_tip: bool = True) -> None:

        # break up destination based on source length
        dests_per_source = math.ceil(len(destinations)/len(source))
        dest_sets_by_source = [
            destinations[i*dests_per_source:(i+1)*dests_per_source]
            if i < len(source)
            else destinations[i*dests_per_source:]
            for i in range(len(source))
        ]

        vol_available_asp = pip.tip_racks[0].wells()[0].max_volume
        if pick_up_tip and not pip.has_tip:
            pick_up(pip)
        for i, outer_set in enumerate(dest_sets_by_source):
            source_column = source[i]
            if vol < vol_available_asp:
                num_wells_per_asp = int(vol_available_asp // vol)
                num_asp = math.ceil(len(outer_set)/num_wells_per_asp)
                dest_sets = [
                    outer_set[i*num_wells_per_asp:(i+1)*num_wells_per_asp]
                    if i < num_asp - 1
                    else outer_set[i*num_wells_per_asp:]
                    for i in range(num_asp)]
                for dest_set in dest_sets:
                    if pre_airgap_vol > 0:
                        pip.aspirate(pre_airgap_vol, source_column.top())
                    pip.aspirate(vol*len(dest_set), source_column)
                    slow_withdraw(pip, source_column)
                    for d in dest_set:
                        pip.dispense(vol, d.bottom(0.5))
                        if wick_after:
                            wick(pip, d)
            else:  # if volume > what can be accommodated by one aspiration
                num_transfers = math.ceil(vol/vol_available_asp)
                vol_per_transfer = round(vol/num_transfers, 2)
                for d in outer_set:
                    for _ in range(num_transfers):
                        pip.aspirate(vol_per_transfer, source_column)
                        slow_withdraw(pip, source_column)
                        for d in dest_set:
                            pip.dispense(vol_per_transfer, d.bottom(0.5))
                            if wick_after:
                                wick(pip, d)
        if drop_tip:
            pip.drop_tip()

    columns_per_h_lysate = 12//len(h_lysate)
    columns_per_l_lysate = 12//len(l_lysate)
    for drug_plate_ind in range(num_drug_plates):
        for i, (drug_well, heating_well) in enumerate(
                zip(drug_plate.rows()[0], tc_plate.rows()[0])):

            h_lysate_column = h_lysate[i//columns_per_h_lysate]
            l_lysate_column = l_lysate[i//columns_per_l_lysate]

            custom_distribute(m300, vol_h_lysate, [h_lysate_column],
                              filter_plate.rows()[0])

#             ctx.pause('\n\n\n\nRemove filter plate (slot 5) and spin the \
# H lysis into wells filter plate.\n\n\n\n')

            pick_up(m300)
            m300.aspirate(vol_l_lysate, l_lysate_column)
            slow_withdraw(m300, l_lysate_column)
            m300.dispense(vol_l_lysate, drug_well)
            m300.mix(reps_mix, vol_mix, drug_well)
            m300.aspirate(vol_l_lysate, drug_well.bottom(0.2))
            m300.dispense(vol_l_lysate, heating_well)
            slow_withdraw(m300, heating_well)
            m300.drop_tip()

            for temp_block, temp_lid, dest in zip(
                    temps_incubation_block,
                    temps_incubation_lid,
                    filter_plate.rows()[0]):
                tc.close_lid()
                tc.set_lid_temperature(temp_lid)
                tc.set_block_temperature(
                    temp_block, hold_time_minutes=hold_time_minutes)
                tc.open_lid()

                custom_distribute(m20,
                                  vol_filter,
                                  [heating_well],
                                  [dest],
                                  destination_height=0.5,
                                  wick_after=True, pick_up_tip=True,
                                  drop_tip=True)
            tc.set_block_temperature(temp_block_start)
            tc.set_lid_temperature(temp_lid_start)

            msg = f'\n\n\n\nCentrifuge filter plate. Insert a new filter \
plate on slot {filter_plate.parent}.'
            if i == len(drug_plate.rows()[0]) - 1:
                if drug_plate_ind < num_drug_plates - 1:
                    msg += f' Insert new drug pool plate on slot \
{drug_plate.parent} and lysate reservoir on temperature module.\n\n\n\n'
                else:
                    msg += ' Protocol complete.\n\n\n\n'
            else:
                msg += '\n\n\n\n'
            ctx.pause(msg)

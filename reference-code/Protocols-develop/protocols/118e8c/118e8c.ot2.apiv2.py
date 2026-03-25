from opentrons.protocol_api.labware import Well
from opentrons import types
import math
import csv
import os

metadata = {
    'protocolName': 'FluoGene HLA NX 96-Well or 384-Well Setup',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [use_384, p20_blowout_height, disposal_volume, p300_transfer_height,
     dispense_volume, p300_mixing_height,
     p20_tube_height, relative_height, tracking_reset,
     p20_reservoir_height, tip_max, water_volume, fluomix_volume,
     dna_volume, reservoir_fill_volume] = get_values(  # noqa: F821
        "use_384", "p20_blowout_height", "disposal_volume",
        "p300_transfer_height", "dispense_volume", "p300_mixing_height",
        "p20_tube_height", "relative_height", "tracking_reset",
        "p20_reservoir_height", "tip_max", "water_volume", "fluomix_volume",
        "dna_volume", "reservoir_fill_volume")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # constant values
    reduced_pick_up_current = 0.15
    touch_radius = 0.75
    touch_v_offset = -3
    touch_speed = 10

    # constrain reduced_pick_up_current value to acceptable range
    if reduced_pick_up_current < 0.1 or reduced_pick_up_current > 0.15:
        raise Exception('''Invalid value for reduced_pick_up_current parameter
                           (must be between 0.1 and 0.15).''')

    """
    for reservoir column tracking between protocol runs
    """
    # for reservoir column tracking between protocol runs
    # if ctx.is_simulating():    # logic reversed for simulation
    if not ctx.is_simulating():
        file_path = '/data/temporary/columnandtiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial csv
        if (not os.path.isfile(file_path) or tracking_reset):
            with open(file_path, 'w') as outfile:
                outfile.write(",".join([
                 "0", "A1 of Opentrons 96 Filter Tip Rack 20 µL on 10",
                 "A1 of Opentrons 96 Filter Tip Rack 200 µL on 11", "\n"]))

    current_data_list = []
    # if not ctx.is_simulating():    # logic reversed for simulation
    if ctx.is_simulating():
        current_data_list = [0,
                             "A1 of Opentrons 96 Filter Tip Rack 20 µL on 10",
                             "A1 of Opentrons 96 Filter Tip Rack 200 µL on 11"]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            current_data_list = next(csv_reader)

    current_col_index = int(current_data_list[0])
    [current_starting_tip_20, current_starting_tip_300] = [
     current_data_list[i] for i in range(1, 3)]

    if current_col_index == 0:
        ctx.pause("Please place an unused, clean source plate in deck slot 7.")

    # reservoir with column tracking between protocol runs
    reservoir = ctx.load_labware('nunc_96_wellplate_500ul', '7')

    # increment column index for future protocol run
    if current_col_index < len(reservoir.columns()) - 1:
        new_col_index = current_col_index + 1
    else:
        new_col_index = 0
    """
    protocol steps using tracked reservoir column
    """
    # reagent mix in reservoir column tracked across protocol runs
    reservoir_col = reservoir.columns()[current_col_index]
    ctx.set_rail_lights(True)

    # tips and p300 multi
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '11')]
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '10')]
    p300s = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)
    p20m = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)

    # trays
    if not use_384:
        trays = [
         ctx.load_labware(labware, slot) for labware, slot in zip(
          ['innotrainot2pcrplate_96_wellplate_200ul',
           'innotrainot22pcrplate_96_wellplate_200ul'], ['5', '6'])]
    else:
        trays = [ctx.load_labware('custom_384_well_tray', '5')]

    # tube rack rxn components: water in A1, pcr mix in A2, DNA dilution in A3
    tube_rack = ctx.load_labware(
     'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '4')
    [w, p, d] = [
     tube_rack.wells_by_name()[well] for well in ['A1', 'A2', 'A3']]

    class WellH(Well):
        def __init__(self, well, min_height=5, comp_coeff=1.15,
                     current_volume=0):
            super().__init__(well._impl)
            self.well = well
            self.min_height = min_height
            self.comp_coeff = comp_coeff
            self.current_volume = current_volume
            if self.diameter is not None:
                self.radius = self.diameter/2
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            self.height = current_volume/cse
            if self.height < min_height:
                self.height = min_height
            elif self.height > well.parent.highest_z:
                raise Exception("""Specified liquid volume
                can not exceed the height of the labware.""")

        def height_dec(self, vol):
            if self.diameter is not None:
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            dh = (vol/cse)*self.comp_coeff
            if self.height - dh > self.min_height:
                self.height = self.height - dh
            else:
                self.height = self.min_height
            if self.current_volume - vol > 0:
                self.current_volume = self.current_volume - vol
            else:
                self.current_volume = 0
            return(self.well.bottom(self.height))

        def height_inc(self, vol, top=False):
            if self.diameter is not None:
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            ih = (vol/cse)*self.comp_coeff
            if self.height < self.min_height:
                self.height = self.min_height
            if self.height + ih < self.depth:
                self.height = self.height + ih
            else:
                self.height = self.depth
            self.current_volume += vol
            if top is False:
                return(self.well.bottom(self.height))
            else:
                return(self.well.top())

    # to track liquid height
    water = WellH(w, min_height=1, current_volume=water_volume)
    pcr_mix = WellH(p, min_height=1, current_volume=0.9*fluomix_volume)
    dna_dilution = WellH(d, min_height=1, current_volume=dna_volume)

    """
    pick_up() function to use only the rear-most channel of the p20 multi
    """
    num_channels_per_pickup = 1  # (only pickup tips on rear-most channel)
    tips_ordered = [
        tip for rack in tips20
        for row in rack.rows(
        )[len(rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]
        for tip in row]

    tip_count = tips_ordered.index(
     tips20[0].wells_by_name()[
      current_starting_tip_20.split()[0].replace('A', 'H')])

    def pick_up(pip):
        nonlocal tip_count
        pip.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # one-tip transfer water, fluomix to 1st col last well
    p20m.flow_rate.aspirate = 3.8
    p20m.flow_rate.dispense = 3.8

    # capture and report original value for p20m pick_up_current
    default_current = ctx._implementation._hw_manager.hardware.\
        _attached_instruments[p20m._implementation.get_mount()].\
        config.pick_up_current
    ctx.comment("""Tip pick-up current for the p20 multi-channel pipette
    initially configured to {} mAmp.""".format(str(default_current)))

    # temporarily reduce p20m pick_up_current for one-channel tip pickup
    ctx._implementation._hw_manager.hardware._attached_instruments[
     p20m._implementation.get_mount()].update_config_item(
     'pick_up_current', reduced_pick_up_current)
    ctx.comment("""Tip pick-up current configuration for the p20 multi-channel
    pipette temporarily reduced to {} mAmp for one-tip pickup.""".format(
     str(reduced_pick_up_current)))

    # one-tip pickup with p20m
    pick_up(p20m)

    # reset p20m pick_up_current to original value
    ctx._implementation._hw_manager.hardware._attached_instruments[
     p20m._implementation.get_mount()].update_config_item(
     'pick_up_current', default_current)
    ctx.comment("""Tip pick-up current for the p20 multi-channel pipette
    restored to initial value of {} mAmp for standard 8-tip pickup.""".format(
     str(ctx._implementation._hw_manager.hardware._attached_instruments[
      p20m._implementation.get_mount()].config.pick_up_current)))

    # water then fluomix to last well of 1st col each tray
    for reagent in [water, pcr_mix]:
        for tray in trays:
            p20m.aspirate(4, reagent.height_dec(4))
            p20m.dispense(4, reagent.height_inc(4))
            p20m.aspirate(4, reagent.height_dec(4))
            d_height = -3 if use_384 else -11.2
            p20m.dispense(
             4, tray.columns()[0][-1].top(d_height))
            p20m.touch_tip(
             tray.columns()[0][-1], radius=touch_radius,
             v_offset=touch_v_offset, speed=touch_speed)
    p20m.drop_tip()

    # helper function for repeat large vol transfers
    def repeat_max_transfer(current_pipette, remaining, source, dest,
                            flowrate, touch=False):
        while remaining > tip_max:
            current_pipette.aspirate(
             tip_max, source.height_dec(tip_max), rate=flowrate)
            current_pipette.dispense(
             tip_max, dest.height_inc(tip_max), rate=flowrate)
            remaining -= tip_max
            if touch:
                ctx.delay(seconds=0.5)
                current_pipette.blow_out()
                current_pipette.touch_tip(radius=0.75, v_offset=-2, speed=10)
        current_pipette.aspirate(
         remaining, source.height_dec(remaining), rate=flowrate)
        current_pipette.dispense(
         remaining, dest.height_inc(remaining), rate=flowrate)
        if touch:
            ctx.delay(seconds=0.5)
            current_pipette.blow_out()
            current_pipette.touch_tip(radius=0.75, v_offset=-2, speed=10)

    # combine DNA dilution with pcr mix
    p300s.starting_tip = tips300[0].wells_by_name()[
     current_starting_tip_300.split()[0]]
    p300s.pick_up_tip()
    for rep in range(10):
        p300s.aspirate(200, dna_dilution.height_dec(200).move(
         types.Point(x=0, y=0, z=-dna_dilution.height*(relative_height))),
         rate=3.2)
        p300s.dispense(200, dna_dilution.height_inc(200).move(
         types.Point(x=0, y=0, z=-dna_dilution.height*(relative_height))),
         rate=3.2)
    repeat_max_transfer(p300s, dna_volume, dna_dilution, pcr_mix, 0.5)
    for rep in range(20):
        p300s.aspirate(200, pcr_mix.height_dec(200).move(
         types.Point(x=0, y=0, z=-pcr_mix.height*(relative_height))), rate=3.2)
        p300s.dispense(200, pcr_mix.height_inc(200).move(
         types.Point(x=0, y=0, z=-pcr_mix.height*(relative_height))), rate=3.2)

    # reservoir filling
    reservoir_mix = [WellH(well, min_height=3) for well in reservoir_col]
    for well in reservoir_mix:
        for rep in range(2):
            repeat_max_transfer(
             p300s, reservoir_fill_volume / 16, pcr_mix,
             well, 0.5, touch=True)
    p300s.drop_tip()
    if tips300[0].next_tip(1, p300s.starting_tip) is not None:
        future_tip_300 = tips300[0].next_tip(1, p300s.starting_tip)
    else:
        future_tip_300 = "A1 of Opentrons 96 Filter Tip Rack 200 µL on 11"

    # 7-tip transfer 8 ul to wells A1-G1 if 96-well tray
    # 7-tip transfer 8 ul to wells B1, D1, F1, H1, J1, L1, N1 if 384
    p20m.flow_rate.dispense = 22
    p20m.reset_tipracks()
    p20m.starting_tip = tips20[0].wells_by_name()[
     current_starting_tip_20.split()[0]]
    p20m.pick_up_tip()
    for tray in trays:
        p20m.aspirate(dispense_volume, reservoir_mix[0].bottom(
         p20_reservoir_height))
        d_height = -3 if use_384 else -11.2
        d_well = 1 if use_384 else 0
        p20m.dispense(dispense_volume, tray.columns()[0][d_well].top(d_height))
        p20m.touch_tip(
         tray.columns()[0][d_well], radius=touch_radius,
         v_offset=touch_v_offset, speed=touch_speed)
    p20m.drop_tip()

    p20m.pick_up_tip()
    # 8-tip transfer 8 ul to wells A1, C1, E1, G1, I1, K1, M1, O1 if 384
    if use_384:
        for tray in trays:
            p20m.aspirate(dispense_volume, reservoir_mix[0].bottom(
             p20_reservoir_height))
            d_height = -3
            d_well = 0
            p20m.dispense(
             dispense_volume, tray.columns()[0][d_well].top(d_height))
            p20m.touch_tip(
             tray.columns()[0][d_well], radius=touch_radius,
             v_offset=touch_v_offset, speed=touch_speed)

    # 8-tip transfer 8 ul to columns 2-12 of each tray
    for tray in trays:
        for index, column in enumerate(tray.columns()[1:12]):
            if use_384:
                p20m.aspirate(2*dispense_volume + disposal_volume,
                              reservoir_mix[0].bottom(p20_reservoir_height))
            else:
                if not index % 2:
                    if index < len(tray.columns()[1:]) - 1:
                        p20m.aspirate(
                         2*dispense_volume + disposal_volume, reservoir_mix[
                          0].bottom(p20_reservoir_height))
                    else:
                        p20m.aspirate(
                         dispense_volume, reservoir_mix[0].bottom(
                          p20_reservoir_height))
            d_height = -3 if use_384 else -11.2
            p20m.dispense(dispense_volume, column[0].top(d_height))
            p20m.touch_tip(
             column[0], radius=touch_radius,
             v_offset=touch_v_offset, speed=touch_speed)
            if use_384:
                p20m.dispense(dispense_volume, column[1].top(d_height))
                p20m.touch_tip(
                 column[1], radius=touch_radius,
                 v_offset=touch_v_offset, speed=touch_speed)
                p20m.dispense(
                 disposal_volume, reservoir_mix[0].bottom(p20_blowout_height))
            else:
                if index % 2:
                    p20m.dispense(disposal_volume, reservoir_mix[0].bottom(
                     p20_blowout_height))

    p20m.drop_tip()
    if tips20[0].next_tip(8, p20m.starting_tip) is not None:
        future_tip_20 = tips20[0].next_tip(8, p20m.starting_tip)
    else:
        future_tip_20 = "A1 of Opentrons 96 Filter Tip Rack 20 µL on 10"
    """
    for reservoir column tracking between protocol runs
    """
    # write future column and starting tips to csv for next protocol run
    new_data = ",".join([
     str(new_col_index), str(future_tip_20), str(future_tip_300), '\n'])
    # if ctx.is_simulating():    # logic reversed for simulation
    if not ctx.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_data)

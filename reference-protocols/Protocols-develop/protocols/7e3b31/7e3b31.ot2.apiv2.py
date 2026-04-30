import string
import math
from opentrons.protocol_api.labware import OutOfTipsError, Well
# import from python types module
from types import MethodType
# import opentrons.types
from opentrons import types

metadata = {
    'protocolName': '''Illumina TruSeq stranded mRNA Sample Prep,
    LT LS Protocol: part 1 -
    polyA mRNA Isolation and cDNA synthesis''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [count_samples, clearance_reservoir, clearance_striptubes,
     time_engage, time_dry, vol_deadreservoir, vol_deaddeepwell, tip_immersion,
     x_offset_bead_pellet] = get_values(  # noqa: F821
      'count_samples', 'clearance_reservoir',
      'clearance_striptubes', 'time_engage', 'time_dry', 'vol_deadreservoir',
      'vol_deaddeepwell', 'tip_immersion', 'x_offset_bead_pellet')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # temporarily changed for testing with smaller reservoir
    if not 8 <= count_samples <= 16:
        raise Exception('Invalid number of samples (must be 8-48).')

    if not 0.05 <= tip_immersion <= 0.15:
        raise Exception(
         'Degree of tip immersion out of range (must be 0.05-0.15).')

    num_cols = math.ceil(count_samples / 8)

    # tips, p20 multi gen2, p300 multi gen2
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [3]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    tips300 = [
     ctx.load_labware(
      "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [6, 9]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # labware, thermocycler module, magnetic module
    reservoir = ctx.load_labware(
     'nest_12_reservoir_15ml', '2', 'Reservoir')
    reagents = ctx.load_labware(
     'nest500ul_96_reservoir_500ul', '5', 'Reagents')
    samples = ctx.load_labware(
     'biorad_96_wellplate_200ul_pcr', '4', 'RNA Samples')

    cycler = ctx.load_module('thermocycler')
    cycler.open_lid()
    cycler_plate = cycler.load_labware(
     'biorad_96_wellplate_200ul_pcr')
    cycler.set_block_temperature(4)

    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()
    mag_plate = mag.load_labware(
     'biorad_96_wellplate_200ul_pcr', 'Mag Plate')

    """
    module - extension of pipettes, labware and wells *************************
    """

    # extended well class for liquid volume and height tracking
    class WellH(Well):
        def __init__(self, well, min_height=5, comp_coeff=1.15,
                     current_volume=0):
            super().__init__(well._impl)
            self.well = well
            # specified minimum well bottom clearance
            self.min_height = min_height
            self.comp_coeff = comp_coeff
            # specified starting volume in ul
            self.current_volume = current_volume
            # cross sectional area
            if self.diameter is not None:
                self.radius = self.diameter/2
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            else:
                cse = None
            self.cse = cse
            # initial liquid level in mm from start vol
            if cse:
                self.height = (current_volume/cse)
            else:
                raise Exception("""Labware definition must
                supply well radius or well length and width.""")
            if self.height < min_height:
                self.height = min_height
            # elif self.height > well.parent.highest_z:
            #    raise Exception("""Specified liquid volume
            #    can not exceed the height of the labware.""")

        def height_dec(self, vol, ppt, channels=1, bottom=False):
            # decrement height (mm)
            dh = channels*(vol/self.cse)*self.comp_coeff
            # tip immersion (mm) as fraction of tip length
            mm_immersed = tip_immersion*ppt._tip_racks[0].wells()[0].depth
            # decrement til target reaches specified min clearance
            self.height = self.height - dh if (
             (self.height - dh - mm_immersed) > self.min_height
             ) else self.min_height
            self.current_volume = self.current_volume - channels*vol if (
             self.current_volume - channels*vol > 0) else 0
            tip_ht = self.height if bottom is False else bottom
            return(self.well.bottom(tip_ht))

        def height_inc(self, vol, top=False):
            # increment height (mm)
            ih = (vol/self.cse)*self.comp_coeff
            # keep calculated liquid ht between min clearance and well depth
            self.height = self.min_height if (
             self.height < self.min_height
             ) else (self.height + ih) if (
             (self.height + ih) < self.depth
             ) else self.depth
            # increment
            self.current_volume += vol
            if top is False:
                tip_ht = self.height
                return(self.well.bottom(tip_ht))
            else:
                return(self.well.top())

    # additional methods for labware

    def instantiate_wells_h(self, clearance):
        self.wells_h_list = []
        for well in self.wells():
            vol = starting_volume.get(well, 0)
            new = WellH(well, min_height=clearance, current_volume=vol)
            self.wells_h_list.append(new)

    def wells_h(self):
        return self.wells_h_list

    def wells_by_name_h(self):
        return {well.well_name: well for well in self.wells_h_list}

    def rows_by_name_h(self):
        return {
         row: [well for well in self.wells_h_list if well.well_name[0] == row
               ] for row in [*string.ascii_uppercase][:len(self.rows())]}

    def columns_by_name_h(self):
        return {
         column: [well for well in self.wells_h_list if well.well_name[
          1:] == column] for column in [str(num+1) for num in range(
           len(self.columns()))]}

    def columns_h(self):
        return [
         [well for well in self.wells_h_list if well.well_name[1:] == column
          ] for column in [str(num+1) for num in range(len(self.columns()))]]

    def rows_h(self):
        return [
         [well for well in self.wells_h_list if well.well_name[0] == row
          ] for row in [*string.ascii_uppercase][:len(self.rows())]]

    # additional methods for pipettes

    def aspirate_h(self, vol, source, rate=1, channels=1, bottom=False):
        self.aspirate(
         vol, source.height_dec(
          vol, self, channels=channels, bottom=bottom), rate=rate)

    def dispense_h(self, vol, dest, rate=1, top=False):
        self.dispense(vol, dest.height_inc(vol, top=top), rate=rate)

    def pick_up_or_refill(self):
        try:
            self.pick_up_tip()
        except OutOfTipsError:
            self.move_to(ctx.loaded_labwares[4].wells()[0].top().move(
             types.Point(x=0, y=0, z=100)))
            ctx.pause(
             """Please Refill the {} Tip Boxes
                and Empty the Tip Waste.""".format(self))
            self.reset_tipracks()
            self.pick_up_tip()

    def slow_tip_withdrawal(
     self, speed_limit, well_location, to_surface=False):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        previous_limit = None
        if axis in ctx.max_speeds.keys():
            for key, value in ctx.max_speeds.items():
                if key == axis:
                    previous_limit = value
        ctx.max_speeds[axis] = speed_limit
        if to_surface is False:
            self.move_to(well_location.top())
        else:
            if isinstance(well_location, WellH):
                self.move_to(well_location.bottom().move(types.Point(
                 x=0, y=0, z=well_location.height+(20*(self._tip_racks[
                  0].wells()[0].depth / 88)))))
            else:
                self.move_to(well_location.center())
        ctx.max_speeds[axis] = previous_limit

    def delay(self, delay_time):
        ctx.delay(seconds=delay_time)

    def blow_out_solvent(self, well_location, reps=1, touch=False):
        for rep in range(reps):
            if rep > 0:
                self.aspirate(self.max_volume, well_location.top())
            self.delay(0.5)
            self.blow_out(well_location.top())
        if touch is True:
            self.touch_tip(radius=0.75, v_offset=-2, speed=20)

    """
    end module - extended pipettes, labware, wells ***********************
    """

    for labware_object in [reservoir, reagents, cycler_plate, mag_plate]:
        for method in [instantiate_wells_h, wells_h, columns_h, rows_h,
                       wells_by_name_h, columns_by_name_h, rows_by_name_h]:
            setattr(
             labware_object, method.__name__,
             MethodType(method, labware_object))

    for pipette_object in [p20m, p300m]:
        for method in [aspirate_h, dispense_h, pick_up_or_refill, delay,
                       slow_tip_withdrawal, blow_out_solvent]:
            setattr(
              pipette_object, method.__name__,
              MethodType(method, pipette_object))

    # reagents
    starting_volume = {
        reservoir.wells()[0]: vol_deadreservoir + count_samples*400,
        reservoir.wells()[4]: vol_deadreservoir + count_samples*400,
        reagents.wells()[0]: vol_deaddeepwell + 1.1*num_cols*50,
        reagents.wells()[8]: vol_deaddeepwell + 1.1*num_cols*50,
        reagents.wells()[16]: vol_deaddeepwell + 1.1*num_cols*50,
        reagents.wells()[24]: vol_deaddeepwell + 1.1*num_cols*20,
        reagents.wells()[32]: vol_deaddeepwell + 1.1*num_cols*8,
        reagents.wells()[40]: vol_deaddeepwell + 1.1*num_cols*5,
        reagents.wells()[48]: vol_deaddeepwell + 1.1*num_cols*20,
        reagents.wells()[56]: vol_deaddeepwell + 1.1*num_cols*45,
        reagents.wells()[64]: vol_deaddeepwell + 1.1*num_cols*45,
        reagents.wells()[72]: vol_deaddeepwell + 1.1*num_cols*18
        }

    for column in cycler_plate.columns()[:num_cols]:
        starting_volume[column[0]] = 50

    for labware, clearance in zip(
     [reservoir, reagents, cycler_plate, mag_plate],
     [clearance_reservoir, clearance_striptubes, 1, 1]):
        labware.instantiate_wells_h(clearance)

    beadwash = reservoir.wells_h()[0]
    etoh = reservoir.wells_h()[4]
    beads_dt = reagents.wells_h()[0]
    elutionbf = reagents.wells_h()[8]
    beadbindingbf = reagents.wells_h()[16]
    fragmentprimefinish = reagents.wells_h()[24]
    firststrand = reagents.wells_h()[32]
    endrepairctrl = reagents.wells_h()[40]
    secondstrandmark = reagents.wells_h()[48]
    beads_xp1 = reagents.wells_h()[56]
    beads_xp2 = reagents.wells_h()[64]
    resuspensionbf = reagents.wells_h()[72]

    for reagent, name in zip(
     [beadwash, etoh],
     ['beadwash', 'etoh']):
        ctx.pause(""" Fill {} with {} mL of {} """.format(
         reagent, str(reagent.current_volume / 1000), name))

    for reagent, name in zip(
     [beads_dt, elutionbf, beadbindingbf, fragmentprimefinish, firststrand,
      endrepairctrl, secondstrandmark, beads_xp1, beads_xp2, resuspensionbf],
     ['beads_dt', 'elutionbf', 'beadbindingbf', 'fragmentprimefinish',
      'firststrand', 'endrepairctrl', 'secondstrandmark', 'beads_xp1',
      'beads_xp2', 'resuspensionbf']):
        ctx.pause(
         """ Fill all wells of column {} with {} uL of {} """.format(
          reagent, str(round(reagent.current_volume, 1)), name))

    # cycler profiles
    mrna_denaturation = [{
     'temperature': temp, 'hold_time_seconds': sec
     } for temp, sec in zip([65, 4, 22], [300, 30, 300])]

    mrna_elution_1 = [{
     'temperature': temp, 'hold_time_seconds': sec
     } for temp, sec in zip([80, 25], [120, 30])]

    elution_2_frag_prime = [{
     'temperature': temp, 'hold_time_seconds': sec
     } for temp, sec in zip([94, 4], [480, 30])]

    synthesize_1st_strand = [{
     'temperature': temp, 'hold_time_seconds': sec
     } for temp, sec in zip([25, 42, 70, 4], [600, 900, 900, 30])]

    synthesize_2nd_strand = [{
     'temperature': temp, 'hold_time_minutes': minutes
     } for temp, minutes in zip([16], [60])]

    ctx.comment("STEP - Make RBP")

    # 50 uL RNA samples
    cycler_plate_cols = cycler_plate.columns_h()[:num_cols]

    # add oligo dT beads
    for reagent, name in zip([beads_dt], ['beads_dt']):
        ctx.pause(
         """ Fill all wells of column {} with {} uL of {} """.format(
          reagent, str(round(reagent.current_volume, 1)), name))

    for column in cycler_plate_cols:
        p300m.pick_up_tip()
        p300m.aspirate_h(50, beads_dt, rate=0.6)
        p300m.delay(1)
        p300m.slow_tip_withdrawal(10, beads_dt)
        p300m.dispense_h(50, column[0], rate=0.6)
        for mix in range(6):
            p300m.aspirate_h(100, column[0], rate=0.6)
            p300m.dispense_h(100, column[0], rate=0.6)
        p300m.delay(1)
        p300m.slow_tip_withdrawal(10, column[0])
        p300m.drop_tip()

    ctx.comment("STEP - Incubate 1 RBP")

    ctx.pause("Seal the cycler plate for step - Incubate 1 RBP")

    cycler.set_lid_temperature(65)
    cycler.close_lid()
    cycler.execute_profile(
     steps=mrna_denaturation, repetitions=1, block_max_volume=100)
    cycler.open_lid()
    cycler.deactivate_lid()
    cycler.set_block_temperature(4)

    ctx.pause(
     "Unseal the cycler plate and place it on the magnetic module.")

    ctx.comment("STEP - Wash RBP")

    # remove sup
    def remove_sup(pip, vol_sup):
        pip.pick_up_or_refill()
        # offset to left to avoid beads (odd col numbers)
        if index % 2 != 1:
            f = -1
        # offset to right to avoid beads (even col numbers)
        else:
            f = 1
        pip.aspirate(vol_sup, column[0].bottom(4), rate=0.3)
        pip.aspirate(vol_sup, column[0].bottom(1).move(
         types.Point(x=f*x_offset_bead_pellet, y=0, z=0)), rate=0.3)
        column[0].current_volume = 0
        column[0].height = column[0].min_height

    mag_plate_cols = mag_plate.columns_h()[:num_cols]
    mag.engage()
    ctx.delay(minutes=time_engage)
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p300m, 90)
        p300m.air_gap(20)
        p300m.drop_tip()

    # add bead wash
    def add_reagent(pip, vol_reagent, name_reagent, count_mix):
        pip.pick_up_or_refill()
        pip.aspirate_h(vol_reagent, name_reagent)
        pip.dispense_h(vol_reagent, column[0])
        vol_total = column[0].current_volume
        vol_tipmax = pip._tip_racks[0].wells()[0].max_volume
        vol_mix = vol_total if vol_total <= vol_tipmax else vol_tipmax
        for mix in range(count_mix):
            pip.aspirate_h(vol_mix, column[0], rate=0.6)
            pip.dispense_h(vol_mix, column[0], rate=0.6)
        pip.drop_tip()

    mag.disengage()
    for column in mag_plate_cols:
        p300m.pick_up_or_refill()
        p300m.aspirate_h(200, beadwash, channels=8)
        p300m.dispense_h(200, column[0])
        vol_total = column[0].current_volume
        vol_tipmax = p300m._tip_racks[0].wells()[0].max_volume
        vol_mix = vol_total if vol_total <= vol_tipmax else vol_tipmax
        for mix in range(2):
            p300m.aspirate_h(vol_mix, column[0], rate=0.6)
            p300m.dispense_h(vol_mix, column[0], rate=0.6)
        p300m.drop_tip()

    # remove sup
    mag.engage()
    ctx.delay(minutes=time_engage)
    waste = reservoir.wells()[-2]
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p300m, 100)
        p300m.dispense(200, waste.top(-3))
        p300m.blow_out()
        p300m.air_gap(20)
        p300m.drop_tip()

    # add elution buffer
    mag.disengage()
    for column in mag_plate_cols:
        add_reagent(p300m, 50, elutionbf, 6)

    ctx.comment("STEP - Incubate 2 RBP")

    # mRNA elution 1
    ctx.pause(
     """Seal the mag plate for step - Incubate 2 RBP.
    Place it on the cycler. Resume.""")

    cycler.set_lid_temperature(80)
    cycler.close_lid()
    cycler.execute_profile(
     steps=mrna_elution_1, repetitions=1, block_max_volume=50)
    cycler.open_lid()
    cycler.deactivate_lid()
    cycler.set_block_temperature(4)

    ctx.pause(
     "Unseal the cycler plate and place it on the magnetic module. Resume.")

    ctx.comment("STEP - Make RFP")

    # add bead binding buffer
    for column in mag_plate_cols:
        add_reagent(p300m, 50, beadbindingbf, 6)

    # bind mRNA
    ctx.delay(minutes=5)

    # remove sup
    mag.engage()
    ctx.delay(minutes=time_engage)
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p300m, 75)
        p300m.air_gap(20)
        p300m.drop_tip()

    # add beadwash
    mag.disengage()
    for column in mag_plate_cols:
        p300m.pick_up_or_refill()
        p300m.aspirate_h(200, beadwash, channels=8)
        p300m.dispense_h(200, column[0])
        vol_total = column[0].current_volume
        vol_tipmax = p300m._tip_racks[0].wells()[0].max_volume
        vol_mix = vol_total if vol_total <= vol_tipmax else vol_tipmax
        for mix in range(2):
            p300m.aspirate_h(vol_mix, column[0], rate=0.6)
            p300m.dispense_h(vol_mix, column[0], rate=0.6)
        p300m.drop_tip()

    # remove sup
    mag.engage()
    ctx.delay(minutes=time_engage)
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p300m, 100)
        p300m.dispense(200, waste.top(-3))
        p300m.blow_out()
        p300m.air_gap(20)
        p300m.drop_tip()

    # add fragment prime finish
    mag.disengage()
    for column in mag_plate_cols:
        add_reagent(p20m, 19.4, fragmentprimefinish, 6)

    ctx.comment("STEP - Incubate RFP")

    # elution 2, fragmentation, random priming
    ctx.pause(
     """Seal the mag plate for step - Incubate RFP.
    Place it on the cycler. Resume.""")

    cycler.set_lid_temperature(94)
    cycler.close_lid()
    cycler.execute_profile(
     steps=elution_2_frag_prime, repetitions=1, block_max_volume=10)
    cycler.open_lid()
    cycler.deactivate_lid()
    cycler.set_block_temperature(4)
    ctx.pause(
     """Unseal the cycler plate and place it on the magnetic module.
    Place a fresh PCR plate on the cycler block.""")
    cycler.set_block_temperature(20)

    def reset(cols, vol, height):
        for column in cols:
            for well in column:
                well.current_volume = vol
                well.height = height

    reset(cycler_plate_cols, 0, cycler_plate.wells_h()[0].min_height)

    ctx.comment("STEP - First Strand cDNA Synthesis")

    # transfer sup to new plate on cycler
    mag.engage()
    ctx.delay(minutes=time_engage)
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p20m, 10)
        p20m.dispense_h(20, cycler_plate.columns_h()[index][0])
        p20m.drop_tip()

    # add first strand synthesis Act D mix + superscript
    for column in cycler_plate_cols:
        add_reagent(p20m, 8, firststrand, 2)

    # first strand synthesis
    ctx.pause(
     "Seal the cycler plate for step - First Strand Synthesis. Resume.")

    cycler.set_lid_temperature(70)
    cycler.close_lid()
    cycler.execute_profile(
     steps=synthesize_1st_strand, repetitions=1, block_max_volume=25)
    cycler.open_lid()
    cycler.deactivate_lid()
    cycler.set_block_temperature(4)
    ctx.pause("Unseal the cycler plate. Resume.")

    ctx.comment("STEP - Second Strand cDNA Synthesis")

    # add end repair control and second strand marking master mix
    for column in cycler_plate_cols:
        add_reagent(p20m, 5, endrepairctrl, 0)

    for column in cycler_plate_cols:
        add_reagent(p20m, 20, secondstrandmark, 6)

    ctx.comment("STEP - Incubate 2 CDP")

    # second strand synthesis
    ctx.pause("Seal the cycler plate for step - Incubate 2 CDP. Resume.")

    cycler.set_lid_temperature(37)
    cycler.close_lid()
    cycler.execute_profile(
     steps=synthesize_2nd_strand, repetitions=1, block_max_volume=50)
    cycler.open_lid()
    cycler.deactivate_lid()

    ctx.pause(
     "Unseal the cycler plate and move it to the magnetic module. Resume.")
    cycler.set_block_temperature(4)

    ctx.comment("STEP - Purify CDP")

    reset(mag_plate_cols, 25, 1.8)

    # add AMPure XP beads
    for column in mag_plate_cols[:3]:
        add_reagent(p300m, 90, beads_xp1, 10)

    if len(mag_plate_cols) > 3:
        for column in mag_plate_cols[3:]:
            add_reagent(p300m, 90, beads_xp2, 10)

    ctx.delay(minutes=15)
    mag.engage()
    ctx.delay(minutes=time_engage)

    # remove sup
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p300m, 90)
        p300m.air_gap(20)
        p300m.dispense(200, waste.top(-3))
        p300m.air_gap(20)
        p300m.drop_tip()

    # wash with 80% etoh
    for rep in range(2):
        p300m.pick_up_or_refill()
        for column in mag_plate_cols:
            p300m.aspirate_h(180, etoh, channels=8)
            p300m.air_gap(20)
            p300m.dispense(200, column[0].top())
            p300m.blow_out_solvent(column[0])
        p300m.drop_tip()

        for index, column in enumerate(mag_plate_cols):
            remove_sup(p300m, 90)
            p300m.air_gap(20)
            p300m.dispense(200, waste.top(-3))
            p300m.blow_out_solvent(waste)
            p300m.air_gap(20)
            p300m.drop_tip()

    # dry beads
    ctx.delay(minutes=time_dry)

    mag.disengage()

    # add resuspension buffer
    for column in mag_plate_cols:
        add_reagent(p20m, 17.5, resuspensionbf, 10)

    ctx.delay(minutes=2)
    mag.engage()
    ctx.delay(minutes=time_engage)

    ctx.pause(
     "Place a fresh PCR plate (for output ds cDNA) in deck slot 4. Resume.")

    # transfer ds cDNA to new PCR plate
    for index, column in enumerate(mag_plate_cols):
        remove_sup(p20m, 10)
        p20m.dispense(20, samples.columns()[index][0])
        p20m.drop_tip()

    ctx.pause(
     """part 1 protocol steps are complete. Seal and store
     output double-stranded cDNA plate (deck slot 4) at -20 C up to 7 days.""")

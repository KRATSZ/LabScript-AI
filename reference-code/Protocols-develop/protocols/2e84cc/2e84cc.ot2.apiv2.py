metadata = {
    'apiLevel': '2.5',
    'protocolName': 'TG Nextera XT index kit v2 Set A to D',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Custom Protocol Request'
}


def run(ctx):
    sample_count = get_values(  # noqa: F821
            'sample_count')[0]

    thermocycler = ctx.load_module('thermocycler')
    thermocycler.open_lid()
    thermocycler_plate = thermocycler.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')

    temp_deck = ctx.load_module(
        'temperature module gen2',
        '1')
    temp_rack = temp_deck.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap')
    temp_deck.set_temperature(4)
    phusion_mm = temp_rack.wells_by_name()["A1"]
    kapa_mm = temp_rack.wells_by_name()["B1"]
    north_indexing_primers = [
        temp_rack.wells_by_name()[x] for x in [
            "{}{}".format(
                b, a) for a in [
                "2", "3"] for b in [
                    "A", "B", "C", "D"]]]
    south_indexing_primers = [
        temp_rack.wells_by_name()[x] for x in [
            "{}{}".format(
                b, a) for a in [
                "4", "5", "6"] for b in [
                    "A", "B", "C", "D"]]]

    mag_deck = ctx.load_module('magnetic module gen2', '4')
    mag_deck.disengage()
    mag_plate = mag_deck.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')

    DNA_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '2')

    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5')
    beads = reservoir.wells_by_name()["A1"]
    h2o = reservoir.wells_by_name()["A2"]

    etoh_list = [reservoir.wells_by_name()[x]
                 for x in ["A3", "A4", "A5", "A6"]]
    liquid_trash_list = [reservoir.wells_by_name()[x]
                         for x in ["A7", "A8", "A9", "A10", "A11"]]

    p20s = ctx.load_instrument(
        "p20_single_gen2", "right", tip_racks=[
            ctx.load_labware(
                "opentrons_96_filtertiprack_20ul", "3")])
    p300s = ctx.load_instrument(
        "p300_single_gen2",
        "left",
        tip_racks=[
            ctx.load_labware(
                "opentrons_96_filtertiprack_200ul",
                x) for x in [
                "6",
                "9"]])

    dna_wells = DNA_plate.wells()[:sample_count]
    mag_wells = mag_plate.wells()[:sample_count]
    thermo_wells = thermocycler_plate.wells()[:sample_count]

    # Ethanol and Liquid trash simulation
    class ReservoirMaterial():
        def __init__(self, lanes):
            self.lanes = lanes
        liquid_taken = 0
        depth_per_lane = 14800
        current_lane = 0

        def get_lane(self, liquid_quantity):
            if liquid_quantity + self.liquid_taken > self.depth_per_lane:
                self.current_lane += 1
                self.liquid_taken = 0
            self.liquid_taken += liquid_quantity
            return self.lanes[self.current_lane]

    etoh = ReservoirMaterial(etoh_list)
    liquid_trash = ReservoirMaterial(liquid_trash_list)

    # Tip simulation function
    class TipCounter():
        def __init__(self, pipette, tip_kind):
            self.pipette = pipette
            self.tip_kind = tip_kind
        i = 0

        def get_tip(self, quantity=sample_count):
            if self.i + quantity > 96:
                ctx.pause("Replace {} tip boxes".format(self.tip_kind))
                self.pipette.reset_tipracks()
            else:
                self.i += quantity

    c20 = TipCounter(p20s, "20ul")
    c300 = TipCounter(p300s, "200ul")

    # Genomic DNA amplification

    c300.get_tip()
    p300s.transfer(
        21,
        phusion_mm,
        thermocycler_plate.wells()[
            :sample_count],
        new_tip='once')
    c20.get_tip()
    p20s.transfer(2, dna_wells, thermo_wells, new_tip='always')
    ctx.pause("Switch DNA plate out with Primer plate")
    c20.get_tip()
    p20s.transfer(2, dna_wells, thermo_wells, new_tip='always')

    def stp(temp, hold):
        return {"temperature": temp, "hold_time_seconds": hold}
    steps = []
    steps.append(stp(98, 300))
    steps += [item for sublist in [[stp(98, 10), stp(69 - x, 10), stp(72, 30)]
                                   for x in range(0, 10)] for item in sublist]
    steps += [item for sublist in [[stp(98, 10), stp(72, 30)]
                                   for _ in range(0, 25)] for item in sublist]
    steps.append(stp(72, 420))
    steps.append(stp(10, 10))

    thermocycler.close_lid()
    thermocycler.set_lid_temperature(99)
    thermocycler.execute_profile(
        steps=steps,
        repetitions=1, block_max_volume=25)
    thermocycler.open_lid()

    ctx.pause("""Move thermocycler plate to magdeck.
    Replace DNA plate with indexing plate I.
    Replace thermocycler plate with reaction plate C""")

    # PCR amplicons beads clean
    def wash():
        c300.get_tip()
        p300s.transfer(
            45, beads, mag_wells, mix_before=(
                5, 100), mix_after=(
                15, 50), new_tip='always')
        ctx.delay(300)
        mag_deck.engage()
        ctx.delay(600)

        # Wash start
        c300.get_tip()
        p300s.transfer(
            200,
            mag_wells,
            liquid_trash.get_lane(200),
            new_tip='always')
        for _ in range(0, 2):
            # Protocol from customer did not include a sample resuspension
            # or a step for removing EtOH. I am doing what I assume it meant.
            for mag_well in mag_wells:
                p300s.pick_up_tip()
                c300.get_tip(quantity=1)
                p300s.transfer(
                    150,
                    etoh.get_lane(150),
                    mag_well,
                    new_tip='never')
                p300s.transfer(
                    150,
                    mag_well,
                    liquid_trash.get_lane(150),
                    new_tip='never')
                p300s.drop_tip()
        c20.get_tip()
        p20s.transfer(
            10,
            mag_wells,
            liquid_trash.get_lane(10),
            new_tip='always')

        ctx.delay(360)
        mag_deck.disengage()

        c300.get_tip()
        p300s.transfer(
            40, h2o, mag_wells, mix_after=(
                20, 30), new_tip='always')
        ctx.delay(120)
        mag_deck.engage()
        ctx.delay(180)
        c300.get_tip()
        p300s.transfer(36, mag_wells, dna_wells)
    wash()

    # Library indexing PCR KAPA
    c20.get_tip()
    p20s.transfer(17.5, kapa_mm, thermo_wells)
    c20.get_tip()
    p20s.transfer(2.5, dna_wells, thermo_wells)

    # transfer north index
    for col in thermocycler_plate.columns():
        for i, well in enumerate(col):
            if well in thermo_wells:
                c20.get_tip(1)
                p20s.transfer(
                    2.5,
                    north_indexing_primers[i],
                    well,
                    new_tip='always')
    # transfer south index
    for row in thermocycler_plate.rows():
        for i, well in enumerate(row):
            if well in thermo_wells:
                c20.get_tip(1)
                p20s.transfer(
                    2.5,
                    south_indexing_primers[i],
                    well,
                    new_tip='always')

    steps = []
    steps.append(stp(95, 30))
    steps += [item for sublist in [[stp(95, 10), stp(55, 30), stp(72, 30)]
                                   for _ in range(0, 12)] for item in sublist]
    steps.append(stp(72, 300))
    steps.append(stp(4, 10))

    thermocycler.close_lid()
    thermocycler.set_lid_temperature(99)
    thermocycler.execute_profile(
        steps=steps,
        repetitions=1, block_max_volume=25)

    thermocycler.open_lid()
    ctx.pause(
        """Move thermocycler plate to magdeck.
        Replace indexing I plate with output plate.""")

    # Index library beads clean
    wash()

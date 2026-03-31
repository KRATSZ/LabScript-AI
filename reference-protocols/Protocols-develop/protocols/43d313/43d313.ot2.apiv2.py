import math

metadata = {
    'protocolName': '''ArcBio RNA Workflow Continuous:
    Pre-PCR Instrument: Part-1: DNase Digestion''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [count_samples, clearance_twintec] = get_values(  # noqa: F821
      'count_samples', 'clearance_twintec')

    ctx.delay(seconds=10)
    ctx.set_rail_lights(True)

    if not 1 <= count_samples <= 96:
        raise Exception('Invalid sample count (must be 1-96).')

    num_cols = math.ceil(count_samples / 8)

    # helper functions

    # pause, flash lights, notify user
    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=3)
        ctx.set_rail_lights(True)
        ctx.delay(seconds=3)
        ctx.set_rail_lights(False)
        ctx.pause(message)

    # set liquid volume in a well
    def liq_volume(wells, vol):
        for well in wells:
            well.liq_vol = vol

    # return liquid height in a well
    def liq_height(well):
        if well.diameter is not None:
            radius = well.diameter / 2
            cse = math.pi*(radius**2)
        elif well.length is not None:
            cse = well.length*well.width
        else:
            cse = None
        if cse:
            return well.liq_vol / cse
        else:
            raise Exception("""Labware definition must
                supply well radius or well length and width.""")

    # tips, p300 multi
    tips300 = [
     ctx.load_labware(
      "opentrons_96_filtertiprack_200ul", str(slot)) for slot in [7, 8, 9]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # reagents block for DNase Master Mix
    reagents = ctx.load_labware(
     'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '2', 'Reagents')
    dnase_mm = [column[0] for column in reagents.columns()][:2]
    liq_volume(dnase_mm, 138)

    # input samples
    temp = ctx.load_module('temperature module gen2', '3')
    sampleplate200 = temp.load_labware(
     'eppendorftwin.tec96_96_aluminumblock_200ul', "Sample Plate at 4 Degrees")
    samples = [column[0] for column in sampleplate200.columns()[:num_cols]]
    liq_volume(samples, 60)
    temp.set_temperature(4)

    # magnetic module
    mag = ctx.load_module('magnetic module gen2', '1')
    mag.disengage()

    ctx.comment("STEP - DNAse Digestion")

    def mm_strips():
        yield from dnase_mm

    mm = mm_strips()
    source = next(mm)

    for sample in samples:
        p300m.pick_up_tip()
        if source.liq_vol <= 18:
            source = next(mm)
        source.liq_vol -= 20
        tipheight = liq_height(source) - 3 if liq_height(source) - 3 > 1 else 1
        p300m.aspirate(20, source.bottom(tipheight), rate=0.5)
        ctx.delay(seconds=1)
        p300m.dispense(20, sample.bottom(clearance_twintec))
        sample.liq_vol += 20
        p300m.mix(10, 0.8*sample.liq_vol, rate=0.5)
        p300m.drop_tip()

    pause_attention(
     """DNase Digestion protocol complete. Proceed to off deck thermocycler
     steps, then the cDNA Synthesis protocol.""")

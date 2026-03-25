"""OPENTRONS."""
import math


metadata = {
    'protocolName': '384 Sample Protocol',
    'author': 'Trevor Ray <trevor.ray@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    # [p300_mount] = get_values(  # noqa: F821
    #     "p300_mount")

    # FLEXIBLE VARIABLES
    num_samples = 96
    # num_plates = 4
    # total_samples = num_plates*num_samples
    z_chloroform_d = -8
    z_chloroform_m = -5
    z_isp_a = -11
    z_isp_ma = -14
    z_isp_c = -5
    trash = ctx.fixed_trash['A1'].top(z=-10)
    Tubes = '3axygen96wellminitubesystemcorning_96_wellplate_1320ul'

    # Load Labware
    tiprack300 = ctx.load_labware('opentrons_96_tiprack_300ul', '9')
    reservoir = ctx.load_labware('nest_1_reservoir_195ml', '6')
    cleaning = ctx.load_labware('nest_1_reservoir_195ml', '3')
    sample_plate_1 = ctx.load_labware(Tubes, '1')
    sample_plate_2 = ctx.load_labware(Tubes, '4')
    sample_plate_3 = ctx.load_labware(Tubes, '7')
    sample_plate_4 = ctx.load_labware(Tubes, '10')
    final_plate_1 = ctx.load_labware(Tubes, '2')
    final_plate_2 = ctx.load_labware(Tubes, '5')
    final_plate_3 = ctx.load_labware(Tubes, '8')
    final_plate_4 = ctx.load_labware(Tubes, '11')

    # define all custom variables above here with descriptions:
    num_columns = math.ceil(num_samples/8)

    # Load Modules

    # Load Instrument
    p300 = ctx.load_instrument('p300_multi_gen2', 'left',
                               tip_racks=[tiprack300])

    # setup
    samples_1 = sample_plate_1.rows()[0][:num_columns]
    samples_2 = sample_plate_2.rows()[0][:num_columns]
    samples_3 = sample_plate_3.rows()[0][:num_columns]
    samples_4 = sample_plate_4.rows()[0][:num_columns]
    final_1 = final_plate_1.rows()[0][:num_columns]
    final_2 = final_plate_2.rows()[0][:num_columns]
    final_3 = final_plate_3.rows()[0][:num_columns]
    final_4 = final_plate_4.rows()[0][:num_columns]
    res = reservoir.wells()[0]
    clean = cleaning.wells()[0]

    ctx.comment('\n~~~~~~~~~~~~~~ADDING Lysis TO SAMPLES~~~~~~~~~~~~~~\n')

    # Dispense Lysis Buffer to all Samples
    def lysis_dispense():
        p300.pick_up_tip()
        for d in samples_1:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        for d in samples_2:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        for d in samples_3:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        for d in samples_4:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        p300.drop_tip()
    lysis_dispense()

    ctx.pause('''
                Remove Lysis Buffer and replace with Chloroform on site 6
                 ''')

    ctx.comment('\n~~~~~~~~~~~~~~ADDING Chloroform TO SAMPLES~~~~~~~~~~~~~~\n')

    # Dispense Chloroform to all samples
    def chloroform_dispense_1():
        p300.pick_up_tip()
        for d in samples_1:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        for d in samples_2:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        for d in samples_3:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        for d in samples_4:
            p300.aspirate(200, res)
            p300.dispense(200, d.top())
        p300.drop_tip()
    chloroform_dispense_1()

    def tip_wash():
        p300.pick_up_tip()
        for d in samples_1:
            p300.aspirate(200, res)
            p300.dispense(200, d.bottom(z=z_chloroform_d))
            p300.mix(40, 190)
            p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        for d in samples_2:
            p300.aspirate(200, res)
            p300.dispense(200, d.bottom(z=z_chloroform_d))
            p300.mix(40, 190)
            p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        for d in samples_3:
            p300.aspirate(200, res)
            p300.dispense(200, d.bottom(z=z_chloroform_d))
            p300.mix(40, 190)
            p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        for i, d in enumerate(samples_4):
            p300.aspirate(200, res)
            p300.dispense(200, d.bottom(z=z_chloroform_d))
            p300.mix(40, 190)
            if i < 11:
                p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        p300.drop_tip()
    tip_wash()

    ctx.pause('''
                Remove Chloroform and replace with Isopropanol on site 6
                 ''')

    ctx.comment('\n~~~~~~~~~~~~~~ADDING Isopropanol TO FINAL~~~~~~~~~~~~~~\n')

    def isopropanol_addition():
        p300.pick_up_tip()
        p300.mix(4, 200, res.bottom(z=4))
        for d in final_1:
            p300.aspirate(200, res)
            p300.air_gap(4)
            p300.dispense(200, d.top())
            p300.blow_out(d.top())
        for d in final_2:
            p300.aspirate(200, res)
            p300.air_gap(4)
            p300.dispense(200, d.top())
            p300.blow_out(d.top())
        for d in final_3:
            p300.aspirate(200, res)
            p300.air_gap(4)
            p300.dispense(200, d.top())
            p300.blow_out(d.top())
        for d in final_4:
            p300.aspirate(200, res)
            p300.air_gap(4)
            p300.dispense(200, d.top())
            p300.blow_out(d.top())
        p300.drop_tip()
    isopropanol_addition()

    ctx.comment('\n~~~~~~~~~~~~~~ADDING Supernatent TO FINAL~~~~~~~~~~~~~~\n')

    def supernatent_addition():
        p300.pick_up_tip()
        for s, d in zip(samples_1, final_1):
            p300.aspirate(200, s)
            p300.dispense(200, d.bottom(z=z_isp_a))
            p300.mix(20, 200, d.bottom(z=z_isp_ma))
            p300.mix(10, 250, clean.bottom(z=z_isp_c))
        for s, d in zip(samples_2, final_2):
            p300.aspirate(200, s)
            p300.dispense(200, d.bottom(z=z_isp_a))
            p300.mix(20, 200, d.bottom(z=z_isp_ma))
            p300.mix(10, 250, clean.bottom(z=z_isp_c))
        for s, d in zip(samples_3, final_3):
            p300.aspirate(200, s)
            p300.dispense(200, d.bottom(z=z_isp_a))
            p300.mix(20, 200, d.bottom(z=z_isp_ma))
            p300.mix(10, 250, clean.bottom(z=z_isp_c))
        for s, d in zip(samples_4, final_4):
            p300.aspirate(200, s)
            p300.dispense(200, d.bottom(z=z_isp_a))
            p300.mix(20, 200, d.bottom(z=z_isp_ma))
            if s.well_name == 'A12':
                break
            p300.mix(10, 250, clean.bottom(z=z_isp_c))
        p300.drop_tip()
    supernatent_addition()

    ctx.pause('''
                Remove Isopropanol on site 6, Add Ethanol to site 6
                 ''')

    ctx.comment('\n~~~~~~~~~~~~REMOVING Supernatent FROM SAMPLES~~~~~~~~~\n')

    def supernatent_removal():
        p300.pick_up_tip()
        for f in final_1:
            p300.aspirate(170, f.bottom(z=5))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.aspirate(170, f.bottom(z=5))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        for f in final_2:
            p300.aspirate(170, f.bottom(z=5))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.aspirate(170, f.bottom(z=5))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        for f in final_3:
            p300.aspirate(170, f.bottom(z=5))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.aspirate(170, f.bottom(z=5))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.mix(10, 250, clean.bottom(z=z_chloroform_m))
        for f in final_4:
            p300.aspirate(170, f.bottom(z=4))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            p300.aspirate(170, f.bottom(z=4))
            p300.air_gap(4)
            p300.dispense(170, trash)
            p300.blow_out(trash)
            if f.well_name == 'A12':
                break
            p300.mix(10, 250, clean.bottom(z=z_isp_c))
        p300.drop_tip()
    supernatent_removal()

    ctx.comment('\n~~~~~~~~~~~~~~ADDING Ethanol TO SAMPLES~~~~~~~~~~~~~~\n')

    def ethanol_addition():
        p300.pick_up_tip()
        for f in final_1:
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
        for f in final_2:
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
        for f in final_3:
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
        for f in final_4:
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
            p300.aspirate(250, res)
            p300.air_gap(4)
            p300.dispense(250, f.top())
            p300.blow_out(f.top())
        p300.drop_tip()
    ethanol_addition()

    ctx.comment('\n~~~~~~~~~~~~~~Protocol Complete~~~~~~~~~~~~~~\n')

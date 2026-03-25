import math

metadata = {
    'protocolName': 'Drop Casting Polymer to Silicon Wafer',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_samp, p20_mount, csv_samp, mix_reps,
        disp_height, disp_rate, mix_vol,
        vol_tube1, vol_tube2,
        vol_tube3, grid, delay_time] = get_values(  # noqa: F821
        "num_samp", "p20_mount", "csv_samp", "mix_reps",
            "disp_height", "disp_rate", "mix_vol",
            "vol_tube1", "vol_tube2", "vol_tube3", "grid", "delay_time")

    if not 1 <= num_samp <= 24 and grid == "wafer_6x4_grid":
        raise Exception("Enter a sample number between 1-24")
    if not 25 <= num_samp <= 48 and grid == "wafer_4x12_grid":
        raise Exception("Enter a sample number between 25-48")
    if not 49 <= num_samp <= 96 and grid == "wafer_4x24_grid":
        raise Exception("Enter a sample number between 49-96")

    # load labware
    mix_plate = ctx.load_labware('corning_96_wellplate_360ul_flat', '1')
    solutions = ctx.load_labware('vial_rack_8x20ml_vials', '2')
    wafer = ctx.load_labware(grid, '3')
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in ['4', '5']]
    tips = [tip for tiprack in tipracks for tip in tiprack.wells()]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tipracks)

    # csv_samp file --> nested list
    transfer = [[val.strip().lower() for val in line.split(',')]
                for line in csv_samp.splitlines()
                if line.split(',')[0].strip()][1:]

    # liquid height tracking
    radius = solutions.wells()[0].diameter/2
    area = math.pi*radius**2
    h_naught1 = (vol_tube1*1000)/area
    h_naught2 = (h_naught1/vol_tube1)*vol_tube2
    h_naught3 = (h_naught1/vol_tube1)*vol_tube3
    h_naughts = [h_naught1, h_naught2, h_naught3]*num_samp
    all_dh = [int(transfer[i][j+1])/area for i in range(0, len(transfer))
              for j, vol in enumerate(transfer[i][1:4])]
    sum_dh = [all_dh[0], all_dh[1], all_dh[2]]
    for j in range(0, len(all_dh)-3):
        running_dh = sum_dh[j] + all_dh[j+3]
        sum_dh.append(running_dh)
    chunks = [sum_dh[i:i+3] for i in range(0, len(sum_dh), 3)]

    # transfer solutions to mix plate
    start = 3
    for i, (mix_well, dest_well) in enumerate(zip(mix_plate.wells(),
                                              wafer.wells()[:num_samp])):
        ctx.comment('\nMaking Next Solution on Mix Plate')
        for vol, tube, tip, h, dz in zip(transfer[i][1:4],
                                         solutions.rows()[0][:3]*num_samp,
                                         tips[:3]*num_samp,
                                         h_naughts,
                                         chunks[i]):
            if vol == '0':
                continue
            p20.pick_up_tip(tip)
            p20.aspirate(int(vol), tube.bottom(z=h-dz-10 if h-dz > 11 else 1))
            p20.dispense(int(vol), mix_well)
            ctx.delay(seconds=delay_time)
            p20.blow_out()
            p20.touch_tip()
            p20.return_tip()
        ctx.comment('\nAdding to Wafer Plate\n')
        p20.pick_up_tip(tips[start])
        p20.mix(mix_reps, mix_vol, mix_well)
        p20.aspirate(int(transfer[i][4]), mix_well)
        p20.dispense(int(transfer[i][4]), dest_well.top(z=disp_height))
        p20.drop_tip()
        start += 1
        ctx.comment('\n')

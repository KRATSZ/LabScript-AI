import math
from datetime import datetime

metadata = {
    'protocolName': 'STANDARD MP',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [input_csv, test_method, vol_aliquot, vol_mobile_phase, vol_tests,
     qc_height, std_height, air_gap_bool] = get_values(  # noqa: F821
        'input_csv', 'test_method', 'vol_aliqout', 'vol_mobile_phase',
        'vol_tests', 'qc_height', 'std_height', 'air_gap_bool')

    class tube():

        def __init__(self, tube, height=0, min_height=5, comp_coeff=1.15):
            self.tube = tube
            self.radius = tube.geometry._diameter/2
            self.height = height
            self.min_height = min_height
            self.comp_coeff = comp_coeff

        def height_dec(self, vol):
            dh = (vol/(math.pi*(self.radius**2)))*self.comp_coeff
            if self.height - dh > self.min_height:
                self.height = self.height - dh
            else:
                self.height = self.min_height
            return(self.tube.bottom(self.height))

        def height_inc(self, vol):
            dh = (vol/(math.pi*(self.radius**2)))*self.comp_coeff
            if self.height + dh < self.tube.geometry._depth:
                self.height = self.height + dh
            else:
                self.height = self.tube.geometry._depth
            return(self.tube.bottom(self.height + 20))

    # load labware
    plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '1',
                             'TEST PLATE 2ML 96 WELL STANDARD, QC, AND IS')
    tuberack15 = ctx.load_labware('opentrons_15_tuberack_nest_15ml_conical',
                                  '2', 'WS AND QC SOLUTIONS')
    tuberack15_50 = ctx.load_labware(
        'opentrons_10_tuberack_nest_4x50ml_6x15ml_conical', '3',
        'DILUENT AND MOBILE PHASE')

    ws_1_4 = [
        ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', slot,
                         'WS ' + '1-4' + ' ' + let)
        for slot, let in zip(['7', '8'], 'AB')]
    ws_5_8 = [
        ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap',
                         slot, 'WS ' + '5-8' + ' ' + let)
        for slot, let in zip(['4', '5'], 'AB')]
    qc = [
        ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap',
                         slot, 'QC ' + let)
        for slot, let in zip(['9', '6'], 'AB')]
    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '10')]
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '11')]

    p300 = ctx.load_instrument('p300_single_gen2', 'left',
                               tip_racks=tiprack300)
    p1000 = ctx.load_instrument('p1000_single_gen2', 'right',
                                tip_racks=tiprack1000)
    p300.flow_rate.blow_out = 300
    p1000.flow_rate.blow_out = 1000

    air_gap_p1000 = 100 if air_gap_bool else 0
    air_gap_p300 = 20 if air_gap_bool else 0
    air_gap_dict = {
        pip: airgap for pip, airgap in zip([p1000, p300],
                                           [air_gap_p1000, air_gap_p300])
    }

    # start reagent setup
    tubes_dict = {
        well: tube(well)
        for rack in [tuberack15_50, tuberack15]
        for well in rack.wells()
    }
    diluent = tuberack15_50.wells_by_name()['A3']
    tubes_dict[diluent].comp_coeff = 1.2
    tubes_dict[diluent].height = 92

    # tip conditioning
    dil_dest = tuberack15_50.wells()[0]

    def tip_condition(pip, vol, loc):
        pip.pick_up_tip()
        pip.flow_rate.aspirate = pip.max_volume/2
        pip.flow_rate.dispense = pip.max_volume
        for i in range(2):
            mix_reps = 2 - i
            pip.transfer(vol, tubes_dict[loc].height_dec(vol),
                         dil_dest.bottom(104),
                         mix_before=(mix_reps, pip.max_volume*2/3),
                         air_gap=air_gap_dict[pip], new_tip='never')
            tubes_dict[dil_dest].height_inc(vol)
            pip.blow_out(dil_dest.bottom(104))

    # create serial dilution from .csv file
    data = [
        line.split(',')[:17] for line in input_csv.splitlines()[14:28]
        if line and line.split(',')[0]]

    # first set of tip conditioning
    tip_condition(p1000, 500, diluent)

    # pre-add diluent in reverse
    for line in data[::-1]:
        dest = ctx.loaded_labwares[int(line[12])].wells_by_name()[line[13]]
        dil_vol = float(line[14])
        num_trans = math.ceil(dil_vol/(p1000.max_volume-air_gap_p1000))
        vol_per_trans = dil_vol/num_trans
        asp_rate = vol_per_trans if vol_per_trans < 150 else 150
        disp_rate = 2*vol_per_trans if vol_per_trans > 37 else 150
        p1000.flow_rate.aspirate = asp_rate
        p1000.flow_rate.dispense = disp_rate
        for n in range(num_trans):
            p1000.transfer(vol_per_trans,
                           tubes_dict[diluent].height_dec(vol_per_trans),
                           tubes_dict[dest].height_inc(vol_per_trans),
                           air_gap=air_gap_p1000, new_tip='never')
            p1000.blow_out(dest.bottom(tubes_dict[dest].height + 20))
    p1000.air_gap(100)
    p1000.drop_tip()

    # parse std sources
    std_dict = {}
    for line in data:
        std = ctx.loaded_labwares[int(line[10])].wells_by_name()[line[11]]
        dest = ctx.loaded_labwares[int(line[12])].wells_by_name()[line[13]]
        std_vol = float(line[9])
        if std in std_dict:
            std_dict[std].append({'dest': dest, 'vol': std_vol})
        else:
            std_dict[std] = [{'dest': dest, 'vol': std_vol}]

    # add standards to pre-added diluents
    for std, vals in std_dict.items():
        if std.parent.parent == '2':
            if p1000.hw_pipette['has_tip']:
                p1000.air_gap(100)
                p1000.drop_tip()
            p1000.pick_up_tip()
            p1000.flow_rate.aspirate = 500
            p1000.flow_rate.dispense = 1000
            p1000.flow_rate.blow_out = 1000
            p1000.mix(5, 1000, std.bottom(tubes_dict[std].height))
            p1000.blow_out(std.top(-2))
            p1000.air_gap(100)
            p1000.drop_tip()
        # p300 tip condition
        tip_condition(p300, 150, diluent)
        if std.display_name.split()[0] == 'H11':
            plate_height = qc_height
        elif std.display_name.split()[0] == 'H12':
            plate_height = std_height
        for val in vals:
            dest = val['dest']
            vol = val['vol']
            num_trans = math.ceil(vol/(p300.max_volume-air_gap_p300))
            vol_per_trans = vol/num_trans
            asp_rate = vol_per_trans if vol_per_trans < 150 else 150
            disp_rate = 2*vol_per_trans if vol_per_trans > 37 else 150
            p300.flow_rate.aspirate = asp_rate
            p300.flow_rate.dispense = disp_rate
            for n in range(num_trans):
                dest_loc = tubes_dict[dest].height_inc(vol_per_trans)
                if std.parent.parent == '1':
                    p300.transfer(vol_per_trans, std.bottom(plate_height),
                                  dest_loc, air_gap=air_gap_p300,
                                  new_tip='never')
                    if plate_height - 1 > 1:
                        plate_height -= 2.5
                    else:
                        plate_height = 1
                else:
                    p300.transfer(vol_per_trans,
                                  tubes_dict[std].height_dec(vol_per_trans),
                                  dest_loc, air_gap=air_gap_p300,
                                  new_tip='never')
                p300.blow_out(dest_loc)
        p300.air_gap(20)
        p300.drop_tip()

    # aliquots
    ws_dests_1_4 = [
        well
        for set in [ws_1_4[0].rows()[i] + ws_1_4[1].rows()[i][:4]
                    for i in range(len(ws_1_4[0].rows()))]
        for well in set]
    ws_dests_5_8 = [
        well
        for set in [ws_5_8[0].rows()[i] + ws_5_8[1].rows()[i][:4]
                    for i in range(len(ws_5_8[0].rows()))]
        for well in set]
    ws_dests_all = ws_dests_1_4 + ws_dests_5_8

    qc_dests = [
        well
        for set in [qc[0].columns()[i] + qc[1].columns()[i]
                    for i in range(len(qc[0].columns())-1, -1, -1)]
        for well in set]
    [qc_dests.remove(well) for well in [
        qc[0].wells_by_name()['B1'],
        qc[0].wells_by_name()['C1'],
        qc[1].wells_by_name()['B6']]]

    std_5x = ['DQC', 'ULOQC', 'LLOQC']
    ws_counter = 0
    qc_counter = 0
    for line in data[::-1]:
        std_name = line[0]
        std = ctx.loaded_labwares[int(line[12])].wells_by_name()[line[13]]
        dest_set = qc_dests if 'QC' in std_name else ws_dests_all
        counter = qc_counter if 'QC' in std_name else ws_counter
        num_aliquots = 5 if std_name in std_5x else 10
        aliquots = dest_set[counter:counter+num_aliquots]

        # mix
        if p1000.hw_pipette['has_tip']:
            p1000.air_gap(100)
            p1000.drop_tip()
        p1000.pick_up_tip()
        p1000.flow_rate.aspirate = 500
        p1000.flow_rate.dispense = 1000
        p1000.flow_rate.blow_out = 1000
        p1000.mix(5, 1000, std.bottom(tubes_dict[std].height))
        p1000.blow_out(std.top(-2))
        for a in aliquots:
            p1000.flow_rate.aspirate = 150
            p1000.flow_rate.dispense = 320
            p1000.transfer(vol_aliquot,
                           tubes_dict[std].height_dec(vol_aliquot),
                           a.bottom(10), air_gap=air_gap_p1000,
                           new_tip='never')
            p1000.blow_out(a.top(-6))
        p1000.air_gap(100)
        p1000.drop_tip()
        if 'QC' in std_name:
            qc_counter += num_aliquots
        else:
            ws_counter += num_aliquots

    # transfer mobile phase
    mobile_phase = tuberack15_50.wells_by_name()['B1']
    tubes_dict[mobile_phase].height = 94
    tip_condition(p1000, 1000, mobile_phase)
    mobile_phase_dests = plate.rows()[0][:8] + plate.rows()[2][:6] + [
        plate.wells_by_name()['E1']] + [plate.wells_by_name()['E3']]
    for i in range(len(mobile_phase_dests)//2):
        p1000.flow_rate.aspirate = 150
        p1000.flow_rate.dispense = 800
        # custom distribution
        asp_vol = vol_mobile_phase*2 + 100 \
            if vol_mobile_phase*2 + 100 < 1000 else 1000
        p1000.aspirate(asp_vol, tubes_dict[mobile_phase].height_dec(asp_vol))
        for well in mobile_phase_dests[i*2:i*2+2]:
            p1000.dispense(vol_mobile_phase, well.bottom(10))
        p1000.dispense(
            p1000.current_volume,
            tubes_dict[mobile_phase].height_inc(p1000.current_volume))
        p1000.blow_out(mobile_phase.top(-2))
    p1000.air_gap(100)
    p1000.drop_tip()

    # transfer IS
    is_ = plate.wells_by_name()['H1']
    tip_condition(p300, 150, diluent)
    for i, m in enumerate(mobile_phase_dests):
        if i < 5:
            h = 3
        elif i >= 5 and i < 8:
            h = 1
        else:
            h = -2
        p300.transfer(30, is_.bottom(h), m.bottom(14), air_gap=air_gap_p300,
                      new_tip='never')
        p300.blow_out(m.bottom(14))
    p300.air_gap(20)
    p300.drop_tip()

    # tests
    ws_counter = 0
    qc_counter = 0
    ws_dests = mobile_phase_dests[:8]
    qc_dests = mobile_phase_dests[8:]
    suitability_transfers = {
        '1': plate.wells_by_name()['E1'],
        '8': plate.wells_by_name()['E3']
    }
    for line in data[::-1]:
        std_name = line[0]
        std = ctx.loaded_labwares[int(line[12])].wells_by_name()[line[13]]
        dest_set = qc_dests if 'QC' in std_name else ws_dests
        counter = qc_counter if 'QC' in std_name else ws_counter

        p300.flow_rate.aspirate = 30
        p300.flow_rate.dispense = 150
        # tip_condition(p300, 150, diluent)
        p300.pick_up_tip()
        p300.transfer(vol_tests, tubes_dict[std].height_dec(vol_tests),
                      dest_set[counter].bottom(14), mix_before=(2, 200),
                      air_gap=air_gap_p300, new_tip='never')
        p300.blow_out(dest_set[counter].bottom(14))
        p300.air_gap(20)
        if std_name in suitability_transfers:
            p300.dispense(20, std.top())  # void air gap
            p300.transfer(vol_tests, tubes_dict[std].height_dec(vol_tests),
                          suitability_transfers[std_name].bottom(10),
                          mix_before=(2, 200), air_gap=air_gap_p300,
                          new_tip='never')
            p300.blow_out(suitability_transfers[std_name].bottom(10))
        p300.drop_tip()

        if 'QC' in std_name:
            qc_counter += 1
        else:
            ws_counter += 1

    write_path = '/data/readout.txt'
    if not ctx.is_simulating():
        p300_serial = p300.hw_pipette['pipette_id']
        p1000_serial = p1000.hw_pipette['pipette_id']
        ot2_serial = []
        with open('/var/serial') as serialfile:
            ot2_serial.append(serialfile.read())
        with open(write_path, 'w') as text_file:
            text_file.write(f'Test method: {test_method}\n')
            text_file.write(f'Date/Time of run: {str(datetime.now())}\n')
            text_file.write(f'P300 Serial: {str(p300_serial)}\n')
            text_file.write(f'P1000 Serial: {str(p1000_serial)}\n')
            text_file.write(f'OT-2 Serial: {str(ot2_serial[0])}\n')
            text_file.write('Protocol execution:\n')
            for c in ctx.commands():
                text_file.write(f'{c}\n')

from opentrons.types import Point
import csv
import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'PCR Setup',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.12'
}

TEST_MODE = False


def run(ctx):

    [protocol_type, scan_9000_plate_barcode, scan_qpcr_plate_barcode,
     plate_1_csv, plate_2_csv, plate_3_csv,
     plate_4_csv] = get_values(  # noqa: F821
      'protocol_type', 'scan_9000_plate_barcode', 'scan_qpcr_plate_barcode',
      'plate_1_csv', 'plate_2_csv', 'plate_3_csv', 'plate_4_csv')

    all_plate_csvs = [
        [line.split(',')
         for line in plate_csv.splitlines()[1:]
         if line and line.split(',')[0]]
        for plate_csv in [plate_1_csv, plate_2_csv, plate_3_csv, plate_4_csv]]

    protocol_map = {
        'biogx': {
            'vol_sample': 5.0,
            'vol_mm': 15.0,
            'plate_type': 'kingfisher_96_deepwell_plate_2ml',
            'header': [['* Instrument Type = QuantStudio(TM) 7 Flex System'],
                       ['* Passive Reference ='],
                       [],
                       ['[Sample Setup]'],
                       ['Well', 'Well Position', 'Sample Name', 'Target Name',
                        'Target Color', 'Task', 'Reporter', 'Quencher', '#']],
            'target_names': ['RNase P', 'N1', 'IAC'],
            'target_colors': ['"RGB(0,0,255)"', '"RGB(176,23,31)"',
                              '"RGB(0,139,69)"'],
            'tasks': ['UNKNOWN', 'UNKNOWN', 'UNKNOWN'],
            'reporters': ['FAM', 'ROX', 'CY5'],
            'quenchers': ['NONE', 'NONE', 'NONE']
        },
        'lgc': {
            'vol_sample': 5.0,
            'vol_mm': 10.0,
            'plate_type': 'kingfisher_96_wellplate_200ul',
            'header': [['* Instrument Type = QuantStudio(TM) 7 Flex System'],
                       ['* Passive Reference ='],
                       [],
                       ['[Sample Setup]'],
                       ['Well', 'Well Position', 'Sample Name', 'Target Name',
                        'Target Color', 'Task', 'Reporter', 'Quencher', '#']],
            'target_names': ['influenza A virus-InfA_m', 'r SARS-CoV-2-SC2_m',
                             'RP-RNaseP', 'influenza B virus-InfB_m'],
            'target_colors': ['"RGB(0,0,255)"', '"RGB(176,23,31)"',
                              '"RGB(255,0,0)"', '"RGB(0,139,69)"'],
            'tasks': ['UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN'],
            'reporters': ['FAM', 'ROX', 'CY5', 'VIC'],
            'quenchers': ['NONE', 'NONE', 'NONE', 'NONE']
        },
        'pkamp': {
            'vol_sample': 10.0,
            'vol_mm': 5.0,
            'plate_type': 'kingfisher_96_wellplate_200ul',
            'header': [['* Instrument Type = QuantStudio(TM) 7 Flex System'],
                       ['* Passive Reference ='],
                       [],
                       ['[Sample Setup]'],
                       ['Well', 'Well Position', 'Sample Name', 'Target Name',
                        'Target Color', 'Task', 'Reporter', 'Quencher', '#']],
            'target_names': ['SARS CoV-2', 'Influenza A', 'Influenza B',
                             'RSV', 'RNase P'],
            'target_colors': ['"RGB(0,0,255)"', '"RGB(176,23,31)"',
                              '"RGB(255,0,0)"', '"RGB(246,0,0)"',
                              '"RGB(0,139,69)"'],
            'tasks': ['UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN'],
            'reporters': ['FAM', 'ROX', 'CY5', 'CY5.5', 'VIC'],
            'quenchers': ['NONE', 'NONE', 'NONE', 'NONE', 'NONE']
        }
    }
    protocol_info = protocol_map[protocol_type]

    source_plates = [
        ctx.load_labware(protocol_info['plate_type'], slot,
                         f'source plate {i+1}')
        for i, slot in enumerate(['4', '6', '1', '3'])]
    dest_plate = ctx.load_labware('microamp_384_wellplate_40ul', '2',
                                  '384 well plate')
    strips = ctx.load_labware('custom_96_wellplate_200ul', '5',
                              'mastermix strips')
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['7', '10', '11']]
    tuberack = ctx.load_labware('custom_24_tuberack_2000ul', '8')
    tipracks300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '9')]
    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tipracks20)
    p300 = ctx.load_instrument(
        'p300_single_gen2', 'right', tip_racks=tipracks300)
    path = '/var/lib/jupyter/notebooks'

    all_sources = [
        well for plate in source_plates for well in plate.wells()]
    all_dests = [
        well for set in [
         dest_plate.columns()[i*2+j][k::2]
         for k, row in enumerate(dest_plate.rows()[:2])
         for j in range(2)
         for i in range(12)]
        for well in set]

    source_plate_data = {
        plate_csv[0][0]: {well: None for well in plate.wells()}
        for plate, plate_csv in zip(source_plates, all_plate_csvs)
        if plate_csv
    }

    source_barcodes = [
        plate_csv[0][0] if plate_csv else None
        for plate_csv in all_plate_csvs]

    source_plate_data = {}
    for barcode, plate in zip(
            source_barcodes, source_plates):
        for well in plate.wells():
            source_plate_data[well] = {
                'sample_id': None, 'plate_barcode': barcode}

    # fill source_plate_data
    for plate, plate_csv in zip(source_plates, all_plate_csvs):
        if plate_csv:
            barcode = plate_csv[0][0].strip()
            for line in plate_csv:
                well_position = line[1]
                well = plate.wells_by_name()[well_position]
                sample_id = line[2]
                source_plate_data[well]['sample_id'] = sample_id

    dest_plate_data = {
        d: {s: source_plate_data[s]}
        for i, (d, s) in enumerate(zip(all_dests, all_sources))
    }

    def pick_up(pip=m20):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace tipracks before resuming.")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def get_well_name(well):
        return well.display_name.split()[' '][0]

    def wick(well, pip=m20, side=1, magnitude_ratio=0.5, z=3):
        if hasattr(well, 'diameter'):
            magnitude = well.diameter/2*0.5
        else:
            magnitude = well.width/2*0.5
        pip.move_to(well.bottom().move(
            Point(x=side*magnitude*magnitude_ratio, z=z)))

    def slow_withdraw(well, pip=m20):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def check_column(well):
        plate = well.parent
        col_index = math.ceil(plate.wells().index(well)/8)
        column = plate.columns()[col_index]
        for well in column:
            if source_plate_data[well]['sample_id']:
                return True
        return False

    all_sources_multi = [
        well for plate in source_plates for well in plate.rows()[0]]
    all_dests_multi = [
         row[i*2+j]
         for row in dest_plate.rows()[:2]
         for j in range(2)
         for i in range(12)]

    if not ctx.is_simulating():
        out_csv_path = f'{path}/{scan_9000_plate_barcode}.csv'
        with open(out_csv_path, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(
                [f'Protocol for {scan_9000_plate_barcode} was not completed.'])

    # mm pre-aliquot
    mm_tubes = tuberack.wells()[:4]
    mm_strips = strips.columns()[:4]
    total_vol_mm_per_strip = protocol_info['vol_mm']*96*1.05
    vol_mm_per_well = total_vol_mm_per_strip/8
    p300.pick_up_tip()
    for barcode_bool, tube, strip in zip(source_barcodes, mm_tubes, mm_strips):
        if barcode_bool:
            for well in strip:
                p300.aspirate(vol_mm_per_well, tube)
                slow_withdraw(tube, p300)
                p300.dispense(vol_mm_per_well, well)
                wick(well, p300)
                slow_withdraw(well, p300)
    if TEST_MODE:
        p300.return_tip()
    else:
        p300.drop_tip()

    # mm transfer
    pick_up(m20)
    for i, (s, d) in enumerate(zip(all_sources_multi, all_dests_multi)):
        mm_source = mm_strips[i//12][0]
        if check_column(s):
            m20.aspirate(protocol_info['vol_mm'], mm_source)
            m20.dispense(protocol_info['vol_mm'], d)
            wick(d, m20, magnitude_ratio=0.6)
            slow_withdraw(d, m20)

    # sample transfer
    for source, dest in zip(all_sources_multi, all_dests_multi):
        if check_column(source):
            if not m20.has_tip:
                pick_up(m20)
            m20.aspirate(protocol_info['vol_sample'], source.bottom(3))
            slow_withdraw(source, m20)
            m20.dispense(protocol_info['vol_sample'], dest)
            m20.mix(3, 10, dest)
            ctx.delay(seconds=1)
            wick(dest, m20, magnitude_ratio=0.6)
            slow_withdraw(dest, m20)
            if TEST_MODE:
                m20.return_tip()
            else:
                m20.drop_tip()

    if not ctx.is_simulating():
        out_csv_path = f'{path}/{scan_9000_plate_barcode}.csv'
        out_csv_path_qs = f'{path}/{scan_9000_plate_barcode}_\
{scan_qpcr_plate_barcode}_QS5_Fire.txt'

#     else:
#         out_csv_path = f'protocols/055b94/supplements/\
# {scan_9000_plate_barcode}.csv'
#         out_csv_path_qs = f'protocols/055b94/supplements/\
# {scan_9000_plate_barcode}_{scan_qpcr_plate_barcode}_QS5_Fire.txt'

        with open(out_csv_path, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['Plate_Barcode', 'WellPos', 'SampleID', 'SourcePlateID',
                 'Chemagic_ID', 'PCRandSampleIDs'])
            for key, val in dest_plate_data.items():
                well = key
                well96 = [key for key in val.keys()][0]
                sample_id = val[well96]['sample_id']
                barcode = val[well96]['plate_barcode']
                well_position = well.display_name.split(' ')[0]
                row = [scan_9000_plate_barcode, well_position, sample_id,
                       barcode, '',
                       f'{scan_qpcr_plate_barcode}_{scan_9000_plate_barcode}']
                writer.writerow(row)

        # QS file
        qs_plate_ordered = [
            well for row in dest_plate.rows() for well in row]

        with open(out_csv_path_qs, 'w') as file:
            for line in protocol_info['header']:
                file.write('\t'.join(line) + '\n')
            for i, (key, val) in enumerate(dest_plate_data.items()):
                well = key
                well96 = [key for key in val.keys()][0]
                sample_id = val[well96]['sample_id']
                well_position = well.display_name.split(' ')[0]
                for j, (target_name, target_color, task, reporter,
                        quencher) in enumerate(
                            zip(protocol_info['target_names'],
                                protocol_info['target_colors'],
                                protocol_info['tasks'],
                                protocol_info['reporters'],
                                protocol_info['quenchers'])):
                    well_num = str(qs_plate_ordered.index(well) + 1)
                    num = str(i*len(protocol_info['target_names'])+j+1)
                    row = [
                        (s or "") for s in
                        [well_num, well_position, sample_id, target_name,
                         target_color, task, reporter, quencher, num]]
                    file.write('\t'.join(row) + '\n')

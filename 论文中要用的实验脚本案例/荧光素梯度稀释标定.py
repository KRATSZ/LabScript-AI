from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def add_parameters(parameters):
    parameters.add_int(
        variable_name="parallel_samples",
        display_name="平行检测数量",
        description="设置需要检测的平行样本数量 (1-8)",
        default=4,
        minimum=1,
        maximum=8
    )

def run(protocol: protocol_api.ProtocolContext):
    # 获取用户输入的平行样本数量
    parallel_samples = protocol.params.parallel_samples
    protocol.comment(f"设置平行检测数量: {parallel_samples}")
    
    # 加载实验器材
    tiprack_200ul = protocol.load_labware("opentrons_flex_96_tiprack_200ul", location="C2", label="Flex 200uL Tips")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", location="B2", label="Dilution Plate")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", location="B3", label="Reagent Reservoir")
    trash = protocol.load_trash_bin(location="A3")

    # 根据平行样本数量选择移液器
    if parallel_samples == 8:
        # 使用8通道移液器
        pipette = protocol.load_instrument("flex_8channel_1000", mount="right", tip_racks=[tiprack_200ul])
        protocol.comment("使用8通道移液器进行操作")
    else:
        # 使用单通道移液器
        pipette = protocol.load_instrument("flex_1channel_1000", mount="left", tip_racks=[tiprack_200ul])
        protocol.comment(f"使用左侧单通道移液器进行{parallel_samples}个样本的操作")

    # 定义试剂位置并添加颜色标识
    pbs_source = reservoir.wells_by_name()["A2"]
    fluorescein_1x_stock_source = reservoir.wells_by_name()["A1"]
    
    # 为液体添加名称和颜色标识
    protocol.comment("储液槽中的液体配置:")
    protocol.comment("A1: 荧光素工作液 (Fluorescein 1X Stock) - 绿色")
    protocol.comment("A2: 1X PBS缓冲液 (1X PBS Buffer) - 透明")

    # --- 第一阶段：板子预处理 ---
    protocol.comment("--- Stage 1: Plate Pre-treatment ---")

    # 1.1 向第2-12列添加100 µL 1X PBS缓冲液
    protocol.comment("1.1 Adding PBS to columns 2-12")
    
    if parallel_samples == 8:
        # 8通道操作
        pipette.pick_up_tip()
        for col_idx_plate in range(1, 12):
            target_well_in_col = plate.columns()[col_idx_plate][0]
            protocol.comment(f"Adding PBS to column {col_idx_plate + 1}")
            pipette.aspirate(100, pbs_source)
            pipette.dispense(100, target_well_in_col)
        pipette.drop_tip()
    else:
        # 单通道操作
        for col_idx_plate in range(1, 12):
            pipette.pick_up_tip()
            for row_idx in range(parallel_samples):
                target_well = plate.wells()[col_idx_plate * 8 + row_idx]  # 计算具体孔位
                protocol.comment(f"Adding PBS to well {target_well.well_name}")
                pipette.aspirate(100, pbs_source)
                pipette.dispense(100, target_well)
            pipette.drop_tip()

    # 1.2 向第1列添加200 µL荧光素工作液
    protocol.comment("1.2 Adding Fluorescein to column 1")
    
    if parallel_samples == 8:
        # 8通道操作
        pipette.pick_up_tip()
        pipette.aspirate(200, fluorescein_1x_stock_source)
        pipette.dispense(200, plate.columns()[0][0])
        pipette.drop_tip()
    else:
        # 单通道操作
        pipette.pick_up_tip()
        for row_idx in range(parallel_samples):
            target_well = plate.wells()[row_idx]  # A1, B1, C1...
            protocol.comment(f"Adding Fluorescein to well {target_well.well_name}")
            pipette.aspirate(200, fluorescein_1x_stock_source)
            pipette.dispense(200, target_well)
        pipette.drop_tip()

    # --- 第二阶段：系列稀释 ---
    protocol.comment("--- Stage 2: Serial Dilution ---")

    if parallel_samples == 8:
        # 8通道操作 (原有逻辑)
        pipette.pick_up_tip()

        # 2.1 初始转移：从第1列转移到第2列
        protocol.comment("2.1 Initial transfer from column 1 to column 2")
        source_wells_col1_ref = plate.columns()[0][0]
        dest_wells_col2_ref = plate.columns()[1][0]

        pipette.aspirate(100, source_wells_col1_ref)
        pipette.dispense(100, dest_wells_col2_ref)

        # 2.2 系列稀释：从第2列开始混合，转移到第3列
        for i in range(1, 10):
            current_col_ref = plate.columns()[i][0]
            next_col_ref = plate.columns()[i+1][0]
            mix_vol = 150

            protocol.comment(f"Mixing in column {i+1}, then transferring to column {i+2}")
            pipette.mix(3, mix_vol, current_col_ref)
            pipette.aspirate(100, current_col_ref)
            pipette.dispense(100, next_col_ref)

        # 2.3 最后一列混匀
        protocol.comment("2.3 Mix in column 11")
        last_col_ref = plate.columns()[10][0]
        pipette.mix(3, 150, last_col_ref)
        pipette.drop_tip()
        
    else:
        # 单通道操作 - 每个样本分别处理
        for row_idx in range(parallel_samples):
            protocol.comment(f"Processing sample {row_idx + 1} (row {chr(65 + row_idx)})")
            pipette.pick_up_tip()
            
            # 2.1 初始转移：从第1列转移到第2列
            source_well = plate.wells()[row_idx]  # A1, B1, C1...
            dest_well = plate.wells()[8 + row_idx]  # A2, B2, C2...
            
            protocol.comment(f"Initial transfer from {source_well.well_name} to {dest_well.well_name}")
            pipette.aspirate(100, source_well)
            pipette.dispense(100, dest_well)
            
            # 2.2 系列稀释：从第2列开始
            for col_idx in range(1, 10):
                current_well = plate.wells()[col_idx * 8 + row_idx]
                next_well = plate.wells()[(col_idx + 1) * 8 + row_idx]
                
                protocol.comment(f"Mixing in {current_well.well_name}, then transferring to {next_well.well_name}")
                pipette.mix(3, 150, current_well)
                pipette.aspirate(100, current_well)
                pipette.dispense(100, next_well)
            
            # 2.3 最后一列混匀
            last_well = plate.wells()[10 * 8 + row_idx]
            protocol.comment(f"Final mix in {last_well.well_name}")
            pipette.mix(3, 150, last_well)
            pipette.drop_tip()

    protocol.comment("Protocol finished.")
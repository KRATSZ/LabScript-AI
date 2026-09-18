from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Flex Cell-FREE Purification - Advanced Multi-Sample',
    'author': 'Gaoyuan',
    'description': 'Cell-FREE with magnetic bead purification - Supports 1-96 samples with smart pipette selection'
}
requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    # ========== 样本配置 ==========
    # 修改这里来选择样本数量: 1, 8, 12, 24 (分区收集限制最大24样本)
    SAMPLE_COUNT = 8  # 可选: 1, 8, 12, 24
    
    # 中断恢复配置 - 如果需要从某个步骤开始，修改这里
    RESUME_FROM_STEP = 1  # 1-11, 设置为1表示从头开始
    
    # 实验器皿位置跟踪 - 避免重复移动错误
    plate_current_location = "magnetic_block"  # 初始位置在磁力模块
    
    # ⚡ 快速验证模式 - 大幅缩短等待时间
    FAST_MODE = False  # 设为False恢复正常实验时间
    protocol.comment("📝 生产环境请将FAST_MODE设为False")
    
    # 样本孔位映射策略
    def generate_sample_layout(count):
        """根据样本数量生成最优孔位布局"""
        if count == 1:
            return ['A1']
        elif count <= 8:
            return [f'{chr(65+i)}1' for i in range(count)]  # A1-H1
        elif count <= 12:
            layout = [f'{chr(65+i)}1' for i in range(8)]  # A1-H1
            layout.extend([f'{chr(65+i)}2' for i in range(count-8)])  # A2-D2
            return layout
        elif count <= 24:
            layout = []
            cols = math.ceil(count / 8)
            for col in range(1, cols + 1):
                remaining = min(8, count - (col-1)*8)
                layout.extend([f'{chr(65+i)}{col}' for i in range(remaining)])
            return layout
        elif count <= 48:
            layout = []
            cols = math.ceil(count / 8)
            for col in range(1, cols + 1):
                remaining = min(8, count - (col-1)*8)
                layout.extend([f'{chr(65+i)}{col}' for i in range(remaining)])
            return layout
        elif count <= 24:
            layout = []
            cols = math.ceil(count / 8)
            for col in range(1, cols + 1):
                remaining = min(8, count - (col-1)*8)
                layout.extend([f'{chr(65+i)}{col}' for i in range(remaining)])
            return layout
        else:
            raise ValueError(f"样本数量 {count} 超出支持范围 (1-24，分区收集限制)")
    
    # 获取当前样本孔位
    sample_wells = generate_sample_layout(SAMPLE_COUNT)
    protocol.comment(f"处理 {SAMPLE_COUNT} 个样本: {sample_wells}")
    
    # 实验台布局说明
    protocol.comment("=== 实验台布局 ===")
    protocol.comment("A3: 垃圾桶")
    protocol.comment("B2: 12列储液槽 (试剂)")
    protocol.comment("C2: 输出板 (收集产物)")
    protocol.comment("C3: Tip架")
    protocol.comment("D1: 加热震荡模块 + PCR板")
    protocol.comment("D2: 磁力模块 + PCR板")
    protocol.comment("==================")
    
    # 移液器选择策略
    def determine_pipette_strategy(count):
        """确定最优移液器策略"""
        if count == 1:
            return "single_only"
        elif count % 8 == 0 and count <= 24:
            return "multi_only"
        else:
            return "mixed"  # 8通道+单通道混合
    
    pipette_strategy = determine_pipette_strategy(SAMPLE_COUNT)
    protocol.comment(f"移液器策略: {pipette_strategy}")
    
    # Tip数量计算
    def calculate_tip_requirements(count, strategy):
        """计算所需tip数量"""
        if FAST_MODE:
            # 快速模式下可以重复使用tip，大大减少需求
            if strategy == "single_only":
                tips_needed = 8  # 只需要少量tip重复使用
            elif strategy == "multi_only":
                tips_needed = 8  # 8通道tip重复使用
            else:  # mixed
                tips_needed = 16  # 单通道+8通道各准备一些
            protocol.comment("⚡ 快速模式：tip将重复使用，大幅减少消耗")
        else:
            # 正常模式每次都用新tip
            steps_per_sample = 11  # 每个样本需要的操作步骤数
            
            if strategy == "single_only":
                tips_needed = count * steps_per_sample
            elif strategy == "multi_only":
                columns = count // 8
                tips_needed = columns * steps_per_sample
            else:  # mixed
                full_columns = count // 8
                remaining_samples = count % 8
                tips_needed = full_columns * steps_per_sample + remaining_samples * steps_per_sample
            
            # 添加10%安全余量
            tips_needed = int(tips_needed * 1.1)
        
        return min(tips_needed, 96)  # 每个tip rack最多96个
    
    required_tips = calculate_tip_requirements(SAMPLE_COUNT, pipette_strategy)
    protocol.comment(f"预计需要 {required_tips} 个tips{'（快速模式重复使用）' if FAST_MODE else ''}")

    # ========== 硬件设置 ==========
    def setup_hardware():
        """设置硬件模块和实验器皿"""
        # 加载模块
        heater_shaker = protocol.load_module("heaterShakerModuleV1", location="D1")
        magnetic_block = protocol.load_module("magneticBlockV1", location="D2")
        trash = protocol.load_trash_bin(location="A3")

        # 在模块上加载实验器皿
        pcr_adapter_96 = heater_shaker.load_adapter('opentrons_96_pcr_adapter')
        pcr_plate_magnetic = magnetic_block.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt")
        pcr_plate_magnetic.set_offset(x=-0.2, y=0.0, z=0.7)

        # 根据tip需求加载tip racks
        tip_racks = []
        if required_tips <= 96:
            tip_racks.append(protocol.load_labware("opentrons_flex_96_tiprack_200ul", location="C3"))
        else:
            tip_racks.append(protocol.load_labware("opentrons_flex_96_tiprack_200ul", location="C3"))
            tip_racks.append(protocol.load_labware("opentrons_flex_96_tiprack_200ul", location="B3"))
        
        # 在工作台上加载实验器皿
        reagent_reservoir = protocol.load_labware("nest_12_reservoir_15ml", location="B2")
        pcr_plate_output = protocol.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt", location="C2")
        pcr_plate_output.set_offset(x=-0.2, y=0.0, z=0.7)

        return heater_shaker, magnetic_block, pcr_adapter_96, pcr_plate_magnetic, tip_racks, reagent_reservoir, pcr_plate_output

    def setup_liquids(reagent_reservoir):
        """定义并加载液体"""
        # Define liquids with colors for visualization
        liquid_500mz = protocol.define_liquid(
            name='500mz',
            description='500mz liquid',
            display_color='#0000FF'  # Blue
        )

        liquid_10mz = protocol.define_liquid(
            name='10mz',
            description='10mz liquid',
            display_color='#00FF00'  # Green
        )

        liquid_0mz = protocol.define_liquid(
            name='0mz',
            description='0mz liquid',
            display_color='#FFFFFF'  # Clear
        )

        liquid_magnetic = protocol.define_liquid(
            name='magnetic',
            description='magnetic liquid',
            display_color='#FF0000'  # Red
        )

        liquid_cellfree = protocol.define_liquid(
            name='cellfree',
            description='cellfree liquid',
            display_color='#FFFF00'  # Yellow
        )

        # 根据样本数量计算所需液体体积
        volume_multiplier = {
            'cellfree': 130,
            'magnetic': 30,
            'wash_0mz': 100,
            'wash_10mz': 100,
            'elution_500mz': 50
        }
        
        base_volume = 500  # 最小体积
        for reagent, per_sample_vol in volume_multiplier.items():
            total_needed = per_sample_vol * SAMPLE_COUNT
            final_volume = max(total_needed * 1.2, base_volume)  # 20%余量
            protocol.comment(f"{reagent}: 需要 {total_needed}µL, 准备 {final_volume}µL")

        # Load liquids into the 12-column reservoir (A1-A12)
        # 储液槽布局：A1=cell-free, A2=magnetic, A3=0mz, A4=10mz, A5=500mz
        liquid_assignments = {
            'A1': (liquid_cellfree, max(130 * SAMPLE_COUNT * 1.2, 2000)),   # Cell-free液体
            'A2': (liquid_magnetic, max(50 * SAMPLE_COUNT * 1.2, 1000)),    # 磁珠
            'A3': (liquid_0mz, max(100 * SAMPLE_COUNT * 1.2, 1500)),        # 0mz洗涤液
            'A4': (liquid_10mz, max(100 * SAMPLE_COUNT * 1.2, 1500)),       # 10mz洗涤液
            'A5': (liquid_500mz, max(50 * SAMPLE_COUNT * 1.2, 1000)),       # 500mz洗脱液
        }

        for position, (liquid, volume) in liquid_assignments.items():
            reagent_reservoir.wells_by_name()[position].load_liquid(liquid=liquid, volume=int(volume))
            protocol.comment(f"储液槽 {position}: {liquid.name} - {int(volume)}µL")

    # ========== 移动函数 ==========
    def move_fromMAG_to_new(labware, slot):
        """从磁性模块移动实验器皿到新位置"""
        protocol.move_labware(
            labware=labware,
            new_location=slot,
            use_gripper=True
        )

    def move_to_new_location(labware, slot):
        """移动实验器皿到新位置"""
        protocol.move_labware(
            labware=labware,
            new_location=slot,
            use_gripper=True
        )

    # ========== 操作函数 ==========
    def heat_shake_operation(heater_shaker, temperature=37, rpm=700, duration_minutes=None, duration_seconds=None):
        """执行加热震荡操作"""
        heater_shaker.set_and_wait_for_temperature(temperature)
        heater_shaker.set_and_wait_for_shake_speed(rpm=rpm)
        
        if duration_minutes:
            if FAST_MODE:
                # ⚡ 快速模式：150分钟 → 10秒
                fast_time = 10
                protocol.comment(f"⚡ 快速模式：原{duration_minutes}分钟缩短为{fast_time}秒")
                protocol.delay(seconds=fast_time)
            else:
                protocol.delay(minutes=duration_minutes)
        elif duration_seconds:
            if FAST_MODE:
                # ⚡ 快速模式：300秒 → 5秒
                fast_time = 5
                protocol.comment(f"⚡ 快速模式：原{duration_seconds}秒缩短为{fast_time}秒")
                protocol.delay(seconds=fast_time)
            else:
                protocol.delay(seconds=duration_seconds)
                
        heater_shaker.deactivate_shaker()
        heater_shaker.deactivate_heater()

    def smart_transfer(pipette_single, pipette_multi, source_well, target_wells, volume, mix_after=None):
        """智能选择单通道或8通道移液器进行转移"""
        if pipette_strategy == "single_only":
            for target_well in target_wells:
                pipette_single.pick_up_tip()
                if mix_after:
                    pipette_single.transfer(volume, source_well, target_well, mix_after=(5, 100), new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                else:
                    pipette_single.transfer(volume, source_well, target_well, new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                
                # 快速模式下将tip放回原位置，否则丢弃
                if FAST_MODE:
                    pipette_single.return_tip()
                    protocol.comment("⚡ 快速模式：tip已放回原位置节省枪头")
                else:
                    pipette_single.drop_tip()
        
        elif pipette_strategy == "multi_only":
            # 按列处理
            columns = {}
            for well_name in [w.well_name for w in target_wells]:
                col = well_name[1:]
                if col not in columns:
                    columns[col] = []
                columns[col].append(well_name)
            
            for col, wells_in_col in columns.items():
                pipette_multi.pick_up_tip()
                target_col = target_wells[0].parent.columns()[int(col)-1]
                if mix_after:
                    pipette_multi.transfer(volume, source_well, target_col[0], mix_after=(5, 100), new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                else:
                    pipette_multi.transfer(volume, source_well, target_col[0], new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                
                # 快速模式下将tip放回原位置，否则丢弃
                if FAST_MODE:
                    pipette_multi.return_tip()
                    protocol.comment("⚡ 快速模式：8通道tip已放回原位置节省枪头")
                else:
                    pipette_multi.drop_tip()
        
        else:  # mixed strategy
            # 先用8通道处理完整列
            full_columns = SAMPLE_COUNT // 8
            for col in range(full_columns):
                pipette_multi.pick_up_tip()
                target_col = target_wells[col*8].parent.columns()[col]
                if mix_after:
                    pipette_multi.transfer(volume, source_well, target_col[0], mix_after=(5, 100), new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                else:
                    pipette_multi.transfer(volume, source_well, target_col[0], new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                
                # 快速模式下将tip放回原位置，否则丢弃
                if FAST_MODE:
                    pipette_multi.return_tip()
                    protocol.comment("⚡ 快速模式：8通道tip已放回原位置节省枪头")
                else:
                    pipette_multi.drop_tip()
            
            # 用单通道处理剩余样本
            remaining_start = full_columns * 8
            for i in range(remaining_start, len(target_wells)):
                pipette_single.pick_up_tip()
                if mix_after:
                    pipette_single.transfer(volume, source_well, target_wells[i], mix_after=(5, 100), new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                else:
                    pipette_single.transfer(volume, source_well, target_wells[i], new_tip='never', blow_out=True, aspirate_rate=0.5, dispense_rate=0.5)
                
                # 快速模式下将tip放回原位置，否则丢弃
                if FAST_MODE:
                    pipette_single.return_tip()
                    protocol.comment("⚡ 快速模式：单通道tip已放回原位置节省枪头")
                else:
                    pipette_single.drop_tip()

    def smart_collect(pipette_single, pipette_multi, source_wells, dest_wells, volume):
        """智能收集函数 - 慢速吸取上清液，避免扰动磁珠"""
        protocol.comment(f"--- smart_collect: 开始收集 {volume}uL ---")
        
        if pipette_strategy == "single_only":
            for source_well, dest_well in zip(source_wells, dest_wells):
                pipette_single.pick_up_tip()
                pipette_single.aspirate(volume, source_well.bottom(3), rate=0.3)
                pipette_single.dispense(volume, dest_well, rate=0.5)
                pipette_single.blow_out(dest_well.top())
                
                # 快速模式下将tip放回原位置，否则丢弃
                if FAST_MODE:
                    pipette_single.return_tip()
                    protocol.comment("⚡ 快速模式：收集tip已放回原位置节省枪头")
                else:
                    pipette_single.drop_tip()
        
        else:  # 统一处理 "multi_only" 和 "mixed" 策略
            # 🐛 关键修复：按目标孔位 (dest_wells) 的列进行分组，而不是源孔位
            dest_columns = {}
            for i, dest_well in enumerate(dest_wells):
                col_name = dest_well.well_name[1:]
                if col_name not in dest_columns:
                    dest_columns[col_name] = []
                dest_columns[col_name].append((source_wells[i], dest_well))

            protocol.comment(f"🧪 smart_collect: 发现目标列 {list(dest_columns.keys())}")

            for col_name, well_pairs in dest_columns.items():
                
                # well_pairs 是一个列表，包含 [(源孔1, 目标孔1), (源孔2, 目标孔2), ...]
                # 使用8通道处理有8个孔位的完整列
                if pipette_multi and len(well_pairs) == 8:
                    pipette_multi.pick_up_tip()
                    
                    # 使用第一个孔位来定位源列和目标列的 labware 对象
                    source_col_labware = well_pairs[0][0].parent.columns_by_name()[well_pairs[0][0].well_name[1:]]
                    dest_col_labware = well_pairs[0][1].parent.columns_by_name()[col_name]

                    protocol.comment(f"  -> (8-ch) 处理目标列 {col_name}: 从 {source_col_labware[0].well_name} 到 {dest_col_labware[0].well_name}")
                    
                    pipette_multi.aspirate(volume, source_col_labware[0].bottom(3), rate=0.3)
                    pipette_multi.dispense(volume, dest_col_labware[0], rate=0.5)
                    pipette_multi.blow_out(dest_col_labware[0].top())
                    
                    # 快速模式下将tip放回原位置，否则丢弃
                    if FAST_MODE:
                        pipette_multi.return_tip()
                        protocol.comment("⚡ 快速模式：8通道收集tip已放回原位置节省枪头")
                    else:
                        pipette_multi.drop_tip()
                
                # 使用单通道处理不完整的列
                elif pipette_single:
                    protocol.comment(f"  -> (1-ch) 处理不完整或单孔列 {col_name}")
                    for source_well, dest_well in well_pairs:
                        pipette_single.pick_up_tip()
                        protocol.comment(f"     * 从 {source_well.well_name} 移动到 {dest_well.well_name}")
                        pipette_single.aspirate(volume, source_well.bottom(3), rate=0.3)
                        pipette_single.dispense(volume, dest_well, rate=0.5)
                        pipette_single.blow_out(dest_well.top())
                        
                        # 快速模式下将tip放回原位置，否则丢弃
                        if FAST_MODE:
                            pipette_single.return_tip()
                            protocol.comment("⚡ 快速模式：单通道收集tip已放回原位置节省枪头")
                        else:
                            pipette_single.drop_tip()

        protocol.comment("--- smart_collect: 收集完成 ---")
        protocol.delay(seconds=20 if not FAST_MODE else 2)  # ⚡ 快速模式：20秒→2秒

    def smart_wash_with_heat(pipette_single, pipette_multi, source_well, target_wells, dest_wells, wash_name, volume=100):
        """完整洗涤函数 - 包含加热震荡和磁珠静置"""
        nonlocal plate_current_location
        
        protocol.comment(f"🧪 开始{wash_name}洗涤流程...")
        
        # 先添加洗涤液
        smart_transfer(pipette_single, pipette_multi, source_well, target_wells, volume, mix_after=(5, 100))
        protocol.comment(f"✅ {wash_name}洗涤液添加完成")
        
        # 🔥 移动到加热震荡模块进行混合
        if plate_current_location != "heater_shaker":
            protocol.comment("📦 移动到加热震荡模块进行洗涤混合...")
            heater_shaker.open_labware_latch()
            move_fromMAG_to_new(pcr_plate_magnetic, pcr_adapter_96)
            plate_current_location = "heater_shaker"
            heater_shaker.close_labware_latch()
        
        # 🌀 加热震荡混合洗涤液
        protocol.comment(f"🌀 {wash_name}洗涤混合震荡...")
        if FAST_MODE:
            protocol.comment("⚡ 快速模式：洗涤震荡90秒缩短为9秒")
            heat_shake_operation(heater_shaker, duration_seconds=9)
        else:
            heat_shake_operation(heater_shaker, duration_seconds=90)  # 90秒洗涤震荡
        
        heater_shaker.open_labware_latch()
        
        # 🧲 移动到磁力模块进行分离
        protocol.comment("🧲 移动到磁力模块进行磁性分离...")
        move_to_new_location(pcr_plate_magnetic, magnetic_block)
        plate_current_location = "magnetic_block"
        
        # ⏱️ 磁性分离静置
        protocol.comment("🧲 磁性分离中，静置让磁珠充分沉降...")
        if FAST_MODE:
            protocol.comment("⚡ 快速模式：60秒静置缩短为3秒")
            protocol.delay(seconds=3)  # ⚡ 快速模式：60秒→3秒
        else:
            protocol.delay(seconds=60)  # 60秒静置时间
        
        # 🗑️ 收集洗涤废液
        protocol.comment(f"🗑️ 收集{wash_name}洗涤废液...")
        smart_collect(pipette_single, pipette_multi, target_wells, dest_wells, volume)
        protocol.comment(f"✅ {wash_name}洗涤完成！")

    # ========== 中断恢复函数 ==========
    def checkpoint(step_number, description):
        """检查点函数"""
        if RESUME_FROM_STEP <= step_number:
            protocol.comment(f"✓ 执行步骤 {step_number}: {description}")
            return True
        else:
            protocol.comment(f"⏭ 跳过步骤 {step_number}: {description}")
            return False

    # ========== 主流程 ==========
    # 初始化硬件
    heater_shaker, magnetic_block, pcr_adapter_96, pcr_plate_magnetic, tip_racks, reagent_reservoir, pcr_plate_output = setup_hardware()
    
    # 设置液体
    setup_liquids(reagent_reservoir)

    # 加载移液器
    pipette_single = None
    pipette_multi = None
    
    if pipette_strategy in ["single_only", "mixed"]:
        pipette_single = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=tip_racks)
    
    if pipette_strategy in ["multi_only", "mixed"]:
        pipette_multi = protocol.load_instrument('flex_8channel_1000', 'right', tip_racks=tip_racks)

    # 获取目标孔位
    magnetic_wells = [pcr_plate_magnetic[well] for well in sample_wells]
    
    # 分区收集策略 - 不同步骤产物分开收集
    def generate_output_wells_by_section(sample_wells, section_offset):
        """按区域生成输出孔位，避免混淆 - 重新设计算法"""
        output_wells = []
        base_col = section_offset * 3 + 1  # 每个区域占3列
        
        protocol.comment(f"🔍 调试：section_offset={section_offset}, base_col={base_col}")
        protocol.comment(f"🔍 样本数量：{len(sample_wells)}")
        
        # 🎯 新算法：简单直接的映射策略
        for i, well_name in enumerate(sample_wells):
            row_letter = well_name[0]  # A, B, C, D, E, F, G, H
            
            # 🔥 关键修复：每个区域都从base_col开始填充
            # 对于8个样本，都放在区域的第一列
            # 对于更多样本，按需扩展到后续列
            if len(sample_wells) <= 8:
                # 8个样本或更少：都放在区域第一列
                target_col = base_col
            else:
                # 超过8个样本：按8个一列分布
                col_offset = i // 8
                target_col = base_col + col_offset
            
            if target_col <= 12:  # 确保不超出96孔板范围
                new_well_name = f"{row_letter}{target_col}"
                output_wells.append(pcr_plate_output[new_well_name])
                protocol.comment(f"🔍 样本{i+1}: {well_name} → {new_well_name} (区域{section_offset+1}, 列{target_col})")
            else:
                protocol.comment(f"⚠️ 警告：样本 {well_name} 超出输出板范围")
        
        protocol.comment(f"✅ 区域{section_offset+1}映射完成：{[w.well_name for w in output_wells]}")
        return output_wells

    # 分区收集布局：
    # 列1-3: 上清液废液 (步骤6)
    # 列4-6: 0mz洗涤废液 (步骤7) 
    # 列7-9: 10mz洗涤废液 (步骤8)
    # 列10-12: 最终纯化蛋白 (步骤11) ⭐重要
    output_wells_1 = generate_output_wells_by_section(sample_wells, 0)  # 上清液废液 (列1-3)
    output_wells_2 = generate_output_wells_by_section(sample_wells, 1)  # 0mz洗涤 (列4-6)
    output_wells_3 = generate_output_wells_by_section(sample_wells, 2)  # 10mz洗涤 (列7-9)
    output_wells_4 = generate_output_wells_by_section(sample_wells, 3)  # 最终产物 (列10-12)

    protocol.comment("=== 分区收集布局 ===")
    protocol.comment(f"列1-3 (上清液废液): {[w.well_name for w in output_wells_1[:3]]}...")
    protocol.comment(f"列4-6 (0mz洗涤): {[w.well_name for w in output_wells_2[:3]]}...")
    protocol.comment(f"列7-9 (10mz洗涤): {[w.well_name for w in output_wells_3[:3]]}...")
    protocol.comment(f"列10-12 (最终产物⭐): {[w.well_name for w in output_wells_4[:3]]}...")
    protocol.comment("====================")

    # 执行实验流程
    if checkpoint(1, "转移cell-free液体"):
        smart_transfer(pipette_single, pipette_multi, reagent_reservoir['A1'], magnetic_wells, 130, mix_after=(4, 100))

    if checkpoint(2, "第一次加热震荡（150分钟）"):
        heater_shaker.open_labware_latch()
        move_fromMAG_to_new(pcr_plate_magnetic, pcr_adapter_96)
        plate_current_location = "heater_shaker"
        heater_shaker.close_labware_latch()
        # ⚡ 原150分钟，快速模式缩短为10秒
        heat_shake_operation(heater_shaker, duration_minutes=150)

    # 人工添加磁珠暂停点
    protocol.pause("⚠️ 请在储液槽A2位置手动添加磁珠试剂，然后点击继续")

    if checkpoint(3, "添加磁珠"):
        smart_transfer(pipette_single, pipette_multi, reagent_reservoir['A2'], magnetic_wells, 50)

    if checkpoint(4, "磁珠结合震荡（5分钟）"):
        # ⚡ 原300秒(5分钟)，快速模式缩短为5秒
        heat_shake_operation(heater_shaker, duration_seconds=300)
        heater_shaker.open_labware_latch()

    if checkpoint(5, "磁性分离"):
        if plate_current_location != "magnetic_block":
            move_to_new_location(pcr_plate_magnetic, magnetic_block)
            plate_current_location = "magnetic_block"
        if FAST_MODE:
            protocol.comment("⚡ 快速模式：磁性分离10秒缩短为1秒")
            protocol.delay(seconds=1)  # ⚡ 快速模式：10秒→1秒
        else:
            protocol.delay(seconds=10)

    if checkpoint(6, "转移上清液"):
        protocol.comment("磁性分离完成，静置60秒让磁珠充分沉降...")
        if FAST_MODE:
            protocol.comment("⚡ 快速模式：60秒静置缩短为3秒")
            protocol.delay(seconds=3)  # ⚡ 快速模式：60秒→3秒
        else:
            protocol.delay(seconds=60)  # 60秒静置时间
        smart_collect(pipette_single, pipette_multi, magnetic_wells, output_wells_1, 170)

    if checkpoint(7, "0mz缓冲液洗涤"):
        smart_wash_with_heat(pipette_single, pipette_multi, reagent_reservoir['A3'], magnetic_wells, output_wells_2, "0mz")

    if checkpoint(8, "10mz缓冲液洗涤"):
        smart_wash_with_heat(pipette_single, pipette_multi, reagent_reservoir['A4'], magnetic_wells, output_wells_3, "10mz")

    if checkpoint(9, "500mz缓冲液洗脱"):
        move_fromMAG_to_new(pcr_plate_magnetic, pcr_adapter_96)
        plate_current_location = "heater_shaker"
        heater_shaker.close_labware_latch()
        smart_transfer(pipette_single, pipette_multi, reagent_reservoir['A5'], magnetic_wells, 50, mix_after=(4, 100))

    if checkpoint(10, "最终加热震荡（5分钟）"):
        # ⚡ 原300秒(5分钟)，快速模式缩短为5秒
        heat_shake_operation(heater_shaker, duration_seconds=300)
        heater_shaker.open_labware_latch()

    if checkpoint(11, "最终磁性分离和收集"):
        if plate_current_location != "magnetic_block":
            move_to_new_location(pcr_plate_magnetic, magnetic_block)
            plate_current_location = "magnetic_block"
        if FAST_MODE:
            protocol.comment("⚡ 快速模式：最终分离20秒缩短为2秒")
            protocol.delay(seconds=2)  # ⚡ 快速模式：20秒→2秒
        else:
            protocol.delay(seconds=20)
        smart_collect(pipette_single, pipette_multi, magnetic_wells, output_wells_4, 50)

    protocol.comment(f"🎉 实验完成！成功处理了 {SAMPLE_COUNT} 个样本")
    protocol.comment(f"📊 使用策略: {pipette_strategy}, 消耗tips: ~{required_tips}个")
    protocol.comment(f"📍 输出位置: 上清液({[w.well_name for w in output_wells_1[:3]]}...), 洗脱液({[w.well_name for w in output_wells_4[:3]]}...)")

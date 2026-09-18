from opentrons import protocol_api
from opentrons.types import Point

# 实验要求配置：使用Flex机器人，API版本2.19
requirements = {"robotType": "Flex", "apiLevel": "2.19"}

# === 测试模式开关 ===
TEST_MODE = True  # True=测试模式（枪头回收重复使用），False=正常模式（枪头丢弃）

def run(protocol: protocol_api.ProtocolContext):
    """
    Bradford蛋白质浓度测定自动化协议 (最终优化版 - 2倍体系)
    
    实验设计：
    - 8个待测样本（第4列：A4-H4）
    - 标准曲线3重复（第1-3列：A1-G1, A2-G2, A3-G3）
    - 2倍放大体系确保稀释操作的准确性和稳定性
    
    用户手动操作：
    1. BSA储液(5mg/mL) 60μL 手动加到稀释板A1
    2. 待测样品(5μL × 8) 手动加到检测板第4列
    
    机器人操作：
    1. 制备1套2倍体积的标准曲线梯度稀释
    2. 用单通道高精度分发标准液到检测板3列
    3. 所有孔位加G250试剂并混匀 (稳健方案)
    """

    # === 实验参数配置 ===
    SAMPLE_COUNT = 8          # 待测样本数量
    STANDARD_REPLICATES = 3   # 标准曲线重复次数
    STANDARD_POINTS = 7       # 每条标准曲线的浓度点数
    
    # 计算总孔位数
    total_standard_wells = STANDARD_POINTS * STANDARD_REPLICATES  # 21孔
    total_sample_wells = SAMPLE_COUNT                             # 8孔
    total_wells = total_standard_wells + total_sample_wells       # 29孔
    
    mode_text = "测试模式（枪头回收）" if TEST_MODE else "正常模式（枪头丢弃）"
    protocol.comment(f"=== 实验配置（最终优化版 - {mode_text}）===")
    protocol.comment(f"🔬 体系: 2倍放大体系，确保精度")
    protocol.comment(f"📊 待测样本: {SAMPLE_COUNT}个（用户手动加载）")
    protocol.comment(f"📈 标准曲线: 1套制备 → {STANDARD_REPLICATES}重复分发 = {total_standard_wells}孔")
    protocol.comment(f"🧪 总检测孔位: {total_wells}孔")
    protocol.comment("==========================================")

    # === 硬件配置区域 ===
    
    # 移液器配置
    p200_s = protocol.load_instrument("flex_1channel_1000", "left")      # 左臂：单通道 (p200_s用于高精度操作)
    p1000_m = protocol.load_instrument("flex_8channel_1000", "right")   # 右臂：8通道 (p1000_m用于高效操作)

    # 功能模块配置
    temp_mod = protocol.load_module("temperature module gen2", "C1")        # 温度模块：保持在C1位置

    # === 甲板布局配置 ===
    trash_bin = protocol.load_trash_bin("A3")                              # A3：垃圾桶
    dilution_plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "A2", "Standard Dilution Plate (2x)")
    reagent_reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2", "Reagents Reservoir")
    tiprack_200ul = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C3")
    assay_plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D3", "Final Assay Plate")

    # 移液器与tip盒关联
    p200_s.tip_racks = [tiprack_200ul]
    p1000_m.tip_racks = [tiprack_200ul]

    # === 枪头管理函数 ===
    def smart_drop_tip(pipette):
        """智能枪头管理：根据测试模式决定枪头去向"""
        if TEST_MODE:
            pipette.return_tip()
            protocol.comment("⚡ 测试模式：枪头已放回原位置节省消耗")
        else:
            pipette.drop_tip()
    
    # === 液体定义和颜色可视化 ===
    diluent_liquid = protocol.define_liquid(
        name='稀释液(PBS)', description='蛋白质稀释用PBS缓冲液', display_color='#87CEEB'
    )
    g250_reagent_liquid = protocol.define_liquid(
        name='G250考马斯亮蓝试剂', description='Bradford蛋白质检测试剂', display_color='#191970'
    )

    # === 试剂位置定义 ===
    diluent = reagent_reservoir.wells_by_name()["A1"]
    g250_reagent = reagent_reservoir.wells_by_name()["A2"]

    # === 液体装载到储液槽 (根据2倍体系调整) ===
    # 稀释液体积 (2倍体系): [140, 60, 40, 60, 120, 120, 120] = 660 uL
    single_set_diluent = sum([140, 60, 40, 60, 120, 120, 120])
    diluent_volume = int(single_set_diluent * 1.5)  # 加1.5倍缓冲
    diluent.load_liquid(liquid=diluent_liquid, volume=diluent_volume)
    
    # G250试剂需求量
    g250_per_well = 250
    total_g250_needed = g250_per_well * total_wells
    g250_volume = int(total_g250_needed * 1.3)
    g250_reagent.load_liquid(liquid=g250_reagent_liquid, volume=g250_volume)
    
    protocol.comment("=== 液体装载信息（2倍体系）===")
    protocol.comment(f"💧 A1-稀释液: {diluent_volume}μL")
    protocol.comment(f"🔵 A2-G250试剂: {g250_volume}μL")
    protocol.comment("================================")

    # === 用户手动操作提示 (2倍体系) ===
    protocol.comment("=== 用户手动操作提示 ===")
    protocol.comment("⚠️  请在机器人开始前完成以下手动操作：")
    protocol.comment("1. 向稀释板(A2)的A1孔加入 60μL BSA储液(5mg/mL)")
    protocol.comment("2. 向检测板(D3)第4列(A4-H4)分别加入5μL待测样品")
    protocol.comment("================================")

    # === 实验步骤执行 ===

    protocol.comment("=== 第一阶段：标准曲线梯度稀释制备 (2倍体系) ===")

    # 步骤1.1：为第1列添加稀释液 (2倍体积)
    protocol.comment("为第1列添加稀释液...")
    diluent_vols = [140, 60, 40, 60, 120, 120, 120]  # 对应A-G行的稀释液体积 (2倍)
    diluent_dest_names = [f"{chr(65+i)}1" for i in range(STANDARD_POINTS)]
    diluent_dests = [dilution_plate.wells_by_name()[name] for name in diluent_dest_names]
    
    # 使用单通道精确分配稀释液
    for vol, dest in zip(diluent_vols, diluent_dests):
        p200_s.pick_up_tip()
        p200_s.transfer(vol, diluent, dest, new_tip='never')
        smart_drop_tip(p200_s)

    # 步骤1.2：混匀A1孔的BSA储液
    protocol.comment("混匀A1孔的BSA储液（制备1.5mg/mL标准品）...")
    target_well_A1 = dilution_plate.wells_by_name()["A1"]
    p200_s.pick_up_tip()
    p200_s.mix(10, 180, target_well_A1)  # 200uL总体积，用180uL混匀
    smart_drop_tip(p200_s)

    # 步骤1.3：执行标准曲线的串行稀释 (2倍体系)
    protocol.comment("执行标准曲线的串行稀释...")
    dilution_steps = [
        {'source': 'A', 'dest': 'B', 'mix_vol': 150}, # 140+60 -> 180ul total in B after transfer
        {'source': 'B', 'dest': 'C', 'mix_vol': 140}, # 60+120 -> 160ul total in C after transfer
        {'source': 'C', 'dest': 'D', 'mix_vol': 150}, # 40+120 -> 180ul total in D after transfer
        {'source': 'D', 'dest': 'E', 'mix_vol': 180}, # 60+120 -> 240ul total in E after transfer
        {'source': 'E', 'dest': 'F', 'mix_vol': 180}, # 120+120 -> 240ul total in F after transfer
    ]
    
    protocol.comment("开始梯度稀释，一个枪头完成A→F...")
    p200_s.pick_up_tip()
    for step in dilution_steps:
        source_well = dilution_plate.wells_by_name()[f"{step['source']}1"]
        dest_well = dilution_plate.wells_by_name()[f"{step['dest']}1"]
        
        protocol.comment(f"梯度稀释 {step['source']}→{step['dest']}: 转移120μL")
        p200_s.transfer(120, source_well, dest_well, new_tip='never', blow_out=True, blowout_location='destination well')
        p200_s.mix(10, step['mix_vol'], dest_well)
        
    smart_drop_tip(p200_s)
    protocol.comment("✅ 2倍体系梯度稀释完成！")


    protocol.comment("=== 第二阶段：高精度标准液分发 ===")
    protocol.comment("单通道移液器逐行分发5uL标准品，每行一换枪头确保无污染...")
    
    for i in range(STANDARD_POINTS): # 0-6 for A-G
        row_char = chr(65 + i)
        source_well = dilution_plate.wells_by_name()[f"{row_char}1"]
        dest_wells = [assay_plate.wells_by_name()[f"{row_char}{j}"] for j in range(1, STANDARD_REPLICATES + 1)]
        
        p200_s.pick_up_tip()
        protocol.comment(f"分发 {row_char} 行标准品到检测板...")
        # distribute更适合这种一源多目的地操作
        p200_s.distribute(5, source_well, dest_wells, new_tip='never', disposal_volume=10)
        smart_drop_tip(p200_s)
        
    protocol.comment("✅ 高精度标准液分发完成!")


    protocol.comment("=== 第三阶段：添加G250试剂并混合 (稳健方案) ===")
    protocol.comment("8通道移液器逐列添加250uL G250并混合，每列更换枪头...")

    g250_target_columns = ['1', '2', '3', '4']
    
    for col in g250_target_columns:
        protocol.comment(f"向第{col}列添加G250试剂并混合...")
        p1000_m.pick_up_tip()
        
        target_column_wells = assay_plate.columns_by_name()[col][0]

        # 分两次添加125uL
        p1000_m.transfer(125, g250_reagent, target_column_wells, new_tip='never')
        p1000_m.transfer(125, g250_reagent, target_column_wells, new_tip='never')
        
        # 立即混合
        protocol.comment(f"混合第 {col} 列...")
        p1000_m.mix(5, 180, target_column_wells)
        p1000_m.blow_out(target_column_wells.top()) # 吹出残液
        
        smart_drop_tip(p1000_m)

    protocol.comment("✅ G250试剂添加与混合完成!")

    # === 实验完成总结 ===
    protocol.comment("=== 实验流程完成 ===")
    protocol.comment(f"🔧 运行模式: {mode_text}")
    protocol.comment("📊 请取出D3检测板，在595nm波长下进行吸光度测定")

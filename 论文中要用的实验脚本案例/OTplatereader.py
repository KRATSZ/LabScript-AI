from opentrons import protocol_api
#Gaoyuan SIAT gaoyuanbio@qq.com
# API版本要求
requirements = {"robotType": "Flex", "apiLevel": "2.21"}

def run(protocol: protocol_api.ProtocolContext):
    """
    一个完整的吸收光读板机使用流程示例
    1. 加载模块和孔板
    2. 初始化读板机（多波长模式）
    3. 移动孔板至读板机
    4. 执行读板并导出数据
    5. 在协议中访问并输出一个数据点
    6. 将孔板移回原位并关闭读板机盖子
    """
    protocol.comment("--- 实验开始 ---")

    # 1. 加载模块和实验器具
    pr_mod = protocol.load_module(
        module_name="absorbanceReaderV1",
        location="D3"
    )
    # 将孔板的初始位置设置为 C3
    plate_location = "C3"
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat", 
        location=plate_location
    )
    
    # (在这里可以添加移液等准备样本的步骤)
    
    # 2. 初始化读板机
    protocol.comment("关闭盖子并初始化读板机...")
    pr_mod.close_lid()
    # 使用多波长模式初始化
    pr_mod.initialize(mode="multi", wavelengths=[450, 600])

    # 3. 移动孔板
    protocol.comment("打开盖子并将孔板移入...")
    pr_mod.open_lid()
    protocol.move_labware(
        labware=plate,
        new_location=pr_mod,
        use_gripper=True
    )

    # 4. 执行读板并导出
    protocol.comment("关闭盖子，开始读板...")
    pr_mod.close_lid()
    # 读取数据，赋值给变量并导出到CSV
    plate_data = pr_mod.read(export_filename="final_readout.csv")

    # 5. 在协议内使用数据
    protocol.comment("数据读取完成！")
    # 从返回的字典中获取A1孔在450nm下的读数
    a1_450nm_value = plate_data[450]["A1"]
    protocol.comment(f"示例数据点：孔 A1 @ 450nm = {a1_450nm_value:.3f} OD")
    
    # --- 以下是新增的补充代码 ---

    # 6. 将孔板移回原位并关闭盖子
    protocol.comment("读板完成，准备将孔板移回原位。")
    
    # 步骤 6.1: 打开盖子，准备取出孔板
    pr_mod.open_lid()
    
    # 步骤 6.2: 使用机械臂将孔板从读板机移回到初始槽位 C3
    protocol.comment(f"正在将孔板移回至槽位 {plate_location}...")
    protocol.move_labware(
        labware=plate,
        new_location=plate_location,
        use_gripper=True
    )

    # 步骤 6.3: 关闭读板机盖子，保护仪器
    protocol.comment("关闭读板机盖子。")
    pr_mod.close_lid()
    protocol.comment("--- 实验结束 ---")
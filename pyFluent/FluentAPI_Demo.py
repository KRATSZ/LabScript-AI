"""
FluentAPI_Demo.py - pyFluent 2.0 新式 Fluent Interface API 演示

这个示例展示了如何使用重构后的 pyFluent 库，通过链式调用来编排复杂的实验流程。
相比于原来的手动列表管理方式，新的 API 更加直观、安全且易于维护。

主要特性：
1. Fluent Interface 设计模式 - 链式调用
2. 状态管理 - 防止逻辑错误
3. 自动参数推导 - 减少重复输入
4. 耗材验证 - 确保耗材已定义

作者: Gaoyuan
版本: 2.0.0
日期: 2024
"""

from Protocol import Protocol
from FluentLabware import LabwareType, Nest_position
from FluentLiquidClass import LiquidClass


def main():
    """
    主演示函数：展示一个完整的液体处理流程
    
    实验流程：
    1. 定义工作台布局
    2. FCA 移液操作 (获取枪头 -> 吸液 -> 排液 -> 丢弃枪头)
    3. 生成并保存 .gwl 文件
    """
    print("🧪 pyFluent 2.0 Fluent API 演示")
    print("=" * 50)
    
    # ================================
    # 第一步：初始化协议
    # ================================
    
    print("📋 初始化协议...")
    protocol = Protocol(
        fluent_sn="19905",
        output_file="fluent_api_demo.gwl"
    )
    
    # ================================
    # 第二步：定义工作台布局 (链式调用)
    # ================================
    
    print("🔧 设置工作台布局...")
    protocol.add_labware(
        labware_type=LabwareType.WELL_96_FLAT,
        labware_label="SourcePlate[001]",
        location=Nest_position.Nest61mm_Pos,
        position=1
    ).add_labware(
        labware_type=LabwareType.WELL_96_FLAT,
        labware_label="DestPlate[001]",
        location=Nest_position.Nest61mm_Pos,
        position=2
    ).add_labware(
        labware_type=LabwareType.TIP_1000ul,
        labware_label="TipRack[001]",
        location=Nest_position.Nest61mm_Pos,
        position=3
    )
    
    print(f"   ✅ 已添加 {len(protocol.get_defined_labware())} 个耗材")
    
    # ================================
    # 第三步：FCA 液体处理流程 (链式调用)
    # ================================
    
    print("🔬 执行 FCA 液体处理流程...")
    
    # 获取 FCA 控制器并执行完整流程
    fca = protocol.fca()
    
    # 定义实验参数
    channels = [0, 1, 2, 3]  # 使用前4个通道
    wells = "A1,B1,C1,D1"    # 目标孔位
    volume = 100             # 移液体积 (μL)
    
    try:
        # 链式调用执行完整流程
        fca.get_tips("1000ul", channels) \
           .aspirate(volume, "SourcePlate[001]", wells=wells, 
                    liquid_class="Water Free Single") \
           .dispense(volume, "DestPlate[001]", wells=wells, 
                    liquid_class="Water Free Single") \
           .drop_tips()
        
        print(f"   ✅ FCA 流程完成：{volume}μL x {len(channels)} 通道")
        
    except Exception as e:
        print(f"   ❌ 流程执行失败: {e}")
        return
    
    # ================================
    # 第四步：演示状态管理和错误防护
    # ================================
    
    print("🛡️  演示状态管理和错误防护...")
    
    try:
        # 尝试在没有枪头时吸液 (应该失败)
        fca.aspirate(50, "SourcePlate[001]", wells="A1")
    except Exception as e:
        print(f"   ✅ 状态验证生效: {e}")
    
    try:
        # 尝试使用未定义的耗材 (应该失败)
        fca.get_tips("1000ul", channels)
        fca.aspirate(50, "UndefinedPlate[001]", wells="A1")
    except Exception as e:
        print(f"   ✅ 耗材验证生效: {e}")
        # 清理状态
        fca.drop_tips()
    
    # ================================
    # 第五步：保存和总结
    # ================================
    
    print("💾 保存协议文件...")
    protocol.save()
    
    print("\n📊 协议统计:")
    print(f"   • 总指令数: {protocol.get_command_count()}")
    print(f"   • 定义耗材: {len(protocol.get_defined_labware())} 个")
    print(f"   • 输出文件: {protocol.output_file}")
    
    print("\n🎉 演示完成！")
    print("💡 提示：请在 Tecan FluentControl™ 中导入生成的 .gwl 文件")


def demonstrate_mca_workflow():
    """
    演示 MCA384 工作流程 (可选)
    """
    print("\n" + "=" * 50)
    print("🔬 MCA384 工作流程演示")
    print("=" * 50)
    
    # 由于 MCA384 需要特殊的适配器对象，这里仅演示API结构
    from FluentLabware import MCA384HeadAdapter
    
    protocol = Protocol(
        fluent_sn="19905", 
        output_file="mca_demo.gwl"
    )
    
    # 添加耗材
    protocol.add_labware(LabwareType.WELL_96_FLAT, "MCASource[001]", 
                        Nest_position.Nest61mm_Pos, 1)
    
    # 获取 MCA 控制器
    mca = protocol.mca()
    
    # 创建适配器 (需要根据实际硬件配置)
    adapter = MCA384HeadAdapter(Label="EVA[001]")
    
    try:
        # MCA 链式调用示例
        mca.get_head_adapter(adapter) \
           .pick_up_tips("MCA96 50ul[001]") \
           .drop_head_adapter()
        
        print("   ✅ MCA384 基础流程演示完成")
        
    except Exception as e:
        print(f"   ⚠️  MCA384 演示跳过: {e}")
    
    protocol.save()


def compare_old_vs_new_api():
    """
    对比旧 API 和新 API 的代码风格
    """
    print("\n" + "=" * 50)
    print("🔄 API 对比：旧式 vs 新式")
    print("=" * 50)
    
    print("""
📜 旧式 API (过程式):
    full_script = []
    fca = TecanFCAScriptGenerator()
    
    full_script.append(fca.GetTips("1000ul", [0,1,2,3], "19905"))
    full_script.append(fca.Aspirate([100]*4, "Source[001]", [0,1,2,3], 
                                   "Water Free Single", "A1,B1,C1,D1", "19905"))
    full_script.append(fca.Dispense([100]*4, "Dest[001]", [0,1,2,3], 
                                   "Water Free Single", "A1,B1,C1,D1", "19905"))
    full_script.append(fca.DropTips([0,1,2,3], "19905"))
    
    with open("output.gwl", 'w') as f:
        for cmd in full_script:
            f.write(cmd + "\\n")

✨ 新式 API (Fluent Interface):
    protocol = Protocol(fluent_sn="19905", output_file="output.gwl")
    
    protocol.add_labware(LabwareType.WELL_96_FLAT, "Source[001]", 
                        Nest_position.Nest61mm_Pos, 1) \\
            .add_labware(LabwareType.WELL_96_FLAT, "Dest[001]", 
                        Nest_position.Nest61mm_Pos, 2)
    
    protocol.fca() \\
           .get_tips("1000ul", [0,1,2,3]) \\
           .aspirate(100, "Source[001]", wells="A1,B1,C1,D1") \\
           .dispense(100, "Dest[001]", wells="A1,B1,C1,D1") \\
           .drop_tips()
    
    protocol.save()

🎯 新式 API 优势:
    • 🔗 链式调用，代码更流畅
    • 🛡️ 状态管理，防止逻辑错误  
    • 🔍 自动验证，减少运行时错误
    • 📦 参数复用，减少重复输入
    • 📖 更易读懂，接近自然语言
    """)


if __name__ == "__main__":
    """
    主入口：运行所有演示
    """
    main()
    demonstrate_mca_workflow()
    compare_old_vs_new_api()
    
    print("\n" + "🎊" * 20)
    print("🌟 pyFluent 2.0 - 让自动化更简单！")
    print("🎊" * 20)
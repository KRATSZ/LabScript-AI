"""
Migration_Guide.py - pyFluent 1.x 到 2.x 迁移指南

这个文件演示了如何将现有的 pyFluent 1.x 代码迁移到 2.x 版本。
新版本保持了向后兼容性，同时提供了更现代化的 API 设计。

迁移策略：
1. 渐进式迁移 - 可以混合使用新旧 API
2. 向后兼容 - 原有代码仍能正常工作
3. 逐步优化 - 根据需要采用新特性

作者: Gaoyuan
版本: 2.0.0
"""

import os
from Protocol import Protocol
from FCACommand import TecanFCAScriptGenerator
from WortableCommand import TecanWorktableScriptGenerator
from FluentLabware import LabwareType, Nest_position
from FluentLiquidClass import LiquidClass


def legacy_style_example():
    """
    演示传统的 pyFluent 1.x 风格代码
    这些代码在 2.x 版本中仍然可以正常工作
    """
    print("📜 传统风格代码演示 (向后兼容)")
    print("-" * 40)
    
    # 传统方式：手动管理指令列表
    fluent_sn = "19905"
    file_path = "legacy_style_output.gwl"
    full_script = []
    
    # 实例化生成器 (不传入 protocol 参数)
    fca_gen = TecanFCAScriptGenerator()  # 旧式：不传 protocol
    worktable_gen = TecanWorktableScriptGenerator()  # 旧式：不传 protocol
    
    # 添加耗材 (传统方式)
    full_script.append(
        worktable_gen.AddLabware(
            LabwareType=LabwareType.WELL_96_FLAT,
            LabwareLabel="LegacySource[001]",
            Location=Nest_position.Nest61mm_Pos,
            Position=1
        )
    )
    
    full_script.append(
        worktable_gen.AddLabware(
            LabwareType=LabwareType.WELL_96_FLAT,
            LabwareLabel="LegacyDest[001]",
            Location=Nest_position.Nest61mm_Pos,
            Position=2
        )
    )
    
    # FCA 操作 (传统方式 - 所有参数都必须明确提供)
    channels = [0, 1, 2, 3]
    
    full_script.append(
        fca_gen.GetTips("1000ul", channels, fluent_sn)
    )
    
    full_script.append(
        fca_gen.Aspirate(
            volume=[100] * 4,
            labwarelabel="LegacySource[001]",
            use_channels=channels,
            liquid_class=LiquidClass.Water_Free_Single.value,
            selected_well="A1,B1,C1,D1",
            fluent_sn=fluent_sn
        )
    )
    
    full_script.append(
        fca_gen.Dispense(
            volume=[100] * 4,
            labwarelabel="LegacyDest[001]",
            use_channels=channels,
            liquid_class=LiquidClass.Water_Free_Single.value,
            selected_well="A1,B1,C1,D1",
            fluent_sn=fluent_sn
        )
    )
    
    full_script.append(
        fca_gen.DropTips(channels, fluent_sn)
    )
    
    # 手动写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        for command in full_script:
            f.write(command + "\n")
    
    print(f"   ✅ 传统风格完成，生成了 {len(full_script)} 条指令")
    print(f"   📁 文件: {file_path}")


def modern_style_example():
    """
    演示现代的 pyFluent 2.x 风格代码
    利用新的 Fluent Interface 和状态管理特性
    """
    print("\n✨ 现代风格代码演示 (推荐)")
    print("-" * 40)
    
    # 现代方式：Protocol 统一管理
    protocol = Protocol(
        fluent_sn="19905",
        output_file="modern_style_output.gwl"
    )
    
    # 链式调用添加耗材
    protocol.add_labware(LabwareType.WELL_96_FLAT, "ModernSource[001]", 
                        Nest_position.Nest61mm_Pos, 1) \
            .add_labware(LabwareType.WELL_96_FLAT, "ModernDest[001]", 
                        Nest_position.Nest61mm_Pos, 2)
    
    # 链式调用 FCA 操作（自动状态管理，参数推导）
    protocol.fca() \
           .get_tips("1000ul", [0, 1, 2, 3]) \
           .aspirate(100, "ModernSource[001]", wells="A1,B1,C1,D1") \
           .dispense(100, "ModernDest[001]", wells="A1,B1,C1,D1") \
           .drop_tips()
    
    # 自动保存
    protocol.save()
    
    print(f"   ✅ 现代风格完成，生成了 {protocol.get_command_count()} 条指令")
    print(f"   📁 文件: {protocol.output_file}")


def hybrid_migration_example():
    """
    演示混合风格：逐步从传统代码迁移到现代代码
    这种方式适合大型项目的渐进式迁移
    """
    print("\n🔄 混合风格迁移演示")
    print("-" * 40)
    
    # 步骤1：创建 Protocol 实例，但仍使用传统方式
    protocol = Protocol(fluent_sn="19905", output_file="hybrid_output.gwl")
    
    # 步骤2：部分使用新 API (工作台设置)
    protocol.add_labware(LabwareType.WELL_96_FLAT, "HybridSource[001]", 
                        Nest_position.Nest61mm_Pos, 1)
    
    # 步骤3：部分使用旧 API (获取传统生成器)
    fca = protocol.fca()  # 获取绑定到 protocol 的生成器
    
    # 步骤4：混合调用风格
    # 传统调用（但会自动添加到 protocol 中）
    fca.GetTips("1000ul", [0, 1], fluent_sn="19905")
    
    # 现代调用（链式）
    fca.aspirate(50, "HybridSource[001]", wells="A1,B1") \
       .dispense(50, "HybridSource[001]", wells="C1,D1") \
       .drop_tips()
    
    protocol.save()
    print(f"   ✅ 混合风格完成，生成了 {protocol.get_command_count()} 条指令")


def error_handling_comparison():
    """
    对比新旧版本的错误处理能力
    """
    print("\n🛡️ 错误处理能力对比")
    print("-" * 40)
    
    # === 传统方式：错误只能在运行时发现 ===
    print("📜 传统方式 - 错误在运行时才发现:")
    
    fca_legacy = TecanFCAScriptGenerator()  # 无状态管理
    
    try:
        # 这些调用在代码层面不会报错，但逻辑上是错误的
        cmd1 = fca_legacy.Aspirate([100], "UndefinedPlate", [0], 
                                  "Water Free Single", "A1", "19905")
        cmd2 = fca_legacy.Aspirate([100], "UndefinedPlate", [0], 
                                  "Water Free Single", "A1", "19905")  # 重复吸液但没有丢枪头
        print("   ⚠️  传统方式：逻辑错误未被检测")
    except Exception as e:
        print(f"   ❌ 传统方式错误: {e}")
    
    # === 现代方式：错误在编写时就能发现 ===
    print("\n✨ 现代方式 - 错误在编写时就能发现:")
    
    protocol = Protocol(fluent_sn="19905", output_file="error_test.gwl")
    protocol.add_labware(LabwareType.WELL_96_FLAT, "TestPlate[001]", 
                        Nest_position.Nest61mm_Pos, 1)
    
    fca_modern = protocol.fca()
    
    try:
        # 尝试在没有枪头时吸液
        fca_modern.aspirate(100, "TestPlate[001]", wells="A1")
    except Exception as e:
        print(f"   ✅ 现代方式捕获状态错误: {e}")
    
    try:
        # 尝试使用未定义的耗材
        fca_modern.get_tips("1000ul", [0])
        fca_modern.aspirate(100, "UndefinedPlate[001]", wells="A1")
    except Exception as e:
        print(f"   ✅ 现代方式捕获耗材错误: {e}")


def migration_checklist():
    """
    提供迁移检查清单
    """
    print("\n📋 迁移检查清单")
    print("=" * 50)
    
    checklist = [
        "✅ 确认现有代码在新版本中能正常运行（向后兼容）",
        "✅ 创建 Protocol 实例替代手动列表管理",
        "✅ 使用 add_labware() 方法添加耗材定义",
        "✅ 将生成器实例化改为从 protocol 获取",
        "✅ 逐步采用链式调用风格",
        "✅ 利用自动参数推导减少重复代码",
        "✅ 添加异常处理以利用状态验证",
        "✅ 更新文档和注释",
        "✅ 运行测试确保功能正确",
        "✅ 团队培训新 API 使用方法"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n💡 迁移建议:")
    print("   1. 先确保向后兼容性，再逐步采用新特性")
    print("   2. 优先迁移新项目，老项目可以逐步优化")
    print("   3. 利用状态管理提升代码健壮性")
    print("   4. 采用链式调用提升代码可读性")


def performance_comparison():
    """
    简单的性能对比测试
    """
    print("\n⚡ 性能对比测试")
    print("-" * 40)
    
    import time
    
    # 测试传统方式
    start_time = time.time()
    legacy_style_example()
    legacy_time = time.time() - start_time
    
    # 测试现代方式  
    start_time = time.time()
    modern_style_example()
    modern_time = time.time() - start_time
    
    print(f"\n📊 性能对比结果:")
    print(f"   📜 传统方式: {legacy_time:.4f} 秒")
    print(f"   ✨ 现代方式: {modern_time:.4f} 秒")
    print(f"   📈 性能差异: {abs(modern_time - legacy_time):.4f} 秒")
    print("\n💡 注意: 性能差异主要来自于额外的状态验证和耗材检查")
    print("   这些开销换来了更高的安全性和更少的运行时错误")


def cleanup_demo_files():
    """
    清理演示生成的文件
    """
    demo_files = [
        "legacy_style_output.gwl",
        "modern_style_output.gwl", 
        "hybrid_output.gwl",
        "error_test.gwl"
    ]
    
    print(f"\n🧹 清理演示文件...")
    for file in demo_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"   🗑️  删除: {file}")


if __name__ == "__main__":
    """
    运行完整的迁移指南演示
    """
    print("🚀 pyFluent 迁移指南")
    print("=" * 50)
    
    try:
        legacy_style_example()
        modern_style_example()
        hybrid_migration_example()
        error_handling_comparison()
        migration_checklist()
        performance_comparison()
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("💡 这可能是由于缺少某些依赖或配置问题")
        
    finally:
        cleanup_demo_files()
    
    print(f"\n🎯 迁移指南完成！")
    print("📚 建议阅读 README.md 了解更多详细信息")
    print("🆘 如有问题请查看文档或联系开发团队")
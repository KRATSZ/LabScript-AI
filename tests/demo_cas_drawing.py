#!/usr/bin/env python3
"""
"""

import sys
import time
from pathlib import Path

# 添加 backend 路径到 sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# 同时添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_agent import generate_protocol_code

def main():
    """运行CAS字样绘制的完整演示"""
    
    print("🚀 " + "="*70)
    print("   Opentrons协议代码生成演示：在PCR板上绘制CAS字样")
    print("="*74)
    
    # 用户的自然语言描述
    user_sop = """
实验目标：在PCR板上用墨水画出"CAS"字样

实验步骤：
1. 在B2位置放置一个96孔PCR板
2. 在B3储液槽的A1孔放置黑色墨水
3. 使用1000μL移液器在PCR板上精确画出"CAS"三个字母
4. C字母设计（形成C形状）：
   - 使用孔位：A1, A2, A3, B1, B3, C1, C2, C3
5. A字母设计（形成A形状）：
   - 使用孔位：A5, A6, A7, B5, B7, C5, C6, C7, D6
6. S字母设计（形成S形状）：
   - 使用孔位：A9, A10, A11, B9, B11, C9, C10, C11
7. 每个孔位精确加入20μL黑色墨水
8. 完成后将tip丢弃到垃圾桶
9. 添加适当的注释说明每个步骤

注意事项：
- 确保移液精度和准确性
- 在每个字母之间添加停顿注释
- 最终形成清晰可见的"CAS"字样
"""
    
    # Opentrons Flex 硬件配置
    hardware_config = """
Robot Model: Opentrons Flex
API Version: 2.19

Deck Layout:
A1: opentrons_flex_96_tiprack_1000ul (tip架)
A3: opentrons_1_trash_3200ml_fixed (垃圾桶)
B2: nest_96_wellplate_100ul_pcr_full_skirt (96孔PCR板，绘制目标)
B3: nest_12_reservoir_15ml (储液槽，放置墨水)
D1: heater_shaker_module_gen1 (加热震荡模块)
C1: temperature_module_gen2 (温度控制模块)

Mount Configuration:
Left Mount: flex_1channel_1000 (Flex 1-Channel 1000 μL Pipette)
Right Mount: flex_8channel_1000 (Flex 8-Channel 1000 μL Pipette)
Extension Mount: Flex Gripper

实验材料:
- 黑色食用色素墨水 (放置在B3储液槽的A1孔)
- 96孔PCR板 (用于绘制CAS字样)
"""
    
    print("\n📝 实验描述:")
    print("-" * 50)
    print(user_sop.strip())
    
    print("\n🔧 硬件配置:")
    print("-" * 50)
    print(hardware_config.strip())
    
    print(f"\n⏱️  开始生成协议代码...")
    print("-" * 50)
    
    # 记录开始时间
    start_time = time.perf_counter()
    
    try:
        # 调用实际的代码生成函数
        result = generate_protocol_code(
            sop_markdown=user_sop,
            hardware_config=hardware_config,
            max_iterations=5
        )
        
        # 记录结束时间
        end_time = time.perf_counter()
        generation_time = end_time - start_time
        
        print(f"✅ 代码生成完成！用时: {generation_time:.3f}秒")
        print(f"📊 生成代码长度: {len(result):,} 字符")
        
        # 分析生成的代码
        analyze_generated_code(result)
        
        # 显示生成的代码
        display_generated_code(result)
        
        # 性能统计
        display_performance_stats(generation_time, result)
        
    except Exception as e:
        print(f"❌ 代码生成失败: {e}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

def analyze_generated_code(code):
    """分析生成的代码质量"""
    print(f"\n🔍 代码质量分析:")
    print("-" * 50)
    
    # 统计分析
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    comment_lines = [line for line in lines if line.strip().startswith('#') or 'comment(' in line]
    
    # 功能检查
    checks = {
        "✅ 包含正确的imports": "from opentrons import protocol_api" in code,
        "✅ 包含metadata定义": "metadata" in code and "protocolName" in code,
        "✅ 包含run函数": "def run(protocol:" in code,
        "✅ 加载PCR板": "nest_96_wellplate_100ul_pcr_full_skirt" in code,
        "✅ 加载储液槽": "nest_12_reservoir_15ml" in code or "reservoir" in code.lower(),
        "✅ 加载移液器": "flex_1channel_1000" in code,
        "✅ 包含移液操作": "aspirate" in code and "dispense" in code,
        "✅ 包含tip管理": "pick_up_tip" in code and "drop_tip" in code,
        "✅ 包含CAS字母": all(letter in code for letter in ['A1', 'A5', 'A9']),  # 检查不同字母的起始位置
        "✅ 包含注释说明": len(comment_lines) > 5,
    }
    
    for check, passed in checks.items():
        status = check if passed else check.replace("✅", "❌")
        print(f"  {status}")
    
    print(f"\n📊 代码统计:")
    print(f"  总行数: {len(lines)}")
    print(f"  有效代码行: {len(non_empty_lines)}")
    print(f"  注释行数: {len(comment_lines)}")
    print(f"  注释比例: {len(comment_lines)/len(non_empty_lines)*100:.1f}%")

def display_generated_code(code):
    """显示生成的代码"""
    print(f"\n💻 生成的协议代码:")
    print("=" * 70)
    
    # 如果代码太长，只显示关键部分
    if len(code) > 2000:
        lines = code.split('\n')
        print("# 显示前40行和后10行...")
        for i, line in enumerate(lines[:40]):
            print(f"{i+1:3d}: {line}")
        
        if len(lines) > 50:
            print(f"    ... (省略中间 {len(lines)-50} 行) ...")
            for i, line in enumerate(lines[-10:], len(lines)-9):
                print(f"{i:3d}: {line}")
    else:
        # 显示完整代码
        for i, line in enumerate(code.split('\n'), 1):
            print(f"{i:3d}: {line}")
    
    print("=" * 70)

def display_performance_stats(generation_time, code):
    """显示性能统计"""
    print(f"\n📈 性能统计:")
    print("-" * 50)
    
    chars_per_second = len(code) / generation_time if generation_time > 0 else 0
    
    print(f"  ⏱️  总生成时间: {generation_time:.3f}秒")
    print(f"  📝 代码字符数: {len(code):,}")
    print(f"  🚀 生成速度: {chars_per_second:,.0f} 字符/秒")
    
    # 与期望性能比较
    if generation_time < 5:
        perf_rating = "🟢 优秀"
    elif generation_time < 15:
        perf_rating = "🟡 良好"
    else:
        perf_rating = "🟠 需要优化"
    
    print(f"  🎯 性能评级: {perf_rating}")
    
    # CAS字样复杂度分析
    cas_wells_count = 8 + 9 + 8  # C + A + S 字母的孔位数
    print(f"\n🎨 CAS字样复杂度:")
    print(f"  字母数量: 3个 (C, A, S)")
    print(f"  总孔位数: {cas_wells_count}个")
    print(f"  移液操作数: ~{cas_wells_count}次")
    print(f"  总墨水体积: {cas_wells_count * 20}μL")

def save_result_to_file(code):
    """将生成的代码保存到文件"""
    output_file = Path(__file__).parent / "generated_cas_protocol.py"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"\n💾 代码已保存到: {output_file}")
    except Exception as e:
        print(f"⚠️  保存文件失败: {e}")

if __name__ == "__main__":
    print("🧪 启动Opentrons CAS字样绘制演示...")
    main()
    
    print(f"\n🎉 演示完成！")
    print(f"   这展示了从自然语言描述到可执行Opentrons协议的完整转换过程。")
    print(f"   新的diff机制确保了代码生成的准确性和一致性。")
    print("=" * 74) 
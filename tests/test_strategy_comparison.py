# -*- coding: utf-8 -*-
"""
自动化测试框架: 对比 "增量修复" vs "全量重写" 策略

本脚本旨在通过一系列预定义的、不同复杂度的测试用例，
量化评估两种代码修复策略在成功率、迭代次数和执行速度上的表现。

测试流程:
1. 定义一个包含多个测试用例的列表 (TEST_CASES)。
2. 针对每个测试用例，分别使用 'diff_edit' 和 'from_scratch' 两种策略运行代码生成。
3. 捕获并记录每次运行的关键指标：是否成功、迭代次数、耗时。
4. 将所有结果保存到 'test_results.csv' 文件中以供分析。
"""

import os
import sys
import csv
import time
import re
from datetime import datetime

# 将项目根目录添加到Python路径中，以便能够导入backend模块
# 这使得脚本可以从任何位置运行
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.langchain_agent import run_code_generation_graph

# ============================================================================
# 测试用例矩阵
# ============================================================================
# 根据您提供的真实脚本范例，我们设计了以下覆盖不同复杂度的测试用例。
# 每个用例都包含一个贴近真实的SOP和相应的硬件配置。

TEST_CASES = [
    # --- 类别: 基础操作 (灵感来源: Letterdraw.py) ---
    {
        'name': 'Basic_Transfer_Single_Well',
        'sop': "使用单通道移液器，从A1储液槽中吸取150ul的黑色墨水，并将其分配到B2孔板的C3孔中。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: None
Deck Layout:
  A1: nest_12_reservoir_15ml
  B2: corning_96_wellplate_360ul_flat
  C2: opentrons_flex_96_tiprack_200ul
"""
    },
    {
        'name': 'Basic_Transfer_Multi_Well',
        'sop': "使用单通道移液器，从A1储液槽的A1孔中吸取液体，然后依次分配50ul到B2孔板的A1, B2, C3孔。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: None
Deck Layout:
  A1: nest_12_reservoir_15ml
  B2: corning_96_wellplate_360ul_flat
  C2: opentrons_flex_96_tiprack_200ul
"""
    },
    # --- 类别: 梯度稀释 (灵感来源: 荧光素梯度稀释标定.py) ---
    {
        'name': 'Dilution_Serial_Single_Channel',
        'sop': "执行1:2的系列稀释。首先，向B2板的第1列加入200ul原液，向第2-6列加入100ul PBS缓冲液。然后，使用单通道移液器从第1列吸取100ul转移到第2列并混匀。重复此过程，从第2列到第3列，直到从第5列转移到第6列。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: None
Deck Layout:
  D3: nest_12_reservoir_15ml (A1孔为原液, A2孔为PBS)
  B2: corning_96_wellplate_360ul_flat
  C2: opentrons_flex_96_tiprack_1000ul
"""
    },
    {
        'name': 'Dilution_Serial_8_Channel',
        'sop': "使用8通道移液器进行梯度稀释。首先，向B2板的第1列加入200ul原液，向第2-12列加入100ul PBS缓冲液。然后，用8通道移液器从第1列吸取100ul转移到第2列并混匀。重复此过程，直到从第10列转移到第11列。最后弃掉第11列的100ul液体。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Right Pipette: flex_8channel_1000
Left Pipette: None
Deck Layout:
  D3: nest_12_reservoir_15ml (A1孔为原液, A2孔为PBS)
  B2: corning_96_wellplate_360ul_flat
  C2: opentrons_flex_96_tiprack_1000ul
"""
    },
    # --- 类别: 生化分析模拟 (灵感来源: Brandford测定蛋白质.py) ---
    {
        'name': 'Assay_Add_Reagent',
        'sop': "模拟Bradford实验。1. 使用8通道移液器，将250ul的G250考马斯亮蓝试剂从储液槽的A2孔，添加到检测板的第1、2、3、4列。2. 每加完一列后，立即在该列进行混匀。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Right Pipette: flex_8channel_1000
Left Pipette: None
Deck Layout:
  C2: nest_12_reservoir_15ml (A2孔为G250试剂)
  D3: corning_96_wellplate_360ul_flat
  C3: opentrons_flex_96_tiprack_200ul
"""
    },
    {
        'name': 'Assay_Transfer_Standards',
        'sop': "模拟Bradford标准品分发。使用单通道移液器，从稀释板A1孔吸取5ul标准品，分发到检测板的A1, A2, A3孔。然后，从稀释板B1孔吸取5ul，分发到检测板的B1, B2, B3孔。为A到G行重复此操作。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: None
Deck Layout:
  A2: corning_96_wellplate_360ul_flat (稀释板)
  D3: corning_96_wellplate_360ul_flat (检测板)
  C3: opentrons_flex_96_tiprack_200ul
"""
    },
    # --- 类别: 完整流程工作流 (灵感来源: D2Pexpress%purification.py) ---
    {
        'name': 'Workflow_Magnetic_Beads_Separation',
        'sop': "执行磁珠纯化中的一个步骤。1. 将50ul磁珠从储液槽A2加入到磁力模块上的PCR板的所有样品孔中。2. 在加热震荡模块上以700rpm震荡5分钟进行结合。3. 将PCR板移动回磁力模块，静置2分钟。4. 使用移液器吸走上清液。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Modules:
  - Heater-Shaker Module in D1
  - Magnetic Block in D2
Deck Layout:
  B2: nest_12_reservoir_15ml
  D1: opentrons_96_pcr_adapter with opentrons_96_wellplate_200ul_pcr_full_skirt
  D2: opentrons_96_wellplate_200ul_pcr_full_skirt
  C3: opentrons_flex_96_tiprack_200ul
"""
    },
    {
        'name': 'Workflow_Heat_Shock_And_Transfer',
        'sop': "模拟一个包含加热和转移的流程。1. 将PCR板从B2移动到D1的加热震荡模块上。2. 将模块加热到42摄氏度，并保持60秒。3. 停止加热，并将板子移动回B2。4. 从A1储液槽向板中所有孔各加入100ul液体。",
        'hardware_config': """Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Modules:
  - Heater-Shaker Module in D1
Deck Layout:
  A1: nest_12_reservoir_15ml
  B2: opentrons_96_wellplate_200ul_pcr_full_skirt
  D1: opentrons_96_pcr_adapter
  C3: opentrons_flex_96_tiprack_200ul
"""
    }
]


def run_single_test(case, strategy, max_iterations=5):
    """运行单个测试用例并返回结果"""
    print(f"\n--- Running Test: '{case['name']}' with Strategy: '{strategy}' ---")

    # 定义一个简单的回调报告器来捕获最终的迭代次数
    # LangGraph的状态里有attempts，所以我们可以在最后读取
    # 但为了模拟真实场景和日志记录，我们创建一个闭包来抓取信息
    reporter_data = {'final_attempt': 0}
    def simple_reporter(event_data):
        # 我们可以从这里捕获很多信息，但目前只关心最终迭代次数
        if event_data.get('event_type') == 'iteration_result':
            reporter_data['final_attempt'] = event_data.get('attempt_num', 0)
        # 可以在此添加更多日志记录
        # print(f"DEBUG: {event_data.get('message')}")

    # 格式化输入
    tool_input = f"{case['sop']}\n---CONFIG_SEPARATOR---\n{case['hardware_config']}"
    
    start_time = time.time()
    
    result_str = run_code_generation_graph(
        tool_input,
        max_iterations=max_iterations,
        repair_strategy=strategy,
        iteration_reporter=simple_reporter
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 解析结果
    success = False
    final_code = ""
    error_details = ""

    if "Error:" in result_str or "**协议生成失败报告**" in result_str:
        success = False
        error_details = result_str
    else:
        # 如果不包含错误，我们认为它是成功的
        success = True
        # 从可能包含警告的文本中提取纯代码
        code_match = re.search(r"```python\n(.*?)\n```", result_str, re.DOTALL)
        if code_match:
            final_code = code_match.group(1).strip()
        else:
            final_code = result_str.strip() # 假设直接返回了代码

    iterations = reporter_data['final_attempt']
    # 如果初次就成功，迭代次数是1，如果失败了但没进入循环，可能为0，统一为1
    if success and iterations == 0:
        iterations = 1

    print(f"--- Result: Success={success}, Iterations={iterations}, Time={execution_time:.2f}s ---")

    return {
        'test_name': case['name'],
        'strategy': strategy,
        'success': success,
        'iterations': iterations,
        'time_seconds': execution_time,
        'final_code': final_code,
        'error_details': error_details
    }


def run_all_tests():
    """运行所有测试用例并保存结果"""
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_filename = f"test_results_{timestamp}.csv"
    
    # 定义CSV文件的表头
    fieldnames = ['test_name', 'strategy', 'success', 'iterations', 'time_seconds', 'final_code', 'error_details']
    
    # 使用上下文管理器确保文件被正确关闭
    with open(results_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        print("==========================================================")
        print("          Starting Automated Strategy Comparison Test     ")
        print(f"         Results will be saved to: {results_filename}          ")
        print("==========================================================")
        
        strategies = ['diff_edit', 'from_scratch']
        
        for i, case in enumerate(TEST_CASES):
            for strategy in strategies:
                try:
                    result = run_single_test(case, strategy)
                    writer.writerow(result)
                    csvfile.flush() # 确保每次结果都写入文件
                except Exception as e:
                    print(f"FATAL ERROR while running test '{case['name']}' with strategy '{strategy}': {e}")
                    # 记录这个致命错误到CSV
                    error_result = {
                        'test_name': case['name'],
                        'strategy': strategy,
                        'success': False,
                        'iterations': 0,
                        'time_seconds': 0,
                        'final_code': '',
                        'error_details': f"Test framework caught an unhandled exception: {e}"
                    }
                    writer.writerow(error_result)
            
            print(f"--- Completed Case {i+1}/{len(TEST_CASES)}: '{case['name']}' ---")

    print("\n==========================================================")
    print("              All tests completed!                      ")
    print(f"         Results saved in: {results_filename}               ")
    print("==========================================================")


if __name__ == "__main__":
    run_all_tests() 
# -*- coding: utf-8 -*-
"""
端到端真实世界场景测试
=========================

此文件包含使用真实LLM API调用来测试从用户目标到可执行Opentrons协议的完整流程的测试用d例。
这些测试旨在模拟用户在真实场景中的使用情况。

注意: 这些测试会发出真实的网络请求，并且依赖于 backend/config.py 中的有效API配置。
      测试运行时间可能会较长。
"""
import pytest
import os
import sys

# 将项目根目录添加到Python路径中，以确保模块可以被正确导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.langchain_agent import generate_protocol_code
from backend.opentrons_utils import run_opentrons_simulation

HW_CONFIG_DNA_LIB_PREP = """
Robot Model: Opentrons Flex
API Version: 2.19
Pipettes:
    flex_8channel_1000 on left mount
"""

@pytest.mark.real_api
def test_e2e_simple_dilution_protocol():
    """
    测试一个简单的真实场景：从一个孔中吸取液体并分配到另外三个孔中，模拟一个简单的稀d释/分配过程。
    """
    # 1. 定义用户目标和硬件配置
    hardware_config = """
        Robot Model: Opentrons Flex
        API Version: 2.20
    Left Pipette: flex_1channel_1000
    Right Pipette: None
        Deck Layout:
        A1: opentrons_flex_96_tiprack_1000ul
      B2: corning_96_wellplate_360ul_flat (Source and Destination Plate)
    """
    
    sop_markdown = """
    **Objective:** Perform a simple 1-to-3 distribution.

    **Procedure:**
    1.  Pick up a tip.
    2.  Aspirate 150uL of liquid from well A1 of the plate in slot B2.
    3.  Dispense 50uL of liquid into wells B1, C1, and D1 of the plate in slot B2.
    4.  Drop the tip in the trash.
    """
    
    # 2. 调用代码生成功能
    # 注意: generate_protocol_code 内部会调用LangGraph工作流
    # 我们设置一个较小的迭代次数以加快测试速度
    print("\n--- [E2E Test] Generating protocol for simple dilution... ---")
    generated_code = generate_protocol_code(sop_markdown, hardware_config, max_iterations=3)
    
    # 打印生成的代码以供调试
    print("--- [E2E Test] Generated Code ---")
    print(generated_code)
    print("---------------------------------")
    
    # 3. 断言生成了非空代码
    assert generated_code is not None, "代码生成失败，返回了None"
    assert "Error" not in generated_code, f"代码生成过程中返回了错误: {generated_code}"
    assert "def run(protocol: protocol_api.ProtocolContext):" in generated_code, "生成的代码不包含run函数"

    # 4. 运行模拟并验证结果
    print("--- [E2E Test] Simulating generated protocol... ---")
    simulation_result = run_opentrons_simulation(generated_code, return_structured=True)

    # 打印模拟结果以供调试
    print("--- [E2E Test] Simulation Result ---")
    print(simulation_result)
    print("-----------------------------------")

    # 5. 断言模拟成功
    assert simulation_result.get("success"), \
        f"模拟失败. Details: {simulation_result.get('error_details', 'No details')}" 
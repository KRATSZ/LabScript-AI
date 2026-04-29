# -*- coding: utf-8 -*-
"""
generate_code_node 性能对比测试
=================================

此文件用于精确测量和比较 `generate_code_node` 节点的两种代码生成路径的性能：
- 路径A (完整生成): 从SOP和硬件配置完整生成代码。
- 路径B (Diff修正): 从错误反馈和旧代码生成diff补丁来修正代码。

测试将使用真实的LLM API调用，以包含网络延迟和模型推理时间。
"""
import pytest
import os
import sys
import time
from typing import Dict, Any

# 将项目根目录添加到Python路径中，以确保模块可以被正确导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.langchain_agent import generate_code_node, CodeGenerationState, prepare_feedback_node
from backend.config import VALID_LABWARE_NAMES, VALID_INSTRUMENT_NAMES, VALID_MODULE_NAMES, CODE_EXAMPLES

# --- 测试配置 ---
NUM_RUNS = 3  # 为了节省时间，我们将运行次数减少到3次

# --- 共享的测试数据 ---
HARDWARE_CONFIG = """
Robot Model: Opentrons Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: None
Deck Layout:
  A1: opentrons_flex_96_tiprack_1000ul
  B2: corning_96_wellplate_360ul_flat
"""

SOP_TEXT = "Transfer 50ul from reservoir A1 to plate well A1."

# --- 用于Diff路径测试的数据 ---
# 包含一个明显错误的板载名称 ('_oops' 后缀)
FAULTY_CODE = """
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware(
        load_name="opentrons_flex_96_tiprack_1000ul", location="A1"
    )
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat_oops", location="B2"
    )
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_1000", mount="left", tip_racks=[tiprack]
    )
    
    pipette.pick_up_tip()
    pipette.aspirate(100, plate['A1'])
    pipette.dispense(100, plate['B1'])
    pipette.drop_tip()
"""

# 模拟的Opentrons模拟器错误输出
SIMULATION_ERROR_OUTPUT = """
Error: opentrons_shared_data.labware.dev_types.LabwareLoadError: Cannot find a definition for corning_96_wellplate_360ul_flat_oops in namespace opentrons. Did you mean corning_96_wellplate_360ul_flat?
"""

# 预先准备的、模拟`prepare_feedback_node`生成的反馈
# 这是基于`prepare_feedback_node`中针对LabwareLoadError的逻辑
FEEDBACK_FOR_LLM = {
    "analysis": "The simulation failed with a `LabwareLoadError`. This almost always means a labware `load_name` in your script does not exactly match a name from the `VALID LABWARE NAMES` list, or it is not compatible with the robot type.",
    "action": "Action: Carefully check every `protocol.load_labware()` call. Compare the `load_name` string against the provided list and correct any misspelling or inconsistency. Ensure you are using labware compatible with the specified robot.",
    "error_log": SIMULATION_ERROR_OUTPUT
}

@pytest.mark.real_api
@pytest.mark.performance
class TestNodePerformance:
    """性能测试类"""

    def test_full_generation_performance(self, capsys):
        """测试路径A: 完整代码生成的性能"""
        durations = []
        print(f"\n--- [Perf Test] Running Full Generation Test ({NUM_RUNS} runs) ---")

        for i in range(NUM_RUNS):
            initial_state = CodeGenerationState(
                original_sop=SOP_TEXT,
                hardware_context=HARDWARE_CONFIG,
                python_code=None,
                llm_diff_output=None,
                simulation_result=None,
                feedback_for_llm={},
                attempts=0,
                max_attempts=5,
                iteration_reporter=None 
            )
            
            start_time = time.perf_counter()
            result_state = generate_code_node(initial_state)
            end_time = time.perf_counter()
            
            duration = end_time - start_time
            durations.append(duration)
            print(f"Run {i+1}/{NUM_RUNS}: {duration:.2f}s")

            # 断言确保测试运行正确
            assert result_state["python_code"] is not None
            assert "def run" in result_state["python_code"]

        avg_duration = sum(durations) / len(durations)
        print(f"--- [Perf Test] Full Generation Average: {avg_duration:.2f}s ---")
        
        # 将结果存储为类的属性，以便在另一个测试中访问
        TestNodePerformance.avg_full_gen_time = avg_duration
        
        assert avg_duration > 0

    def test_diff_correction_performance(self, capsys):
        """测试路径B: Diff修正路径的性能"""
        durations = []
        print(f"\n--- [Perf Test] Running Diff Correction Test ({NUM_RUNS} runs) ---")

        for i in range(NUM_RUNS):
            initial_state = CodeGenerationState(
                original_sop=SOP_TEXT,
                hardware_context=HARDWARE_CONFIG,
                python_code=FAULTY_CODE,
                llm_diff_output=None,
                simulation_result={"success": False, "raw_output": SIMULATION_ERROR_OUTPUT},
                feedback_for_llm=FEEDBACK_FOR_LLM,
                attempts=1,  # 关键: 尝试次数 > 0
                max_attempts=5,
                iteration_reporter=None
            )

            start_time = time.perf_counter()
            result_state = generate_code_node(initial_state)
            end_time = time.perf_counter()

            duration = end_time - start_time
            durations.append(duration)
            print(f"Run {i+1}/{NUM_RUNS}: {duration:.2f}s")
            
            # 断言确保测试运行正确
            assert result_state["python_code"] is not None
            assert "corning_96_wellplate_360ul_flat_oops" not in result_state["python_code"]
            assert "corning_96_wellplate_360ul_flat" in result_state["python_code"]

        avg_duration = sum(durations) / len(durations)
        print(f"--- [Perf Test] Diff Correction Average: {avg_duration:.2f}s ---")
        
        TestNodePerformance.avg_diff_corr_time = avg_duration
        assert avg_duration > 0

    def test_performance_comparison(self):
        """比较两种路径的性能"""
        print("\n--- [Perf Test] Performance Comparison ---")
        full_gen_time = getattr(TestNodePerformance, 'avg_full_gen_time', None)
        diff_corr_time = getattr(TestNodePerformance, 'avg_diff_corr_time', None)

        assert full_gen_time is not None, "Full generation test must run before comparison."
        assert diff_corr_time is not None, "Diff correction test must run before comparison."
        
        print(f"Average Full Generation Time: {full_gen_time:.2f}s")
        print(f"Average Diff Correction Time: {diff_corr_time:.2f}s")

        performance_improvement = ((full_gen_time - diff_corr_time) / full_gen_time) * 100
        print(f"Performance Improvement (Diff vs Full): {performance_improvement:.2f}%")

        assert diff_corr_time < full_gen_time, \
            "Assertion Failed: Diff correction path should be faster than full generation." 
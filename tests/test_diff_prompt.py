"""
提示词集成测试
====================

测试新的 CODE_CORRECTION_DIFF_TEMPLATE 能正确工作，包括：
- 提示词模板格式化正确
- 包含所有必要的变量占位符
- 无语法错误
"""

import pytest
import sys
from pathlib import Path

# 添加 backend 路径到 sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from prompts import CODE_CORRECTION_DIFF_TEMPLATE
from langchain_core.prompts import PromptTemplate


class TestDiffPromptTemplate:
    """测试 CODE_CORRECTION_DIFF_TEMPLATE 提示词模板"""
    
    def test_prompt_template_creation(self):
        """测试提示词模板对象能正确创建"""
        # 创建 PromptTemplate 对象
        prompt = PromptTemplate(
            input_variables=["analysis_of_failure", "recommended_action", "full_error_log", "previous_code"],
            template=CODE_CORRECTION_DIFF_TEMPLATE
        )
        
        # 验证模板对象创建成功
        assert prompt is not None
        assert prompt.template == CODE_CORRECTION_DIFF_TEMPLATE
        
        # 验证输入变量正确
        expected_vars = {"analysis_of_failure", "recommended_action", "full_error_log", "previous_code"}
        assert set(prompt.input_variables) == expected_vars
    
    def test_prompt_template_formatting(self):
        """测试提示词模板能正确格式化输入参数"""
        prompt = PromptTemplate(
            input_variables=["analysis_of_failure", "recommended_action", "full_error_log", "previous_code"],
            template=CODE_CORRECTION_DIFF_TEMPLATE
        )
        
        # 准备测试数据
        dummy_data = {
            "analysis_of_failure": "Test analysis of what went wrong",
            "recommended_action": "Test recommended action to fix the issue",
            "full_error_log": "Test error log with details",
            "previous_code": "def test_function():\n    pass"
        }
        
        # 尝试格式化模板
        formatted_prompt = prompt.format(**dummy_data)
        
        # 验证格式化成功且包含输入数据
        assert formatted_prompt is not None
        assert len(formatted_prompt) > 0
        
        # 验证所有输入数据都出现在格式化后的提示词中
        for key, value in dummy_data.items():
            assert value in formatted_prompt, f"Value for {key} not found in formatted prompt"
    
    def test_prompt_template_contains_required_sections(self):
        """测试提示词模板包含所有必要的部分"""
        # 验证模板包含关键指令部分
        assert "SEARCH/REPLACE" in CODE_CORRECTION_DIFF_TEMPLATE
        assert "------- SEARCH" in CODE_CORRECTION_DIFF_TEMPLATE
        assert "=======" in CODE_CORRECTION_DIFF_TEMPLATE  
        assert "+++++++ REPLACE" in CODE_CORRECTION_DIFF_TEMPLATE
        
        # 验证模板包含错误分析相关部分
        assert "{analysis_of_failure}" in CODE_CORRECTION_DIFF_TEMPLATE
        assert "{recommended_action}" in CODE_CORRECTION_DIFF_TEMPLATE
        assert "{full_error_log}" in CODE_CORRECTION_DIFF_TEMPLATE
        assert "{previous_code}" in CODE_CORRECTION_DIFF_TEMPLATE
    
    def test_prompt_template_no_extra_variables(self):
        """测试提示词模板没有未定义的变量占位符"""
        import re
        
        # 查找所有的变量占位符 {variable_name}
        variables_in_template = re.findall(r'\{(\w+)\}', CODE_CORRECTION_DIFF_TEMPLATE)
        
        # 期望的变量列表
        expected_variables = ["analysis_of_failure", "recommended_action", "full_error_log", "previous_code"]
        
        # 验证模板中的变量都在期望列表中
        for var in variables_in_template:
            assert var in expected_variables, f"Unexpected variable {var} found in template"
        
        # 验证所有期望的变量都在模板中
        for var in expected_variables:
            assert var in variables_in_template, f"Expected variable {var} not found in template"
    
    def test_prompt_with_real_error_scenario(self):
        """测试提示词在真实错误场景下的表现"""
        prompt = PromptTemplate(
            input_variables=["analysis_of_failure", "recommended_action", "full_error_log", "previous_code"],
            template=CODE_CORRECTION_DIFF_TEMPLATE
        )
        
        # 模拟真实的错误场景
        real_scenario = {
            "analysis_of_failure": "The simulation failed with a `LabwareLoadError`. This almost always means a labware `load_name` in your script does not exactly match a name from the `VALID LABWARE NAMES` list.",
            "recommended_action": "Action: Carefully check every `protocol.load_labware()` call. Compare the `load_name` string against the provided list and correct any misspelling or inconsistency.",
            "full_error_log": """Traceback (most recent call last):
  File "protocol.py", line 15, in run
    plate = protocol.load_labware('invalid_plate_name', 'D1')
opentrons.protocol_api.labware.LabwareLoadError: cannot find a definition for labware invalid_plate_name""",
            "previous_code": """from opentrons import protocol_api

metadata = {
    'protocolName': 'Test Protocol',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    plate = protocol.load_labware('invalid_plate_name', 'D1')
    tips = protocol.load_labware('opentrons_96_tiprack_1000ul', 'A1')
    
    # Load pipette
    pipette = protocol.load_instrument('p1000_single', 'left', tip_racks=[tips])"""
        }
        
        # 格式化提示词
        formatted_prompt = prompt.format(**real_scenario)
        
        # 验证格式化成功
        assert formatted_prompt is not None
        assert len(formatted_prompt) > 500  # 确保提示词有足够的内容
        
        # 验证关键信息都包含在内
        assert "LabwareLoadError" in formatted_prompt
        assert "invalid_plate_name" in formatted_prompt
        assert "protocol.load_labware" in formatted_prompt
    
    def test_empty_values_handling(self):
        """测试空值处理"""
        prompt = PromptTemplate(
            input_variables=["analysis_of_failure", "recommended_action", "full_error_log", "previous_code"],
            template=CODE_CORRECTION_DIFF_TEMPLATE
        )
        
        # 使用空值进行测试
        empty_data = {
            "analysis_of_failure": "",
            "recommended_action": "",
            "full_error_log": "",
            "previous_code": ""
        }
        
        # 格式化应该成功，即使值为空
        formatted_prompt = prompt.format(**empty_data)
        assert formatted_prompt is not None
        
        # 模板的基本结构应该仍然存在
        assert "SEARCH/REPLACE" in formatted_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
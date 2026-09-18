"""
工作流集成测试
====================

验证整个 LangGraph 工作流在 diff 模式下能正常运行，包括：
- 成功路径测试（首次生成成功）
- 失败->修正路径测试（通过diff自动修正）
- Mock LLM调用以确保测试稳定性
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加 backend 路径到 sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from langchain_agent import (
    run_code_generation_graph,
    generate_code_node,
    simulate_code_node,
    prepare_feedback_node,
    should_continue,
    CodeGenerationState
)


class TestWorkflowSuccessPath:
    """测试工作流成功路径"""
    
    @patch('langchain_agent.code_gen_chain')
    @patch('langchain_agent.run_opentrons_simulation')
    def test_first_attempt_success(self, mock_simulation, mock_code_gen_chain):
        """测试首次尝试就成功的情况"""
        # Mock LLM生成完美的代码
        mock_code_gen_chain.run.return_value = """from opentrons import protocol_api

metadata = {
    'protocolName': 'Test Protocol',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Perfect code that should pass simulation
    pass"""
        
        # Mock模拟成功
        mock_simulation.return_value = {
            'success': True,
            'has_warnings': False,
            'final_status': 'SUCCESS',
            'error_details': '',
            'raw_output': 'Simulation completed successfully'
        }
        
        # 创建测试输入
        test_sop = "Simple test SOP: Add 100ul water to well A1"
        test_hardware = "Robot Model: Opentrons OT-2\nAPI Version: 2.19"
        tool_input = f"{test_sop}\n---CONFIG_SEPARATOR---\n{test_hardware}"
        
        # 运行工作流
        result = run_code_generation_graph(tool_input, max_iterations=3)
        
        # 验证结果
        assert result is not None
        assert "from opentrons import protocol_api" in result
        assert "def run(protocol:" in result
        
        # 验证只调用了一次代码生成（首次成功）
        assert mock_code_gen_chain.run.call_count == 1
        
        # 验证调用了模拟
        assert mock_simulation.call_count == 1


class TestWorkflowFailureToSuccessPath:
    """测试失败->修正路径"""
    
    @patch('langchain_agent.code_correction_chain')
    @patch('langchain_agent.code_gen_chain')
    @patch('langchain_agent.run_opentrons_simulation')
    def test_failure_then_diff_correction_success(self, mock_simulation, mock_code_gen_chain, mock_correction_chain):
        """测试首次失败，然后通过diff修正成功"""
        
        # Mock首次生成的错误代码
        initial_bad_code = """from opentrons import protocol_api

metadata = {
    'protocolName': 'Test Protocol',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware with WRONG name
    plate = protocol.load_labware('invalid_plate_name', 'D1')
    pass"""
        
        mock_code_gen_chain.run.return_value = initial_bad_code
        
        # Mock diff修正
        mock_diff_output = """------- SEARCH
    plate = protocol.load_labware('invalid_plate_name', 'D1')
=======
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'D1')
+++++++ REPLACE"""
        
        mock_correction_chain.run.return_value = mock_diff_output
        
        # Mock模拟结果：第一次失败，第二次成功
        mock_simulation.side_effect = [
            # 第一次模拟：失败
            {
                'success': False,
                'has_warnings': False,
                'final_status': 'FAILED',
                'error_details': 'LabwareLoadError: cannot find a definition for labware invalid_plate_name',
                'raw_output': 'Error: LabwareLoadError'
            },
            # 第二次模拟：成功
            {
                'success': True,
                'has_warnings': False,
                'final_status': 'SUCCESS',
                'error_details': '',
                'raw_output': 'Simulation completed successfully'
            }
        ]
        
        # 创建测试输入
        test_sop = "Load plate and do something"
        test_hardware = "Robot Model: Opentrons OT-2\nAPI Version: 2.19"
        tool_input = f"{test_sop}\n---CONFIG_SEPARATOR---\n{test_hardware}"
        
        # 运行工作流
        result = run_code_generation_graph(tool_input, max_iterations=3)
        
        # 验证最终结果包含修正后的代码
        assert result is not None
        assert "corning_96_wellplate_360ul_flat" in result
        assert "invalid_plate_name" not in result
        
        # 验证调用次数
        assert mock_code_gen_chain.run.call_count == 1  # 只调用首次生成
        assert mock_correction_chain.run.call_count == 1  # 调用一次diff修正
        assert mock_simulation.call_count == 2  # 两次模拟


class TestWorkflowNodeFunctions:
    """测试工作流中的单个节点函数"""
    
    def test_generate_code_node_first_attempt(self):
        """测试代码生成节点的首次尝试"""
        # 创建测试状态
        initial_state = {
            'original_sop': 'Test SOP content',
            'hardware_context': 'Test hardware',
            'python_code': None,
            'attempts': 0,
            'iteration_reporter': None
        }
        
        with patch('langchain_agent.code_gen_chain') as mock_chain:
            mock_chain.run.return_value = "Generated Python code"
            
            # 调用节点函数
            result = generate_code_node(initial_state)
            
            # 验证状态更新
            assert result['python_code'] == "Generated Python code"
            assert result['attempts'] == 1
            assert result.get('llm_diff_output') is None  # 首次尝试不应该有diff
    
    def test_generate_code_node_diff_attempt(self):
        """测试代码生成节点的diff修正尝试"""
        # 创建第二次尝试的状态
        state_with_failure = {
            'original_sop': 'Test SOP content',
            'hardware_context': 'Test hardware',
            'python_code': 'Previous code with error',
            'attempts': 1,
            'feedback_for_llm': {
                'analysis': 'Error analysis',
                'action': 'Recommended action',
                'error_log': 'Error details'
            },
            'iteration_reporter': None
        }
        
        mock_diff = """------- SEARCH
Previous code with error
=======
Fixed code
+++++++ REPLACE"""
        
        with patch('langchain_agent.code_correction_chain') as mock_correction:
            with patch('langchain_agent.apply_diff') as mock_apply_diff:
                mock_correction.run.return_value = mock_diff
                mock_apply_diff.return_value = "Fixed code after diff"
                
                # 调用节点函数
                result = generate_code_node(state_with_failure)
                
                # 验证状态更新
                assert result['python_code'] == "Fixed code after diff"
                assert result['attempts'] == 2
                assert result['llm_diff_output'] == mock_diff
                
                # 验证diff被正确应用
                mock_apply_diff.assert_called_once_with('Previous code with error', mock_diff)
    
    def test_simulate_code_node(self):
        """测试代码模拟节点"""
        test_state = {
            'python_code': 'Test Python code',
            'attempts': 1,
            'iteration_reporter': None
        }
        
        with patch('langchain_agent.run_opentrons_simulation') as mock_sim:
            mock_sim.return_value = {'success': True, 'details': 'Test result'}
            
            result = simulate_code_node(test_state)
            
            assert result['simulation_result'] == {'success': True, 'details': 'Test result'}
            mock_sim.assert_called_once_with('Test Python code', return_structured=True)
    
    def test_prepare_feedback_node(self):
        """测试反馈准备节点"""
        test_state = {
            'simulation_result': {
                'success': False,
                'raw_output': 'Error: LabwareLoadError: cannot find definition for invalid_labware'
            },
            'attempts': 1,
            'iteration_reporter': None
        }
        
        result = prepare_feedback_node(test_state)
        
        # 验证反馈结构
        feedback = result['feedback_for_llm']
        assert 'analysis' in feedback
        assert 'action' in feedback
        assert 'error_log' in feedback
        
        # 验证智能错误分析
        assert 'LabwareLoadError' in feedback['analysis']
        assert 'load_labware' in feedback['action']
    
    def test_should_continue_function(self):
        """测试条件边函数"""
        # 测试成功情况
        success_state = {
            'simulation_result': {'success': True, 'has_warnings': False},
            'attempts': 1,
            'max_attempts': 3,
            'iteration_reporter': None
        }
        assert should_continue(success_state) == "end"
        
        # 测试失败但未达到最大次数
        retry_state = {
            'simulation_result': {'success': False, 'has_warnings': False},
            'attempts': 1,
            'max_attempts': 3,
            'iteration_reporter': None
        }
        assert should_continue(retry_state) == "continue"
        
        # 测试达到最大次数
        max_attempts_state = {
            'simulation_result': {'success': False, 'has_warnings': False},
            'attempts': 3,
            'max_attempts': 3,
            'iteration_reporter': None
        }
        assert should_continue(max_attempts_state) == "end"


class TestWorkflowErrorScenarios:
    """测试工作流错误场景"""
    
    @patch('langchain_agent.code_gen_chain')
    @patch('langchain_agent.run_opentrons_simulation')
    def test_max_attempts_reached(self, mock_simulation, mock_code_gen_chain):
        """测试达到最大尝试次数的情况"""
        # Mock总是生成错误代码
        mock_code_gen_chain.run.return_value = "Bad code"
        
        # Mock总是失败的模拟
        mock_simulation.return_value = {
            'success': False,
            'has_warnings': False,
            'final_status': 'FAILED',
            'error_details': 'Persistent error',
            'raw_output': 'Error output'
        }
        
        # 设置很小的最大尝试次数
        test_sop = "Test SOP"
        test_hardware = "Robot Model: Opentrons OT-2\nAPI Version: 2.19"
        tool_input = f"{test_sop}\n---CONFIG_SEPARATOR---\n{test_hardware}"
        
        result = run_code_generation_graph(tool_input, max_iterations=1)
        
        # 验证结果包含失败信息
        assert "协议生成失败报告" in result
        assert "经过 1 次尝试后失败" in result
        assert "Persistent error" in result
    
    def test_invalid_input_format(self):
        """测试无效输入格式"""
        # 缺少分隔符的输入
        invalid_input = "Just some text without separator"
        
        result = run_code_generation_graph(invalid_input, max_iterations=3)
        
        assert "Error:" in result
        assert "CONFIG_SEPARATOR" in result


class TestReporterIntegration:
    """测试报告器集成"""
    
    @patch('langchain_agent.code_gen_chain')
    @patch('langchain_agent.run_opentrons_simulation')
    def test_reporter_callback_called(self, mock_simulation, mock_code_gen_chain):
        """测试报告器回调是否被正确调用"""
        mock_code_gen_chain.run.return_value = "Test code"
        mock_simulation.return_value = {
            'success': True,
            'has_warnings': False,
            'final_status': 'SUCCESS'
        }
        
        # 创建Mock报告器
        mock_reporter = Mock()
        
        test_sop = "Test SOP"
        test_hardware = "Robot Model: Opentrons OT-2\nAPI Version: 2.19"
        tool_input = f"{test_sop}\n---CONFIG_SEPARATOR---\n{test_hardware}"
        
        result = run_code_generation_graph(
            tool_input, 
            max_iterations=3,
            iteration_reporter=mock_reporter
        )
        
        # 验证报告器被调用
        assert mock_reporter.call_count > 0
        
        # 检查报告器调用的事件类型
        call_args_list = [call[0][0] for call in mock_reporter.call_args_list]
        event_types = [args.get('event_type') for args in call_args_list]
        
        assert 'code_attempt' in event_types
        assert 'simulation_start' in event_types
        assert 'iteration_result' in event_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
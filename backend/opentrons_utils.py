# -*- coding: utf-8 -*-
"""Opentrons utility functions, primarily for simulation."""
import os
import subprocess
import tempfile
import sys
import re
import traceback
import json
from typing import Dict, Any, Union
from pydantic import BaseModel, Field
from pathlib import Path
import platform

# 缩短模拟超时时间（秒）- 正常模拟应该在30秒内完成
SIMULATION_TIMEOUT = 30

class SimulateToolInput(BaseModel):
    """Input schema for the Opentrons simulation tool."""
    protocol_code: str = Field(description="The complete, raw Python code string for the Opentrons protocol.")

def get_error_recommendations(simulation_output: str) -> list[str]:
    """根据模拟输出提供具体错误恢复建议"""
    recommendations = []
    output_lower = simulation_output.lower()
    if "labwareloaderror" in output_lower or "cannot find a definition for labware" in output_lower:
        recommendations.append("载具定义错误: 检查载具名称是否正确，确保使用当前 API 版本支持的载具。")
    if "instrumentloaderror" in output_lower or "cannot find a definition for instrument" in output_lower:
        recommendations.append("移液器定义错误: 确保使用正确的移液器名称和挂载位置。")
    if "moduleloaderror" in output_lower:
        recommendations.append("模块错误: 检查模块类型、位置是否正确。")
    if "syntaxerror" in output_lower:
        recommendations.append("Python 语法错误: 检查代码语法。")
    if "non-existent directory" in output_lower:
        recommendations.append("路径错误: 确保协议中引用的所有文件路径都存在。")
    if "timeout" in output_lower or "too long" in output_lower:
        recommendations.append("模拟超时: 协议可能包含过多复杂操作，尝试简化transfer操作或检查循环逻辑。")
    if not recommendations and "error" in output_lower:
        recommendations.append("通用错误: 检查移液器配置、载具兼容性以及代码逻辑。")
    return recommendations

def get_ot_env_python_executable() -> Path:
    """定位 .ot_env 环境的 Python 解释器路径"""
    project_root = Path(__file__).parent.parent
    # 根据操作系统确定路径
    if platform.system() == "Windows":
        python_exe = project_root / ".ot_env" / "Scripts" / "python.exe"
    else:
        python_exe = project_root / ".ot_env" / "bin" / "python"
    return python_exe


def run_opentrons_simulation(protocol_code: str, return_structured: bool = False) -> Union[str, Dict[str, Any]]:
    """
    通过子进程调用隔离的 .ot_env 环境来安全地运行 Opentrons 模拟。
    优化了超时处理和错误诊断。
    """
    result_data = {
        "success": False, "has_warnings": False, "error_details": "",
        "recommendations": [], "raw_output": "", "final_status": ""
    }

    python_executable = get_ot_env_python_executable()

    if not python_executable.exists():
        error_msg = "错误: 未找到 '.ot_env' 隔离环境。请运行 'scripts/setup-uv.ps1' 脚本来创建它。"
        if return_structured:
            result_data.update({"error_details": error_msg, "final_status": "失败 - 环境缺失"})
            return result_data
        return error_msg

    temp_file_path = ""
    try:
        # 创建临时文件，确保UTF-8编码无BOM
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(protocol_code)
        
        command = [str(python_executable), "-m", "opentrons.simulate", temp_file_path]

        # 添加详细的进程监控
        print(f"🔍 开始模拟: {temp_file_path}")
        print(f"🔧 命令: {' '.join(command)}")
        
        proc = subprocess.run(
            command,
            capture_output=True, 
            text=True,
            encoding='utf-8',
            timeout=SIMULATION_TIMEOUT,
            cwd=str(Path(__file__).parent.parent)  # 确保工作目录正确
        )

        full_output = f"--- Simulation STDOUT ---\n{proc.stdout}\n--- Simulation STDERR ---\n{proc.stderr}"
        result_data["raw_output"] = full_output.strip()

        if proc.returncode == 0:
            result_data["success"] = True
            # Opentrons 模拟成功时也可能在 stderr 中打印警告
            if proc.stderr:
                result_data["has_warnings"] = True
                result_data["warning_details"] = proc.stderr.strip()
                result_data["final_status"] = "成功，但有警告"
            else:
                result_data["final_status"] = "成功"
        else:
            result_data["success"] = False
            result_data["error_details"] = proc.stderr.strip() if proc.stderr else "模拟失败，但未提供错误详情。"
            result_data["recommendations"] = get_error_recommendations(proc.stderr)
            result_data["final_status"] = "失败"

    except subprocess.TimeoutExpired:
        error_msg = f"❌ 模拟超时（超过 {SIMULATION_TIMEOUT} 秒）。可能原因：\n" \
                   f"1. 协议包含过多复杂的transfer操作\n" \
                   f"2. 存在无限循环或长时间计算\n" \
                   f"3. 模拟器卡在某个操作上\n" \
                   f"建议：简化协议或检查transfer操作的复杂度。"
        result_data.update({
            "success": False, 
            "error_details": error_msg, 
            "final_status": "失败 - 超时",
            "recommendations": ["尝试简化transfer操作", "检查是否有无限循环", "分段测试协议的各个部分"]
        })
    except Exception as e:
        error_msg = f"模拟过程中发生意外错误: {e}\n{traceback.format_exc()}"
        result_data.update({"success": False, "error_details": error_msg, "final_status": "失败 - 未知异常"})

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    if return_structured:
        return result_data
    else:
        return result_data["raw_output"]

if __name__ == '__main__':
    # 注意: 由于此模块不再直接导入 opentrons，此处的测试用例需要一个已正确设置的 ot_env 环境才能运行。
    print("--- Testing opentrons_utils.py (Subprocess Mode) ---")

    valid_flex_code = """
from opentrons.protocol_api import ProtocolContext
metadata = {"apiLevel": "2.19"}
def run(protocol: ProtocolContext):
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3')
    pipette = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])
    pipette.pick_up_tip()
    pipette.drop_tip()
    protocol.comment('Flex Test Protocol Complete!')
"""
    print("\n--- Test 1: Valid Flex Protocol ---")
    result1 = run_opentrons_simulation(valid_flex_code, return_structured=True)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    assert result1['success'], "Test 1 Failed"

    error_code = """
from opentrons.protocol_api import ProtocolContext
metadata = {"apiLevel": "2.19"}
def run(protocol: ProtocolContext):
    protocol.load_labware('non_existent_labware_12345', 'A1')
"""
    print("\n--- Test 2: Protocol with Error ---")
    result2 = run_opentrons_simulation(error_code, return_structured=True)
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    assert not result2['success'], "Test 2 Failed"
    assert "recommendations" in result2 and len(result2['recommendations']) > 0, "Test 2 did not provide recommendations"

    print("\n--- All tests complete. Review output. ---") 
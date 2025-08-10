# 1. Imports
import os
import subprocess
import tempfile
import sys
import re
import traceback
import json
from datetime import datetime
from typing import Union

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent, Tool, AgentOutputParser
from langchain import hub
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser
from langchain_core.exceptions import OutputParserException

# =============================================================================
# 用户配置区域 - 请根据您的需求修改以下配置
# =============================================================================
API_KEY = "sk-TnKnlDtgvZgrG9wP543180A16aA34a1a978c90333dCa8746"
BASE_URL = "https://api.pumpkinaigc.online/v1"
MODEL_NAME = "gemini-2.5-pro-preview-06-05"

# 设置环境变量
os.environ["DEEPSEEK_API_KEY"] = API_KEY
os.environ["DEEPSEEK_API_BASE"] = BASE_URL

# =============================================================================
# Opentrons 知识库（保持不变）
# =============================================================================
VALID_LABWARE_NAMES = [
    "agilent_1_reservoir_290ml", "appliedbiosystemsmicroamp_384_wellplate_40ul",
    "axygen_1_reservoir_90ml", "biorad_384_wellplate_50ul",
    "biorad_96_wellplate_200ul_pcr", "corning_12_wellplate_6.9ml_flat",
    "corning_24_wellplate_3.4ml_flat", "corning_384_wellplate_112ul_flat",
    "corning_48_wellplate_1.6ml_flat", "corning_6_wellplate_16.8ml_flat",
    "corning_96_wellplate_360ul_flat", "geb_96_tiprack_1000ul",
    "geb_96_tiprack_10ul", "nest_12_reservoir_15ml", "nest_1_reservoir_195ml",
    "nest_1_reservoir_290ml", "nest_96_wellplate_100ul_pcr_full_skirt",
    "nest_96_wellplate_200ul_flat", "nest_96_wellplate_2ml_deep",
    "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical",
    "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical",
    "opentrons_15_tuberack_falcon_15ml_conical", "opentrons_15_tuberack_nest_15ml_conical",
    "opentrons_24_aluminumblock_generic_2ml_screwcap",
    "opentrons_24_aluminumblock_nest_0.5ml_screwcap",
    "opentrons_24_aluminumblock_nest_1.5ml_screwcap",
    "opentrons_24_aluminumblock_nest_1.5ml_snapcap",
    "opentrons_24_aluminumblock_nest_2ml_screwcap",
    "opentrons_24_aluminumblock_nest_2ml_snapcap",
    "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
    "opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap",
    "opentrons_24_tuberack_generic_2ml_screwcap",
    "opentrons_24_tuberack_nest_0.5ml_screwcap",
    "opentrons_24_tuberack_nest_1.5ml_screwcap",
    "opentrons_24_tuberack_nest_1.5ml_snapcap",
    "opentrons_24_tuberack_nest_2ml_screwcap",
    "opentrons_24_tuberack_nest_2ml_snapcap",
    "opentrons_6_tuberack_falcon_50ml_conical", "opentrons_6_tuberack_nest_50ml_conical",
    "opentrons_96_deep_well_temp_mod_adapter",
    "opentrons_96_aluminumblock_biorad_wellplate_200ul",
    "opentrons_96_aluminumblock_generic_pcr_strip_200ul",
    "opentrons_96_aluminumblock_nest_wellplate_100ul",
    "opentrons_96_deep_well_adapter",
    "opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep",
    "opentrons_96_filtertiprack_1000ul", "opentrons_96_filtertiprack_10ul",
    "opentrons_96_filtertiprack_200ul", "opentrons_96_filtertiprack_20ul",
    "opentrons_96_flat_bottom_adapter",
    "opentrons_96_flat_bottom_adapter_nest_wellplate_200ul_flat",
    "opentrons_96_pcr_adapter",
    "opentrons_96_pcr_adapter_nest_wellplate_100ul_pcr_full_skirt",
    "opentrons_96_tiprack_1000ul", "opentrons_96_tiprack_10ul",
    "opentrons_96_tiprack_20ul", "opentrons_96_tiprack_300ul",
    "opentrons_96_well_aluminum_block",
    "opentrons_96_wellplate_200ul_pcr_full_skirt",
    "opentrons_aluminum_flat_bottom_plate",
    "opentrons_flex_96_filtertiprack_1000ul", "opentrons_flex_96_filtertiprack_200ul",
    "opentrons_flex_96_filtertiprack_50ul", "opentrons_flex_96_tiprack_1000ul",
    "opentrons_flex_96_tiprack_200ul", "opentrons_flex_96_tiprack_50ul",
    "opentrons_flex_96_tiprack_adapter", "opentrons_flex_deck_riser",
    "opentrons_tough_pcr_auto_sealing_lid", "opentrons_universal_flat_adapter",
    "opentrons_universal_flat_adapter_corning_384_wellplate_112ul_flat",
    "thermoscientificnunc_96_wellplate_1300ul",
    "thermoscientificnunc_96_wellplate_2000ul", "usascientific_12_reservoir_22ml",
    "usascientific_96_wellplate_2.4ml_deep"
]

VALID_INSTRUMENT_NAMES = [
    # OT-2 GEN2
    "p20_single_gen2", "p300_single_gen2", "p1000_single_gen2",
    "p20_multi_gen2", "p300_multi_gen2", "p1000_multi_gen2",
    # Flex
    "flex_1channel_50", "flex_1channel_1000",
    "flex_8channel_50", "flex_8channel_1000",
    "flex_96channel_1000"
]

VALID_MODULE_NAMES = [
    # API Names (Prefer these in code)
    "temperatureModuleV2",     # OT-2/Flex API Name
    "thermocyclerModuleV2",    # OT-2/Flex API Name
    "magneticModuleV2",        # OT-2 API Name
    "heaterShakerModuleV1",    # OT-2/Flex API Name
    "magneticBlockV1",         # Flex Only API Name
    # User-facing Names (Less preferred for load_module)
    "temperature module gen2", # OT-2/Flex
    "thermocycler module gen2",# OT-2/Flex
    "magnetic module gen2",    # OT-2/Flex?
]

CODE_EXAMPLES = """
Example 1: Basic Setup (Flex, API 2.20)
```python
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.20"} # Use appropriate API level

def run(protocol: protocol_api.ProtocolContext):
    # load tip rack in deck slot D3
    tiprack = protocol.load_labware(
        load_name="opentrons_flex_96_tiprack_1000ul", location="D3"
    )
    # attach pipette to left mount
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_1000",
        mount="left",
        tip_racks=[tiprack]
    )
    # load well plate in deck slot D2
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat", location="D2"
    )
    # load reservoir in deck slot D1
    reservoir = protocol.load_labware(
        load_name="usascientific_12_reservoir_22ml", location="D1"
    )
    # load trash bin in deck slot A3 (Flex specific - REQUIRED!)
    trash = protocol.load_trash_bin(location="A3")
    # Put protocol commands here
```

Example 2: Basic Transfer (Flex, API 2.20)
```python
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel":"2.20"}

def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat",
        location="D1")
    tiprack_1 = protocol.load_labware(
        load_name="opentrons_flex_96_tiprack_200ul",
        location="D2")
    # IMPORTANT: Flex requires explicit trash bin definition
    trash = protocol.load_trash_bin("A3")
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_1000", # Use a valid Flex instrument name
        mount="left",
        tip_racks=[tiprack_1])

    pipette.pick_up_tip()
    pipette.aspirate(100, plate["A1"])
    pipette.dispense(100, plate["B1"])
    pipette.drop_tip() # Drop into trash bin loaded earlier
```

Example 3: OT-2 Setup (API 2.20)
```python
from opentrons import protocol_api

metadata = {'apiLevel': '2.20'} # Example for OT-2

def run(protocol: protocol_api.ProtocolContext):
    # load tip rack in deck slot 3
    tiprack = protocol.load_labware(
        load_name="opentrons_96_tiprack_300ul", location="3" # Use OT-2 slot numbering
    )
    # attach pipette to left mount
    pipette = protocol.load_instrument(
        instrument_name="p300_single_gen2", # Use a valid OT-2 instrument name
        mount="left",
        tip_racks=[tiprack]
    )
    # load well plate in deck slot 2
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat", location="2"
    )
    # load tube rack in deck slot 1
    tube_rack = protocol.load_labware(
        load_name="opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap", location="1"
    )
    # OT-2 uses fixed trash in slot 12 by default, no need to load trash bin
    # Put protocol commands here
```
"""

# =============================================================================
# Opentrons 仿真工具函数（优化本地化支持）
# =============================================================================
def clean_protocol_code(protocol_code: str) -> str:
    """清理协议代码，确保只包含纯净的 Python 代码"""
    if not protocol_code or not isinstance(protocol_code, str):
        return ""
    
    # 按行处理
    lines = protocol_code.split('\n')
    clean_lines = []
    code_started = False
    run_function_found = False
    in_run_function = False
    brace_count = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        # 检查是否是代码开始的标志
        if any(line_stripped.startswith(starter) for starter in 
               ["from opentrons import", "metadata =", "requirements ="]):
            if not code_started:  # 只处理第一次出现
                code_started = True
            elif run_function_found and not in_run_function:
                # 如果已经找到了完整的代码块，停止处理
                break
        
        # 如果代码还没开始，跳过这行
        if not code_started:
            continue
        
        # 检查是否是明显的日志行（包含时间戳）
        if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line_stripped):
            continue
            
        # 检查是否是污染内容
        pollution_patterns = [
            r"✔ 协议成功运行！.*",
            r"--- 结果:.*",
            r"--- 仿真.*",
            r"--- 日志:.*", 
            r"--- 结束.*",
            r"INFO:.*",
            r"DEBUG:.*",
            r"Observation:.*",
            r"Action:.*",
            r"Thought:.*",
            r"Final Answer:.*",
            r"```python.*",
            r"```.*",
            r"加载实验室器具.*",
            r"加载移液管.*",
            r"加载垃圾桶.*",
            r"Picking up tip.*",
            r"Aspirating.*",
            r"Dispensing.*",
            r"Dropping tip.*",
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}.*",  # 时间戳格式的日志
            r"opentrons\..*INFO.*",  # Opentrons日志
            r"opentrons\..*DEBUG.*",  # Opentrons调试日志
            r"Homing.*",  # 归位日志
        ]
        
        is_pollution = False
        for pattern in pollution_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                is_pollution = True
                break
        
        # 检查是否是明显的非Python代码行
        non_python_indicators = [
            "--- ", "✔ ", "INFO:", "DEBUG:", "ERROR:", "WARNING:",
            "Observation:", "Action:", "Thought:", "Final Answer:",
            "```", "加载", "Picking up", "Aspirating", "Dispensing", "Dropping",
            "Homing", "Connecting to hardware"
        ]
        
        if any(line_stripped.startswith(indicator) for indicator in non_python_indicators):
            is_pollution = True
        
        # 特殊检查：如果行包含opentrons日志关键字，跳过
        if any(keyword in line for keyword in ["opentrons.hardware_control", "thread_manager", "ot3api"]):
            is_pollution = True
        
        # 检查run函数
        if line_stripped.startswith("def run("):
            if run_function_found:
                # 如果已经找到了一个run函数，停止处理
                break
            run_function_found = True
            in_run_function = True
            brace_count = 0
        
        # 如果在run函数内，跟踪缩进来判断函数是否结束
        if in_run_function and line.strip():
            # 如果这行不是空行且没有缩进（或只有很少缩进），可能是函数结束
            if len(line) - len(line.lstrip()) <= 0 and not line_stripped.startswith("def run("):
                # 函数可能结束了
                if not any(line_stripped.startswith(keyword) for keyword in ["#", "\"\"\"", "'''"]):
                    in_run_function = False
        
        # 如果不是污染内容，保留这行
        if not is_pollution:
            clean_lines.append(line)
    
    cleaned_code = '\n'.join(clean_lines).strip()
    
    # 验证清理后的代码
    if not cleaned_code:
        return ""
    
    # 确保代码包含基本结构
    if "from opentrons import" not in cleaned_code:
        return ""
    
    if "def run(" not in cleaned_code:
        return ""
    
    print(f"DEBUG: 代码清理前长度: {len(protocol_code)}, 清理后长度: {len(cleaned_code)}")
    print(f"DEBUG: 清理后的代码预览:\n{cleaned_code[:200]}...")
    
    return cleaned_code

def run_opentrons_simulation(protocol_code: str, robot_type: str = "OT-2") -> str:
    """
    运行Opentrons协议仿真并返回结果。
    优化版本：返回给Agent更简洁、更明确的结果。
    """
    # 首先清理协议代码，确保是纯净的 Python 代码
    cleaned_code = clean_protocol_code(protocol_code)
    
    if not cleaned_code:
        return "--- 结果: 仿真失败 ---\n错误: 输入的代码为空或无效。"
    
    # 显示清理后的代码（仅前几行用于调试）
    code_preview = '\n'.join(cleaned_code.split('\n')[:5])
    print(f"DEBUG: 清理后的代码预览:\n{code_preview}...")
    
    simulate_command = 'opentrons_simulate'
    possible_bin_paths = []

    try:
        subprocess.run(f'{simulate_command} --version', check=True, capture_output=True, text=True, errors='ignore', shell=True)
        print(f"INFO: 在 PATH 中找到 '{simulate_command}'")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"INFO: 在 PATH 中未找到 '{simulate_command}'，搜索常见位置...")
        try:
            python_executable_path = sys.executable
            possible_bin_paths = [
                os.path.join(os.path.dirname(python_executable_path)),
                os.path.join(sys.prefix, 'bin'),
                os.path.join(sys.prefix, 'Scripts'),  # Windows 虚拟环境
                '/usr/local/bin',
                os.path.expanduser('~/.local/bin')
            ]
            
            # 添加更多可能的路径
            for path in sys.path:
                if 'site-packages' in path:
                    bin_path = os.path.join(path, '..', '..', 'bin')
                    if os.path.isdir(bin_path): possible_bin_paths.append(bin_path)
                    bin_path_alt = os.path.join(path, 'bin')
                    if os.path.isdir(bin_path_alt): possible_bin_paths.append(bin_path_alt)
                    # Windows Scripts 目录
                    scripts_path = os.path.join(path, '..', '..', 'Scripts')
                    if os.path.isdir(scripts_path): possible_bin_paths.append(scripts_path)

            possible_bin_paths = sorted(list(set(os.path.abspath(p) for p in possible_bin_paths if os.path.isdir(p))))

            opentrons_simulate_path = None
            print(f"INFO: 搜索 'opentrons_simulate' 位置: {possible_bin_paths}")
            for path in possible_bin_paths:
                # Windows 和 Unix 系统的可执行文件扩展名
                potential_names = ['opentrons_simulate', 'opentrons_simulate.exe']
                for name in potential_names:
                    potential_path = os.path.join(path, name)
                    if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
                        opentrons_simulate_path = potential_path
                        print(f"INFO: 找到 'opentrons_simulate' 位置: {opentrons_simulate_path}")
                        break
                if opentrons_simulate_path:
                    break

            if not opentrons_simulate_path:
                error_msg = f"错误: 未找到 'opentrons_simulate' 命令。搜索路径: {possible_bin_paths}"
                print(error_msg)
                return error_msg

            subprocess.run([opentrons_simulate_path, '--version'], check=True, capture_output=True, text=True, errors='ignore')
            simulate_command = opentrons_simulate_path

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = f"错误: 即使搜索后也未找到 'opentrons_simulate' 命令。错误: {e}. 搜索路径: {possible_bin_paths}."
            print(error_msg)
            return error_msg

    temp_file_path = None
    result_text = f"--- 正在运行代码仿真 ---\n{cleaned_code}\n---\n"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(cleaned_code)  # 使用清理后的代码
            temp_file_path = temp_file.name

        cmd = [simulate_command, temp_file_path]
        use_shell = False

        print(f"INFO: 执行仿真命令: {' '.join(cmd)}")
        
        # 设置环境变量强制使用 UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8',
            errors='replace',  # 改为 replace 而不是 ignore，可以看到问题字符
            shell=use_shell,
            env=env  # 传递修改后的环境变量
        )

        stdout = process.stdout.strip() if process.stdout else ""
        stderr = process.stderr.strip() if process.stderr else ""

        result_text += f"--- 仿真 STDOUT: ---\n{stdout}\n---\n"
        result_text += f"--- 仿真 STDERR: ---\n{stderr}\n---\n"

        # 更健壮的仿真结果分析
        # 定义表明严重失败的错误模式
        critical_error_patterns = [
            "opentrons.protocols.types",  # 协议层面的错误
            "Exception:",
            "Error:",
            "Traceback (most recent call last):"
        ]
        
        # 在 stderr 中检查关键错误，忽略常见警告
        has_critical_error = any(p in stderr for p in critical_error_patterns)
        
        # 成功条件：退出代码为 0 且 stderr 中没有发现严重错误
        if process.returncode == 0 and not has_critical_error:
            # 从 stdout 日志中提取简洁的摘要
            log_lines = stdout.strip().split('\n')
            
            # 找到协议命令执行的起始点
            start_index = -1
            for i, line in enumerate(log_lines):
                if "Picking up tip" in line or "Aspirating" in line or "Dispensing" in line:
                    start_index = i
                    break
            
            if start_index != -1:
                run_log = '\n'.join(log_lines[start_index:])
            else:
                # 如果找不到特定命令，则回退到使用最后几行日志
                run_log = '\n'.join(log_lines[-10:]) if len(log_lines) > 10 else stdout

            return (
                "--- 结果: 仿真成功 ---\n"
                "✔ 协议成功运行！\n"
                f"--- 摘要 ---\n{run_log.strip()}"
            )
        
        # 失败条件：退出代码非零 或 stderr 中存在严重错误
        else:
            # 从 stderr 中提取最相关的错误信息
            error_lines = stderr.strip().split('\n')
            
            # 过滤掉 opentrons 有时会打印的、无害的警告信息
            common_warnings = [
                "robot_settings.json not found",
                "Belt calibration not found",
                "Deck calibration not found"
            ]
            
            meaningful_error_lines = [
                line for line in error_lines 
                if not any(warning in line for warning in common_warnings)
            ]
            
            # 如果过滤后内容为空，回退到使用未经过滤的 stderr
            if not meaningful_error_lines:
                meaningful_error_lines = error_lines

            # 尝试定位具体的错误行，否则使用最后几行作为错误信息
            error_message = ""
            # 从后向前查找，以获取最根本的错误
            for line in reversed(meaningful_error_lines):
                if any(p in line for p in critical_error_patterns):
                    error_message = line.strip()
                    break
            
            if not error_message:
                error_message = '\n'.join(meaningful_error_lines[-5:])

            return (
                "--- 结果: 仿真失败 ---\n"
                f"错误: {error_message}\n"
                "请修正代码后重试。"
            )

    except Exception as e:
        result_text += f"--- 仿真执行错误: {e} ---\n"
        result_text += f"Traceback:\n{traceback.format_exc()}\n"
        result_text += "--- 结果: 仿真失败 (执行异常) ---\n"
        print(f"ERROR: 仿真执行异常: {e}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"INFO: 删除临时文件: {temp_file_path}")
            except OSError as e:
                print(f"\n警告: 无法删除临时文件 {temp_file_path}: {e}")

    max_output_length = 3500
    if len(result_text) > max_output_length:
        start_kept = 1000
        end_kept = max_output_length - start_kept - len("\n... [仿真输出被截断] ...\n")
        result_text = (
            result_text[:start_kept]
            + "\n... [仿真输出被截断] ...\n"
            + result_text[-end_kept:]
        )
        print("INFO: 仿真输出被截断")

    return result_text

# =============================================================================
# 对话历史管理类
# =============================================================================
class ChatSession:
    """管理对话会话的类"""
    
    def __init__(self):
        self.history = []
        self.current_code = None
        self.robot_type = None
    
    def add_user_message(self, message: str):
        """添加用户消息到历史"""
        self.history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message: str, code: str = None):
        """添加助手消息到历史"""
        self.history.append({"role": "assistant", "content": message})
        if code:
            self.current_code = code
    
    def get_history_string(self) -> str:
        """获取格式化的历史记录字符串"""
        if not self.history:
            return "这是我们的第一次对话。"
        
        history_str = "=== 对话历史 ===\n"
        for i, msg in enumerate(self.history, 1):
            role = "用户" if msg["role"] == "user" else "AI助手"
            history_str += f"{i}. {role}: {msg['content']}\n"
        history_str += "=== 历史结束 ===\n\n"
        return history_str
    
    def get_current_context(self) -> str:
        """获取当前上下文信息"""
        context = f"机器人类型: {self.robot_type or '未设置'}\n"
        if self.current_code:
            context += f"当前代码版本:\n```python\n{self.current_code}\n```\n"
        else:
            context += "当前还没有生成代码。\n"
        return context

# =============================================================================
# LangChain 工具和 Agent 设置
# =============================================================================
class SimulateToolInput(BaseModel):
    protocol_code: str = Field(description="完整的 Opentrons Python 协议代码字符串")

active_robot_type = "Flex" # 全局变量，用于在工具调用中访问

def run_simulation_wrapper(protocol_code: str) -> str:
    """包装器函数，允许工具调用时访问全局机器人类型"""
    global active_robot_type
    return run_opentrons_simulation(protocol_code, robot_type=active_robot_type)

simulate_tool = Tool(
    name="opentrons_simulator",
    func=run_simulation_wrapper,
    description="""Simulate Opentrons Python protocol code using 'opentrons_simulate'.

Input Requirements:
- ONLY pure Python code (no logs, outputs, or previous simulation results)
- Complete Python code string (including imports, requirements/metadata, and run function)
- Code must start with 'from opentrons import' or 'requirements =' or 'metadata ='
- NO markdown formatting, NO extra text, NO previous outputs

The tool automatically cleans the input to remove any contamination from previous runs.

Output Analysis:
- Check the '--- 结果: ---' line for success/failure status
- If you see '✔ 协议成功运行！' it means SUCCESS - immediately stop and output Final Answer
- If failure: analyze traceback/errors and create clean, corrected Python code for re-simulation

CRITICAL: Once you see success indicator, absolutely DO NOT call tools again, immediately provide Final Answer!""",
    args_schema=SimulateToolInput
)

tools = [simulate_tool]

llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL,
    temperature=0.05,
    streaming=True,
)

# Updated Prompt Template with English instructions for better model understanding
prompt_template_str = """
You are a professional Opentrons protocol generation assistant. Generate or modify Opentrons Python code based on user requests and chat history.

{chat_history}

Current Context:
{current_context}

You have access to the following tools:
{tools}

CRITICAL RULES:
1.  **Tool Use Format**: For each step using a tool, you MUST use this format:
    Thought: [Your reasoning for using the tool.]
    Action: [The tool name, e.g., opentrons_simulator]
    Action Input: [The input for the tool. For opentrons_simulator, this MUST be the complete, raw Python code.]
    Observation: [The result from the tool will be inserted here.]

2.  **Success Condition**: When you see "✔ 协议成功运行！" in the Observation, the simulation was successful. You MUST NOT call any more tools. You must immediately proceed to the final answer.

3.  **Final Answer Format**: The final answer MUST follow this exact format:
    Thought: I have successfully generated and verified the protocol. I will now output the final code.
    Final Answer: [The complete, final, raw Python code. NO extra text, NO explanations, and NO markdown formatting like ```python.]

Your task is to follow the user's request, use the simulator to verify your code, and then output the single, correct, final code block.

--- Context: Valid Opentrons Information ---

Valid labware names: {valid_labware}
Valid instrument names: {valid_instruments}  
Valid module API names: {valid_modules}

Code examples:
{code_examples}

--- Context End ---

Question: {input}

Begin!

{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(prompt_template_str)
prompt = prompt.partial(
    valid_labware=", ".join(VALID_LABWARE_NAMES),
    valid_instruments=", ".join(VALID_INSTRUMENT_NAMES),
    valid_modules=", ".join(VALID_MODULE_NAMES),
    code_examples=CODE_EXAMPLES,
    tool_names=[tool.name for tool in tools]  # 添加工具名称列表
)

# 3. Agent和执行器
# 修改OutputParser使其能处理更多异常情况
class CustomOpentronsOutputParser(AgentOutputParser):
    """
    能够处理最终答案和可解析操作混合的输出解析器，
    并能从不完整的输出中提取代码。
    """
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # 捕获最终答案和操作混合的特殊情况
        if "Final Answer:" in text and "Action:" in text:
            # 这是一个 LangChain 的已知问题，我们优先选择 Final Answer
            final_answer_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                return AgentFinish({"output": final_answer}, text)
        
        # 正常的解析逻辑
        try:
            # 尝试使用 ReAct 解析器
            return ReActSingleInputOutputParser().parse(text)
        except OutputParserException as e:
            # 如果解析失败，我们将整个文本作为最终输出来处理
            # 这样可以捕获到被截断或格式不正确的代码
            print(f"INFO: 标准解析失败 ({e})，将整个文本作为输出来处理。")
            return AgentFinish({"output": text}, text)

# 使用自定义的解析器
output_parser = CustomOpentronsOutputParser()

agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=15,  # 增加迭代次数以应对复杂请求
    handle_parsing_errors=True, # 让AgentExecutor自己处理一些解析错误
    # 直接在这里使用新的解析器
    output_parser=CustomOpentronsOutputParser()
)

# =============================================================================
# 用户交互和界面函数
# =============================================================================
def get_robot_type():
    """获取用户选择的机器人类型"""
    print("\n=== Opentrons 机器人选择 ===")
    print("1: Flex (默认)")
    print("2: OT-2")
    choice = input("选择机器人类型 (1/2) 或按 Enter 使用默认: ").strip()

    if choice == "2":
        return "OT-2"
    return "Flex"

def get_initial_request(robot_type):
    """获取初始用户请求"""
    print(f"\n=== 使用 {robot_type} 机器人 ===")
    use_default = input("使用默认协议示例? (y/n, 默认: y): ").strip().lower() != "n"

    if use_default:
        if robot_type == "Flex":
            return f"创建一个 Flex 协议 (API 2.20)，将 50uL 液体从位于甲板槽 D1 的 96 孔板 'source_plate' 的 A1 孔转移到位于甲板槽 D2 的另一个 96 孔板 'destination_plate' 的 B2 孔。使用 flex_1channel_1000 移液器。吸头架是位于甲板槽 D3 的 opentrons_flex_96_tiprack_1000ul 吸头架。"
        else:  # OT-2
            return f"创建一个 OT-2 协议 (API 2.20)，将 50uL 液体从位于甲板槽 1 的 96 孔板 'source_plate' 的 A1 孔转移到位于甲板槽 2 的另一个 96 孔板 'destination_plate' 的 B2 孔。使用 p300_single_gen2 移液器。吸头架是位于甲板槽 3 的 opentrons_96_tiprack_300ul 吸头架。"
    else:
        print("\n请输入您的自定义协议请求。请具体说明:")
        print("- 机器人类型 (OT-2 或 Flex)")
        print("- API 版本 (Flex 使用 2.20)")
        print("- 器皿类型和位置")
        print("- 移液器型号")
        print("- 体积和操作")
        return input("\n您的请求: ").strip()

def save_protocol_to_file(code: str, robot_type: str) -> str:
    """保存协议到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"opentrons_{robot_type.lower()}_{timestamp}.py"
    
    filename = input(f"输入文件名保存协议 (默认: {default_filename}): ").strip()
    if not filename:
        filename = default_filename
    
    if not filename.endswith('.py'):
        filename += '.py'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        full_path = os.path.abspath(filename)
        print(f"协议已保存到: {full_path}")
        return full_path
    except Exception as e:
        print(f"保存协议时出错: {e}")
        return None

def display_code_with_line_numbers(code: str):
    """显示带行号的代码"""
    lines = code.split('\n')
    print("\n=== 生成的代码 ===")
    for i, line in enumerate(lines, 1):
        print(f"{i:3d}: {line}")
    print("=== 代码结束 ===\n")

def extract_code_from_response(response: str) -> str:
    """从 AI 响应中提取代码 - 最终优化版本"""
    if not isinstance(response, str):
        return str(response)

    # 完整性检查：确保响应包含一个完整的代码块
    if "from opentrons import" not in response or "def run(" not in response:
        # 如果响应中没有明显代码，可能整个响应就是错误信息
        if len(response) < 200: # 假设短响应是错误消息
             print(f"DEBUG: 响应中未找到代码，可能为错误消息: {response}")
        return "未能提取代码"

    # 查找所有可能的代码块
    # 策略：找到所有以 'from opentrons import' 开头的块
    code_blocks = re.findall(r"(from opentrons import.*?)(?=from opentrons import|$)", response, re.DOTALL)
    
    if not code_blocks:
        return "未能提取代码"
        
    # 选择最后一个（最新的）代码块进行处理
    latest_block = code_blocks[-1]
    
    # 清理这个块
    cleaned_code = clean_protocol_code(latest_block)

    if cleaned_code and "def run(" in cleaned_code:
        print("✅ 从响应中成功提取和清理了代码")
        return cleaned_code
    
    print("❌ 未能从响应中提取有效的Opentrons代码")
    return "未能提取代码"

# =============================================================================
# 主对话循环
# =============================================================================
def main_chat_loop():
    """主对话循环函数"""
    global active_robot_type
    print("=== Opentrons 协议生成器 - 对话模式 ===")
    print("这是一个交互式的 Opentrons 协议生成工具。")
    print("您可以与 AI 助手进行多轮对话来完善您的协议。\n")
    
    # 初始化会话
    session = ChatSession()
    
    # 获取机器人类型
    session.robot_type = get_robot_type()
    active_robot_type = session.robot_type # 在循环开始时设置全局变量
    
    # 获取初始请求
    initial_request = get_initial_request(session.robot_type)
    session.add_user_message(initial_request)
    
    print(f"\n=== 开始处理您的请求 ===")
    print(f"请求: {initial_request}\n")
    
    # 主对话循环
    while True:
        try:
            # 准备当前请求（初始请求或修改请求）
            if len(session.history) == 1:  # 首次请求
                current_input = initial_request
            else:  # 后续修改请求
                latest_user_msg = [msg for msg in session.history if msg["role"] == "user"][-1]
                current_input = latest_user_msg["content"]
            
            # 准备 agent 输入
            agent_input = {
                "input": current_input,
                "chat_history": session.get_history_string(),
                "current_context": session.get_current_context()
            }
            
            # 调用 agent
            print("正在生成/修改协议，请稍候...")
            result = agent_executor.invoke(agent_input)
            
            # 直接从 result 中提取最终输出
            raw_output = result.get('output', '未能生成代码')
            
            # 使用增强的代码提取函数
            final_code = extract_code_from_response(raw_output)

            if "未能提取代码" in final_code:
                print("❌ 代码生成失败，AI Agent 可能超时或出现错误")
                print("原始响应:")
                print(raw_output)
            else:
                print("✅ 协议生成成功！")
                display_code_with_line_numbers(final_code)
                
                # 保存协议
                saved_path = save_protocol_to_file(final_code, session.robot_type)
                if saved_path:
                    print("协议已成功保存！")
                
                # 运行最终验证仿真
                print("=== 运行最终验证仿真 ===")
                final_verification = run_opentrons_simulation(final_code, session.robot_type)
                print(final_verification)

            # 检查仿真结果
            success_indicators = [
                "结果: 仿真成功",
                "结果: 仿真可能成功", 
                "结果: 仿真成功但有警告",
                "结果: 仿真完成但有警告"
            ]
            
            simulation_succeeded = any(indicator in final_verification for indicator in success_indicators)

            if simulation_succeeded:
                print("✅ 最终验证: 成功")
                if "警告" in final_verification:
                    print("注意: 仿真成功但有警告，这在仿真模式下是正常的。")
            else:
                print("❌ 最终验证: 失败")
                print("请查看仿真输出中的错误并提供修改建议。")
            
            # 用户选择下一步
            print("\n=== 您的选择 ===")
            print("1. 保存协议到文件")
            print("2. 继续修改协议（输入修改要求）")
            print("3. 重新开始")
            print("4. 退出")
            
            choice = input("请选择 (1-4): ").strip()
            
            if choice == "1":
                # 保存协议
                saved_path = save_protocol_to_file(final_code, session.robot_type)
                if saved_path:
                    print("协议已成功保存！")
                
                # 询问是否继续
                continue_choice = input("是否继续修改协议? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    break
                    
            elif choice == "2":
                # 继续修改
                modification_request = input("\n请描述您希望的修改（例如：'将移液量从50uL改为100uL'，'添加混匀步骤'等）: ").strip()
                if modification_request:
                    session.add_user_message(modification_request)
                    print(f"\n=== 处理修改请求 ===")
                    print(f"修改: {modification_request}\n")
                    continue
                else:
                    print("未输入修改要求，请重新选择。")
                    
            elif choice == "3":
                # 重新开始
                print("\n=== 重新开始 ===")
                return main_chat_loop()
                
            elif choice == "4":
                # 退出
                print("感谢使用 Opentrons 协议生成器！")
                break
                
            else:
                print("无效选择，请重新输入。")

        except KeyboardInterrupt:
            print("\n\n用户中断操作。")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")
            traceback.print_exc()
            
            continue_after_error = input("是否继续? (y/n): ").strip().lower()
            if continue_after_error != 'y':
                break

# =============================================================================
# 主程序入口
# =============================================================================
if __name__ == "__main__":
    try:
        main_chat_loop()
    except KeyboardInterrupt:
        print("\n\n程序已退出。")
    except Exception as e:
        print(f"\n程序运行时发生未预期的错误: {e}")
    traceback.print_exc()
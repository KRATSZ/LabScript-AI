import streamlit as st
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Union, Optional

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.outputs import LLMResult

# 1. 设置页面配置
st.set_page_config(
    page_title="Opentrons AI 协议生成器",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """# Opentrons AI 协议生成器
使用AI生成和验证Opentrons实验协议"""
    }
)

# 基础样式
st.markdown("""
<style>
    .main {
        background-color: #F5F7FA;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: 500;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #388E3C;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* 绿色主要按钮 */
    button[data-testid="chat-input-submit-button"] {
        background-color: #4CAF50 !important;
    }
    button[data-testid="chat-input-submit-button"]:hover {
        background-color: #388E3C !important;
    }
    
    .success {
        background-color: #E8F5E9;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 20px;
    }
    
    .error {
        background-color: #FFEBEE;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #F44336;
        color: #C62828;
        margin-bottom: 20px;
    }
    
    .info-card {
        background-color: #E3F2FD;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    code {
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# 导入必要的模块
try:
    from langchain_agent import agent_executor
    from opentrons_utils import run_opentrons_simulation
    has_langchain = True
except ImportError:
    st.error("无法导入LangChain代理或其依赖。应用将在演示模式下运行。请检查是否已安装 `langchain_openai` 等包。")
    has_langchain = False
    
    def run_opentrons_simulation(protocol_code):
        return """--- 模拟模式 ---
模拟验证协议...
--- Result: Simulation SUCCEEDED ---"""
    
    class MockAgent:
        def invoke(self, data, config=None):
            return {"output": """from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.20"}

def run(protocol: protocol_api.ProtocolContext):
    # 加载移液器吸头架到D3位置
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "D3")
    
    # 加载左侧移液器
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_1000",
        mount="left",
        tip_racks=[tiprack]
    )
    
    # 加载源板到D1位置
    source_plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D1", 
                                        label="source_plate")
    
    # 加载目标板到D2位置
    destination_plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D2",
                                             label="destination_plate")
    
    # 执行移液操作
    pipette.pick_up_tip()
    pipette.aspirate(50, source_plate["A1"])
    pipette.dispense(50, destination_plate["B2"])
    pipette.drop_tip()
"""}
    
    agent_executor = MockAgent()

# Callback Handler for progress display
class SimpleStreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, status_container, task_name: str = "通用任务") -> None:
        super().__init__()
        self.status_container = status_container
        self.task_name = task_name
        self._current_tool_step = 0
        self._current_tool_name: Optional[str] = None

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        prompt_preview = prompts[0][:120] + "..." if len(prompts[0]) > 120 else prompts[0]
        self.status_container.update(
            label=f"🧠 [{self.task_name}] AI 正在思考...\n提示片段: \"{prompt_preview}\"",
            state="running",
            expanded=True
        )

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        pass # Not displaying token by token for now

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        # If an agent is still running, LLM end doesn't mean the task is complete.
        self.status_container.update(
            label=f"✅ [{self.task_name}] AI 思考完毕，准备后续步骤...",
            state="running", 
            expanded=True
        )

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        self.status_container.update(
            label=f"⚠️ [{self.task_name}] AI 思考出错: {error}", 
            state="error"
        )

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        # This can be too generic if agent has multiple chains.
        pass

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        pass

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        self._current_tool_step += 1
        self._current_tool_name = serialized.get("name", "未知工具")
        tool_name_display = self._current_tool_name.replace("_", " ").title()
        # Truncate input_str if it's too long
        display_input = input_str
        if len(display_input) > 200:
            display_input = display_input[:200] + "..."
        self.status_container.update(
            label=f"🛠️ [{self.task_name}] 步骤 {self._current_tool_step}: 使用工具 `{tool_name_display}`\n输入 (片段): {display_input}",
            state="running"
        )

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        tool_name_display = self._current_tool_name.replace("_", " ").title() if self._current_tool_name else "工具"
        # Truncate output if it's too long
        display_output = output
        if len(display_output) > 150:
            display_output = display_output[:150] + "..."
        self.status_container.update(
            label=f"✔️ [{self.task_name}] 工具 `{tool_name_display}` 使用完毕。\n输出 (片段): {display_output}",
            state="running"
        )

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        tool_name_display = self._current_tool_name.replace("_", " ").title() if self._current_tool_name else "工具"
        self.status_container.update(
            label=f"⚠️ [{self.task_name}] 工具 `{tool_name_display}` 使用出错: {error}",
            state="error"
        )

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        tool_name_display = action.tool.replace("_", " ").title()
        self.status_container.update(
            label=f"➡️ [{self.task_name}] AI 计划: 使用工具 `{tool_name_display}`",
            state="running"
        )

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        self.status_container.update(
            label=f"🎉 [{self.task_name}] 所有步骤已顺利完成!",
            state="complete",
            expanded=False
        )
        self._current_tool_step = 0
        self._current_tool_name = None

def save_protocol_to_file(protocol_code, robot_type, api_level):
    """保存生成的协议到文件"""
    os.makedirs("generated_protocols", exist_ok=True)
    now_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated_protocols/protocol_{robot_type.lower()}_api{api_level.replace('.', '_')}_{now_timestamp}.py"
    
    with open(filename, 'w', encoding='utf-8') as pf:
        pf.write(protocol_code)
    
    return os.path.abspath(filename)

# 初始化会话状态
if 'history' not in st.session_state:
    st.session_state.history = []
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = None
if 'simulation_result' not in st.session_state:
    st.session_state.simulation_result = None
if 'file_path' not in st.session_state:
    st.session_state.file_path = None
if 'is_successful' not in st.session_state:
    st.session_state.is_successful = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# 侧边栏设置
with st.sidebar:
    st.title("🧪 Opentrons AI")
    st.caption("自动化协议生成器")
    
    if not has_langchain:
        st.warning("⚠️ 演示模式：AI功能受限。请确保所有依赖已正确安装以启用完整功能。")
    
    try:
        st.image("https://opentrons.com/wp-content/uploads/2023/07/Logo.svg", width=200)
    except:
        pass
    
    st.subheader("⚙️ 设备设置")
    
    # 机器人类型选择
    if 'robot_type' not in st.session_state:
        st.session_state.robot_type = "Flex"
    
    robot_type = st.radio(
        "选择机器人类型",
        options=["Flex", "OT-2"],
        index=0 if st.session_state.robot_type == "Flex" else 1,
        format_func=lambda x: f"🦾 Flex - 新一代灵活型机器人" if x == "Flex" else f"🔬 OT-2 - 经典型自动化平台",
        key="robot_type_radio"
    )
    
    st.session_state.robot_type = robot_type
    
    # API版本选择
    default_api_index = 6 if robot_type == "Flex" else 2  # 2.20 for Flex, 2.16 for OT-2
    api_level = st.selectbox(
        "API版本",
        options=["2.14", "2.15", "2.16", "2.17", "2.18", "2.19", "2.20", "2.21"],
        index=default_api_index,
        help="选择Opentrons API版本"
    )
    
    # 历史协议
    st.header("📜 历史生成的协议")
    if os.path.exists("generated_protocols"):
        protocol_files = sorted([f for f in os.listdir("generated_protocols") if f.startswith("protocol_") and f.endswith(".py")], reverse=True)
        if protocol_files:
            for file_idx, file_name in enumerate(protocol_files[:5]):  # 只显示最近5个
                parts = file_name.split('_')
                robot_info = parts[1] if len(parts) > 1 else ""
                api_info = parts[2].replace('api', '') if len(parts) > 2 else ""
                timestamp_parts = parts[-1].split('.')[0] if len(parts) > 3 else ""
                
                robot_icon = "🦾" if "flex" in robot_info.lower() else "🔬"
                button_label = f"{robot_icon} {robot_info.upper()} {api_info}"
                
                if st.button(button_label, key=f"history_btn_{file_idx}"):
                    file_path = os.path.join("generated_protocols", file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            st.session_state.generated_code = f.read()
                            st.session_state.file_path = file_path
                        st.session_state.is_successful = True 
                        st.session_state.simulation_result = "从历史记录加载。"
                        st.success(f"✅ 已加载历史协议: {file_name}")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ 加载历史协议时出错: {str(e)}")
        else:
            st.info("📭 暂无历史协议文件")
    else:
        st.info("📁 历史记录目录不存在，将在生成第一个协议时创建")

# 主界面
st.title("🧪 Opentrons AI 协议生成器")

# 设备信息提示
robot_emoji = "🦾" if robot_type == "Flex" else "🔬"
st.info(f"{robot_emoji} 当前设备: {robot_type} 机器人 | API版本: {api_level}")

# 显示聊天历史
if st.session_state.chat_messages:
    for message in st.session_state.chat_messages:
        with st.chat_message(name=message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
        content = message.get("content", "")
            if message["role"] == "assistant" and isinstance(content, str) and (
            content.startswith("from opentrons import") or 
            "def run(" in content or 
            "protocol_api" in content
        ):
                st.code(content, language="python")
        else:
            st.markdown(content)
else:
    st.markdown("👋 还没有对话记录！请在下方输入您的协议需求。")

# 聊天输入
prompt = st.chat_input("请在此处输入您的协议需求...")

if prompt:
    # 添加用户消息
    st.session_state.chat_messages.append({
        "role": "user", 
        "content": prompt
    })
    
    # 构建请求
    full_request = f"Generate an Opentrons protocol for a {robot_type} robot using API version {api_level}. {prompt}"
    
    # 重置状态
    st.session_state.generated_code = None
    st.session_state.simulation_result = None
    st.session_state.file_path = None
    st.session_state.is_successful = None
    
    with st.status("🤖 AI 正在处理您的请求...", expanded=True) as status_ui_element:
        try:
            callback_handler = SimpleStreamlitCallbackHandler(
                status_container=status_ui_element,
                task_name="协议生成"
            )
            response = agent_executor.invoke(
                {"input": full_request},
                config={"callbacks": [callback_handler]}
            )
            protocol_code = response.get('output', '')
            simulation_result = run_opentrons_simulation(protocol_code)
            
            # 更新成功条件，包括"Simulation likely SUCCEEDED"
            if "Simulation SUCCEEDED" in simulation_result or "Simulation likely SUCCEEDED" in simulation_result:
                is_successful = True
                file_path = save_protocol_to_file(protocol_code, robot_type, api_level)
            else:
                is_successful = False
                file_path = None
            
            st.session_state.generated_code = protocol_code
            st.session_state.simulation_result = simulation_result
            st.session_state.file_path = file_path
            st.session_state.is_successful = is_successful
            
            # 添加AI回复
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": protocol_code
            })
            
            # 如果模拟失败，进行错误分析
            if not is_successful and has_langchain:
                # 提示错误分析正在进行
                status_ui_element.update(
                    label="🧐 AI 正在分析错误原因并提供建议...", 
                    state="running", 
                    expanded=True
                )
                
                # 构造用于错误分析的提示
                analysis_prompt_text = f"""作为Opentrons协议调试专家，请分析以下失败的协议生成尝试。
用户原始请求: "{prompt}"
机器人类型: {robot_type}
API版本: {api_level}
已生成的代码:
```python
{protocol_code if protocol_code else "错误：未能生成任何代码。"}
```
模拟器返回的错误/结果:
```
{simulation_result}
```
请严格按照以下步骤进行：
1. **根本原因分析**：清晰地指出导致模拟失败或代码问题的最可能的一个或多个根本原因。
2. **具体修改建议**：
   * 如果问题在于用户原始请求的歧义或不足，请提供如何改进用户请求的具体例子。
   * 如果问题在于生成的代码，请指出代码中的具体问题行（如果可能）或问题逻辑，并解释如何修正。
3. **解释**：简要解释你的分析过程和你为什么会给出这些建议。
请以友好、乐于助人的助手口吻，直接提供上述分析和建议。避免不必要的寒暄。
"""
                try:
                    # 为错误分析任务实例化新的回调处理器
                    error_analysis_callback = SimpleStreamlitCallbackHandler(
                        status_container=status_ui_element,
                        task_name="错误分析"
                    )
                    # 调用LLM进行分析
                    analysis_response = agent_executor.invoke(
                        {"input": analysis_prompt_text},
                        config={"callbacks": [error_analysis_callback]}
                    )
                    analysis_output = analysis_response.get('output', '抱歉，我目前无法对此错误进行详细分析。请检查模拟器日志。')

                    # 将分析结果添加到聊天记录
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"❌ **模拟验证未通过分析**\n\n{analysis_output}"
                    })
                    status_ui_element.update(
                        label="💡 AI 已提供错误分析和改进建议。", 
                        state="complete", 
                        expanded=False
                    )
                    
                except Exception as analysis_exc:
                    st.error(f"⚠️ 错误分析过程中发生意外：{str(analysis_exc)}")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"⚠️ 尝试分析错误时出现内部问题: {str(analysis_exc)}"
                    })
                    status_ui_element.update(
                        label="⚠️ 错误分析失败。", 
                        state="error", 
                        expanded=False
                    )
            
        except Exception as e:
            st.error(f"⚠️ 生成过程中发生错误：{str(e)}")
            st.code(traceback.format_exc(), language="python")
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"⚠️ 抱歉，处理您的请求时出错: {str(e)}"
            })

# 结果展示
if st.session_state.generated_code is not None:
    st.markdown("---")
    st.subheader("🔍 生成结果")
    
    if st.session_state.is_successful:
        # 修改成功消息以包含可能成功的情况
        success_msg = "✅ 协议生成成功！"
        if "Simulation SUCCEEDED" in st.session_state.simulation_result:
            success_msg += "模拟验证完全通过。"
        elif "Simulation likely SUCCEEDED" in st.session_state.simulation_result:
            success_msg += "模拟验证可能通过（部分警告）。"
            
        st.markdown(f"<div class='success'>{success_msg}</div>", unsafe_allow_html=True)
        if st.session_state.file_path:
            st.success(f"📁 协议已保存到: {st.session_state.file_path}")
            
            # 下载按钮
            with open(st.session_state.file_path, "r", encoding='utf-8') as f:
                        st.download_button(
                    "📥 下载协议文件",
                    f.read(),
                    file_name=os.path.basename(st.session_state.file_path),
                    mime="text/x-python"
                )
            
            # 显示代码
            st.code(st.session_state.generated_code, language="python")
            
            # 显示模拟结果
            with st.expander("🧪 查看模拟结果"):
                    st.text(st.session_state.simulation_result)
    else:
        st.markdown("<div class='error'>❌ 协议生成失败或模拟验证未通过。</div>", unsafe_allow_html=True)
        st.error("请查看以下生成的代码和详细模拟结果，或参考AI提供的错误分析和建议。")
        
        if st.session_state.generated_code:
            with st.expander("📝 查看生成的代码", expanded=True):
                st.code(st.session_state.generated_code, language="python")
        if st.session_state.simulation_result:
            with st.expander("⚠️ 查看详细模拟结果", expanded=True):
                st.text(st.session_state.simulation_result)

# 首次使用提示
if not prompt and not st.session_state.generated_code:
    st.markdown("""
    <div class='info-card'>
    <h2>👋 欢迎使用 Opentrons AI 协议生成器!</h2>
    
    这个工具可以帮助您快速生成 Opentrons 实验协议。只需描述您的实验需求，AI 将生成可执行的 Python 代码。
    
    <h3>💡 提问示例:</h3>
    <ul>
        <li>"生成一个方案，用1000uL移液器将A1孔的50uL液体转移到B2孔，使用Flex机器人和API 2.20"</li>
        <li>"设计一个实验，从源板的A1-A6孔吸取100uL液体，分别分配到目标板的B1-B6孔，并为每次转移更换吸头"</li>
        <li>"编写一个OT-2协议，API版本2.16，实现从第一列开始，在96孔板中进行1:2的连续稀释，共稀释6列，每孔总体积200uL"</li>
    </ul>
    
    <h3>使用步骤:</h3>
    1. 在侧边栏选择您的机器人类型和 API 版本
    2. 在下方输入框描述您的实验需求
    3. AI 将生成协议并自动验证
    4. 下载并使用生成的协议文件
    </div>
    """, unsafe_allow_html=True)
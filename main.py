# -*- coding: utf-8 -*-
"""Main execution script for the Opentrons AI Protocol Generator."""
import os
import re
import traceback
import shutil
from datetime import datetime
import time
import colorama
from colorama import Fore, Style, Back

# Initialize colorama for cross-platform colored terminal output
colorama.init()

# Import necessary components from our modules
from langchain_agent import agent_executor
from opentrons_utils import run_opentrons_simulation # For final verification

# Utility Functions for Terminal UI
def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header."""
    terminal_width = shutil.get_terminal_size().columns
    header = f"{Fore.CYAN}Opentrons AI Protocol Generator{Style.RESET_ALL}"
    centered_header = header.center(terminal_width)
    
    print("\n" + "=" * terminal_width)
    print(centered_header)
    print("=" * terminal_width + "\n")

def print_info(message):
    """Print info message with styling."""
    print(f"{Fore.BLUE}ℹ️ INFO:{Style.RESET_ALL} {message}")

def print_success(message):
    """Print success message with styling."""
    print(f"{Fore.GREEN}✅ SUCCESS:{Style.RESET_ALL} {message}")

def print_warning(message):
    """Print warning message with styling."""
    print(f"{Fore.YELLOW}⚠️ WARNING:{Style.RESET_ALL} {message}")

def print_error(message):
    """Print error message with styling."""
    print(f"{Fore.RED}❌ ERROR:{Style.RESET_ALL} {message}")

def print_robot_info(robot_type, api_level):
    """Print current robot and API settings."""
    print(f"\n{Fore.CYAN}Current Settings:{Style.RESET_ALL}")
    print(f"  Robot Type: {Fore.MAGENTA}{robot_type}{Style.RESET_ALL}")
    print(f"  API Level: {Fore.MAGENTA}{api_level}{Style.RESET_ALL}\n")

def print_thinking_animation(message="AI思考中", duration=2):
    """Show a thinking animation."""
    for _ in range(duration * 2):
        for dots in [".", "..", "..."]:
            print(f"\r{Fore.YELLOW}{message}{dots}{Style.RESET_ALL}", end='', flush=True)
            time.sleep(0.25)
    print("\r" + " " * (len(message) + 5), end="\r")  # Clear the line

def format_chat_history(chat_history):
    """Format the chat history for display."""
    if not chat_history:
        return f"{Fore.YELLOW}暂无对话历史{Style.RESET_ALL}"
    
    formatted_history = []
    for msg in chat_history:
        role_color = Fore.BLUE if msg["role"] == "user" else Fore.GREEN
        role_icon = "🧑" if msg["role"] == "user" else "🤖"
        role_name = "User" if msg["role"] == "user" else "AI"
        
        # Format content based on type
        content = msg["content"]
        if msg["role"] == "assistant" and (
            content.startswith("from opentrons import") or 
            content.startswith("metadata =") or 
            content.startswith("requirements =")
        ):
            # For code responses, shorten and indicate it's code
            lines = content.split("\n")
            if len(lines) > 5:
                content = "\n".join(lines[:5]) + f"\n{Fore.YELLOW}... [code continues, {len(lines)} lines total]{Style.RESET_ALL}"
            content = f"{Fore.CYAN}[Python Code]{Style.RESET_ALL}\n{content}"
        
        formatted_msg = f"{role_color}{role_icon} {role_name}:{Style.RESET_ALL} {content}"
        formatted_history.append(formatted_msg)
    
    return "\n\n".join(formatted_history)

# User Interaction Functions (Improved from the original script)
def get_robot_type_and_api_level():
    """Ask user to choose robot model and optionally API level."""
    clear_screen()
    print_header()
    print(f"{Fore.CYAN}Robot Selection{Style.RESET_ALL}")
    print(f"{Fore.WHITE}------------------------{Style.RESET_ALL}")
    print(f"1: {Fore.MAGENTA}Flex{Style.RESET_ALL} - 新一代灵活型机器人 [推荐API: 2.20+]")
    print(f"2: {Fore.MAGENTA}OT-2{Style.RESET_ALL} - 经典型自动化平台 [推荐API: 2.16-2.20]")
    print(f"{Fore.WHITE}------------------------{Style.RESET_ALL}")
    
    robot_choice_input = input(f"\n选择机器人类型 (1=Flex, 2=OT-2) [{Fore.CYAN}默认: 1{Style.RESET_ALL}]: ").strip()
    robot_type = "OT-2" if robot_choice_input == "2" else "Flex"
    
    default_api = "2.20" if robot_type == "Flex" else "2.16" # Best default API version for each robot
    
    if robot_type == "OT-2":
        api_recommendation = "2.16-2.20 (建议: 2.16)"
    else: # Flex
        api_recommendation = "2.20 或更高 (建议: 2.20)"

    api_level_input = input(f"\n输入 {robot_type} 的API版本 [推荐: {Fore.CYAN}{api_recommendation}{Style.RESET_ALL}, 默认: {Fore.CYAN}{default_api}{Style.RESET_ALL}]: ").strip()
    # Basic validation to check if it looks like a version number
    api_level = api_level_input if api_level_input and api_level_input.replace('.', '', 1).isdigit() else default_api
    
    print_success(f"已选择机器人: {Fore.MAGENTA}{robot_type}{Style.RESET_ALL}, API版本: {Fore.MAGENTA}{api_level}{Style.RESET_ALL}")
    time.sleep(1)  # Brief pause to show the selection
    return robot_type, api_level

def get_user_request(robot_type, api_level, chat_history=None):
    """Get user request for the protocol with better UI."""
    clear_screen()
    print_header()
    print_robot_info(robot_type, api_level)
    
    # Show chat history if it exists
    if chat_history and len(chat_history) > 0:
        print(f"{Fore.CYAN}对话历史:{Style.RESET_ALL}")
        print(format_chat_history(chat_history))
        print("\n" + "-" * shutil.get_terminal_size().columns + "\n")
    
    print(f"{Fore.CYAN}请求输入{Style.RESET_ALL}")
    print(f"{Fore.WHITE}------------------------{Style.RESET_ALL}")
    
    use_default_q = input(f"使用默认协议示例? (y/n) [{Fore.CYAN}默认: y{Style.RESET_ALL}]: ").strip().lower()
    
    contextual_request_prefix = f"Generate an Opentrons protocol for a {robot_type} robot using API version {api_level}. The protocol should: "

    if use_default_q != "n": 
        if robot_type == "Flex":
            return contextual_request_prefix + ("transfer 50uL of liquid from well A1 of a 'corning_96_wellplate_360ul_flat' labware (named 'source_plate') on deck slot D1 "
                                                "to well B2 of another 'corning_96_wellplate_360ul_flat' labware (named 'destination_plate') on deck slot D2. "
                                                "Use a 'flex_1channel_1000' pipette mounted on the left. "
                                                "The tip rack is an 'opentrons_flex_96_tiprack_1000ul' located on deck slot D3. "
                                                "Load a trash bin in deck slot A3.")
        else:  # OT-2
            return contextual_request_prefix + ("transfer 50uL of liquid from well A1 of a 'corning_96_wellplate_360ul_flat' labware (named 'source_plate') on deck slot 1 "
                                                "to well B2 of another 'corning_96_wellplate_360ul_flat' labware (named 'destination_plate') on deck slot 2. "
                                                "Use a 'p300_single_gen2' pipette mounted on the left. "
                                                "The tip rack is an 'opentrons_96_tiprack_300ul' located on deck slot 3. "
                                                "The OT-2 has a fixed trash in slot 12, so no need to load it explicitly for basic transfers.")
    else:
        print(f"\n{Fore.CYAN}请描述您的自定义协议. 具体说明:{Style.RESET_ALL}")
        print(f"- {robot_type} 机器人上的动作 (转移液体, 混合, 加载模块等)")
        print("- 实验材料: 准确的API名称, 自定义名称, 平台位置")
        print("- 移液器: 准确的API名称和加载位置 (左/右)")
        print("- 体积, 吸头处理方式 (新吸头，重复使用), 混合参数等\n")
        
        if chat_history and len(chat_history) > 0:
            print(f"{Fore.YELLOW}💡 提示: 您可以引用之前的对话或要求修改已生成的协议{Style.RESET_ALL}")
        
        custom_request_description = input(f"\n您的协议描述: ").strip()
        
        if not custom_request_description:
            print_warning("描述为空，将使用默认协议示例。")
            return get_user_request(robot_type, api_level, chat_history)
        
        # Ensure the contextual prefix is part of the request for the agent, without duplicating if user included it.
        # Check if the user request already starts with a similar phrase
        lower_custom_request = custom_request_description.lower()
        lower_prefix_start = contextual_request_prefix.lower().split(':')[0] # e.g., "generate an opentrons protocol for a flex robot..."
        
        if not lower_custom_request.startswith(lower_prefix_start):
             print_info("正在将机器人类型和API版本上下文预先添加到请求中。")
             return contextual_request_prefix + custom_request_description
        else:
             print_info("用户请求似乎已经包含机器人/API上下文。")
             return custom_request_description


# Main Execution Block
if __name__ == "__main__":
    clear_screen()
    print_header()
    print_info("正在初始化...")
    
    selected_robot_type, selected_api_level = get_robot_type_and_api_level()
    
    # Initialize chat history
    chat_history = []
    generated_code = None
    
    # Multi-turn conversation loop
    while True:
        user_protocol_request = get_user_request(selected_robot_type, selected_api_level, chat_history)
        
        # Add user message to chat history
        chat_history.append({
            "role": "user",
            "content": user_protocol_request,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        clear_screen()
        print_header()
        print_robot_info(selected_robot_type, selected_api_level)
        print_info(f"正在处理您的请求...")
        print_thinking_animation("AI正在生成协议", 3)
        
        try:
            # Invoke the agent executor from langchain_agent module
            agent_response = agent_executor.invoke({"input": user_protocol_request})
            generated_code = agent_response.get('output', 'Agent did not return code in the expected format, or an error occurred.')

            # Add AI response to chat history
            chat_history.append({
                "role": "assistant",
                "content": generated_code,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # --- Code Extraction Logic ---
            print_info("正在提取Python代码...")
            
            if isinstance(generated_code, str):
                markdown_match = re.search(r"```(?:python)?\n(.*?)```", generated_code, re.DOTALL | re.IGNORECASE)
                if markdown_match:
                    print_info("在AI输出中找到Python代码块.")
                    extracted_code = markdown_match.group(1).strip()
                else:
                    code_start_indicators = ["from opentrons import", "metadata =", "requirements ="]
                    stripped_agent_output = generated_code.strip()
                    if any(stripped_agent_output.startswith(indicator) for indicator in code_start_indicators):
                        print_info("AI输出看起来是原始Python代码.")
                        extracted_code = stripped_agent_output
                    else:
                        print_info("AI输出不是原始代码或Markdown格式. 搜索关键词...")
                        code_found_by_keyword_search = False
                        for keyword in code_start_indicators:
                            if keyword in stripped_agent_output:
                                start_idx = stripped_agent_output.find(keyword)
                                extracted_code = stripped_agent_output[start_idx:]
                                print_info(f"找到关键词 '{keyword}'. 提取潜在代码.")
                                code_found_by_keyword_search = True
                                break
                        if not code_found_by_keyword_search:
                            print_warning("无法可靠地提取Python代码块.")
                            extracted_code = stripped_agent_output 
                generated_code = extracted_code
            else:
                print_warning(f"AI返回非字符串输出: {type(generated_code)}. 正在转换.")
                generated_code = str(generated_code)

            # Show the generated code
            print("\n" + "=" * shutil.get_terminal_size().columns)
            print(f"{Fore.CYAN}生成的协议代码:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{generated_code}{Style.RESET_ALL}")
            print("=" * shutil.get_terminal_size().columns + "\n")

            # --- Final Verification Simulation ---
            print_info("正在运行最终验证模拟...")
            
            looks_like_a_protocol = isinstance(generated_code, str) and \
                                    generated_code.strip() and \
                                    "def run(" in generated_code and \
                                    ("from opentrons import protocol_api" in generated_code or "import opentrons.protocol_api" in generated_code) and \
                                    ("metadata =" in generated_code or "requirements =" in generated_code)

            if looks_like_a_protocol:
                print_info("提取的代码看起来合理. 运行模拟...")
                
                # Show thinking animation
                print_thinking_animation("模拟验证中", 2)
                
                final_sim_output = run_opentrons_simulation(generated_code) # Use the imported function
                
                # Check if simulation successful
                strict_success_indicators = [
                    "Result: Simulation SUCCEEDED",
                    "Result: Simulation likely SUCCEEDED"
                ]
                is_strictly_successful = any(indicator in final_sim_output for indicator in strict_success_indicators)
                is_successful_with_warnings = "Result: Simulation SUCCEEDED WITH UNEXPECTED STDERR" in final_sim_output or \
                                              "Result: Simulation COMPLETED WITH UNEXPECTED STDERR" in final_sim_output
                
                if is_strictly_successful or (is_successful_with_warnings and "Result: Simulation FAILED" not in final_sim_output):
                    print_success("模拟验证通过!")
                    if is_successful_with_warnings and not is_strictly_successful:
                        print_warning("模拟通过但有意外的STDERR. 请仔细检查输出.")
                    
                    save_file_q = input(f"\n保存协议到.py文件? (y/n) [{Fore.CYAN}默认: y{Style.RESET_ALL}]: ").strip().lower()
                    if save_file_q != "n":
                        # Create directory if it doesn't exist
                        os.makedirs("generated_protocols", exist_ok=True)
                        
                        now_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        suggested_filename = f"generated_protocols/protocol_{selected_robot_type.lower()}_api{selected_api_level.replace('.', '_')}_{now_timestamp}.py"
                        
                        user_filename = input(f"输入文件名 [{Fore.CYAN}默认: {os.path.basename(suggested_filename)}{Style.RESET_ALL}]: ").strip()
                        chosen_filename = user_filename if user_filename else suggested_filename
                        if not chosen_filename.endswith('.py'):
                            chosen_filename += '.py'
                        
                        # Ensure directory part exists
                        dirname = os.path.dirname(chosen_filename)
                        if dirname and not os.path.exists(dirname):
                            os.makedirs(dirname, exist_ok=True)
                        
                        try:
                            with open(chosen_filename, 'w', encoding='utf-8') as pf:
                                pf.write(generated_code)
                            print_success(f"协议已保存到: {os.path.abspath(chosen_filename)}")
                        except IOError as e_save_io:
                            print_error(f"保存文件时出错: {e_save_io}")
                        except Exception as e_save_gen:
                            print_error(f"保存文件时出错: {e_save_gen}")
                else:
                    print_error("模拟报告了严重错误或未成功.")
                    print(f"\n{Fore.YELLOW}模拟输出摘要:{Style.RESET_ALL}")
                    
                    # Extract and show the relevant error parts
                    error_lines = [line for line in final_sim_output.split('\n') 
                                if "ERROR" in line or "Error" in line or "Traceback" in line or "FAILED" in line]
                    if error_lines:
                        for line in error_lines[:10]:  # Show first 10 error lines
                            print(f"{Fore.RED}{line}{Style.RESET_ALL}")
                        if len(error_lines) > 10:
                            print(f"{Fore.YELLOW}... 还有 {len(error_lines) - 10} 行错误信息 ...{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}未找到具体错误信息. 请查看完整模拟输出.{Style.RESET_ALL}")
            else:
                print_error("提取的AI输出不像有效的Opentrons协议.")
                print(f"{Fore.YELLOW}AI输出片段 (供审查):{Style.RESET_ALL}")
                print(f"{Fore.RED}{generated_code[:600]}...{Style.RESET_ALL}")

        except Exception as main_execution_error:
            print_error("AI执行过程中发生错误")
            print(f"{Fore.RED}错误类型: {type(main_execution_error)}{Style.RESET_ALL}")
            print(f"{Fore.RED}错误详情: {main_execution_error}{Style.RESET_ALL}")
            traceback.print_exc()
        
        # Ask if the user wants to continue the conversation
        print("\n" + "-" * shutil.get_terminal_size().columns)
        continue_chat = input(f"\n继续对话? (y/n) [{Fore.CYAN}默认: y{Style.RESET_ALL}]: ").strip().lower()
        if continue_chat == "n":
            print_info("感谢使用Opentrons AI协议生成器!")
            break 
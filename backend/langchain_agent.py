# -*- coding: utf-8 -*-
"""Sets up the Langchain agent for Opentrons protocol generation."""
import os
import requests
import re
from typing import Optional, Callable, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_experimental.tools import PythonREPLTool

# Import from our other modules
from config import (
    api_key, base_url, model_name,
    VALID_LABWARE_NAMES, VALID_INSTRUMENT_NAMES, VALID_MODULE_NAMES,
    CODE_EXAMPLES
)
from opentrons_utils import run_opentrons_simulation, SimulateToolInput

# Dify API configuration
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "app-QE605476I1QdGjG7N3W1dlCa")
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")

def call_dify_sop_workflow(user_goal_with_hardware_context: str) -> str:
    """Call Dify API to generate detailed Standard Operating Procedure (SOP)"""
    try:
        # Split input to extract hardware config and user goal
        if "---" in user_goal_with_hardware_context:
            parts = user_goal_with_hardware_context.split("---", 1)
            hardware_context = parts[0].strip()
            user_goal = parts[1].strip()
        else:
            hardware_context = "No specific hardware configuration provided."
            user_goal = user_goal_with_hardware_context.strip()
        
        # Build complete prompt
        full_prompt = f"Hardware Configuration:\n{hardware_context}\n\nExperimental Goal:\n{user_goal}"
        
        # Prepare request payload
        payload = {
            "inputs": {
                "request": full_prompt
            },
            "response_mode": "blocking",
            "user": "labscript-ai-user-1"
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # API call with timeout and retry logic
        timeout_seconds = 200
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{DIFY_API_URL}/workflows/run",
                    json=payload,
                    headers=headers,
                    timeout=timeout_seconds
                )
                response.raise_for_status()
                break
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    return f"Error: Dify API timeout after {max_retries} retries. Please try again later."
                continue
                
            except requests.exceptions.RequestException as e:
                if "504" in str(e) or "Gateway Time-out" in str(e):
                    if attempt == max_retries - 1:
                        return f"Error: Dify API gateway timeout after {max_retries} retries. Server may be overloaded."
                    continue
                else:
                    raise e
        
        # Parse response
        data = response.json()
        
        # Extract SOP text from response
        if "data" in data and "outputs" in data["data"]:
            outputs = data["data"]["outputs"]
            if "text" in outputs:
                sop_text = outputs["text"]
                return f"## Generated Standard Operating Procedure (SOP)\n\n{sop_text}"
            elif "answer" in outputs:
                sop_text = outputs["answer"]
                return f"## Generated Standard Operating Procedure (SOP)\n\n{sop_text}"
            elif "SOP" in outputs:
                sop_text = outputs["SOP"]
                return f"## Generated Standard Operating Procedure (SOP)\n\n{sop_text}"
        elif "answer" in data:
            sop_text = data["answer"]
            return f"## Generated Standard Operating Procedure (SOP)\n\n{sop_text}"
        else:
            return f"Error: Unexpected Dify API response format. Could not extract SOP. Response keys: {list(data.keys())}"
            
    except Exception as e:
        import traceback
        return f"Error: An unexpected error occurred during SOP generation. Details: {str(e)}\nTraceback:\n{traceback.format_exc()}"

# LLM Setup
llm = ChatOpenAI(
    model=model_name,
    openai_api_key=api_key,
    openai_api_base=base_url,
    temperature=0.05,
    streaming=True,
)

# Code Generation Prompt Template
code_gen_prompt_template_str = """
Task: Generate a complete, runnable Opentrons Python protocol script based on the provided SOP, Hardware Configuration, and extensive reference material.

**Crucial Instructions:**
1. **Output Format:** Output ONLY the Python code block, starting with 'from opentrons import ...' or 'metadata = ...' (or 'requirements = ...'). Do not include any other text, comments, or explanations before or after the code block.
2. **API Version & Robot Type:**
   * The script's API level must use the version specified in the `hardware_context` (default to '2.20' if not specified there, but prioritize `hardware_context`).
   * The robot type (e.g., 'OT-2' or 'Flex') MUST be strictly consistent with the `hardware_context`. Use `requirements = {{'robotType': 'Flex', 'apiLevel': 'YOUR_API_LEVEL'}}` for Flex, and `metadata = {{'apiLevel': 'YOUR_API_LEVEL'}}` for OT-2.
3. **Hardware Compatibility & Naming:**
   * You MUST strictly use labware names from the **VALID LABWARE NAMES LIST** provided below that are compatible with the robot model.
   * You MUST strictly use instrument names (pipettes) from the **VALID INSTRUMENT NAMES LIST** provided below that are compatible with the robot model.
   * You MUST strictly use module names from the **VALID MODULE NAMES LIST** provided below when loading modules.
   * Refer to the **DETAILED CODE EXAMPLES** provided below as your primary reference for correct syntax, common patterns, and module/instrument loading for the specified robot type.
4. **Error Correction:**
   * If the `sop_text` input below includes previous simulation error feedback, you MUST analyze it and correct the Python code accordingly.
   * Pay close attention to errors indicating incompatibility. Adjust the protocol to use components compatible with the robot model in `hardware_context` and listed in the VALID NAMES.

**Inputs & Context:**

Hardware Configuration:
{hardware_context}

Detailed SOP (and previous error feedback if any):
{sop_text}

**REFERENCE MATERIAL (Adhere to this strictly):**

VALID LABWARE NAMES (Use these exact names):
{valid_labware_list_str}

VALID INSTRUMENT NAMES (Pipettes - Use these exact names):
{valid_instrument_list_str}

VALID MODULE NAMES (Use these exact API names for `protocol.load_module`):
{valid_module_list_str}

DETAILED CODE EXAMPLES (Follow these patterns closely for the specified robot type):
{code_examples_str}

Begin Python code block now:
"""

CODE_GEN_PROMPT = PromptTemplate(
    input_variables=["hardware_context", "sop_text", 
                     "valid_labware_list_str", "valid_instrument_list_str", 
                     "valid_module_list_str", "code_examples_str"],
    template=code_gen_prompt_template_str
)

# Initialize the code generation chain
code_gen_chain = LLMChain(llm=llm, prompt=CODE_GEN_PROMPT)

def extract_error_from_simulation(simulation_output: str) -> str:
    """Extract relevant error information from simulation output"""
    # First, try to find Cleaned STDERR section
    cleaned_stderr_match = re.search(r"--- Cleaned STDERR ---\n(.*?)(?:\n---|\Z)", simulation_output, re.DOTALL)
    if cleaned_stderr_match and cleaned_stderr_match.group(1).strip():
        cleaned_stderr = cleaned_stderr_match.group(1).strip()
        return cleaned_stderr
    
    # If no Cleaned STDERR, use original extraction logic
    error_lines = []
    in_traceback = False
    error_keywords = ["Error", "Exception", "Traceback (most recent call last)", "FAILED"]
    
    for line in simulation_output.splitlines():
        if any(keyword in line for keyword in error_keywords):
            in_traceback = True
        if in_traceback:
            error_lines.append(line)
            if len(error_lines) > 15 and not line.startswith(" "):
                break
    
    if not error_lines:
        # Check for warnings
        warning_lines = []
        for line in simulation_output.splitlines():
            if "warning" in line.lower() or "caution" in line.lower():
                warning_lines.append(line)
        
        if warning_lines:
            return "Warnings found:\n" + "\n".join(warning_lines[:10])
            
        # General failure check
        if "FAIL" in simulation_output.upper():
            return "General failure detected in simulation output"
        
        return "No specific errors found in simulation output"
    
    return "\n".join(error_lines)

def run_automated_protocol_generation_with_iteration(
    tool_input: str, 
    iteration_reporter: Optional[Callable[[Dict[str, Any]], None]] = None
) -> str:
    """Run automated protocol generation with iteration until success or max attempts"""
    
    if iteration_reporter is None:
        def default_reporter(event_data: Dict[str, Any]):
            print(f"Event: {event_data}")
        iteration_reporter = default_reporter
    
    # Parse input
    if "---CONFIG_SEPARATOR---" in tool_input:
        parts = tool_input.split("---CONFIG_SEPARATOR---", 1)
        sop_text = parts[0].strip()
        hardware_context = parts[1].strip()
    else:
        sop_text = tool_input
        hardware_context = "No hardware configuration provided"
    
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        iteration_reporter({
            "event_type": "iteration_log",
            "attempt_num": attempt,
            "message": f"Starting attempt {attempt}/{max_attempts}"
        })
        
        try:
            # Generate code
            iteration_reporter({
                "event_type": "llm_call_start",
                "attempt_num": attempt,
                "message": "Generating protocol code..."
            })
            
            # Prepare context for code generation
            code_result = code_gen_chain.run(
                hardware_context=hardware_context,
                sop_text=sop_text,
                valid_labware_list_str="\n".join(VALID_LABWARE_NAMES),
                valid_instrument_list_str="\n".join(VALID_INSTRUMENT_NAMES),
                valid_module_list_str="\n".join(VALID_MODULE_NAMES),
                code_examples_str=CODE_EXAMPLES
            )
            
            iteration_reporter({
                "event_type": "code_attempt",
                "attempt_num": attempt,
                "generated_code": code_result[:500] + "..." if len(code_result) > 500 else code_result,
                "error_details": None
            })
            
            # Test the generated code
            iteration_reporter({
                "event_type": "simulation_start",
                "attempt_num": attempt,
                "message": "Testing generated code with Opentrons simulator..."
            })
            
            simulation_result = run_opentrons_simulation(code_result, return_structured=True)
            
            if simulation_result["success"]:
                iteration_reporter({
                    "event_type": "simulation_result",
                    "attempt_num": attempt,
                    "status": "SUCCEEDED",
                    "stdout": simulation_result.get("raw_output", "")[:500],
                    "stderr": ""
                })
                
                iteration_reporter({
                    "event_type": "iteration_result",
                    "attempt_num": attempt,
                    "status": "SUCCESS",
                    "final_code": code_result
                })
                
                return code_result
            else:
                # Simulation failed, extract error
                error_info = extract_error_from_simulation(simulation_result.get("raw_output", ""))
                
                iteration_reporter({
                    "event_type": "simulation_result",
                    "attempt_num": attempt,
                    "status": "FAILED",
                    "stdout": simulation_result.get("raw_output", "")[:500],
                    "stderr": error_info[:500] if error_info else ""
                })
                
                if attempt < max_attempts:
                    # Add error feedback to SOP for next iteration
                    sop_text += f"\n\n--- PREVIOUS SIMULATION ERROR (Attempt {attempt}) ---\n{error_info}\n--- Please fix the above error in the next code generation ---"
                    
                    iteration_reporter({
                        "event_type": "iteration_result",
                        "attempt_num": attempt,
                        "status": "FAILED - WILL RETRY",
                        "error_details": error_info
                    })
                else:
                    iteration_reporter({
                        "event_type": "iteration_result",
                        "attempt_num": attempt,
                        "status": "FAILED - MAX ATTEMPTS REACHED",
                        "error_details": error_info
                    })
                    
                    return f"Error: Code generation failed after {max_attempts} attempts. Last error: {error_info}"
                
        except Exception as e:
            error_msg = f"Exception during attempt {attempt}: {str(e)}"
            iteration_reporter({
                "event_type": "iteration_result",
                "attempt_num": attempt,
                "status": "ERROR",
                "error_details": error_msg
            })
            
            if attempt == max_attempts:
                return f"Error: {error_msg}"
    
    return "Error: Unexpected end of iteration loop"

# Simulation Tool Input class for compatibility
class SimulateToolInput:
    def __init__(self, protocol_code: str):
        self.protocol_code = protocol_code
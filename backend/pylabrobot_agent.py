"""
PyLabRobot Agent Service

This module provides a LangGraph-based PyLabRobot protocol generation service
that can be called from the FastAPI backend. It includes streaming capabilities
for real-time frontend updates.
"""

import asyncio
import os
import sys
import json
import re
from typing import TypedDict, Optional, Dict, AsyncGenerator
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# Import utilities - Enhanced version
from backend.pylabrobot_utils import (
    run_pylabrobot_simulation, 
    load_hardware_configuration,
    generate_dynamic_pylabrobot_knowledge
)
from backend.diff_utils import apply_diff
from backend.config import (
    api_key, base_url, model_name,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_INTENT_MODEL
)
from backend.prompts import (
    PYLABROBOT_CODE_GENERATION_PROMPT_TEMPLATE,
    PYLABROBOT_CODE_CORRECTION_DIFF_PROMPT_TEMPLATE,
    PYLABROBOT_FORCE_REGENERATE_PROMPT_TEMPLATE
)

# State definition for LangGraph - enhanced version with hardware configuration support
class PyLabRobotGraphState(TypedDict):
    user_query: str                 # User's natural language requirements
    hardware_config: Dict           # Hardware configuration loaded from file
    pylabrobot_knowledge: str       # Dynamically generated PyLabRobot knowledge based on hardware
    python_code: Optional[str]      # Current LLM-generated PyLabRobot protocol code
    llm_diff_output: Optional[str]  # LLM-generated raw diff text for debugging
    simulation_result: Optional[dict] # Structured simulation results from real backend
    feedback_for_llm: Dict[str, str] # Structured feedback for LLM to generate diff
    attempts: int                     # Current attempt number
    max_attempts: int                 # Maximum allowed attempts
    final_outcome: Optional[str]    # Final result status
    iteration_reporter: Optional[callable] # Callback function for reporting progress
    force_regenerate: bool           # Flag to force regeneration of code

# NOTE: Static PYLABROBOT_KNOWLEDGE has been replaced with dynamic generation
# The knowledge is now generated dynamically based on hardware configuration
# using generate_dynamic_pylabrobot_knowledge() function from pylabrobot_utils.py
# This allows for hardware-specific prompts that reflect the actual available resources

# Advanced diff correction prompt template with context awareness
PYLABROBOT_CODE_CORRECTION_DIFF_TEMPLATE = """
You are an expert PyLabRobot protocol programmer. Your task is to fix a bug in the provided protocol script based on detailed error analysis and code context.

**CRITICAL**: You must output your fix as a diff in the SEARCH/REPLACE format. This is the ONLY acceptable format.

**Precise Error Analysis**:
{analysis_of_failure}

**Specific Action Required**:
{recommended_action}

**Error Type**: {error_type}
**Extracted Error Entities**: {extracted_entities}

**Code Context Around Error ({context_range})**:
```python
{code_snippet}
```

**Correct Usage Example from Your Code**:
{usage_example}

**Full Error Log**:
{full_error_log}

**Complete Previous Code** (for reference):
```python
{previous_code}
```

**Advanced Instructions for generating the diff**:
1. **Focus Area**: The error is likely around {context_range}. Pay special attention to this area.
2. **Entity-Specific Fix**: The error involves these specific entities: {extracted_entities}
3. **Pattern Matching**: Use the "Correct Usage Example" as a reference pattern for your fix.
4. **SEARCH/REPLACE Format**:
   - Start with: ------- SEARCH
   - Include the EXACT problematic code (check the Code Context section)
   - End search block with: =======  
   - Start replace block with: +++++++ REPLACE
   - Include the corrected code following the pattern from the usage example
5. **Precision**: The SEARCH block must match exactly. Copy directly from the Code Context if possible.
6. **Minimal Changes**: Only fix the specific error - don't make unnecessary changes.

**Example format**:
------- SEARCH
    problematic_line_with_error()
    related_context_line = "value"
=======
    corrected_line_following_pattern()
    related_context_line = "value"  
+++++++ REPLACE

Generate the precise diff now:
"""

# ============================================================================
# LLM Instances Initialization - Mixed Strategy (moved to function level)
# ============================================================================

def get_pylabrobot_llm_instances():
    """
    Get PyLabRobot LLM instances with lazy initialization
    """
    # LLM for initial protocol creation - use powerful model for complex reasoning
    creation_llm = ChatOpenAI(
        model_name=model_name,  # gemini-2.5-pro for complex protocol generation
        openai_api_base=base_url,
        openai_api_key=api_key,
        temperature=0.1,
        max_tokens=4096
    )

    # LLM for code correction and diff generation - use fast model for efficiency
    correction_llm = ChatOpenAI(
        model_name=DEEPSEEK_INTENT_MODEL,  # DeepSeek-V3-Fast for quick fixes
        openai_api_base=DEEPSEEK_BASE_URL,
        openai_api_key=DEEPSEEK_API_KEY,
        temperature=0.1,
        max_tokens=2048
    )
    
    return creation_llm, correction_llm

def load_golden_template() -> str:
    """
    Load the golden template for PyLabRobot protocols
    """
    try:
        template_path = os.path.join(os.path.dirname(__file__), "pylabrobot_template.py")
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Failed to load golden template: {e}")
        # Fallback template
        return """
import asyncio
from pylabrobot.liquid_handling import LiquidHandler

async def protocol(lh: LiquidHandler):
    # [AGENT_CODE_STUB]
    pass

async def main():
    lh = LiquidHandler()
    await lh.setup()
    try:
        await protocol(lh)
    finally:
        await lh.stop()

if __name__ == "__main__":
    asyncio.run(main())
"""

def fill_template_with_logic(template: str, protocol_logic: str) -> str:
    """
    Replace the [AGENT_CODE_STUB] placeholder in template with actual protocol logic.
    This version uses a more robust regex to find the insertion point.
    """
    # This regex finds the line with the stub, any comments below it, and the 'pass' statement.
    # It ensures that we can robustly replace the placeholder block.
    pattern = re.compile(r"(\s*#\s*\[AGENT_CODE_STUB\].*?\n)(?:.*?\n)*?(\s*pass)", re.DOTALL)
    
    # The replacement string consists of the initial stub line (to keep it for reference if needed)
    # followed by the AI-generated protocol logic.
    # The protocol_logic should already be correctly indented by the generation node.
    replacement = r'\1' + protocol_logic

    if pattern.search(template):
        # Replace the matched block with our new logic.
        new_code = pattern.sub(replacement, template, count=1)
        # The 'pass' statement is consumed by the regex, so the logic is inserted correctly.
        return new_code
    else:
        # Fallback if the primary pattern is not found for some reason.
        print("Warning: Could not find [AGENT_CODE_STUB] placeholder with primary pattern. Using fallback.")
        return template.replace("    # [AGENT_CODE_STUB]\n    pass", protocol_logic)

def generate_code_node(state: PyLabRobotGraphState) -> PyLabRobotGraphState:
    """
    Enhanced template-based code generation node - eliminates "MissingProtocolFunction" errors
    """
    attempt_num = state['attempts'] + 1
    print(f"\n=== PyLabRobot Generate Code (Attempt {attempt_num}) ===")
    
    # Report to frontend
    if state.get('iteration_reporter'):
        state['iteration_reporter']({
            "event_type": "node_start",
            "node_name": "generator",
            "attempt_num": attempt_num,
            "message": f"Starting template-based code generation for attempt #{attempt_num}"
        })
    
    llm_diff_output = None
    final_code = None
    
    # Load the golden template
    template = load_golden_template()
    
    # Determine generation strategy
    if state.get("force_regenerate", False) or state['attempts'] == 0:
        # Generate protocol logic using template-based approach
        print("Template-based generation: Generating protocol function logic only")
        selected_llm = get_pylabrobot_llm_instances()[0]  # Use creation_llm
        
        # Create specialized prompt for protocol logic generation
        protocol_logic_prompt = f"""
You are an expert PyLabRobot protocol developer. Your task is to generate ONLY the internal logic 
for a PyLabRobot protocol function. This logic will be inserted into an `async def protocol(lh: LiquidHandler):` function.

**CRITICAL REQUIREMENTS:**
1. Generate ONLY the function body content (no function signature)
2. Use proper indentation (4 spaces for each line)
3. Use `lh` as the LiquidHandler instance
4. All operations must use `await` keyword (e.g., `await lh.pick_up_tips(...)`)
5. Focus on the protocol logic, not the function wrapper

**User Requirements:**
{state["user_query"]}

**Available Hardware Resources:**
{json.dumps(state["hardware_config"], indent=2)}

**PyLabRobot Knowledge:**
{state["pylabrobot_knowledge"]}

**Template Context:**
The generated logic will be inserted into this function structure:
```python
async def protocol(lh: LiquidHandler):
    # YOUR LOGIC GOES HERE
```

Generate ONLY the protocol logic (function body content) with proper indentation:
"""
        
        if state.get("force_regenerate", False):
            print("Force regeneration mode: Creating fresh protocol logic")
            state["force_regenerate"] = False
        else:
            print("First generation: Creating initial protocol logic")
        
        try:
            messages = [
                SystemMessage(content="You are a PyLabRobot protocol expert. Generate only protocol function logic, not the complete file."), 
                HumanMessage(content=protocol_logic_prompt)
            ]
            response = selected_llm.invoke(messages)
            protocol_logic = response.content.strip()
            
            # Clean the response
            if protocol_logic.startswith("```python"):
                protocol_logic = protocol_logic[9:]
            if protocol_logic.endswith("```"):
                protocol_logic = protocol_logic[:-3]
            protocol_logic = protocol_logic.strip()
            
            # Ensure proper indentation
            logic_lines = protocol_logic.split('\n')
            indented_lines = []
            for line in logic_lines:
                if line.strip():  # Non-empty line
                    if not line.startswith('    '):  # Not already indented
                        indented_lines.append('    ' + line)
                    else:
                        indented_lines.append(line)
                else:
                    indented_lines.append(line)  # Keep empty lines as is
            
            protocol_logic = '\n'.join(indented_lines)
            
            # Fill template with generated logic
            final_code = fill_template_with_logic(template, protocol_logic)
            
            print(f"Generated protocol logic and filled template, total length: {len(final_code)} characters")
            
        except Exception as e:
            print(f"Error in LLM generation: {e}")
            # Fallback: use template with minimal logic
            fallback_logic = """    print("ERROR: Failed to generate protocol logic from LLM")
    raise Exception("LLM generation failed")"""
            final_code = fill_template_with_logic(template, fallback_logic)
            
    else:
        # Function-level regeneration for fixes (replace diff approach)
        print("Function-level regeneration: Re-generating protocol logic based on error feedback")
        selected_llm = get_pylabrobot_llm_instances()[1]  # Use correction_llm
        
        feedback = state["feedback_for_llm"]
        
        # Create fix-focused prompt for protocol logic
        fix_logic_prompt = f"""
You are a PyLabRobot protocol expert specializing in error correction. 

**PREVIOUS ERROR ANALYSIS:**
{feedback.get("analysis", "Unknown error")}

**REQUIRED ACTION:**
{feedback.get("action", "Please review the code")}

**ERROR TYPE:** {feedback.get("error_type", "Unknown")}

**FULL ERROR LOG:**
{feedback.get("error_log", "No detailed error log")}

**PREVIOUS PROTOCOL LOGIC (that had errors):**
{state.get("python_code", "No previous code")}

Your task is to generate FIXED protocol function logic that addresses the above errors.

**CRITICAL REQUIREMENTS:**
1. Generate ONLY the function body content (no function signature)
2. Use proper indentation (4 spaces for each line)
3. Use `lh` as the LiquidHandler instance
4. All operations must use `await` keyword
5. Fix the specific error mentioned in the analysis

**Available Hardware Resources:**
{json.dumps(state["hardware_config"], indent=2)}

Generate the CORRECTED protocol logic (function body only) with proper indentation:
"""
        
        try:
            messages = [
                SystemMessage(content="You are a PyLabRobot error correction expert. Generate only the corrected protocol function logic."), 
                HumanMessage(content=fix_logic_prompt)
            ]
            response = selected_llm.invoke(messages)
            protocol_logic = response.content.strip()
            
            # Clean the response
            if protocol_logic.startswith("```python"):
                protocol_logic = protocol_logic[9:]
            if protocol_logic.endswith("```"):
                protocol_logic = protocol_logic[:-3]
            protocol_logic = protocol_logic.strip()
            
            # Ensure proper indentation
            logic_lines = protocol_logic.split('\n')
            indented_lines = []
            for line in logic_lines:
                if line.strip():  # Non-empty line
                    if not line.startswith('    '):  # Not already indented
                        indented_lines.append('    ' + line)
                    else:
                        indented_lines.append(line)
                else:
                    indented_lines.append(line)  # Keep empty lines as is
            
            protocol_logic = '\n'.join(indented_lines)
            
            # Fill template with corrected logic
            final_code = fill_template_with_logic(template, protocol_logic)
            
            print(f"Generated corrected protocol logic and filled template, total length: {len(final_code)} characters")
            
        except Exception as e:
            print(f"Error in LLM fix generation: {e}")
            # Fallback to original code
            final_code = state["python_code"]
    
    # Report completion to frontend
    if state.get('iteration_reporter'):
        state['iteration_reporter']({
            "event_type": "node_complete",
            "node_name": "generator",
            "attempt_num": attempt_num,
            "has_code": bool(final_code),
            "message": f"Template-based code generation complete for attempt #{attempt_num}"
        })
    
    # Update state
    return {
        "python_code": final_code,
        "llm_diff_output": llm_diff_output,
        "attempts": attempt_num
    }

async def simulate_code_node(state: PyLabRobotGraphState) -> PyLabRobotGraphState:
    """
    Code simulation node: executes PyLabRobot protocol simulation verification
    """
    print("=== PyLabRobot Simulating Code ===")
    
    # Report to frontend
    if state.get('iteration_reporter'):
        state['iteration_reporter']({
            "event_type": "node_start",
            "node_name": "simulator",
            "attempt_num": state["attempts"],
            "message": f"Starting simulation for attempt #{state['attempts']}"
        })
    
    code_to_simulate = state["python_code"]
    if not code_to_simulate:
        # If code is empty, return error directly
        simulation_result = {
            "success": False, 
            "raw_output": "No code to simulate",
            "error_details": "Code generation resulted in empty script.",
            "result_summary": "Empty code"
        }
    else:
        try:
            print("Executing PyLabRobot simulation...")
            # Use the enhanced simulation utility with hardware configuration
            hardware_config = state.get("hardware_config")
            print(f"Debug - [simulate_code_node] Using hardware config: {hardware_config.get('deck_type', 'unknown') if hardware_config else 'None'}")
            simulation_results = await run_pylabrobot_simulation(
                code_to_simulate, 
                return_structured=True,
                hardware_config=hardware_config  # Pass the hardware config directly
            )
            
            # Convert to structured format compatible with the graph
            simulation_result = {
                "success": simulation_results["success"],
                "raw_output": simulation_results["raw_output"],
                "error_details": simulation_results["error_details"] if not simulation_results["success"] else "",
                "result_summary": simulation_results["final_status"],
                "has_warnings": simulation_results.get("has_warnings", False),
                "warning_details": simulation_results.get("warning_details", "")
            }
            
            print(f"Simulation Success: {simulation_results['success']}")
            print(f"Result Summary: {simulation_results['final_status']}")
            
        except Exception as e:
            print(f"Error during simulation execution: {e}")
            simulation_result = {
                "success": False,
                "raw_output": f"Simulation execution error: {e}",
                "error_details": str(e),
                "result_summary": f"Simulation failed: {e}",
                "has_warnings": False,
                "warning_details": ""
            }
    
    # Report completion to frontend
    if state.get('iteration_reporter'):
        state['iteration_reporter']({
            "event_type": "node_complete",
            "node_name": "simulator",
            "attempt_num": state["attempts"],
            "simulation_success": simulation_result["success"],
            "has_warnings": simulation_result.get("has_warnings", False),
            "error_details": simulation_result.get("error_details", ""),
            "message": f"Simulation complete: {'Success' if simulation_result['success'] else 'Failed'}"
        })
    
    return {"simulation_result": simulation_result}

def _analyze_pylabrobot_error(simulation_output: str) -> dict:
    """
    Enhanced PyLabRobot error analyzer with surgical precision.
    Extracts detailed error information including exact code lines and resource details.
    """
    if not simulation_output:
        return {
            "error_type": "Unknown",
            "error_message": "No error output to analyze",
            "extracted_entities": {},
            "line_number": None,
            "context_lines": [],
            "offending_line": None,
            "full_traceback": ""
        }
    
    # Advanced error patterns with enhanced capturing
    error_extraction_patterns = {
        "IndexError": [
            r"IndexError: (list index out of range)",
            r"IndexError: (.+)"
        ],
        "MissingProtocolFunction": [
            r"Protocol function 'async def protocol\(lh\):' not found",
            r"Error: Protocol function.*not found",
            r"Missing.*protocol.*function",
            r"No.*protocol.*function.*defined"
        ],
        "PyLabRobotNotInstalled": [
            r"PyLabRobot is not installed",
            r"No module named 'pylabrobot'",
            r"Please install PyLabRobot"
        ],
        "ResourceNotFoundError": [
            r"Resource with name ['\"](.+?)['\"] not found",
            r"ResourceNotFoundError.*['\"](.+?)['\"]",
            r"lh\.get_resource\(['\"](.+?)['\"]",
            r"Resource '(.+?)' not found"
        ],
        "NoTipAttachedError": [
            r"No tip attached to perform liquid handling",
            r"NoTipAttachedError",
            r"Cannot perform.*without tips"
        ],
        "TipAttachedError": [
            r"Tip already attached",
            r"TipAttachedError",
            r"Tips already present"
        ],
        "IndentationError": [
            r"IndentationError.*line (\d+)",
            r"unindent does not match.*line (\d+)",
            r"Expected an indented block.*line (\d+)"
        ],
        "SyntaxError": [
            r"SyntaxError: (unterminated string literal.*)",
            r"SyntaxError: (invalid syntax.*)",
            r"SyntaxError.*line (\d+)"
        ],
        "AttributeError": [
            r"'(.+?)' object has no attribute '(.+?)'",
            r"AttributeError.*'(.+?)'.*'(.+?)'",
            r"module.*has no attribute '(.+?)'"
        ],
        "NameError": [
            r"name '(.+?)' is not defined",
            r"NameError.*'(.+?)'",
            r"'(.+?)' is not defined"
        ],
        "ImportError": [
            r"ImportError.*cannot import.*'(.+?)'",
            r"No module named '(.+?)'",
            r"cannot import name '(.+?)'"
        ],
        "VolumeError": [
            r"Volume.*exceeds.*volume",
            r"Volume.*out of range",
            r"Invalid volume.*(\d+)",
            r"Volume must be.*(\d+)",
            r"(\d+\.?\d*)\s*exceeds.*(\d+\.?\d*)"
        ]
    }
    
    # Initialize extraction variables
    detected_error = None
    extracted_entities = {}
    error_message = ""
    line_number = None
    offending_line = None
    full_traceback = ""
    
    lines = simulation_output.split('\n')
    
    # ENHANCED: Multi-stage traceback parsing for precise line extraction
    # Stage 1: Find the error line in user code
    traceback_patterns = [
        r'File "<string>", line (\d+), in protocol',
        r'File "<string>", line (\d+)',
        r'line (\d+), in protocol'
    ]
    
    traceback_start = -1
    for i, line in enumerate(lines):
        for pattern in traceback_patterns:
            match = re.search(pattern, line)
            if match:
                line_number = int(match.group(1))
                traceback_start = i
                print(f"[DEBUG] Found error at line {line_number} in traceback at index {i}")
                break
        if line_number:
            break
    
    # Stage 2: Extract the actual offending code line with multiple strategies
    if traceback_start >= 0:
        # Strategy 1: Look for the code line immediately after the traceback line
        for i in range(traceback_start + 1, min(traceback_start + 5, len(lines))):
            line_content = lines[i].strip()
            # Skip empty lines and obvious traceback continuation
            if line_content and not line_content.startswith('File ') and not line_content.startswith('Traceback'):
                # This looks like actual code
                if any(keyword in line_content for keyword in ['await', 'lh.', 'source_plate', 'destination_plate', 'tip_rack']):
                    offending_line = line_content
                    print(f"[DEBUG] Found offending code: {offending_line}")
                    break
        
        # Strategy 2: Build full traceback context for better analysis
        full_traceback = '\n'.join(lines[max(0, traceback_start-2):traceback_start+10])
    
    # Stage 3: Extract the actual error line from the current code if we have line number
    # This will be used later when we have access to the current code
    
    # Stage 4: Enhanced error type detection and entity extraction
    for error_type, patterns in error_extraction_patterns.items():
        for pattern in patterns:
            for i, line in enumerate(lines):
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    detected_error = error_type
                    error_message = line.strip()
                    
                    # Enhanced entity extraction with surgical precision
                    if error_type == "MissingProtocolFunction":
                        extracted_entities["missing_function"] = "async def protocol(lh)"
                        extracted_entities["requirement"] = "All PyLabRobot code must be wrapped in this function"
                    
                    elif error_type == "PyLabRobotNotInstalled":
                        extracted_entities["missing_package"] = "pylabrobot"
                        extracted_entities["installation_note"] = "PyLabRobot package not available"
                    
                    elif error_type == "ResourceNotFoundError":
                        extracted_entities["missing_resource"] = match.group(1)
                    
                    elif error_type == "SyntaxError":
                        # Enhanced SyntaxError analysis
                        extracted_entities["error_line"] = str(line_number) if line_number else "unknown"
                        extracted_entities["offending_code"] = offending_line if offending_line else "unknown"
                        if match.groups():
                            extracted_entities["syntax_details"] = match.group(1)
                        else:
                            extracted_entities["syntax_details"] = "syntax error detected"
                        
                        # Try to extract the specific error type for better guidance
                        if "unterminated string literal" in error_message.lower():
                            extracted_entities["error_category"] = "unclosed_string"
                            extracted_entities["fix_hint"] = "Add missing closing quote"
                        elif "invalid syntax" in error_message.lower():
                            extracted_entities["error_category"] = "invalid_syntax"
                            extracted_entities["fix_hint"] = "Check for missing commas, colons, or parentheses"
                    
                    elif error_type == "IndexError":
                        # ENHANCED IndexError analysis - the key improvement!
                        extracted_entities["error_line"] = str(line_number) if line_number else "unknown"
                        extracted_entities["offending_code"] = offending_line if offending_line else "unknown"
                        
                        if offending_line:
                            # Strategy 1: Look for resource access patterns like "resource_name['A13']" or "resource_name[index]"
                            resource_patterns = [
                                r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\[['\"]*([A-Z0-9]+)['\"]*\]",  # resource['A1'] or resource["A1"]
                                r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\[([0-9]+)\]",  # resource[0]
                                r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\[",  # just resource[
                            ]
                            
                            for resource_pattern in resource_patterns:
                                resource_match = re.search(resource_pattern, offending_line)
                                if resource_match:
                                    extracted_entities["resource_in_error"] = resource_match.group(1)
                                    if len(resource_match.groups()) > 1:
                                        extracted_entities["invalid_index"] = resource_match.group(2)
                                    print(f"[DEBUG] IndexError - Resource: {resource_match.group(1)}, Index: {resource_match.group(2) if len(resource_match.groups()) > 1 else 'unknown'}")
                                    break
                            
                            # Strategy 2: If no specific pattern found, try to extract any resource-like name
                            if "resource_in_error" not in extracted_entities:
                                general_resource_match = re.search(r"(source_plate|destination_plate|tip_rack|reagent_trough|plate|rack)", offending_line, re.IGNORECASE)
                                if general_resource_match:
                                    extracted_entities["resource_in_error"] = general_resource_match.group(1)
                        
                        # Provide context about the error
                        extracted_entities["error_category"] = "index_out_of_range"
                        extracted_entities["fix_hint"] = "Check that the well name or index exists for this resource type"
                    
                    elif error_type == "IndentationError":
                        extracted_entities["error_line"] = str(line_number) if line_number else "unknown"
                        extracted_entities["offending_code"] = offending_line if offending_line else "unknown"
                        if match.groups():
                            extracted_entities["indentation_details"] = match.group(1)
                    
                    elif error_type == "AttributeError":
                        extracted_entities["problematic_object"] = match.group(1) if match.groups() else "unknown"
                        if len(match.groups()) > 1:
                            extracted_entities["missing_attribute"] = match.group(2)
                    
                    elif error_type == "NameError":
                        extracted_entities["undefined_name"] = match.group(1)
                    
                    elif error_type == "ImportError":
                        extracted_entities["import_problem"] = match.group(1)
                    
                    elif error_type == "VolumeError":
                        if match.groups():
                            extracted_entities["problematic_volume"] = match.group(1)
                    
                    break
            if detected_error:
                break
        if detected_error:
            break
    
    # If no specific pattern matched, use general detection
    if not detected_error:
        general_error_keywords = ["Error", "Exception", "Traceback", "Failed"]
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in general_error_keywords):
                detected_error = "GeneralError"
                error_message = line.strip()
                break
    
    # Extract error context lines with enhanced context
    context_lines = []
    if error_message:
        for i, line in enumerate(lines):
            if error_message in line or any(str(entity) in line for entity in extracted_entities.values() if entity):
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context_lines = lines[start:end]
                break
    
    # If still no context, take the last few lines
    if not context_lines:
        context_lines = lines[-10:]
    
    # Debug output for verification
    print(f"[DEBUG] Error Analysis Results:")
    print(f"  - Error Type: {detected_error}")
    print(f"  - Line Number: {line_number}")
    print(f"  - Offending Code: {offending_line}")
    print(f"  - Extracted Entities: {extracted_entities}")
    
    return {
        "error_type": detected_error or "Unknown",
        "error_message": error_message or "Unknown error occurred",
        "extracted_entities": extracted_entities,
        "line_number": line_number,
        "context_lines": context_lines,
        "offending_line": offending_line,
        "full_traceback": full_traceback
    }

def prepare_feedback_node(state: PyLabRobotGraphState) -> PyLabRobotGraphState:
    """
    Analyze simulation failure and prepare structured, actionable feedback for LLM - enhanced version
    """
    print("=== Preparing Advanced Feedback for LLM ===")
    
    # Report to frontend
    if state.get('iteration_reporter'):
        state['iteration_reporter']({
            "event_type": "node_start",
            "node_name": "feedback_preparer",
            "attempt_num": state["attempts"],
            "message": f"Analyzing error and preparing feedback for attempt #{state['attempts']}"
        })
    
    simulation_result = state["simulation_result"]
    raw_error_output = simulation_result.get("raw_output", "")
    error_info = _analyze_pylabrobot_error(raw_error_output)
    
    error_type = error_info["error_type"]
    entities = error_info["extracted_entities"]
    error_message = error_info["error_message"]
    
    print(f"Detected Error Type: {error_type}")
    print(f"Extracted Entities: {entities}")
    
    # Check for infinite loop detection (borrowed from langchain_agent.py)
    previous_feedback = state.get("feedback_for_llm", {})
    previous_error = previous_feedback.get("error_log", "")
    # If error message is exactly the same and we've tried more than once, we're stuck
    is_stuck = error_message == previous_error and state["attempts"] > 1
    
    if is_stuck:
        print("🔥🔥🔥 LOOP DETECTED! The previous PyLabRobot fix failed. Escalating feedback to LLM. 🔥🔥🔥")
        # Set force regeneration flag
        state["force_regenerate"] = True
        
        # ENHANCED: Provide original task context to help AI reorient
        user_query = state.get("user_query", "No user query available")
        hardware_config = state.get("hardware_config", {})
        available_resources = list(hardware_config.get("resources", {}).keys())
        
        analysis = (
            "🚨 CRITICAL: The previous attempt to fix the PyLabRobot code was unsuccessful and resulted in the exact same error. "
            "This indicates the initial analysis or the proposed fix was incorrect. A completely different approach is required. "
            f"The error '{error_message}' has now occurred multiple times, showing that the current fix strategy is fundamentally flawed."
        )
        action = (
            "Action: **EMERGENCY RESET** - Start completely fresh and forget all previous attempts. "
            "\n\n**ORIGINAL TASK (re-read this carefully):**\n"
            f"User Request: {user_query}\n"
            f"Available Resources: {available_resources}\n"
            f"Hardware Type: {hardware_config.get('deck_type', 'unknown')}\n"
            "\n**RESET INSTRUCTIONS:**\n"
            "1. **FORGET all previous attempts.** They were wrong.\n"
            "2. **Start with the simplest possible solution** that fulfills the user's request.\n"
            "3. **Use ONLY the available resources listed above** - do not invent resource names.\n"
            "4. **Follow basic PyLabRobot patterns**: pick_up_tips → aspirate → dispense → drop_tips.\n"
            "5. **Use simple, valid well names** like 'A1', 'B1', 'C1' - avoid complex indexing.\n"
            "6. **If the previous error was IndexError**, use only basic well names (A1-H12).\n"
            "7. **If the previous error was SyntaxError**, write simple, clean code without complex expressions.\n"
            "\n**Generate a completely new, simple solution from scratch.**"
        )
    else:
        # Generate precise feedback based on error type and extracted entities
        analysis = "An unknown PyLabRobot error occurred."
        action = "Please review the protocol code and fix any logical inconsistencies."
        
        # CRITICAL: Missing protocol function error - highest priority
        if error_type == "MissingProtocolFunction":
            analysis = (
                "The protocol failed because it is missing the required entry function 'async def protocol(lh):'. "
                "PyLabRobot protocols MUST be wrapped in this specific async function signature. "
                "The simulation engine cannot execute the protocol without this function wrapper."
            )
            action = (
                "Action: **CRITICAL FIX REQUIRED** - Wrap ALL protocol logic inside a function with the exact signature: "
                "`async def protocol(lh: LiquidHandler):`. This is MANDATORY for PyLabRobot. "
                "Move all your liquid handling operations (pick_up_tips, aspirate, dispense, etc.) inside this function. "
                "Ensure proper async/await syntax is used for all PyLabRobot operations."
            )
        
        # PyLabRobot installation error
        elif error_type == "PyLabRobotNotInstalled":
            missing_package = entities.get("missing_package", "pylabrobot")
            analysis = f"The protocol failed because the '{missing_package}' package is not installed or available in the simulation environment."
            action = f"Action: This is an environment issue. The PyLabRobot package needs to be installed. Contact system administrator or check if PyLabRobot is properly configured in the simulation environment."
        
        # Resource-related errors - precision
        elif error_type == "ResourceNotFoundError":
            missing_resource = entities.get("missing_resource", "unknown_resource")
            analysis = f"The protocol failed with a `ResourceNotFoundError` when trying to access resource '{missing_resource}'. This specific resource was referenced in the code but never defined or loaded onto the deck."
            action = f"Action: Add a resource definition for '{missing_resource}' before it's used. Use either `await lh.load_labware(name='{missing_resource}', ...)` or `lh.deck.assign_resource(...)` to properly initialize this resource."
        
        # Import related errors
        elif error_type == "ImportError":
            import_problem = entities.get("import_problem", "unknown")
            analysis = f"The protocol failed with an `ImportError` for '{import_problem}'. This indicates a missing or incorrect import statement."
            action = f"Action: Check the import statement for '{import_problem}'. Verify the module name is correct and the package is available. Common PyLabRobot imports include: 'from pylabrobot.liquid_handling import LiquidHandler', 'from pylabrobot.resources import *'."
        
        # Volume related errors
        elif error_type == "VolumeError":
            problematic_volume = entities.get("problematic_volume", "unknown")
            analysis = f"The protocol failed with a volume-related error. Volume '{problematic_volume}' is outside the acceptable range for the pipette or operation."
            action = f"Action: Check that volume '{problematic_volume}' is within the pipette's capacity range. PyLabRobot volumes are typically in microliters (µL). Ensure volumes are positive numbers and within the 1-1000µL range for most pipettes."
        
        # Pipette tip related errors - precision
        elif error_type == "NoTipAttachedError":
            analysis = "The protocol failed with a `NoTipAttachedError`. This means a liquid handling operation (aspirate/dispense) was attempted without a tip attached to the pipette."
            action = "Action: Ensure that `await lh.pick_up_tips(tip_rack['A1'])` is called before any liquid handling operation. Check your tip management workflow."
        elif error_type == "TipAttachedError":
            analysis = "The protocol failed with a `TipAttachedError`. This means the protocol tried to pick up a tip when a tip was already attached."
            action = "Action: Check the tip management logic. Ensure `await lh.drop_tips()` is called before trying to pick up new tips, or use `await lh.drop_tips()` then `await lh.pick_up_tips()`."
        
        # Python syntax and code errors - ENHANCED precision
        elif error_type == "SyntaxError":
            error_line = entities.get("error_line", "unknown")
            syntax_details = entities.get("syntax_details", "a syntax error")
            offending_code = entities.get("offending_code", "the line in question")
            error_category = entities.get("error_category", "general_syntax")
            fix_hint = entities.get("fix_hint", "review the syntax")
            
            analysis = (f"The protocol failed with a Python `SyntaxError` on line {error_line}. "
                       f"Specific error: '{syntax_details}'. ")
            
            if error_category == "unclosed_string":
                analysis += "This is an unclosed string literal error - a string was started but never properly closed with a matching quote."
                action = (f"Action: **IMMEDIATE FIX REQUIRED** - Find the unclosed string on line {error_line} in this code: `{offending_code}`. "
                         f"Look for a string that starts with a quote (' or \") but doesn't have a matching closing quote. "
                         f"Add the missing closing quote to fix this error.")
            elif error_category == "invalid_syntax":
                analysis += "This is a general syntax structure error."
                action = (f"Action: Review line {error_line} carefully: `{offending_code}`. "
                         f"Check for: missing commas between function arguments, missing colons after if/for/while statements, "
                         f"unclosed parentheses or brackets, or incorrect indentation.")
            else:
                action = (f"Action: Review line {error_line} for syntax issues: `{offending_code}`. "
                         f"Hint: {fix_hint}. Common issues include missing commas, incorrect indentation, "
                         f"unclosed parentheses, or unclosed string literals.")
        
        elif error_type == "IndexError":
            # ENHANCED IndexError analysis with surgical precision
            error_line = entities.get("error_line", "unknown")
            resource = entities.get("resource_in_error", "unknown_resource")
            invalid_index = entities.get("invalid_index", "unknown")
            offending_code = entities.get("offending_code", "the line in question")
            
            analysis = (f"The protocol failed with an `IndexError` on line {error_line} when trying to access '{resource}'. ")
            
            if resource != "unknown_resource" and invalid_index != "unknown":
                analysis += (f"Specifically, the code tried to access '{resource}[{invalid_index}]', but this index/well does not exist for this resource. ")
                action = (f"Action: **PRECISE FIX REQUIRED** - The error is in this line: `{offending_code}`. "
                         f"The problem is '{resource}[{invalid_index}]' - the index '{invalid_index}' is invalid for resource '{resource}'. ")
                
                # Provide specific guidance based on resource type and invalid index
                if "plate" in resource.lower() and invalid_index.startswith(('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')):
                    action += (f"For a 96-well plate, valid wells are A1-H12. '{invalid_index}' is outside this range. "
                              f"Change '{invalid_index}' to a valid well name like 'A1', 'B2', etc.")
                elif "rack" in resource.lower():
                    action += (f"For a tip rack, ensure the well name '{invalid_index}' exists. "
                              f"Common valid names are A1-H12 for a 96-tip rack.")
                else:
                    action += f"Verify that '{invalid_index}' is a valid index for the '{resource}' resource."
            else:
                analysis += "The code is trying to access an index or well that doesn't exist for this resource."
                action = (f"Action: Examine this line: `{offending_code}`. "
                         f"Find the resource access (like resource_name['A13']) and verify the index/well name is valid. "
                         f"For 96-well plates, valid wells are A1-H12. For other resources, check the available indices.")
            
            # Add hardware configuration reference
            action += f" Consult the hardware configuration to confirm valid wells/indices for '{resource}'."
        elif error_type == "IndentationError":
            error_line = entities.get("error_line", "unknown")
            analysis = f"The protocol failed with an `IndentationError` on line {error_line}. This is a Python indentation structure error."
            action = f"Action: Review line {error_line} and ensure proper indentation. All code inside functions should be indented with 4 spaces."
        elif error_type == "AttributeError":
            problematic_name = entities.get("problematic_object", "unknown")
            missing_attr = entities.get("missing_attribute", "unknown")
            if missing_attr != "unknown":
                analysis = f"The protocol failed with an `AttributeError`. Object '{problematic_name}' doesn't have attribute '{missing_attr}'."
                action = f"Action: Check the PyLabRobot API for correct method names for '{problematic_name}' objects. The attribute/method '{missing_attr}' doesn't exist."
            else:
                analysis = f"The protocol failed with an `AttributeError` related to '{problematic_name}'."
                action = f"Action: Review the usage of '{problematic_name}' and ensure you're using valid PyLabRobot API methods."
        elif error_type == "NameError":
            undefined_name = entities.get("undefined_name", "unknown")
            analysis = f"The protocol failed with a `NameError`. Variable '{undefined_name}' was used before being defined."
            action = f"Action: Define '{undefined_name}' before using it. If it's a resource, ensure it's loaded with `await lh.load_labware()` or similar."
        
        else:
            # General error handling
            analysis = f"The protocol simulation failed with error type '{error_type}'. Error message: {error_message}"
            action = "Action: Carefully review the error message and protocol logic to identify and fix the root cause."
    
    # Enhanced: Extract actual error line from current code for better precision
    current_code = state.get("python_code", "")
    line_number = error_info.get("line_number")
    
    # Get the actual error line from generated code (more reliable than traceback extraction)
    if line_number and current_code:
        actual_error_line = _extract_actual_error_line_from_code(current_code, line_number)
        # Update entities with the real error line if we got a better one
        if actual_error_line != "unknown" and actual_error_line != entities.get("offending_code", ""):
            entities["actual_error_line"] = actual_error_line
            print(f"[DEBUG] Updated offending code from traceback to actual: {actual_error_line}")
    
    # Extract error context code snippet
    code_snippet_info = _extract_code_snippet_around_error(current_code, error_info)
    
    # Find correct usage pattern examples
    usage_example = _find_correct_usage_examples(current_code, error_type, entities)
    
    feedback_dict = {
        "analysis": analysis,
        "action": action,
        "error_log": error_message,
        "error_type": error_type,
        "extracted_entities": entities,
        "context_lines": error_info["context_lines"],
        "code_snippet": code_snippet_info["error_snippet"],
        "error_line_number": code_snippet_info["line_number"],
        "context_range": code_snippet_info["context_range"],
        "usage_example": usage_example,
        "full_traceback": error_info.get("full_traceback", "")
    }
    
    print(f"Advanced Error Analysis: {analysis}")
    print(f"Precision Action: {action}")
    
    # Report completion to frontend
    if state.get('iteration_reporter'):
        state['iteration_reporter']({
            "event_type": "node_complete",
            "node_name": "feedback_preparer", 
            "attempt_num": state["attempts"],
            "has_feedback": True,
            "error_analysis": analysis,
            "message": f"Error analysis complete for attempt #{state['attempts']}"
        })
    
    return {"feedback_for_llm": feedback_dict}

def _extract_actual_error_line_from_code(code: str, line_number: int) -> str:
    """
    Extract the actual line of code that caused the error.
    This provides the real context for AI analysis.
    """
    if not code or not line_number:
        return "unknown"
    
    try:
        code_lines = code.split('\n')
        if 1 <= line_number <= len(code_lines):
            actual_line = code_lines[line_number - 1].strip()
            print(f"[DEBUG] Extracted actual error line {line_number}: {actual_line}")
            return actual_line
        else:
            print(f"[DEBUG] Line number {line_number} out of range (code has {len(code_lines)} lines)")
            return "line number out of range"
    except Exception as e:
        print(f"[DEBUG] Error extracting line: {e}")
        return "extraction failed"

def _extract_code_snippet_around_error(code: str, error_info: dict) -> dict:
    """
    Extract code snippet context based on error information
    """
    if not code:
        return {
            "error_snippet": "No code available",
            "line_number": None,
            "context_range": None
        }
    
    code_lines = code.split('\n')
    line_number = error_info.get("line_number")
    error_type = error_info.get("error_type")
    entities = error_info.get("extracted_entities", {})
    
    # If there's a clear line number, use line number positioning
    if line_number:
        target_line = line_number - 1  # Convert to 0-based index
        start_line = max(0, target_line - 3)
        end_line = min(len(code_lines), target_line + 4)
        
        snippet_lines = []
        for i in range(start_line, end_line):
            marker = " -> " if i == target_line else "    "
            snippet_lines.append(f"{i+1:3d}{marker}{code_lines[i]}")
        
        return {
            "error_snippet": '\n'.join(snippet_lines),
            "line_number": line_number,
            "context_range": f"lines {start_line + 1}-{end_line}"
        }
    
    # If no line number, try fuzzy positioning based on entities
    elif entities:
        # Find lines containing error entities
        target_lines = []
        for i, line in enumerate(code_lines):
            for entity_value in entities.values():
                if isinstance(entity_value, str) and entity_value in line:
                    target_lines.append(i)
                    break
        
        if target_lines:
            # Take the first matching line as target
            target_line = target_lines[0]
            start_line = max(0, target_line - 2)
            end_line = min(len(code_lines), target_line + 3)
            
            snippet_lines = []
            for i in range(start_line, end_line):
                marker = " -> " if i == target_line else "    "
                snippet_lines.append(f"{i+1:3d}{marker}{code_lines[i]}")
            
            return {
                "error_snippet": '\n'.join(snippet_lines),
                "line_number": target_line + 1,
                "context_range": f"lines {start_line + 1}-{end_line}"
            }
    
    # Fallback strategy: return first few lines of code
    snippet_lines = []
    for i in range(min(8, len(code_lines))):
        snippet_lines.append(f"{i+1:3d}    {code_lines[i]}")
    
    return {
        "error_snippet": '\n'.join(snippet_lines),
        "line_number": None,
        "context_range": f"lines 1-{min(8, len(code_lines))}"
    }

def _find_correct_usage_examples(code: str, error_type: str, entities: dict) -> str:
    """
    Find correct usage pattern examples in current code
    """
    if not code:
        return "No code available for reference"
    
    code_lines = code.split('\n')
    examples = []
    
    # Find corresponding correct patterns based on error type
    if error_type == "ResourceNotFoundError":
        missing_resource = entities.get("missing_resource", "")
        
        # Find correct resource definition patterns
        resource_patterns = [
            r'await\s+lh\.load_labware\s*\(',
            r'lh\.deck\.assign_resource\s*\(',
            r'=\s*await\s+lh\.load_labware\s*\('
        ]
        
        for i, line in enumerate(code_lines):
            for pattern in resource_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Extract multi-line complete definition
                    start_line = i
                    end_line = i + 1
                    
                    # Search downward until finding complete statement
                    while end_line < len(code_lines) and (
                        not code_lines[end_line-1].strip().endswith(')') or
                        code_lines[end_line].strip().startswith('.')
                    ):
                        end_line += 1
                    
                    example_lines = code_lines[start_line:end_line]
                    example = '\n'.join(f"    {line}" for line in example_lines)
                    examples.append(f"Example of correct resource loading:\n{example}")
                    break
            
            if examples:  # Only need one good example
                break
    
    elif error_type == "NoTipAttachedError":
        # Find correct tip management patterns
        tip_patterns = [
            r'await\s+lh\.pick_up_tips\s*\(',
            r'lh\.pick_up_tips\s*\('
        ]
        
        for i, line in enumerate(code_lines):
            for pattern in tip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Find pick_up_tips -> operation -> drop_tips complete workflow
                    workflow_lines = [line]
                    
                    # Search downward for related liquid handling operations
                    for j in range(i+1, min(i+6, len(code_lines))):
                        next_line = code_lines[j]
                        if any(op in next_line.lower() for op in ['aspirate', 'dispense', 'drop_tips']):
                            workflow_lines.append(next_line)
                    
                    if len(workflow_lines) > 1:
                        example = '\n'.join(f"    {wline}" for wline in workflow_lines)
                        examples.append(f"Example of correct tip workflow:\n{example}")
                        break
    
    # If examples found, return the first one; otherwise return empty
    if examples:
        return examples[0]
    else:
        return f"No correct usage example found in current code for {error_type}"

def should_continue_edge(state: PyLabRobotGraphState) -> str:
    """
    Conditional edge: determine whether to continue iteration
    """
    print("=== Checking Condition ===")
    
    # Get simulation results
    simulation_result = state.get("simulation_result")
    if not simulation_result:
        print("Condition: No simulation result, continuing.")
        return "continue"
    
    # Check success status
    success = simulation_result.get("success", False)
    
    if success:
        # Success, end process
        print("✅ PyLabRobot protocol successfully simulated and validated!")
        state["final_outcome"] = "Success"
        return "end"
    elif state["attempts"] >= state["max_attempts"]:
        # Reached maximum attempts, end process
        print(f"❌ Max attempts ({state['max_attempts']}) reached. PyLabRobot protocol failed to validate.")
        state["final_outcome"] = "Max attempts reached"
        return "end"
    else:
        # Failed but not reached max attempts, continue loop
        print(f"🔄 Attempt {state['attempts']} failed. Retrying...")
        return "continue"

# Build LangGraph - enhanced version with diff-based repair
def create_pylabrobot_agent():
    """
    Create and compile LangGraph Agent - enhanced version
    """
    workflow = StateGraph(PyLabRobotGraphState)
    
    # Add three independent nodes
    workflow.add_node("generator", generate_code_node)           # Code generator node
    workflow.add_node("simulator", simulate_code_node)           # Code simulator node  
    workflow.add_node("feedback_preparer", prepare_feedback_node) # Feedback preparer node
    
    # Define graph flow
    workflow.add_edge(START, "generator")                        # From start node to code generator
    workflow.add_edge("generator", "simulator")                  # From code generator to simulator
    workflow.add_conditional_edges(                              # Conditional edge: decide next step based on simulation results
        "simulator",
        should_continue_edge,
        {
            "continue": "feedback_preparer",  # If need to continue, go to feedback preparer
            "end": END                        # If complete, end process
        }
    )
    workflow.add_edge("feedback_preparer", "generator")          # Loop back to code generator
    
    return workflow.compile()

async def run_pylabrobot_agent_and_stream_events(
    user_query: str, 
    hardware_config_str: str, 
    max_attempts: int = 3
) -> AsyncGenerator[Dict, None]:
    """
    Run PyLabRobot Agent and stream events for real-time frontend updates
    
    Args:
        user_query: User's natural language requirement
        hardware_config_str: The hardware configuration as a JSON string
        max_attempts: Maximum number of attempts
        
    Yields:
        Dict: Event data for frontend SSE stream
    """
    
    print(f"🚀 Starting PyLabRobot Protocol Generation Agent")
    print(f"📝 User Query: {user_query}")
    print(f"🔄 Max Attempts: {max_attempts}")
    
    # Create Agent
    app = create_pylabrobot_agent()
    
    # Create event reporter function
    async def report_event(event_data: Dict):
        """Report events to frontend via streaming"""
        yield event_data
    
    event_queue = []
    
    def sync_reporter(event_data: Dict):
        """Synchronous event reporter for graph nodes"""
        event_queue.append(event_data)
    
    # Parse the hardware configuration from the string
    try:
        hardware_config = json.loads(hardware_config_str)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in hardware_config_str. Falling back to default.")
        # Fallback to loading the default configuration
        from .pylabrobot_utils import load_hardware_configuration
        hardware_config = load_hardware_configuration()

    dynamic_knowledge = generate_dynamic_pylabrobot_knowledge(hardware_config)
    
    print(f"Debug - [PyLabRobot Agent] Loaded hardware config: {hardware_config.get('deck_type', 'unknown')}")
    print(f"Debug - [PyLabRobot Agent] Available resources: {list(hardware_config.get('resources', {}).keys())}")
    
    # Initial state
    initial_state = {
        "user_query": user_query,
        "hardware_config": hardware_config, # Now a dictionary
        "pylabrobot_knowledge": dynamic_knowledge,
        "python_code": None,
        "llm_diff_output": None,
        "simulation_result": None,
        "feedback_for_llm": {},
        "attempts": 0,
        "max_attempts": max_attempts,
        "final_outcome": None,
        "iteration_reporter": sync_reporter,
        "force_regenerate": False
    }
    
    # Send initial event
    yield {
        "event_type": "initialization",
        "message": f"Starting PyLabRobot protocol generation for: {user_query}",
        "max_attempts": max_attempts,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    try:
        # Use astream for real-time event processing
        async for event in app.astream(
            initial_state,
            config={"recursion_limit": 100}  # Increase recursion limit
        ):
            # The event dictionary contains information about the current step
            # We can extract the node name and output
            
            node_name = list(event.keys())[0]
            node_output = event[node_name]
            
            # The 'iteration_reporter' in each node already sends detailed updates.
            # Here, we can yield the raw events if needed for deeper debugging,
            # but the primary reporting is handled within the nodes.
            # For now, we'll just print a high-level trace.
            
            print(f"--- Agent Step: {node_name} ---")
            # print(f"Output: {node_output}") # Uncomment for verbose logging

            # The 'sync_reporter' collects events from nodes. We yield them here.
            while event_queue:
                yield event_queue.pop(0)
                await asyncio.sleep(0.01)

        # After the stream is finished, the final state is in the last event
        final_state = event.get('__end__', {})

        # Send final result event
        simulation_result = final_state.get('simulation_result', {})
        success = simulation_result.get('success', False)
        
        yield {
            "event_type": "final_result",
            "success": success,
            "generated_code": final_state.get('python_code'),
            "total_attempts": final_state.get('attempts'),
            "final_outcome": final_state.get('final_outcome'),
            "error_report": simulation_result.get('error_details') if not success else None,
            "message": f"PyLabRobot Agent completed after {final_state.get('attempts')} attempts"
        }
        
    except Exception as e:
        print(f"❌ PyLabRobot Agent failed with exception: {e}")
        # Yield a comprehensive error event
        yield {
            "event_type": "error",
            "message": f"PyLabRobot Agent execution failed: {str(e)}",
            "error_details": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }
    finally:
        # Always send a stream completion event
        yield {
            "event_type": "stream_complete"
        }

if __name__ == "__main__":
    # Test function
    async def test_pylabrobot_agent():
        """
        Main test function
        """
        test_query = "Print hello and show deck information"
        
        print(f"Testing PyLabRobot Agent with query: {test_query}")
        
        try:
            async for event in run_pylabrobot_agent_and_stream_events(test_query, max_attempts=2):
                print(f"Event: {event}")
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Run test
    asyncio.run(test_pylabrobot_agent()) 
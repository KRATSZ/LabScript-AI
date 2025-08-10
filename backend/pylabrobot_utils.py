"""
PyLabRobot Protocol Simulation Utilities - Enhanced Version

This module provides enhanced PyLabRobot protocol simulation functionality,
featuring real simulation backend integration and dynamic hardware configuration.

Inspired by the robust design patterns from langchain_agent.py, this module
implements a true simulation environment that can accurately execute and validate
PyLabRobot protocols with real error reporting and feedback.
"""

import asyncio
import traceback
import re
import tempfile
import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Union, Optional

# PyLabRobot imports for real simulation
try:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import ChatterBoxBackend  # 正确的模拟后端
    from pylabrobot.resources import Deck
    # Import resource classes as needed
    try:
        from pylabrobot.resources.hamilton import STARLetDeck
    except ImportError:
        STARLetDeck = None
    try:
        from pylabrobot.resources.opentrons import OTDeck
    except ImportError:
        OTDeck = None
    PYLABROBOT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PyLabRobot not available: {e}")
    PYLABROBOT_AVAILABLE = False

# Hardware configuration file path
HARDWARE_PROFILES_DIR = Path(__file__).parent / "hardware_profiles"
DEFAULT_HARDWARE_CONFIG = HARDWARE_PROFILES_DIR / "pylabrobot_default.json"

# Default hardware configuration (fallback if file doesn't exist)
DEFAULT_HARDWARE_SETUP = {
    "deck_type": "hamilton_star",
    "deck_name": "simple_deck",
    "resources": {
        "tip_rack_50ul": {
            "type": "TIP_50ul_L",
            "location": {"x": 100, "y": 100, "z": 0},
            "description": "50µL tip rack"
        },
        "source_plate": {
            "type": "Cos_96_DW_1mL", 
            "location": {"x": 200, "y": 100, "z": 0},
            "description": "Source 96-well plate"
        },
        "destination_plate": {
            "type": "Cos_96_DW_1mL",
            "location": {"x": 300, "y": 100, "z": 0}, 
            "description": "Destination 96-well plate"
        }
    }
}

def load_hardware_configuration(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load hardware configuration from JSON file with fallback to defaults.
    
    Args:
        config_path: Optional path to hardware configuration file
        
    Returns:
        Dict containing hardware configuration
    """
    if config_path is None:
        config_path = DEFAULT_HARDWARE_CONFIG
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"Debug - [load_hardware_configuration] Loaded config from {config_path}")
            return config
        else:
            print(f"Debug - [load_hardware_configuration] Config file not found, using defaults")
            return DEFAULT_HARDWARE_SETUP
    except Exception as e:
        print(f"Warning - [load_hardware_configuration] Failed to load config: {e}")
        return DEFAULT_HARDWARE_SETUP

def generate_dynamic_pylabrobot_knowledge(hardware_config: Dict[str, Any]) -> str:
    """
    Generate dynamic PyLabRobot knowledge prompt based on hardware configuration.
    
    This function now generates device-specific knowledge and best practices based on
    the robot_model field, providing tailored guidance for different robot platforms.
    
    Args:
        hardware_config: Hardware configuration dictionary, should include:
            - robot_model: str (optional) - specific robot model
            - deck_type: str - type of deck
            - resources: dict - available resources
        
    Returns:
        Formatted knowledge string for LLM prompts with device-specific context
    """
    resources = hardware_config.get("resources", {})
    deck_type = hardware_config.get("deck_type", "hamilton_star")
    robot_model = hardware_config.get("robot_model", "").lower()
    
    # Generate device-specific introduction
    if robot_model == "hamilton_star":
        device_intro = """
You are an expert in generating Python protocols for the **Hamilton STAR** liquid handling robot using PyLabRobot.
The Hamilton STAR is a high-precision, flexible liquid handling platform known for its accuracy and reliability.

== HAMILTON STAR SPECIFIC CONSIDERATIONS ==
- High precision: Suitable for very small volumes (1µL to 1000µL)
- Multiple pipetting channels available
- Excellent for complex multi-step protocols
- Supports advanced features like tip tracking and liquid level detection
- Ideal for pharmaceutical and research applications
"""
    elif robot_model == "hamilton_vantage":
        device_intro = """
You are an expert in generating Python protocols for the **Hamilton Vantage** liquid handling robot using PyLabRobot.
The Hamilton Vantage is designed for high-throughput applications with exceptional speed and precision.

== HAMILTON VANTAGE SPECIFIC CONSIDERATIONS ==
- High-throughput capabilities: Designed for 96/384-well plate processing
- Fast pipetting operations for batch processing
- Optimized for screening and assay applications
- Advanced plate handling and stacking capabilities
- Excellent for pharmaceutical discovery workflows
"""
    elif robot_model == "tecan_evo":
        device_intro = """
You are an expert in generating Python protocols for the **Tecan Freedom EVO** liquid handling robot using PyLabRobot.
The Tecan EVO series is known for its modularity and flexibility in laboratory automation.

== TECAN EVO SPECIFIC CONSIDERATIONS ==
- Modular design: Highly customizable for specific applications
- Multiple arm configurations available
- Excellent for complex workflows with multiple liquid handling steps
- Strong integration with other laboratory instruments
- Preferred for clinical diagnostics and life science research
"""
    elif robot_model == "opentrons":
        device_intro = """
You are an expert in generating Python protocols for the **Opentrons** liquid handling robot using PyLabRobot.
Opentrons robots are known for their accessibility, open-source approach, and ease of use.

== OPENTRONS SPECIFIC CONSIDERATIONS ==
- User-friendly and cost-effective platform
- Strong community support and protocol sharing
- Ideal for educational and research environments
- Standardized labware and consumables
- Great for routine laboratory tasks and protocol development
"""
    else:
        device_intro = f"""
You are an expert in generating Python protocols for PyLabRobot platform.
{f'Current setup: {robot_model.upper()} robot' if robot_model else 'Using generic simulation environment'}

== GENERAL PYLABROBOT CONSIDERATIONS ==
- Hardware-agnostic design allows protocol portability
- Focus on clear, maintainable code structure
- Always follow PyLabRobot best practices for liquid handling
"""
    
    knowledge = f"""{device_intro}

Your task is to write an async Python function `async def protocol(lh): ...` based on the user's request.

== PyLabRobot Key API Summary ==
- The main object is `lh` (LiquidHandler). All operations are methods of `lh`.
- All `lh` operations are asynchronous and MUST be awaited. e.g., `await lh.pick_up_tips(...)`.
- Getting resources: Use `lh.get_resource("resource_name")` to get a resource object from the deck.
- Core commands:
  - `await lh.pick_up_tips(tip_rack["A1"])`: Picks up tips from a specific spot.
  - `await lh.drop_tips(tip_rack["A1"])`: Drops tips back to a specific spot.
  - `await lh.aspirate(plate["A1"], vols=[100])`: Aspirates 100uL from well A1.
  - `await lh.dispense(plate["B1"], vols=[100])`: Dispenses 100uL into well B1.

== CURRENT HARDWARE SETUP ({deck_type.upper()}) ==
{f'Robot Model: {robot_model.upper()}' if robot_model else 'Generic Setup'}
The deck has been pre-configured with the following resources that you MUST use:
"""
    
    for resource_name, resource_info in resources.items():
        resource_type = resource_info.get("type", "Unknown")
        description = resource_info.get("description", "")
        knowledge += f"\n- `{resource_name}`: {description} (Type: {resource_type})"
        knowledge += f"\n  Access with: `{resource_name} = lh.get_resource('{resource_name}')`"
    
    # Add device-specific best practices
    if robot_model in ["hamilton_star", "hamilton_vantage"]:
        best_practices = """

== HAMILTON-SPECIFIC BEST PRACTICES ==
1. **Tip Management**: Hamilton robots have excellent tip tracking - leverage this for complex protocols
2. **Volume Precision**: Take advantage of high-precision capabilities for small volumes
3. **Liquid Classes**: Consider different liquid properties when designing protocols
4. **Error Handling**: Hamilton robots provide detailed error feedback - protocols should be robust
"""
    elif robot_model == "tecan_evo":
        best_practices = """

== TECAN EVO-SPECIFIC BEST PRACTICES ==
1. **Modular Approach**: Design protocols to take advantage of EVO's modular architecture
2. **Batch Processing**: Optimize for multiple plate handling when possible
3. **Flexible Positioning**: Utilize EVO's flexible arm positioning for complex layouts
4. **Integration Ready**: Design protocols that can easily integrate with other instruments
"""
    elif robot_model == "opentrons":
        best_practices = """

== OPENTRONS-SPECIFIC BEST PRACTICES ==
1. **Standardized Labware**: Stick to Opentrons-verified labware for best results
2. **Community Protocols**: Leverage community-tested protocol patterns
3. **Simplicity**: Keep protocols straightforward and well-documented
4. **Cost Efficiency**: Design protocols to minimize tip and reagent usage
"""
    else:
        best_practices = """

== GENERAL BEST PRACTICES ==
1. **Hardware Agnostic**: Write protocols that can be easily adapted to different robots
2. **Clear Structure**: Maintain clean, readable code structure
3. **Error Handling**: Include appropriate error checking and recovery
4. **Documentation**: Comment complex operations clearly
"""
    
    knowledge += best_practices
    
    knowledge += f"""

== IMPORTANT PROTOCOL REQUIREMENTS ==
1. **Use only the pre-defined resources listed above**
2. **Always pick up tips before aspirating and drop them after dispensing**
3. **Use exact resource names as specified**
4. **All operations must be awaited with `await`**
5. **End successful protocols with `print("--- PROTOCOL_SUCCESS ---")`**
{f'6. **Follow {robot_model.upper()}-specific best practices as outlined above**' if robot_model else ''}

== Example Protocol Structure ==
```python
async def protocol(lh):
    # Get pre-configured resources
    tip_rack = lh.get_resource("tip_rack_50ul")
    source = lh.get_resource("source_plate")
    dest = lh.get_resource("destination_plate")
    
    # Perform operations{f' (optimized for {robot_model.upper()})' if robot_model else ''}
    await lh.pick_up_tips(tip_rack["A1"])
    await lh.aspirate(source["A1"], vols=[100])
    await lh.dispense(dest["A1"], vols=[100])
    await lh.drop_tips()
    
    print("--- PROTOCOL_SUCCESS ---")
```
"""
    
    return knowledge

async def run_pylabrobot_simulation(
    protocol_code: str, 
    return_structured: bool = False,
    hardware_config_path: Optional[str] = None,
    hardware_config: Optional[Dict[str, Any]] = None
) -> Union[str, Dict[str, Any]]:
    """
    Run PyLabRobot protocol simulation (Enhanced Public Interface)
    
    This is the main public interface that mirrors the style of opentrons_utils.py
    but provides real PyLabRobot simulation capabilities.
    
    Args:
        protocol_code: PyLabRobot protocol code string
        return_structured: If True, return structured dict; if False, return formatted string
        hardware_config_path: Optional path to hardware configuration file
        hardware_config: Optional hardware configuration dict (takes precedence over path)
    
    Returns:
        Union[str, Dict[str, Any]]: Simulation results
    """
    
    # Load hardware configuration - prefer passed config over file path
    if hardware_config is not None:
        hw_config = hardware_config
        print(f"Debug - [run_pylabrobot_simulation] Using provided hardware config")
    else:
        hw_config = load_hardware_configuration(hardware_config_path)
        print(f"Debug - [run_pylabrobot_simulation] Loaded hardware config from file")
    
    # Initialize result data structure (mirroring langchain_agent.py style)
    result_data = {
        "success": False,
        "raw_output": "",
        "error_details": None,
        "has_warnings": False,
        "warning_details": None,
        "final_status": "Unknown",
        "recommendations": None,
        "hardware_config": hw_config
    }
    
    try:
        # Run the real async simulation
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we are, create a task
            simulation_result = await run_pylabrobot_protocol_async(protocol_code, hw_config)
        except RuntimeError:
            # No running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                simulation_result = loop.run_until_complete(
                    run_pylabrobot_protocol_async(protocol_code, hw_config)
                )
            finally:
                loop.close()
        
        # Process simulation results
        stdout_content = simulation_result.get('stdout', '')
        stderr_content = simulation_result.get('stderr', '')
        
        full_output = f"--- PyLabRobot Simulation STDOUT ---\n{stdout_content}\n--- PyLabRobot Simulation STDERR ---\n{stderr_content}"
        result_data["raw_output"] = full_output.strip()
        
        if simulation_result["success"]:
            result_data["success"] = True
            result_data["final_status"] = "PyLabRobot simulation completed successfully"
            
            # Check for warnings in stderr (even on success)
            if stderr_content and stderr_content.strip():
                result_data["has_warnings"] = True
                result_data["warning_details"] = stderr_content.strip()
                result_data["final_status"] = "Success with warnings"
        else:
            result_data["success"] = False
            result_data["error_details"] = stderr_content.strip() if stderr_content else "PyLabRobot simulation failed without specific error details."
            result_data["recommendations"] = get_pylabrobot_error_recommendations(stderr_content)
            result_data["final_status"] = "PyLabRobot simulation failed"
        
        if return_structured:
            return result_data
        else:
            # Format as string for backward compatibility (mirroring opentrons style)
            if result_data["success"]:
                status_msg = "✅ PyLabRobot 协议模拟成功"
                if result_data["has_warnings"]:
                    status_msg += f" (有警告: {result_data['warning_details']})"
                return f"{status_msg}\n\n{result_data['raw_output']}"
            else:
                error_msg = f"❌ PyLabRobot 协议模拟失败\n错误: {result_data['error_details']}"
                if result_data["recommendations"]:
                    error_msg += f"\n建议: {result_data['recommendations']}"
                return f"{error_msg}\n\n{result_data['raw_output']}"
                
    except Exception as e:
        error_msg = f"PyLabRobot simulation execution error: {str(e)}"
        result_data["success"] = False
        result_data["error_details"] = error_msg
        result_data["raw_output"] = f"Exception: {error_msg}\n{traceback.format_exc()}"
        result_data["final_status"] = "Simulation execution failed"
        
        if return_structured:
            return result_data
        else:
            return f"❌ PyLabRobot 模拟执行异常: {error_msg}"

async def setup_simulation_environment(hardware_config: Dict[str, Any]):
    """
    Set up a real PyLabRobot simulation environment with specified hardware configuration.
    Based on the working Hamilton_vantage.py script pattern.
    
    This function creates a fully configured LiquidHandler with all resources properly set up,
    allowing Agent-generated protocol functions to work with `lh.get_resource()` calls.
    
    Args:
        hardware_config: Hardware configuration dictionary
    
    Returns:
        Configured LiquidHandler instance with all resources loaded
        
    Raises:
        Exception: If PyLabRobot is not available or setup fails
    """
    if not PYLABROBOT_AVAILABLE:
        raise Exception("PyLabRobot is not installed. Please install PyLabRobot to use real simulation.")
    
    try:
        # Import required PyLabRobot components
        from pylabrobot.resources import Deck
        try:
            from pylabrobot.resources.coordinate import Coordinate
        except ImportError:
            # 备用方案：使用简单的坐标表示
            class Coordinate:
                def __init__(self, x=0, y=0, z=0):
                    self.x, self.y, self.z = x, y, z
        
        robot_model = hardware_config.get("robot_model", "").lower()
        print(f"Debug - [setup_simulation_environment] Setting up {robot_model} simulation environment")
        
        # Use ChatterBoxBackend for reliable simulation
        backend = ChatterBoxBackend()
        
        # Create deck based on robot model
        if robot_model == "hamilton_star" or robot_model == "hamilton_vantage":
            if STARLetDeck:
                deck = STARLetDeck()
                print(f"Debug - [setup_simulation_environment] Using Hamilton deck")
            else:
                # Fallback to generic deck
                deck = Deck(name="hamilton_deck", size_x=600, size_y=400, size_z=120)
                print(f"Debug - [setup_simulation_environment] Using generic deck (Hamilton imports not available)")
        else:
            # Generic deck
            deck = Deck(
                name=hardware_config.get("deck_name", "generic_deck"),
                size_x=hardware_config.get("size_x", 500),
                size_y=hardware_config.get("size_y", 400), 
                size_z=hardware_config.get("size_z", 100)
            )
            print(f"Debug - [setup_simulation_environment] Using generic deck")
        
        # Create liquid handler
        lh = LiquidHandler(backend=backend, deck=deck)
        await lh.setup()
        
        # Configure resources from hardware config - THIS IS THE KEY FIX
        resources_config = hardware_config.get('resources', {})
        configured_resources = {}
        
        print(f"Debug - [setup_simulation_environment] Configuring {len(resources_config)} resources...")
        
        for resource_name, resource_info in resources_config.items():
            try:
                # Create a simple resource object that can be accessed via lh.get_resource()
                # For simulation, we'll create mock resource objects with the expected interface
                
                # Import basic resource types
                try:
                    from pylabrobot.resources import (
                        TipRack, Plate, Container,
                        Coordinate
                    )
                    
                    resource_type = resource_info.get("type", "generic")
                    location = resource_info.get("location", {"x": 0, "y": 0, "z": 0})
                    
                    # Create coordinate
                    coord = Coordinate(
                        x=location.get("x", 0),
                        y=location.get("y", 0), 
                        z=location.get("z", 0)
                    )
                    
                    # Create appropriate resource based on type
                    if "tip" in resource_type.lower() or "tip" in resource_name.lower():
                        # Create tip rack
                        resource = TipRack(
                            name=resource_name,
                            size_x=85.48, size_y=127.76, size_z=97,  # Standard 96-tip rack
                            num_items_x=12, num_items_y=8
                        )
                    elif "plate" in resource_type.lower() or "plate" in resource_name.lower():
                        # Create plate
                        resource = Plate(
                            name=resource_name,
                            size_x=85.48, size_y=127.76, size_z=14.22,  # Standard 96-well plate
                            num_items_x=12, num_items_y=8
                        )
                    else:
                        # Create generic container
                        resource = Container(
                            name=resource_name,
                            size_x=85.48, size_y=127.76, size_z=50
                        )
                    
                    # Assign resource to deck
                    deck.assign_child_resource(resource, location=coord)
                    configured_resources[resource_name] = resource
                    
                    print(f"Debug - [setup_simulation_environment] Configured {resource_name} ({type(resource).__name__})")
                    
                except ImportError as e:
                    print(f"Warning - [setup_simulation_environment] Could not import PyLabRobot resources: {e}")
                    # Create a simple mock object
                    class MockResource:
                        def __init__(self, name):
                            self.name = name
                            
                        def __getitem__(self, key):
                            # Return a mock well/position
                            return MockWell(f"{self.name}[{key}]")
                    
                    class MockWell:
                        def __init__(self, name):
                            self.name = name
                    
                    configured_resources[resource_name] = MockResource(resource_name)
                    print(f"Debug - [setup_simulation_environment] Created mock resource {resource_name}")
                    
            except Exception as e:
                print(f"Warning - [setup_simulation_environment] Failed to configure resource {resource_name}: {e}")
        
        # Monkey-patch get_resource method to return our configured resources
        original_get_resource = getattr(lh, 'get_resource', None)
        
        def get_resource(name):
            if name in configured_resources:
                return configured_resources[name]
            else:
                print(f"Warning - Resource '{name}' not found in configuration")
                if original_get_resource:
                    return original_get_resource(name)
                else:
                    raise ValueError(f"Resource '{name}' not found")
        
        lh.get_resource = get_resource
        
        print(f"Debug - [setup_simulation_environment] Environment ready with {len(configured_resources)} resources")
        print(f"Debug - [setup_simulation_environment] Available resources: {list(configured_resources.keys())}")
        
        return lh
        
    except Exception as e:
        print(f"Error - [setup_simulation_environment] Failed to setup simulation: {e}")
        raise

async def run_pylabrobot_protocol_async(
    protocol_code: str, 
    hardware_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute PyLabRobot protocol using real SimulationBackend (Enhanced Version)
    
    This function replaces the fake simulation with a true PyLabRobot simulation environment.
    It creates a real LiquidHandler instance, executes the protocol code dynamically,
    and captures genuine Python exceptions and simulation events.
    
    Args:
        protocol_code: Python protocol code string containing `async def protocol(lh):`
        hardware_config: Optional hardware configuration. If None, loads default config.
    
    Returns:
        Dict containing:
        - success: bool
        - stdout: str (simulation events and output)
        - stderr: str (error details if failed)
        - result_summary: str
        - execution_info: dict (additional execution details)
    """
    
    # Load hardware configuration
    if hardware_config is None:
        hardware_config = load_hardware_configuration()
    
    execution_info = {
        "hardware_config": hardware_config,
        "protocol_length": len(protocol_code),
        "execution_time": None
    }
    
    # Validate protocol code structure (支持类型注解)
    import re
    # 使用正则表达式匹配 async def protocol(lh) 或 async def protocol(lh: LiquidHandler)
    protocol_pattern = r'async\s+def\s+protocol\s*\(\s*lh\s*(?::\s*[^)]+)?\s*\)\s*:'
    if not re.search(protocol_pattern, protocol_code):
        return {
            "success": False,
            "stdout": "",
            "stderr": "Error: Protocol function 'async def protocol(lh):' or 'async def protocol(lh: LiquidHandler):' not found in code",
            "result_summary": "Missing required protocol function definition",
            "execution_info": execution_info
        }
    
    # Check for basic Python syntax
    try:
        compile(protocol_code, '<protocol>', 'exec')
    except SyntaxError as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"SyntaxError: {e.msg} at line {e.lineno}",
            "result_summary": f"Python syntax error at line {e.lineno}",
            "execution_info": execution_info
        }
    
    start_time = asyncio.get_event_loop().time()
    lh = None
    
    try:
        # Set up real simulation environment
        print("Debug - [run_pylabrobot_protocol_async] Setting up simulation environment...")
        lh = await setup_simulation_environment(hardware_config)
        
        # Create safe execution context
        exec_globals = {
            'lh': lh,
            'asyncio': asyncio,
            'print': print,  # Allow printing for protocol output
            '__builtins__': __builtins__,
        }
        
        # Execute protocol code to define the function
        print("Debug - [run_pylabrobot_protocol_async] Executing protocol code...")
        exec(protocol_code, exec_globals)
        
        # Get the protocol function from executed context
        protocol_func = exec_globals.get('protocol')
        if not callable(protocol_func):
            raise ValueError("Protocol function 'protocol' not found or not callable after code execution")
        
        # Execute the protocol function
        print("Debug - [run_pylabrobot_protocol_async] Running protocol function...")
        await protocol_func(lh)
        
        # Get simulation events/logs
        simulation_events = []
        if hasattr(lh.backend, 'get_events'):
            simulation_events = lh.backend.get_events()
        
        # Format successful output
        stdout_output = "PyLabRobot protocol simulation completed successfully\n"
        stdout_output += f"Hardware configuration: {hardware_config.get('deck_type', 'unknown')}\n"
        stdout_output += f"Resources used: {list(hardware_config.get('resources', {}).keys())}\n"
        
        if simulation_events:
            stdout_output += "\nSimulation Events:\n"
            for i, event in enumerate(simulation_events, 1):
                stdout_output += f"  {i}. {event}\n"
        
        stdout_output += "\n--- PROTOCOL_SUCCESS ---\n"
        
        execution_info["execution_time"] = asyncio.get_event_loop().time() - start_time
        execution_info["events_count"] = len(simulation_events)
        
        return {
            "success": True,
            "stdout": stdout_output,
            "stderr": "",
            "result_summary": "Protocol executed successfully",
            "execution_info": execution_info
        }
        
    except Exception as e:
        # Capture real Python exceptions with full traceback
        error_traceback = traceback.format_exc()
        execution_info["execution_time"] = asyncio.get_event_loop().time() - start_time
        execution_info["error_type"] = type(e).__name__
        
        print(f"Debug - [run_pylabrobot_protocol_async] Protocol execution failed: {e}")
        
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Exception during protocol execution: {str(e)}\n\nFull traceback:\n{error_traceback}",
            "result_summary": f"Protocol execution failed: {type(e).__name__}",
            "execution_info": execution_info
        }
    
    finally:
        # Clean up simulation environment
        if lh:
            try:
                await lh.stop()
                print("Debug - [run_pylabrobot_protocol_async] Simulation environment cleaned up")
            except Exception as cleanup_error:
                print(f"Warning - [run_pylabrobot_protocol_async] Cleanup failed: {cleanup_error}")

def get_pylabrobot_error_recommendations(error_output: str) -> str:
    """
    Provide intelligent recommendations based on PyLabRobot error patterns.
    
    Enhanced version that provides more specific guidance based on common
    PyLabRobot errors, similar to the error analysis in langchain_agent.py.
    
    Args:
        error_output: Error output from PyLabRobot simulation
        
    Returns:
        str: Recommendations for fixing the error
    """
    if not error_output:
        return "No specific error information available."
    
    error_lower = error_output.lower()
    
    # PyLabRobot-specific error patterns (enhanced)
    if "resourcenotfounderror" in error_lower or "resource not found" in error_lower:
        return "请确保所有引用的资源都已在硬件配置中正确定义。检查资源名称是否与配置文件中的名称完全匹配。"
    elif "notipattachederror" in error_lower or "no tip attached" in error_lower:
        return "在进行液体处理操作前，请确保已使用 await lh.pick_up_tips() 安装tip。"
    elif "tipattachederror" in error_lower or "tip already attached" in error_lower:
        return "在安装新tip前，请先使用 await lh.drop_tips() 丢弃当前tip。"
    elif "backend not setup" in error_lower or "setup" in error_lower:
        return "确保模拟器后端已正确初始化。这通常是内部错误，请检查硬件配置。"
    elif "deck" in error_lower and "not found" in error_lower:
        return "Deck配置有问题。请检查硬件配置文件中的deck设置。"
    elif "indentationerror" in error_lower:
        return "请检查代码缩进，确保所有代码块都有正确的缩进级别。"
    elif "syntaxerror" in error_lower:
        return "请检查Python语法，确保所有括号、引号、冒号等符号都正确配对。"
    elif "attributeerror" in error_lower:
        return "请检查PyLabRobot API调用，确保使用的方法和属性名称正确。参考官方文档获取正确的API用法。"
    elif "nameerror" in error_lower:
        return "请检查变量名称，确保所有使用的变量都已正确定义。特别检查资源获取语句。"
    elif "await" in error_lower and "coroutine" in error_lower:
        return "请确保所有PyLabRobot操作都使用了 await 关键字。所有 lh.* 操作都是异步的。"
    else:
        return "请参考PyLabRobot文档，检查协议代码的正确性。确保所有资源都已正确配置并且API调用符合规范。"

# ============================================================================
# Hardware Configuration Management
# ============================================================================

def create_default_hardware_config():
    """
    Create default hardware configuration file if it doesn't exist.
    """
    if not HARDWARE_PROFILES_DIR.exists():
        HARDWARE_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Debug - [create_default_hardware_config] Created hardware profiles directory")
    
    if not DEFAULT_HARDWARE_CONFIG.exists():
        try:
            with open(DEFAULT_HARDWARE_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_HARDWARE_SETUP, f, indent=2, ensure_ascii=False)
            print(f"Debug - [create_default_hardware_config] Created default hardware config at {DEFAULT_HARDWARE_CONFIG}")
        except Exception as e:
            print(f"Warning - [create_default_hardware_config] Failed to create default config: {e}")

def get_available_hardware_profiles() -> list:
    """
    Get list of available hardware profile files, excluding the default config.
    
    Returns:
        List of hardware profile file paths
    """
    if not HARDWARE_PROFILES_DIR.exists():
        return []
    
    # Exclude the default profile from the list presented to the user
    return [
        f for f in HARDWARE_PROFILES_DIR.glob("*.json") 
        if f.name != "pylabrobot_default.json"
    ]

# Initialize hardware configuration on module import
create_default_hardware_config()

async def test_pylabrobot_simulation():
    """Test function for the enhanced simulation utility."""
    test_code = '''
async def protocol(lh):
    print("Hello PyLabRobot Enhanced Simulation!")
    # Get pre-configured resources
    deck = lh.deck
    print(f"Working with deck: {deck.name}")
    print(f"Deck size: {deck.size_x} x {deck.size_y} x {deck.size_z}")
    print("--- PROTOCOL_SUCCESS ---")
'''
    
    print("Testing Enhanced PyLabRobot simulation utility...")
    result = await run_pylabrobot_simulation(test_code, return_structured=True)
    print(f"Structured result: {result}")
    
    result_str = await run_pylabrobot_simulation(test_code, return_structured=False)
    print(f"String result: {result_str}")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_pylabrobot_simulation()) 
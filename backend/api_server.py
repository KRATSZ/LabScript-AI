# -*- coding: utf-8 -*-
"""
FastAPI server for Opentrons AI Protocol Generator - Simplified Version

=== API 端点说明 ===

1. GET / 
   - 作用：健康检查，返回服务状态
   - 返回：服务名称、状态、时间戳

2. POST /api/generate-sop
   - 作用：根据硬件配置和用户目标生成标准操作程序(SOP)
   - 输入：hardware_config (硬件配置), user_goal (用户目标)
   - 返回：success, sop_markdown (生成的SOP), timestamp
   - 功能：使用LangChain生成详细的实验操作步骤

3. POST /api/generate-protocol-code  
   - 作用：根据SOP和硬件配置生成Opentrons Python协议代码
   - 输入：sop_markdown (SOP文档), hardware_config (硬件配置)
   - 返回：success, generated_code (生成的代码), attempts, warnings, iteration_logs, timestamp
   - 功能：AI自动编写可执行的Opentrons协议脚本

4. POST /api/simulate-protocol
   - 作用：模拟验证Opentrons协议代码
   - 输入：protocol_code (协议代码字符串)
   - 返回：success, raw_simulation_output, error_message, warnings_present, warning_details, final_status_message, timestamp
   - 功能：等同于opentrons_validator的simulate.py功能，验证代码正确性

5. GET /api/health
   - 作用：API服务健康检查
   - 返回：status, version, timestamp

6. GET /api/tools
   - 作用：列出可用的工具和功能
   - 返回：tools_available (工具列表)

7. POST /api/generate-sop-stream
   - 作用：流式生成SOP，实时返回生成过程
   - 输入：hardware_config, user_goal
   - 返回：Server-Sent Events流式数据
   - 功能：实时显示SOP生成进度

8. POST /api/export/protocols-io
   - 作用：生成协议的zip文件以供上传到protocols.io
   - 输入：user_goal (用户目标), hardware_config (硬件配置), sop_markdown (SOP文档), generated_code (生成的代码)
   - 返回：zip文件流
   - 功能：生成并返回一个zip文件，其中包含协议脚本和详细说明，以便于上传到protocols.io

=== 核心工作流程 ===
用户目标 → 生成SOP → 生成代码 → 模拟验证 → 完成协议
"""

import json
import traceback
import asyncio
import io
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Use absolute imports
from backend.langchain_agent import (
    generate_sop_with_langchain,
    run_code_generation_graph_stream,  # 流式代码生成函数
    generate_sop_with_langchain_stream,
    converse_about_sop,
    converse_about_code, # Keep the non-streaming version
    converse_about_code_stream, # Add the new streaming function
)
from backend.opentrons_utils import run_opentrons_simulation
from backend.pylabrobot_utils import run_pylabrobot_simulation
from backend.pylabrobot_agent import run_pylabrobot_agent_and_stream_events
from backend.file_exporter import ProtocolsIOExporter

# Request/Response models
class SOPGenerationRequest(BaseModel):
    hardware_config: str
    user_goal: str

class SOPGenerationResponse(BaseModel):
    success: bool
    sop_markdown: str
    timestamp: str

class ProtocolCodeGenerationRequest(BaseModel):
    sop_markdown: str
    hardware_config: str
    robot_model: Optional[str] = None  # Add explicit robot model field

class ProtocolCodeGenerationResponse(BaseModel):
    success: bool
    generated_code: str
    attempts: int
    warnings: List[str]
    iteration_logs: List[Dict[str, Any]]
    timestamp: str

class ProtocolSimulationRequest(BaseModel):
    protocol_code: str

class PyLabRobotSimulationRequest(BaseModel):
    protocol_code: str

class ProtocolSimulationResponse(BaseModel):
    success: bool
    raw_simulation_output: str
    error_message: Optional[str] = None
    warnings_present: bool = False
    warning_details: Optional[str] = None
    final_status_message: str
    timestamp: str

class ProtocolExportRequest(BaseModel):
    user_goal: str = Field(..., description="The original user goal for the experiment.")
    hardware_config: str = Field(..., description="The hardware configuration string.")
    sop_markdown: str = Field(..., description="The generated SOP in Markdown format.")
    generated_code: str = Field(..., description="The final, validated Python protocol code.")

class SopEditRequest(BaseModel):
    original_sop: str
    user_instruction: str
    hardware_context: str

class SopConverseResponse(BaseModel):
    success: bool
    type: str  # 'edit' or 'chat'
    modified_sop: Optional[str] = None
    chat_response: Optional[str] = None
    timestamp: str

class CodeEditRequest(BaseModel):
    original_code: str
    user_instruction: str

class CodeConverseResponse(BaseModel):
    type: str # "edit" or 'chat'
    content: str

# FastAPI app setup
app = FastAPI(
    title="Opentrons AI Protocol Generator API (Simplified)",
    description="Simplified API focusing on core functionalities for protocol generation and simulation.",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define dependencies
def get_sop_generator():
    return generate_sop_with_langchain

def get_protocol_simulator():
    return run_opentrons_simulation

@app.get("/")
async def root():
    """Health check endpoint for the API."""
    return {
        "message": "Opentrons AI Protocol Generator API (Simplified)",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/generate-sop", response_model=SOPGenerationResponse)
async def generate_sop(
    request: SOPGenerationRequest,
    sop_generator: callable = Depends(get_sop_generator)
):
    """Generates a Standard Operating Procedure (SOP) based on hardware configuration and user goal. Simplified version."""
    try:
        # Build input - hardware config is part of the prompt
        combined_input = f"{request.hardware_config}---{request.user_goal}"
        
        print(f"Debug - Starting SOP generation, input length: {len(combined_input)}")
        
        # Call local LangChain SOP generation
        sop_result = sop_generator(combined_input)
        
        if sop_result and sop_result.startswith("Error:"):
            raise HTTPException(status_code=500, detail=sop_result)
        
        return SOPGenerationResponse(
            success=True,
            sop_markdown=sop_result,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"SOP generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"SOP generation failed: {str(e)}"
        )

@app.post("/api/generate-protocol-code")
async def generate_protocol_code_stream(
    request: ProtocolCodeGenerationRequest
):
    """
    Generates protocol code using streaming SSE (Server-Sent Events).
    Returns real-time progress updates during the AI-powered code generation and iteration process.
    
    This endpoint now acts as a dispatcher based on robot type:
    - If hardware_config contains 'PyLabRobot': uses PyLabRobot Agent
    - Otherwise: uses Opentrons Agent (Flex/OT-2)
    """
    try:
        print(f"Debug - Starting streaming code generation")
        print(f"Debug - SOP length: {len(request.sop_markdown)}")
        print(f"Debug - Hardware config length: {len(request.hardware_config)}")
        
        # Dispatcher logic: check robot type from explicit robot_model field
        is_pylabrobot = request.robot_model == 'PyLabRobot'
        print(f"Debug - Robot model from request: {request.robot_model}")
        print(f"Debug - Detected robot type: {'PyLabRobot' if is_pylabrobot else 'Opentrons'}")

        async def event_stream():
            try:
                if is_pylabrobot:
                    # Use PyLabRobot Agent
                    print("Debug - Using PyLabRobot Agent for code generation")
                    
                    # Extract user query from SOP for PyLabRobot Agent
                    user_query = f"Generate PyLabRobot protocol based on SOP: {request.sop_markdown}"
                    
                    async for event_data in run_pylabrobot_agent_and_stream_events(
                        user_query=user_query, 
                        hardware_config_str=request.hardware_config, # Pass hardware config string
                        max_attempts=9
                    ):
                        # Format as SSE event
                        payload = json.dumps(event_data)
                        yield f"data: {payload}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to allow proper streaming
                else:
                    # Use existing Opentrons Agent
                    print("Debug - Using Opentrons Agent for code generation")
                    
                    # Combine SOP and hardware config into a single string for the agent
                    tool_input = f"{request.sop_markdown}\n---CONFIG_SEPARATOR---\n{request.hardware_config}"

                    async for event_data in run_code_generation_graph_stream(tool_input, max_iterations=9):
                        # Format as SSE event
                        payload = json.dumps(event_data)
                        yield f"data: {payload}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to allow proper streaming
                
                # Signal completion
                done_payload = json.dumps({"event_type": "stream_complete"})
                yield f"data: {done_payload}\n\n"

            except Exception as e:
                print(f"Error during code generation stream: {e}")
                import traceback
                error_traceback = traceback.format_exc()
                error_payload = json.dumps({
                    "event_type": "error", 
                    "message": f"代码生成流程中发生异常: {str(e)}",
                    "error_traceback": error_traceback,
                    "timestamp": datetime.now().isoformat()
                })
                yield f"data: {error_payload}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
        
    except Exception as e:
        print(f"Failed to start code generation stream: {e}")
        print(f"Error details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to initiate code generation stream",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/simulate-protocol", response_model=ProtocolSimulationResponse)
async def simulate_protocol(
    request: ProtocolSimulationRequest,
    simulator: callable = Depends(get_protocol_simulator)
):
    """Simulates the provided Opentrons protocol code."""
    try:
        simulation_result = simulator(request.protocol_code, return_structured=True)
        
        return ProtocolSimulationResponse(
            success=simulation_result.get("success", False),
            raw_simulation_output=simulation_result.get("raw_output", "No simulation output available."),
            error_message=simulation_result.get("error_details"),
            warnings_present=simulation_result.get("warnings_present", False),
            warning_details=simulation_result.get("warning_details"),
            final_status_message=simulation_result.get("final_status", "Simulation status unknown."),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        print(f"Simulation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during simulation: {str(e)}"
        )

@app.post("/api/simulate-pylabrobot-protocol", response_model=ProtocolSimulationResponse)
async def simulate_pylabrobot_protocol(
    request: PyLabRobotSimulationRequest
):
    """Simulates the provided PyLabRobot protocol code."""
    try:
        print(f"Debug - Starting PyLabRobot simulation")
        print(f"Debug - Protocol code length: {len(request.protocol_code)}")
        
        simulation_result = await run_pylabrobot_simulation(request.protocol_code, return_structured=True)
        
        return ProtocolSimulationResponse(
            success=simulation_result.get("success", False),
            raw_simulation_output=simulation_result.get("raw_output", "No PyLabRobot simulation output available."),
            error_message=simulation_result.get("error_details"),
            warnings_present=simulation_result.get("has_warnings", False),
            warning_details=simulation_result.get("warning_details"),
            final_status_message=simulation_result.get("final_status", "PyLabRobot simulation status unknown."),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        print(f"PyLabRobot simulation error: {e}")
        print(f"Error details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during PyLabRobot simulation: {str(e)}"
        )

@app.post(
    "/api/export/protocols-io",
    tags=["Export"],
    summary="Generate a Zip Archive for protocols.io",
    description="Takes protocol data and generates a downloadable zip file formatted for easy uploading to protocols.io.",
)
async def export_for_protocols_io(request: ProtocolExportRequest):
    """
    Generates a zip archive containing:
    - `protocol_script.py`: The Python protocol code.
    - `protocol_details.md`: A markdown file with instructions and formatted text for easy copy-pasting into the protocols.io web interface.
    """
    try:
        exporter = ProtocolsIOExporter()
        zip_bytes = exporter.create_export_zip(
            user_goal=request.user_goal,
            hardware_config=request.hardware_config,
            sop_markdown=request.sop_markdown,
            generated_code=request.generated_code,
        )
        
        headers = {
            'Content-Disposition': 'attachment; filename="protocols_io_export.zip"'
        }
        
        return StreamingResponse(io.BytesIO(zip_bytes), media_type="application/zip", headers=headers)
    except Exception as e:
        print(f"Export error: {e}")
        print(f"Error details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate export file: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Returns basic health check information for the API."""
    try:
        return {
            "status": "healthy",
            "version": "2.0.0 (Simplified)",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # This should ideally not happen for a simple health check
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/api/tools")
async def list_tools():
    """Lists available tools or configurations (example)."""
    # This is a placeholder. In a real scenario, you might list
    # available LangChain tools, Dify workflows, or other resources.
    return {
        "tools_available": [
            {"name": "Local SOP Generation (LangChain)", "description": "Generates detailed SOPs from hardware config and user goal using local LangChain."},
            {"name": "Protocol Code Generation Agent (LangChain)", "description": "Generates Python protocol code from SOP and hardware config, with iteration."},
            {"name": "Opentrons Protocol Simulator", "description": "Simulates Opentrons Python protocols."}
        ],
        "status": "ok"
    }

# PyLabRobot profile models
class PyLabRobotProfile(BaseModel):
    id: str
    robot_model: str
    display_name: str
    manufacturer: str
    description: str
    precision_class: str
    volume_range: Dict[str, float]
    special_features: List[str]
    recommended_for: List[str]
    default_config: Dict[str, Any]  # New field for the full config

class PyLabRobotProfilesResponse(BaseModel):
    success: bool
    profiles: List[PyLabRobotProfile]
    timestamp: str

@app.get("/api/pylabrobot/profiles", response_model=PyLabRobotProfilesResponse)
async def get_pylabrobot_profiles():
    """
    Get all available PyLabRobot hardware configuration profiles.
    
    Returns:
        PyLabRobotProfilesResponse: List of available robot configurations
    """
    try:
        import os
        import json
        from pathlib import Path
        
        profiles = []
        profiles_dir = Path(__file__).parent / "hardware_profiles"
        
        if profiles_dir.exists():
            # Scan for PyLabRobot configuration files
            for config_file in profiles_dir.glob("pylabrobot_*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Extract profile information
                    robot_model = config_data.get("robot_model", "unknown")
                    
                    # Create display name from robot model
                    display_name = robot_model.replace("_", " ").title()
                    if display_name == "Generic":
                        display_name = "Generic PyLabRobot"
                    elif display_name == "Hamilton Star":
                        display_name = "Hamilton STAR"
                    elif display_name == "Hamilton Vantage":
                        display_name = "Hamilton Vantage"
                    elif display_name == "Tecan Evo":
                        display_name = "Tecan Freedom EVO"
                    elif display_name == "Opentrons":
                        display_name = "Opentrons OT-2"
                    
                    profile = PyLabRobotProfile(
                        id=config_file.stem,
                        robot_model=robot_model,
                        display_name=display_name,
                        manufacturer=config_data.get("manufacturer", "Unknown"),
                        description=config_data.get("description", ""),
                        precision_class=config_data.get("precision_class", "standard"),
                        volume_range=config_data.get("volume_range", {"min_ul": 1, "max_ul": 1000}),
                        special_features=config_data.get("special_features", []),
                        recommended_for=config_data.get("recommended_for", []),
                        default_config=config_data  # Pass the entire config object
                    )
                    profiles.append(profile)
                    
                except Exception as e:
                    print(f"Warning: Failed to load PyLabRobot profile {config_file}: {e}")
                    continue
        
        # Sort profiles by display name for consistent ordering
        profiles.sort(key=lambda x: x.display_name)
        
        return PyLabRobotProfilesResponse(
            success=True,
            profiles=profiles,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error loading PyLabRobot profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load PyLabRobot profiles: {str(e)}")

# Streaming Endpoints - Keep SOP streaming functionality

async def generate_sop_stream(request: SOPGenerationRequest) -> AsyncGenerator[str, None]:
    """Stream SOP generation process using Server-Sent Events"""
    try:
        # Build input - hardware config is part of the prompt
        combined_input = f"{request.hardware_config}---{request.user_goal}"
        
        print(f"Debug - Starting streaming SOP generation, input length: {len(combined_input)}")
        
        # Prepare inputs for streaming SOP generation
        if "---" in combined_input:
            parts = combined_input.split("---", 1)
            hardware_context = parts[0].strip()
            user_goal = parts[1].strip()
        else:
            hardware_context = "No specific hardware configuration provided."
            user_goal = combined_input.strip()
        
        print(f"Debug - Hardware context: {hardware_context}")
        print(f"Debug - User goal: {user_goal}")
        
        # Send start signal
        start_data = {"type": "start", "message": "Starting real-time SOP generation..."}
        yield f"data: {json.dumps(start_data)}\n\n"
        
        # Import the streaming function
        from backend.langchain_agent import generate_sop_with_langchain_stream
        
        # Use real-time streaming generation
        token_count = 0
        try:
            async for token in generate_sop_with_langchain_stream(hardware_context, user_goal):
                if token:
                    token_count += 1
                    # Send each token immediately as it's generated
                    token_data = {"type": "content", "token": token}
                    yield f"data: {json.dumps(token_data)}\n\n"
                    
                    # Add a small delay to pace the stream for the frontend
                    await asyncio.sleep(0.01)
            
            print(f"Debug - API: 流式传输完成，总共发送了 {token_count} 个token")
        
        except Exception as stream_error:
            print(f"Error - API: 流式生成过程中发生错误: {stream_error}")
            error_data = {"type": "error", "message": f"Real-time SOP generation failed: {str(stream_error)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
            return
        
        # Send completion signal
        completion_data = {"type": "complete", "message": "SOP generation completed"}
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        print(f"Streaming SOP generation error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        error_data = {"type": "error", "message": f"SOP generation failed: {str(e)}"}
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/api/generate-sop-stream")
async def stream_sop_generation(request: SOPGenerationRequest):
    """Generates an SOP via a real-time stream."""
    try:
        # We need a wrapper async function to bridge our sync langchain call to fastapi's async world
        async def event_stream():
            try:
                # The generator is an async generator
                async for chunk in generate_sop_with_langchain_stream(request.hardware_config, request.user_goal):
                    if "STREAM_ERROR:" in chunk:
                        # Handle errors propagated from the stream
                        error_payload = json.dumps({"event": "error", "message": chunk})
                        yield f"data: {error_payload}\n\n"
                        return
                    
                    payload = json.dumps({"token": chunk})
                    yield f"data: {payload}\n\n"
                    await asyncio.sleep(0.01) # Small sleep to allow for message sending
                
                # Signal completion
                done_payload = json.dumps({"event": "done"})
                yield f"data: {done_payload}\n\n"

            except Exception as e:
                print(f"Error during SOP stream: {e}")
                error_payload = json.dumps({"event": "error", "message": f"An unexpected error occurred in the stream: {str(e)}"})
                yield f"data: {error_payload}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        print(f"Failed to start SOP stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate SOP stream: {str(e)}")


# ==== SOP Conversational Edit Endpoints ====

class SopEditRequest(BaseModel):
    original_sop: str
    user_instruction: str
    hardware_context: str

class SopConverseResponse(BaseModel):
    type: str # "edit" or "chat"
    content: str

@app.post("/api/converse-sop", response_model=SopConverseResponse)
async def converse_sop(request: SopEditRequest):
    """
    Handles a conversation about the SOP, which can be an edit instruction or a general chat question.
    """
    try:
        from backend.langchain_agent import converse_about_sop
        result = converse_about_sop(
            original_sop=request.original_sop,
            user_instruction=request.user_instruction,
            hardware_context=request.hardware_context
        )
        return result
    except Exception as e:
        print(f"Error during SOP conversation: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")


# ==== Code Conversational Edit Endpoints ====

class CodeEditRequest(BaseModel):
    original_code: str
    user_instruction: str

class CodeConverseResponse(BaseModel):
    type: str # "edit" or "chat"
    content: str

@app.post("/api/converse-code-stream")
async def converse_code_stream_endpoint(request: CodeEditRequest):
    """
    Handles conversational interactions about code via a real-time stream.
    Yields events for agent thoughts, tool calls, and final results.
    """
    async def event_stream():
        try:
            async for event in converse_about_code_stream(request.original_code, request.user_instruction):
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.01) # Small delay to allow proper streaming
            
            done_payload = json.dumps({"event_type": "stream_complete"})
            yield f"data: {done_payload}\n\n"
        except Exception as e:
            print(f"Error during code conversation stream: {traceback.format_exc()}")
            error_payload = json.dumps({
                "event_type": "error",
                "message": f"An unexpected error occurred in the stream: {str(e)}"
            })
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/converse-code", response_model=CodeConverseResponse)
async def converse_code_endpoint(request: CodeEditRequest):
    """
    Handles conversational interactions about the code.
    Can either be an edit instruction or a general chat question.
    """
    try:
        from backend.langchain_agent import converse_about_code
        result = converse_about_code(
            original_code=request.original_code,
            user_instruction=request.user_instruction
        )
        return result
    except Exception as e:
        print(f"Error during code conversation: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")
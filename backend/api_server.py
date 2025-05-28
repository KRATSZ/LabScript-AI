# -*- coding: utf-8 -*-
"""FastAPI server for Opentrons AI Protocol Generator - Simplified Version"""

import json
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our modules
from langchain_agent import (
    call_dify_sop_workflow,
    run_automated_protocol_generation_with_iteration
)
from opentrons_utils import run_opentrons_simulation

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

class ProtocolCodeGenerationResponse(BaseModel):
    success: bool
    generated_code: str
    attempts: int
    warnings: List[str]
    iteration_logs: List[Dict[str, Any]]
    timestamp: str

class ProtocolSimulationRequest(BaseModel):
    protocol_code: str

class ProtocolSimulationResponse(BaseModel):
    success: bool
    raw_simulation_output: str
    error_message: Optional[str] = None
    warnings_present: bool = False
    warning_details: Optional[str] = None
    final_status_message: str
    timestamp: str

# Simple progress tracker
class SimpleProgressTracker:
    def __init__(self):
        self.logs = []
        self.current_attempt = 0
        self.generated_codes = []
        self.warnings = []
    
    def __call__(self, event_data: Dict[str, Any]):
        """Simple event collector for tracking progress."""
        self.logs.append(event_data)
        
        if event_data.get("event_type") == "iteration_log":
            self.current_attempt = event_data.get("attempt_num", 0)
        elif event_data.get("event_type") == "code_attempt":
            code = event_data.get("generated_code", "")
            if code:
                self.generated_codes.append({
                    "attempt": event_data.get("attempt_num", 0),
                    "code": code
                })
        elif event_data.get("event_type") == "iteration_result":
            if "WARNING" in event_data.get("status", ""):
                warning_details = event_data.get("warning_details", "")
                if warning_details:
                    self.warnings.append(warning_details)

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

@app.get("/")
async def root():
    """Health check endpoint for the API."""
    return {
        "message": "Opentrons AI Protocol Generator API (Simplified)",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/generate-sop", response_model=SOPGenerationResponse)
async def generate_sop(request: SOPGenerationRequest):
    """Generates a Standard Operating Procedure (SOP) based on hardware configuration and user goal. Simplified version."""
    try:
        # Build input - hardware config is part of the prompt
        combined_input = f"{request.hardware_config}---{request.user_goal}"
        
        print(f"Debug - Starting SOP generation, input length: {len(combined_input)}")
        
        # Call Dify SOP workflow
        sop_result = call_dify_sop_workflow(combined_input)
        
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

@app.post("/api/generate-protocol-code", response_model=ProtocolCodeGenerationResponse)
async def generate_protocol_code(request: ProtocolCodeGenerationRequest):
    """
    Generates protocol code - Simplified version, returns the final result synchronously.
    Removes complex SSE streaming, directly returns the final code.
    """
    try:
        print(f"Debug - Starting code generation")
        print(f"Debug - SOP length: {len(request.sop_markdown)}")
        print(f"Debug - Hardware config length: {len(request.hardware_config)}")
        
        # Create simple progress tracker
        progress_tracker = SimpleProgressTracker()
        
        # Prepare tool input
        tool_input = f"{request.sop_markdown}\\n---CONFIG_SEPARATOR---\\n{request.hardware_config}"
        
        # Directly call protocol generation tool (synchronous)
        result = run_automated_protocol_generation_with_iteration(
            tool_input,
            progress_tracker  # Use simple progress tracker
        )
        
        print(f"Debug - Code generation complete, result type: {type(result)}")
        print(f"Debug - Total attempts: {progress_tracker.current_attempt}")
        
        # Check result
        if result.startswith("Error:"):
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Code generation failed",
                    "details": result,
                    "attempts": progress_tracker.current_attempt,
                    "logs": progress_tracker.logs[-5:]  # Return last 5 logs
                }
            )
        
        # Extract final code
        final_code = result
        
        # If result contains warning markers, extract pure code
        if "Warning:" in result and "```python" in result:
            import re
            code_match = re.search(r"```python\\n([\\s\\S]*?)\\n```", result)
            if code_match:
                final_code = code_match.group(1)
        
        print(f"Debug - [api_server.py] Preparing to send successful response to frontend. Attempts: {progress_tracker.current_attempt}, Warnings: {len(progress_tracker.warnings)}")
        return ProtocolCodeGenerationResponse(
            success=True,
            generated_code=final_code,
            attempts=progress_tracker.current_attempt,
            warnings=progress_tracker.warnings,
            iteration_logs=progress_tracker.logs,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        print(f"Code generation error: {e}")
        print(f"Error details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Code generation failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/simulate-protocol", response_model=ProtocolSimulationResponse)
async def simulate_protocol(request: ProtocolSimulationRequest):
    """Simulates the provided Opentrons protocol code."""
    try:
        simulation_result_dict = run_opentrons_simulation(
            request.protocol_code, 
            return_structured=True
        )
        
        return ProtocolSimulationResponse(
            success=simulation_result_dict.get("success", False),
            raw_simulation_output=simulation_result_dict.get("raw_output", "No simulation output available."),
            error_message=simulation_result_dict.get("error_details"),
            warnings_present=simulation_result_dict.get("has_warnings", False),
            warning_details=simulation_result_dict.get("cleaned_stderr") if simulation_result_dict.get("has_warnings") else None,
            final_status_message=simulation_result_dict.get("final_status", "Status unknown"),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        print(f"Error during protocol simulation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "SimulationFailedError",
                "message": f"Protocol simulation failed: {str(e)}",
                "details": traceback.format_exc()
            }
        )

@app.get("/api/health")
async def health_check():
    """Health check for API services."""
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
            {"name": "SOP Generation Workflow (Dify)", "description": "Generates SOP from hardware config and user goal."},
            {"name": "Protocol Code Generation Agent (LangChain)", "description": "Generates Python protocol code from SOP and hardware config, with iteration."},
            {"name": "Opentrons Protocol Simulator", "description": "Simulates Opentrons Python protocols."}
        ],
        "status": "ok"
    }

if __name__ == "__main__":
    import uvicorn
    # Note: When running directly, reload is often useful for development
    # uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
    # For production or when reload is handled by main.py:
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 
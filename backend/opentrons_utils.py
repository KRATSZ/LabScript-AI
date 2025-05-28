# -*- coding: utf-8 -*-
"""Utility functions for Opentrons protocol simulation and management."""

import subprocess
import tempfile
import os
import re
from typing import Dict, Any, Union

class SimulateToolInput:
    """Input class for simulation tool"""
    def __init__(self, protocol_code: str):
        self.protocol_code = protocol_code

def run_opentrons_simulation(protocol_code: str, return_structured: bool = False) -> Union[str, Dict[str, Any]]:
    """
    Run Opentrons protocol simulation using opentrons_simulate command.
    
    Args:
        protocol_code: Python protocol code to simulate
        return_structured: If True, return structured dict; if False, return formatted string
    
    Returns:
        Union[str, Dict[str, Any]]: Simulation results
    """
    try:
        # Create temporary file for the protocol
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(protocol_code)
            temp_file_path = temp_file.name
        
        try:
            # Run opentrons_simulate command
            result = subprocess.run(
                ['opentrons_simulate', temp_file_path, '--log-level', 'DEBUG'],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # Process results
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            return_code = result.returncode
            
            # Determine success
            success = return_code == 0 and not any(error_keyword in stderr.lower() 
                                                  for error_keyword in ['error', 'exception', 'failed'])
            
            # Clean stderr for better readability
            cleaned_stderr = clean_stderr_output(stderr)
            
            # Check for warnings
            has_warnings = bool(cleaned_stderr and 
                              any(warning_keyword in cleaned_stderr.lower() 
                                  for warning_keyword in ['warning', 'caution']))
            
            # Combine output
            combined_output = f"--- STDOUT ---\n{stdout}\n--- STDERR ---\n{stderr}"
            if cleaned_stderr:
                combined_output += f"\n--- Cleaned STDERR ---\n{cleaned_stderr}"
            
            # Determine final status
            if success:
                if has_warnings:
                    final_status = "Simulation completed with warnings"
                else:
                    final_status = "Simulation completed successfully"
            else:
                final_status = "Simulation failed with errors"
            
            if return_structured:
                return {
                    "success": success,
                    "raw_output": combined_output,
                    "stdout": stdout,
                    "stderr": stderr,
                    "cleaned_stderr": cleaned_stderr,
                    "return_code": return_code,
                    "has_warnings": has_warnings,
                    "final_status": final_status,
                    "error_details": cleaned_stderr if not success else None
                }
            else:
                # Return formatted string for backwards compatibility
                status_emoji = "✅" if success else "❌"
                warning_text = " (with warnings)" if has_warnings else ""
                
                formatted_output = f"{status_emoji} {final_status}{warning_text}\n\n"
                formatted_output += f"Return Code: {return_code}\n\n"
                formatted_output += combined_output
                
                return formatted_output
                
        except subprocess.TimeoutExpired:
            os.unlink(temp_file_path)  # Clean up
            error_msg = "Simulation timed out after 60 seconds"
            
            if return_structured:
                return {
                    "success": False,
                    "raw_output": error_msg,
                    "stdout": "",
                    "stderr": error_msg,
                    "cleaned_stderr": error_msg,
                    "return_code": -1,
                    "has_warnings": False,
                    "final_status": "Simulation timed out",
                    "error_details": error_msg
                }
            else:
                return f"❌ {error_msg}"
                
        except FileNotFoundError:
            error_msg = "opentrons_simulate command not found. Please ensure Opentrons API is installed."
            
            if return_structured:
                return {
                    "success": False,
                    "raw_output": error_msg,
                    "stdout": "",
                    "stderr": error_msg,
                    "cleaned_stderr": error_msg,
                    "return_code": -1,
                    "has_warnings": False,
                    "final_status": "Command not found",
                    "error_details": error_msg
                }
            else:
                return f"❌ {error_msg}"
    
    except Exception as e:
        error_msg = f"Unexpected error during simulation: {str(e)}"
        
        if return_structured:
            return {
                "success": False,
                "raw_output": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "cleaned_stderr": error_msg,
                "return_code": -1,
                "has_warnings": False,
                "final_status": "Unexpected error",
                "error_details": error_msg
            }
        else:
            return f"❌ {error_msg}"

def clean_stderr_output(stderr: str) -> str:
    """
    Clean and filter stderr output to show only relevant information.
    
    Args:
        stderr: Raw stderr output from simulation
    
    Returns:
        str: Cleaned stderr output
    """
    if not stderr:
        return ""
    
    lines = stderr.split('\n')
    cleaned_lines = []
    
    # Filter out common noise patterns
    noise_patterns = [
        r'^DEBUG:',
        r'^INFO:',
        r'UserWarning: Protocol .* has no run function',
        r'warnings.warn',
        r'stacklevel=2',
        r'^\s*$',  # Empty lines
    ]
    
    for line in lines:
        # Skip lines that match noise patterns
        if any(re.match(pattern, line, re.IGNORECASE) for pattern in noise_patterns):
            continue
        
        # Keep lines that contain important information
        if any(keyword in line.lower() for keyword in 
               ['error', 'exception', 'warning', 'failed', 'invalid', 'not found']):
            cleaned_lines.append(line.strip())
        elif line.strip() and not line.startswith(' '):
            # Keep non-indented non-empty lines that might be important
            cleaned_lines.append(line.strip())
    
    return '\n'.join(cleaned_lines) if cleaned_lines else ""

def validate_protocol_syntax(protocol_code: str) -> Dict[str, Any]:
    """
    Validate protocol syntax without running simulation.
    
    Args:
        protocol_code: Python protocol code to validate
    
    Returns:
        Dict containing validation results
    """
    try:
        # Basic Python syntax check
        compile(protocol_code, '<protocol>', 'exec')
        
        # Check for required Opentrons imports and functions
        required_patterns = [
            r'from opentrons import protocol_api',
            r'def run\(protocol:.*protocol_api\.ProtocolContext\)',
        ]
        
        missing_patterns = []
        for pattern in required_patterns:
            if not re.search(pattern, protocol_code, re.MULTILINE):
                missing_patterns.append(pattern)
        
        if missing_patterns:
            return {
                "valid": False,
                "errors": [f"Missing required pattern: {pattern}" for pattern in missing_patterns]
            }
        
        return {
            "valid": True,
            "errors": []
        }
        
    except SyntaxError as e:
        return {
            "valid": False,
            "errors": [f"Python syntax error: {str(e)}"]
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }

def extract_protocol_metadata(protocol_code: str) -> Dict[str, Any]:
    """
    Extract metadata and requirements from protocol code.
    
    Args:
        protocol_code: Python protocol code
    
    Returns:
        Dict containing extracted metadata
    """
    metadata = {}
    
    # Extract metadata dict
    metadata_match = re.search(r'metadata\s*=\s*({.*?})', protocol_code, re.DOTALL)
    if metadata_match:
        try:
            metadata.update(eval(metadata_match.group(1)))
        except:
            pass
    
    # Extract requirements dict
    requirements_match = re.search(r'requirements\s*=\s*({.*?})', protocol_code, re.DOTALL)
    if requirements_match:
        try:
            requirements = eval(requirements_match.group(1))
            metadata.update(requirements)
        except:
            pass
    
    return metadata
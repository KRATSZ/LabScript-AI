# -*- coding: utf-8 -*-
"""Opentrons utility functions, primarily for simulation."""
import os
import subprocess
import tempfile
import sys
import re
import traceback
import json
from pydantic import BaseModel, Field # For SimulateToolInput

class SimulateToolInput(BaseModel):
    """Input schema for the Opentrons simulation tool."""
    protocol_code: str = Field(description="The complete, raw Python code string for the Opentrons protocol (API v2 or later). Ensure it includes imports (e.g., 'from opentrons import protocol_api'), metadata/requirements (e.g., apiLevel), and a 'run(protocol: protocol_api.ProtocolContext)' function. DO NOT include markdown formatting like ```python.")

def run_opentrons_simulation(protocol_code: str) -> str:
    """Runs the Opentrons simulation for the given Python protocol code."""
    simulate_command = 'opentrons_simulate'
    # This variable will store the command used, whether from PATH or a found path.
    effective_simulate_command = None
    # Store paths searched for better error reporting, initialized here
    searched_paths_for_error_msg = []


    # Attempt to run from PATH first
    try:
        print(f"INFO: Attempting to run '{simulate_command}' from system PATH...")
        # Use a simple command like --version to check existence and executability
        subprocess.run(f'{simulate_command} --version', check=True, capture_output=True, text=True, errors='ignore', shell=True)
        effective_simulate_command = simulate_command # Command is in PATH
        print(f"INFO: Successfully found and verified '{simulate_command}' in system PATH.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"INFO: '{simulate_command}' not found in PATH or initial version check failed. Searching common Python binary locations...")
        # If not in PATH, search common Python bin directories
        try:
            python_executable_path = sys.executable
            # Common paths relative to Python executable or environment
            # sys.prefix is often the root of the venv or Python installation
            # os.path.dirname(sys.executable) is the directory containing the python interpreter
            base_paths_to_check = [
                os.path.dirname(python_executable_path),
                os.path.join(sys.prefix, 'bin'),
                # For Windows, scripts might be in 'Scripts' not 'bin'
                os.path.join(sys.prefix, 'Scripts') if os.name == 'nt' else None,
                '/usr/local/bin', # Common system-wide location for user-installed executables
                os.path.expanduser('~/.local/bin') # User-specific local bin for pip --user installs
            ]
            # Filter out None paths (like the Windows-specific one on non-Windows)
            base_paths_to_check = [p for p in base_paths_to_check if p]

            # Add site-packages related bin paths (more robustly)
            # This attempts to find bin/Scripts folders relative to site-packages directories
            for path_entry in sys.path: # sys.path includes site-packages
                 if 'site-packages' in path_entry and os.path.isdir(path_entry):
                     # Check .../site-packages/../../bin (typical for venvs like <venv>/lib/pythonX.Y/site-packages)
                     potential_venv_bin = os.path.abspath(os.path.join(path_entry, '..', '..', 'bin'))
                     if os.path.isdir(potential_venv_bin):
                         base_paths_to_check.append(potential_venv_bin)
                     # For Windows, check .../site-packages/../../Scripts
                     if os.name == 'nt':
                         potential_venv_scripts = os.path.abspath(os.path.join(path_entry, '..', '..', 'Scripts'))
                         if os.path.isdir(potential_venv_scripts):
                             base_paths_to_check.append(potential_venv_scripts)
                     # Some tools might install directly into a 'bin' under site-packages, though less common
                     potential_site_packages_bin = os.path.join(path_entry, 'bin')
                     if os.path.isdir(potential_site_packages_bin):
                        base_paths_to_check.append(potential_site_packages_bin)


            # Deduplicate, ensure paths are absolute, and filter only existing directories
            # This list is primarily for the error message if not found
            searched_paths_for_error_msg = sorted(list(set(os.path.abspath(p) for p in base_paths_to_check if p and os.path.isdir(p))))
            print(f"INFO: Potential directories being actively searched for 'opentrons_simulate': {searched_paths_for_error_msg}")

            found_path = None
            for path_dir in searched_paths_for_error_msg: # Iterate over confirmed existing directories
                potential_path = os.path.join(path_dir, 'opentrons_simulate')
                # On Windows, executables might have .exe
                potential_path_exe = f"{potential_path}.exe" if os.name == 'nt' else None

                if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
                    found_path = potential_path
                    break
                elif potential_path_exe and os.path.exists(potential_path_exe) and os.access(potential_path_exe, os.X_OK):
                    found_path = potential_path_exe
                    break
            
            if not found_path:
                 error_msg = (f"Error: 'opentrons_simulate' command not found in system PATH or the following searched directories:\n"
                              f"{json.dumps(searched_paths_for_error_msg, indent=2)}\n"
                              f"Please ensure the Opentrons software (including the Opentrons App or opentrons-cli) is correctly installed and that "
                              f"'opentrons_simulate' is available in your system's PATH or one of the standard Python script directories. "
                              f"If you installed with pip, it might be in a user-specific bin or virtual environment bin not currently in PATH.")
                 print(error_msg)
                 return error_msg

            # Verify the found executable by running --version
            subprocess.run([found_path, '--version'], check=True, capture_output=True, text=True, errors='ignore')
            effective_simulate_command = found_path # Use the full path to the found executable
            print(f"INFO: Using 'opentrons_simulate' found at: {effective_simulate_command}")

        except (subprocess.CalledProcessError, FileNotFoundError) as e_search:
             error_msg = (f"Error: 'opentrons_simulate' command search failed or the found executable is not working.\n"
                          f"Underlying Error during search/verification: {e_search}\n"
                          f"Searched directories list (may not be exhaustive if error was early): {json.dumps(searched_paths_for_error_msg, indent=2)}\n"
                          f"Please ensure Opentrons software is correctly installed and 'opentrons_simulate' is functional.")
             print(error_msg)
             return error_msg
        except Exception as e_unexpected_search: # Catch any other unexpected error during search
            error_msg = (f"Unexpected Error: An unexpected issue occurred while searching for 'opentrons_simulate'.\n"
                         f"Error details: {e_unexpected_search}\n"
                         f"Searched directories list (may not be exhaustive): {json.dumps(searched_paths_for_error_msg, indent=2)}\n"
                         f"Please check your Python environment and Opentrons installation.")
            print(error_msg)
            return error_msg


    temp_file_path = None
    result_text = f"--- Running Simulation with command: '{effective_simulate_command}' ---\n--- Protocol Code: ---\n{protocol_code}\n---\n"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(protocol_code)
            temp_file_path = temp_file.name

        cmd = [effective_simulate_command, temp_file_path]
        
        print(f"INFO: Executing simulation command list: {cmd}")
        
        # 为Windows系统设置控制台代码页
        if os.name == 'nt':
            try:
                subprocess.run("chcp 65001", shell=True, check=False, capture_output=True)
                print("INFO: Setting Windows console to UTF-8 code page (65001)")
            except Exception as e:
                print(f"WARNING: Could not set Windows console code page: {e}")
        
        # Create a copy of the current environment and update it
        process_env = os.environ.copy()
        process_env["PYTHONIOENCODING"] = "utf-8"
        process_env["PYTHONUTF8"] = "1" # Add PYTHONUTF8=1 for Python 3.7+ for broader UTF-8 mode
        
        # 添加Windows特定的环境变量
        if os.name == 'nt':
            process_env["PYTHONLEGACYWINDOWSSTDIO"] = "0" # 禁用旧版Windows stdio
            process_env["PYTHONIOENCODING"] = "utf-8:backslashreplace" # Windows下使用更安全的替换策略

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=False, # Set text=False to handle decoding manually
            check=False, 
            # errors='ignore' is not used when text=False; decoding errors handled below
            shell=False,
            env=process_env # Pass the modified environment
        )

        # 解码时使用适合Windows的错误处理策略
        decode_errors = 'backslashreplace' if os.name == 'nt' else 'replace'
        
        # Decode stdout and stderr explicitly with utf-8, replacing errors
        stdout = process.stdout.decode('utf-8', errors=decode_errors).strip() if process.stdout else ""
        stderr = process.stderr.decode('utf-8', errors=decode_errors).strip() if process.stderr else ""

        result_text += f"--- Simulation STDOUT: ---\n{stdout}\n---\n"
        result_text += f"--- Simulation STDERR: ---\n{stderr}\n---\n"

        common_warnings = [
            "robot_settings.json not found", "deck_calibration.json not found",
            "pipette_calibration.json not found", "tip_length_calibrations.json not found",
            "Belt calibration not found", "Gantry calibration not found",
            "Deck calibration not found", "Calibration data not found",
            "Defaulting to global settings", "Failed to initialize USB", "Failed to connect to /dev/ttyAMA0",
            "Smoothie stats not available", "No valid configuration for USB-connected GEN2 pipette",
            "falling back to default values", "Please calibrate your deck.",
            "This robot has not been calibrated", "Deck calibration is not valid",
            "Failed to find any valid hardware modules", 
            "Failed to find smoothie board", 
            "Deck calibration file" 
        ]
        critical_error_patterns = [
            "Error", "Traceback", "Exception", "Failed to execute", "Cannot import name", "SyntaxError",
            "NameError", "AttributeError", "TypeError", "ValueError", "IndexError", "KeyError",
            "FileNotFoundError", 
            "LabwareLoadError", "PipetteMountError", "ModuleLoadError", "RobotNotSupportedError",
            "ProtocolAnalysisError", "opentrons.protocols.types.LocationError",
            "Cannot perform operation: missing tip"
        ]

        cleaned_stderr_lines = []
        if stderr:
            for line in stderr.splitlines():
                if not any(warning.lower() in line.lower() for warning in common_warnings):
                    cleaned_stderr_lines.append(line)
        cleaned_stderr = "\n".join(cleaned_stderr_lines).strip()

        has_critical_error_in_cleaned_stderr = any(pattern.lower() in cleaned_stderr.lower() for pattern in critical_error_patterns)
        
        has_critical_error_in_stdout = "protocol analysis failed" in stdout.lower() or \
                                       "error loading labware" in stdout.lower() or \
                                       "failed to simulate" in stdout.lower()

        if process.returncode != 0 or has_critical_error_in_cleaned_stderr or has_critical_error_in_stdout:
             result_text += f"--- Result: Simulation FAILED (Exit code: {process.returncode}. Critical errors detected.) ---\n"
             print(f"INFO: Simulation FAILED. Exit Code: {process.returncode}. Critical Cleaned STDERR: {has_critical_error_in_cleaned_stderr}. Critical STDOUT: {has_critical_error_in_stdout}")
             if cleaned_stderr: print(f"DEBUG: Cleaned STDERR (relevant parts):\n{cleaned_stderr}\n")
        else:
             success_patterns_stdout = ["protocol complete", "run() finish", "done simulating", "protocol analysis completed successfully"]
             has_success_msg_in_stdout = any(pattern in stdout.lower() for pattern in success_patterns_stdout)

             if has_success_msg_in_stdout and not cleaned_stderr:
                 result_text += "--- Result: Simulation SUCCEEDED ---\n"
                 print("INFO: Simulation SUCCEEDED (explicit success message in STDOUT, no critical errors in STDERR).")
             elif has_success_msg_in_stdout and cleaned_stderr: 
                 result_text += "--- Result: Simulation SUCCEEDED WITH UNEXPECTED STDERR (Review STDERR carefully) ---\n"
                 print("INFO: Simulation SUCCEEDED (explicit success message in STDOUT), but STDERR contains unexpected messages that were not filtered as common warnings. Please review.")
                 print(f"DEBUG: Cleaned STDERR (unexpected parts to review):\n{cleaned_stderr}\n")
             elif not cleaned_stderr: 
                 result_text += "--- Result: Simulation likely SUCCEEDED (No critical errors in STDERR, no explicit STDOUT success message) ---\n"
                 print("INFO: Simulation likely SUCCEEDED (no critical errors in STDERR, though no explicit success message in STDOUT. This can be normal for some valid protocols).")
             else: 
                 result_text += "--- Result: Simulation COMPLETED WITH UNEXPECTED STDERR (Review STDERR for potential issues, no explicit STDOUT success message) ---\n"
                 print("INFO: Simulation COMPLETED, but STDERR contains unexpected messages. No explicit success message in STDOUT. Please review carefully.")
                 print(f"DEBUG: Cleaned STDERR (unexpected parts to review):\n{cleaned_stderr}\n")
    
    except subprocess.CalledProcessError as e_subproc: 
        result_text += f"--- Simulation Subprocess Error: {e_subproc} ---\n"
        result_text += f"Traceback:\n{traceback.format_exc()}\n"
        result_text += "--- Result: Simulation FAILED (Subprocess execution error) ---\n"
        print(f"ERROR: Subprocess execution error for simulation: {e_subproc}. STDOUT:\n{e_subproc.stdout}\nSTDERR:\n{e_subproc.stderr}")
    except FileNotFoundError as e_fnf: 
        result_text += f"--- Simulation FileNotFoundError: {e_fnf} ---\n"
        result_text += f"Traceback:\n{traceback.format_exc()}\n"
        result_text += f"--- Result: Simulation FAILED (Simulate command '{effective_simulate_command}' not found at execution time) ---\n"
        print(f"ERROR: Simulate command '{effective_simulate_command}' not found when attempting to execute: {e_fnf}")
    except Exception as e_sim_general:
        result_text += f"--- Simulation General Python Error: {e_sim_general} ---\n"
        result_text += f"Traceback:\n{traceback.format_exc()}\n"
        result_text += "--- Result: Simulation FAILED (Python exception during simulation wrapper execution) ---\n"
        print(f"ERROR: General Python exception during simulation wrapper execution: {e_sim_general}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"INFO: Removed temporary protocol file: {temp_file_path}")
            except OSError as e_remove_temp:
                print(f"Warning: Could not remove temporary protocol file {temp_file_path}: {e_remove_temp}")

    max_output_length = 5000 
    if len(result_text) > max_output_length:
        start_kept = 1500
        end_kept = max_output_length - start_kept - len("\n... [Simulation output truncated for brevity] ...\n")
        if end_kept < 1000: end_kept = 1000 
        result_text = (
            result_text[:start_kept]
            + "\n... [Simulation output truncated for brevity] ...\n"
            + result_text[-end_kept:]
        )
        print("INFO: Simulation output was long and has been truncated for display.")

    return result_text 
# -*- coding: utf-8 -*-
"""
Opentrons Code Generation Benchmark Runner

This script runs a series of benchmark tests for the AI-powered protocol
generation. It uses a predefined dataset of prompts, calls the code
generation agent, and records various performance metrics.

Outputs:
- A summary markdown and CSV file with key metrics.
- A directory with detailed artifacts (code and logs) for each test case.
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# --- Pre-run check for dependencies ---
try:
    import pandas as pd
except ImportError:
    print("Error: pandas is not installed. Please install it using 'pip install pandas'")
    sys.exit(1)

# --- Add project root to path to allow absolute imports ---
# This allows the script to be run from anywhere and still find the 'backend' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.langchain_agent import run_code_generation_graph
except ImportError as e:
    print(f"Error: Could not import from 'backend'. Make sure the project structure is correct.")
    print(f"Project root calculated as: {project_root}")
    print(f"Sys path: {sys.path}")
    print(f"Original error: {e}")
    sys.exit(1)


# --- Configuration ---

BENCHMARK_FILE = os.path.join(os.path.dirname(__file__), 'benchmark_dataset.json')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'benchmark_results')
DETAILS_DIR = os.path.join(RESULTS_DIR, 'details')
RESULTS_SUMMARY_MD = os.path.join(RESULTS_DIR, 'summary.md')
RESULTS_SUMMARY_CSV = os.path.join(RESULTS_DIR, 'summary.csv')
MAX_ITERATIONS = 5

# A rich, default hardware configuration for OT-2 to be used for all tests.
# The AI should be able to select the necessary labware from this list based on the prompt.
DEFAULT_OT2_HARDWARE_CONFIG = """
Robot Model: Opentrons OT-2
API Version: 2.15

Left Pipette: p1000_single_gen2
Right Pipette: p300_multi_gen2

Deck Layout:
  1: opentrons_96_tiprack_1000ul
  2: opentrons_96_tiprack_300ul
  3: corning_96_wellplate_360ul_flat
  4: nest_12_reservoir_15ml
  5: opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap
  6: corning_6_wellplate_16.8ml_flat
  7: opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical
  8: nest_96_wellplate_2ml_deep
  9: opentrons_96_wellplate_200ul_pcr_full_skirt
  10: opentrons_temperature_module_gen2
  11: opentrons_magnetic_module_gen2
"""

# --- Helper Classes & Functions ---

class IterationLogger:
    """A simple class to collect iteration logs from the agent."""
    def __init__(self, case_id: str):
        self.logs: List[Dict[str, Any]] = []
        self._case_id = case_id

    def reporter(self, data: Dict[str, Any]):
        """Callback function for the LangGraph agent to report progress."""
        print(f"  [{self._case_id}] {data.get('event_type')}: {data.get('message', '')}")
        self.logs.append(data)

    def get_final_status(self) -> Dict[str, Any]:
        """Extracts the final status from the logs."""
        final_results = [log for log in self.logs if log.get('event_type') == 'iteration_result']
        if final_results:
            return final_results[-1]
        return {}

def categorize_error(error_message: str) -> str:
    """Categorize errors into common types for analysis."""
    error_lower = error_message.lower()
    
    if "labwareloaderror" in error_lower or "cannot find a definition for labware" in error_lower:
        return "LabwareLoadError"
    elif "instrumentloaderror" in error_lower or "cannot find a definition for instrument" in error_lower:
        return "InstrumentLoadError"
    elif "moduleloaderror" in error_lower:
        return "ModuleLoadError"
    elif "syntaxerror" in error_lower:
        return "SyntaxError"
    elif "attributeerror" in error_lower:
        return "AttributeError"
    elif "nameerror" in error_lower:
        return "NameError"
    elif "volume" in error_lower and ("out of range" in error_lower or "not a valid" in error_lower):
        return "VolumeError"
    elif "missing tip" in error_lower:
        return "TipError"
    elif "invalidspecificationforrobottypeerror" in error_lower:
        return "RobotTypeError"
    elif "timeout" in error_lower:
        return "TimeoutError"
    elif "agent returned failure report" in error_lower:
        return "AgentFailure"
    else:
        return "Other"

def run_single_test(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a single benchmark test case and returns a results dictionary."""
    
    case_id = test_case['id']
    print(f"\n--- Running test case: {case_id} ---")
    
    sop = test_case['prompt']
    hardware_config = DEFAULT_OT2_HARDWARE_CONFIG
    
    tool_input = f"{sop}\n---CONFIG_SEPARATOR---\n{hardware_config}"
    
    logger = IterationLogger(case_id)
    
    start_time = time.time()
    
    output = run_code_generation_graph(
        tool_input=tool_input,
        max_iterations=10,  # 增加最大迭代次数到10次
        iteration_reporter=logger.reporter
    )
    
    end_time = time.time()
    
    generation_time = round(end_time - start_time, 2)
    final_status_log = logger.get_final_status()
    
    status = "FAIL"
    attempts = 0
    error_type = "N/A"
    error_category = "N/A"
    generated_code = ""

    if final_status_log:
        attempts = final_status_log.get('attempt_num', 0)
        log_status = final_status_log.get('status', 'FINAL_FAILED')
        if log_status == "SUCCESS":
            status = "PASS"
            generated_code = final_status_log.get("final_code", "")
        elif log_status == "SUCCESS_WITH_WARNINGS":
            status = "PASS_WITH_WARNINGS"
            generated_code = final_status_log.get("final_code", output)
        else:
            status = "FAIL"
            error_type = final_status_log.get('error_details', 'Unknown failure')
            error_category = categorize_error(str(error_type))
            generated_code = final_status_log.get("final_code", "No code produced.")
    else:
        if "**协议生成失败报告**" in output:
            status = "FAIL"
            error_type = "Agent returned failure report."
            error_category = "AgentFailure"
        elif "Warning:" in output:
            status = "PASS_WITH_WARNINGS"
        elif output and not output.startswith("Error:"):
            status = "PASS"
        else:
            error_type = "Unknown error or no output."
            error_category = "Other"
        generated_code = output

    first_pass = "Yes" if status.startswith("PASS") and attempts == 1 else "No"
    
    # Save generated code
    code_filename = f"{case_id}_code.py"
    code_filepath = os.path.join(DETAILS_DIR, code_filename)
    with open(code_filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Benchmark: {case_id}\n# Status: {status}\n# Attempts: {attempts}\n# Error Type: {error_category}\n\n")
        code_to_write = generated_code
        if '```python' in code_to_write:
            match = re.search(r"```python\n([\s\S]*?)\n```", code_to_write, re.DOTALL)
            if match:
                code_to_write = match.group(1).strip()
        f.write(code_to_write)
    
    # Save iteration logs
    log_filename = f"{case_id}_log.json"
    log_filepath = os.path.join(DETAILS_DIR, log_filename)
    with open(log_filepath, 'w', encoding='utf-8') as f:
        json.dump(logger.logs, f, indent=2, ensure_ascii=False)
        
    return {
        "ID": case_id,
        "Category": test_case['category'],
        "Difficulty": test_case['difficulty'],
        "Status": status,
        "Time (s)": generation_time,
        "Attempts": attempts,
        "First Pass": first_pass,
        "Error Category": error_category,
        "Error Details": str(error_type)[:200].replace('\n', ' '),
        "Code Path": f"./details/{code_filename}",
        "Log Path": f"./details/{log_filename}",
    }

def generate_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive summary statistics."""
    total_cases = len(df)
    pass_count = len(df[df['Status'].str.startswith('PASS')])
    fail_count = total_cases - pass_count
    pass_rate = (pass_count / total_cases * 100) if total_cases > 0 else 0
    first_pass_count = len(df[df['First Pass'] == 'Yes'])
    first_pass_rate = (first_pass_count / total_cases * 100) if total_cases > 0 else 0
    
    # Only calculate time/attempts stats for non-crashed cases
    valid_df = df[df['Status'] != 'CRASH']
    avg_time = valid_df['Time (s)'].mean() if len(valid_df) > 0 else 0
    avg_attempts = valid_df['Attempts'].mean() if len(valid_df) > 0 else 0
    
    # Error analysis
    failed_df = df[df['Status'] == 'FAIL']
    error_counts = failed_df['Error Category'].value_counts().to_dict() if len(failed_df) > 0 else {}
    
    # Performance by difficulty
    difficulty_stats = {}
    for difficulty in df['Difficulty'].unique():
        subset = df[df['Difficulty'] == difficulty]
        difficulty_pass_rate = (len(subset[subset['Status'].str.startswith('PASS')]) / len(subset) * 100) if len(subset) > 0 else 0
        difficulty_stats[difficulty] = {
            'total': len(subset),
            'pass_rate': round(difficulty_pass_rate, 2)
        }
    
    # Performance by category
    category_stats = {}
    for category in df['Category'].unique():
        subset = df[df['Category'] == category]
        category_pass_rate = (len(subset[subset['Status'].str.startswith('PASS')]) / len(subset) * 100) if len(subset) > 0 else 0
        category_stats[category] = {
            'total': len(subset),
            'pass_rate': round(category_pass_rate, 2)
        }
    
    return {
        'total_cases': total_cases,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'pass_rate': round(pass_rate, 2),
        'first_pass_count': first_pass_count,
        'first_pass_rate': round(first_pass_rate, 2),
        'avg_time': round(avg_time, 2),
        'avg_attempts': round(avg_attempts, 2),
        'error_counts': error_counts,
        'difficulty_stats': difficulty_stats,
        'category_stats': category_stats
    }

def main():
    """Main function to run the benchmark suite."""
    print("Starting Opentrons Code Generation Benchmark...")
    print(f"Results will be saved to: {RESULTS_DIR}")
    
    os.makedirs(DETAILS_DIR, exist_ok=True)
    
    # Load test cases
    with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        benchmark_data = json.load(f)
    
    # 之前失败的7个测试用例
    failed_cases_ids = [
        "v2.cell2", "v3", "v3.1", "elisa_assay", 
        "v4.1", "v8_1", "v8_2"
    ]
    test_cases = [tc for tc in benchmark_data['test_cases'] if tc['id'] in failed_cases_ids]
    
    print(f"Running re-test for {len(test_cases)} failed cases...")
    
    # Check if a specific test case is requested via command-line argument
    if len(sys.argv) > 1:
        requested_id = sys.argv[1]
    
    all_results = []
    
    # Optional: limit test cases for debugging
    # test_cases = [tc for tc in test_cases if tc['id'] in ['v1', 'error_labware_name', 'pcr_setup_basic']]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Running test {i}/{len(test_cases)}: {test_case['id']}")
        print(f"Category: {test_case['category']}, Difficulty: {test_case['difficulty']}")
        print(f"{'='*60}")
        
        try:
            result = run_single_test(test_case)
            all_results.append(result)
            print(f"Result: {result['Status']} in {result['Time (s)']}s ({result['Attempts']} attempts)")
        except Exception as e:
            print(f"FATAL: Test case {test_case['id']} crashed the runner: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({
                "ID": test_case['id'],
                "Category": test_case['category'],
                "Difficulty": test_case['difficulty'],
                "Status": "CRASH", "Time (s)": 0, "Attempts": 0, "First Pass": "No",
                "Error Category": "Crash", "Error Details": str(e)[:200],
                "Code Path": "N/A", "Log Path": "N/A",
            })
            
    # Create DataFrame and save results
    df = pd.DataFrame(all_results)
    df.to_csv(RESULTS_SUMMARY_CSV, index=False)
    print(f"\nBenchmark summary saved to {RESULTS_SUMMARY_CSV}")

    # Generate comprehensive statistics
    stats = generate_summary_statistics(df)
    
    # Create markdown report
    md_table = df.to_markdown(index=False)
    
    summary_header = f"""# Opentrons Code Generation Benchmark Results

- **Run Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Test Cases:** {stats['total_cases']}
- **Pass Rate:** {stats['pass_rate']}% ({stats['pass_count']}/{stats['total_cases']})
- **First Pass Rate:** {stats['first_pass_rate']}% ({stats['first_pass_count']}/{stats['total_cases']})
- **Average Generation Time:** {stats['avg_time']}s
- **Average Attempts:** {stats['avg_attempts']}

## Performance by Difficulty

"""
    
    for difficulty, data in stats['difficulty_stats'].items():
        summary_header += f"- **{difficulty}**: {data['pass_rate']}% ({data['total']} cases)\n"
    
    summary_header += "\n## Performance by Category\n\n"
    
    for category, data in stats['category_stats'].items():
        summary_header += f"- **{category}**: {data['pass_rate']}% ({data['total']} cases)\n"
    
    if stats['error_counts']:
        summary_header += "\n## Error Analysis\n\n"
        for error_type, count in stats['error_counts'].items():
            summary_header += f"- **{error_type}**: {count} cases\n"
    
    summary_header += "\n## Detailed Results\n\n"

    with open(RESULTS_SUMMARY_MD, 'w', encoding='utf-8') as f:
        f.write(summary_header)
        f.write(md_table)
        
    print(f"Benchmark report saved to {RESULTS_SUMMARY_MD}")
    print(f"\nSummary Statistics:")
    print(f"  Overall Pass Rate: {stats['pass_rate']}%")
    print(f"  First Pass Rate: {stats['first_pass_rate']}%")
    print(f"  Average Time: {stats['avg_time']}s")
    print(f"  Average Attempts: {stats['avg_attempts']}")
    print("\nBenchmark finished.")


if __name__ == "__main__":
    main() 
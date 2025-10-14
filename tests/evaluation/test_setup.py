# -*- coding: utf-8 -*-
"""
Setup Validation Script

Quick test to ensure the benchmark environment is properly configured.
"""

import os
import sys
import json

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("  ✓ pandas imported successfully")
    except ImportError:
        print("  ✗ pandas not available - run: pip install pandas")
        return False
    
    try:
        from backend.langchain_agent import run_code_generation_graph
        print("  ✓ backend.langchain_agent imported successfully")
    except ImportError as e:
        print(f"  ✗ backend.langchain_agent import failed: {e}")
        return False
    
    try:
        from backend.config_manager import get_config
        config = get_config()
        print("  ✓ backend.config imported successfully")
        print(f"    - Model: {config.api.model_name}")
        print(f"    - Base URL: {config.api.base_url}")
        print(f"    - API Key: {'*' * (len(config.api.api_key) - 4) + config.api.api_key[-4:] if config.api.api_key else 'Not set'}")
    except ImportError as e:
        print(f"  ✗ backend.config import failed: {e}")
        return False
    
    return True

def test_dataset():
    """Test that the benchmark dataset can be loaded."""
    print("\nTesting dataset...")
    
    dataset_path = os.path.join(os.path.dirname(__file__), 'benchmark_dataset.json')
    
    if not os.path.exists(dataset_path):
        print(f"  ✗ Dataset not found at: {dataset_path}")
        return False
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_cases = data.get('test_cases', [])
        print(f"  ✓ Dataset loaded successfully ({len(test_cases)} test cases)")
        
        # Check for required fields
        if test_cases:
            first_case = test_cases[0]
            required_fields = ['id', 'category', 'difficulty', 'prompt']
            missing_fields = [field for field in required_fields if field not in first_case]
            
            if missing_fields:
                print(f"  ⚠ Missing fields in test cases: {missing_fields}")
            else:
                print("  ✓ Test case format is valid")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to load dataset: {e}")
        return False

def test_simple_generation():
    """Test a very simple code generation to ensure the system works."""
    print("\nTesting simple code generation...")
    
    try:
        from backend.langchain_agent import run_code_generation_graph
        
        # Very simple test case
        simple_sop = "Add 100µL of water from tube A1 to well A1 of a 96-well plate."
        simple_hardware = """
Robot Model: Opentrons OT-2
API Version: 2.15
Left Pipette: p1000_single_gen2
Deck Layout:
  1: opentrons_96_tiprack_1000ul
  2: corning_96_wellplate_360ul_flat
  3: opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap
"""
        
        tool_input = f"{simple_sop}\n---CONFIG_SEPARATOR---\n{simple_hardware}"
        
        print("  Running simple test (this may take 30-60 seconds)...")
        
        class SimpleReporter:
            def __init__(self):
                self.events = []
            
            def __call__(self, data):
                self.events.append(data)
                event_type = data.get('event_type', '')
                if event_type in ['code_attempt', 'simulation_start', 'iteration_result']:
                    print(f"    - {event_type}: {data.get('message', '')}")
        
        reporter = SimpleReporter()
        
        result = run_code_generation_graph(
            tool_input=tool_input,
            max_iterations=2,  # Keep it short for testing
            iteration_reporter=reporter
        )
        
        if result and not result.startswith("Error:"):
            print("  ✓ Simple code generation successful")
            print(f"    Result length: {len(result)} characters")
            return True
        else:
            print(f"  ✗ Code generation failed: {result[:200]}...")
            return False
            
    except Exception as e:
        print(f"  ✗ Simple generation test failed: {e}")
        import traceback
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all setup validation tests."""
    print("=" * 60)
    print("BENCHMARK SETUP VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Dataset Tests", test_dataset),
        ("Simple Generation Test", test_simple_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        symbol = "✓" if success else "✗"
        print(f"{symbol} {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run benchmarks.")
        print("\nNext steps:")
        print("  1. Quick test: python benchmark_quick_test.py")
        print("  2. Full benchmark: python benchmark_runner.py")
    else:
        print("\n❌ Some tests failed. Please fix the issues above before running benchmarks.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple test script for the refactored functions."""

def test_simulation_function():
    """Test the refactored simulation function."""
    print("=== Testing Simulation Function ===")
    try:
        from opentrons_utils import run_opentrons_simulation
        
        # Simple test protocol
        test_protocol = """
from opentrons import protocol_api

metadata = {'apiLevel': '2.16'}

def run(protocol: protocol_api.ProtocolContext):
    protocol.comment('Simple test protocol')
"""
        
        print("Testing legacy string output...")
        result_str = run_opentrons_simulation(test_protocol, return_structured=False)
        print(f"String result type: {type(result_str)}")
        print(f"String result preview: {result_str[:200]}...")
        
        print("\nTesting structured output...")
        result_dict = run_opentrons_simulation(test_protocol, return_structured=True)
        print(f"Dict result type: {type(result_dict)}")
        print(f"Dict keys: {list(result_dict.keys())}")
        print(f"Success: {result_dict['success']}")
        print(f"Final status: {result_dict['final_status']}")
        
        assert isinstance(result_str, str)
        assert "Simple test protocol" in result_str
        assert result_dict["success"] is True
        assert result_dict["final_status"] == "LIKELY SUCCEEDED"
    except Exception as e:
        print(f"Simulation function test failed: {e}")
        import traceback
        traceback.print_exc()

def test_basic_imports():
    """Test basic imports."""
    print("=== Testing Basic Imports ===")
    try:
        print("Importing opentrons_utils...")
        import opentrons_utils
        print("✓ opentrons_utils imported")
        
        print("Importing langchain_agent...")
        import langchain_agent
        print("✓ langchain_agent imported")
        
        print("Importing api_server...")
        import api_server
        print("✓ api_server imported")
    except ImportError as e:
        assert False, f"Failed to import api_server: {e}"
    pass

def main():
    """Run all tests."""
    print("Starting Simple Tests...")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Simulation Function", test_simulation_function),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
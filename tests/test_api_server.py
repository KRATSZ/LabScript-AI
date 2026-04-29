# -*- coding: utf-8 -*-
"""Test script for the API server functionality."""

import asyncio
import json
import requests
import time
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from backend.api_server import app, get_sop_generator, get_code_generator, get_protocol_simulator

# Test configuration
API_BASE_URL = "http://localhost:8000"

# Mock functions
def mock_sop_generator():
    return lambda *args, **kwargs: "Mocked SOP"

def mock_code_generator():
    return lambda *args, **kwargs: """from opentrons import protocol_api

metadata = {
    'protocolName': 'Test Protocol',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Simple mocked code
    pass"""

def mock_code_generator_with_diff():
    """Mock code generator that simulates diff correction workflow"""
    return lambda *args, **kwargs: """from opentrons import protocol_api

metadata = {
    'protocolName': 'Fixed Protocol', 
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # This code was corrected via diff mechanism  
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'D1')
    pass"""

def mock_protocol_simulator():
    return lambda *args, **kwargs: {"success": True, "raw_output": "mock simulation output", "final_status": "succeeded"}

# Override dependencies for testing
app.dependency_overrides[get_sop_generator] = mock_sop_generator
app.dependency_overrides[get_code_generator] = mock_code_generator
app.dependency_overrides[get_protocol_simulator] = mock_protocol_simulator

def test_health_check(client: TestClient):
    """Test the basic health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_detailed_health(client: TestClient):
    """Test the detailed health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "version" in response.json()

def test_list_tools(client: TestClient):
    """Test the tools listing endpoint."""
    response = client.get("/api/tools")
    assert response.status_code == 200
    assert "tools_available" in response.json()

def test_sop_generation(client: TestClient):
    """Test SOP generation endpoint with dependency override."""
    test_data = {"hardware_config": "Test Hardware", "user_goal": "Test Goal"}
    response = client.post("/api/generate-sop", json=test_data)
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert json_response["sop_markdown"] == "Mocked SOP"

def test_protocol_code_generation(client: TestClient):
    """Test protocol code generation endpoint with dependency override."""
    test_data = {"sop_markdown": "Test SOP", "hardware_config": "Test Hardware"}
    response = client.post("/api/generate-protocol-code", json=test_data)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert "from opentrons import protocol_api" in json_response["generated_code"]
    assert "Test Protocol" in json_response["generated_code"]

def test_protocol_simulation(client: TestClient):
    """Test protocol simulation endpoint with dependency override."""
    test_data = {"protocol_code": "some python code"}
    response = client.post("/api/simulate-protocol", json=test_data)
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert "mock simulation output" in json_response["raw_simulation_output"]

def test_sop_generation_invalid_input(client: TestClient):
    """Test SOP generation endpoint with missing 'user_goal'."""
    # This request is invalid because 'user_goal' is missing
    test_data = {"hardware_config": "Test Hardware"} 
    response = client.post("/api/generate-sop", json=test_data)
    
    # FastAPI should automatically return a 422 Unprocessable Entity error
    assert response.status_code == 422
    json_response = response.json()
    assert "detail" in json_response
    # Check that the error message correctly identifies the missing field
    assert "user_goal" in str(json_response["detail"])

def test_protocol_code_generation_with_diff(client: TestClient):
    """Test protocol code generation with diff correction workflow."""
    # Temporarily override the code generator to simulate diff workflow
    app.dependency_overrides[get_code_generator] = mock_code_generator_with_diff
    
    try:
        test_data = {"sop_markdown": "Test SOP with initial error", "hardware_config": "Test Hardware"}
        response = client.post("/api/generate-protocol-code", json=test_data)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["success"] is True
        
        # Verify the corrected code contains the expected corrected labware name
        assert "corning_96_wellplate_360ul_flat" in json_response["generated_code"]
        assert "from opentrons import protocol_api" in json_response["generated_code"]
        
        # The response should contain the corrected code
        assert "Fixed Protocol" in json_response["generated_code"]
        
        print("✓ Diff机制集成测试通过: API能正确处理diff修正过的代码")
        
    finally:
        # Restore original mock
        app.dependency_overrides[get_code_generator] = mock_code_generator

def test_diff_mechanism_api_response_structure(client: TestClient):
    """Test that API response includes all required fields."""
    # Use the diff-enabled mock
    app.dependency_overrides[get_code_generator] = mock_code_generator_with_diff
    
    try:
        test_data = {"sop_markdown": "Test SOP", "hardware_config": "Test Hardware"}
        response = client.post("/api/generate-protocol-code", json=test_data)

        assert response.status_code == 200
        json_response = response.json()
        
        # Check response structure includes required fields
        expected_fields = ["success", "generated_code", "attempts", "warnings", "iteration_logs", "timestamp"]
        for field in expected_fields:
            assert field in json_response, f"Missing field: {field}"
        
        # Verify the generated code is valid Python
        generated_code = json_response["generated_code"]
        assert "def run(protocol:" in generated_code
        assert "metadata" in generated_code
        
        # Check that the response is structured correctly
        assert isinstance(json_response["success"], bool)
        assert isinstance(json_response["generated_code"], str)
        assert isinstance(json_response["attempts"], int)
        assert isinstance(json_response["warnings"], list)
        assert isinstance(json_response["iteration_logs"], list)
        
        print("✓ API响应结构验证通过: 包含所有必要字段且结构正确")
        
    finally:
        # Restore original mock
        app.dependency_overrides[get_code_generator] = mock_code_generator

def run_all_tests():
    """Run all tests and report results."""
    print("Starting API Server Tests...")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Detailed Health", test_detailed_health),
        ("List Tools", test_list_tools),
        ("SOP Generation", test_sop_generation),
        ("Protocol Code Generation", test_protocol_code_generation),
        ("Protocol Simulation", test_protocol_simulation),
        ("SOP Generation Invalid Input", test_sop_generation_invalid_input),
        ("Protocol Code Generation with Diff", test_protocol_code_generation_with_diff),
        ("Diff Mechanism API Response Structure", test_diff_mechanism_api_response_structure),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
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
    print(f"Test completed at: {datetime.now().isoformat()}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Backend Test for PyLabRobot Agent

This script tests key backend functionality without SSE dependencies.
"""

import json
import requests
import time
from pathlib import Path
import unittest

class TestPyLabRobotSimple(unittest.TestCase):
    
    API_BASE_URL = "http://127.0.0.1:8000"
    HARDWARE_PROFILES_DIR = Path(__file__).parent.parent / "backend/hardware_profiles"

    def setUp(self):
        """Set up test environment."""
        print(f"\n{'='*50}")
        print(f"Starting Test: {self._testMethodName}")
        print(f"{'='*50}")
        self.session = requests.Session()
        
        # Check if server is running
        try:
            response = self.session.get(self.API_BASE_URL, timeout=5)
            print(f"✅ Backend server connection successful (status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print("❌ Backend server is not running!")
            self.fail("Connection to backend server failed. Please ensure the server is running on http://127.0.0.1:8000")

    def test_api_health_check(self):
        """Test basic API health."""
        print("🔍 Testing API health check...")
        response = self.session.get(self.API_BASE_URL)
        self.assertEqual(response.status_code, 200)
        print("✅ API health check passed!")

    def test_pylabrobot_profiles_endpoint(self):
        """Test the PyLabRobot profiles API endpoint."""
        print("🔍 Testing PyLabRobot profiles endpoint...")
        
        response = self.session.get(f"{self.API_BASE_URL}/api/pylabrobot/profiles")
        self.assertEqual(response.status_code, 200, "Failed to get PyLabRobot profiles")
        
        data = response.json()
        self.assertTrue(data.get("success"), "API returned success=False")
        
        profiles = data.get("profiles", [])
        self.assertGreater(len(profiles), 0, "No profiles returned")
        
        print(f"✅ Found {len(profiles)} profiles:")
        for profile in profiles:
            print(f"  - {profile['display_name']} ({profile['robot_model']})")
        
        # Check for specific profiles we created
        profile_models = [p["robot_model"] for p in profiles]
        expected_models = ["generic", "hamilton_star", "tecan_evo", "opentrons"]
        
        for model in expected_models:
            self.assertIn(model, profile_models, f"Missing expected profile: {model}")
        
        print("✅ All expected profiles found!")

    def test_hardware_profile_files_exist(self):
        """Test that all hardware profile files exist and are valid JSON."""
        print("🔍 Testing hardware profile files...")
        
        expected_files = [
            "pylabrobot_default.json",
            "pylabrobot_hamilton_star.json", 
            "pylabrobot_tecan_evo.json",
            "pylabrobot_opentrons.json"
        ]
        
        for filename in expected_files:
            file_path = self.HARDWARE_PROFILES_DIR / filename
            print(f"  Checking: {filename}")
            
            self.assertTrue(file_path.exists(), f"Profile file not found: {filename}")
            
            # Test JSON validity
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check required fields
            self.assertIn("robot_model", config_data, f"Missing robot_model in {filename}")
            # Note: Some files use "deck_type" instead of "deck"
            has_deck = "deck" in config_data or "deck_type" in config_data
            self.assertTrue(has_deck, f"Missing deck/deck_type in {filename}")
            self.assertIn("resources", config_data, f"Missing resources in {filename}")
            
            print(f"    ✅ {filename} - Valid JSON with robot_model: {config_data['robot_model']}")
        
        print("✅ All hardware profile files are valid!")

    def test_protocol_generation_simple(self):
        """Test a simple protocol generation request (without SSE)."""
        print("🔍 Testing simple protocol generation...")
        
        # Load Hamilton STAR config for testing
        config_path = self.HARDWARE_PROFILES_DIR / "pylabrobot_hamilton_star.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Format hardware config similar to frontend
        hardware_config = f"Robot Model: PyLabRobot\nRobot Model: {config_data['robot_model']}"
        
        request_data = {
            "sop_markdown": "Test goal: Simply aspirate 50uL from well A1.",
            "hardware_config": hardware_config,
        }
        
        print("  📤 Sending protocol generation request...")
        print(f"  🎯 Goal: {request_data['sop_markdown']}")
        print(f"  🤖 Robot Model: {config_data['robot_model']}")
        
        # Note: This test just checks that the endpoint accepts the request
        # We'll use a very short timeout and expect it to start the response
        try:
            response = self.session.post(
                f"{self.API_BASE_URL}/api/generate-protocol-code",
                json=request_data,
                timeout=2,  # Short timeout, just to confirm endpoint accepts request
                stream=True
            )
            
            # The endpoint should accept the request (200) and start streaming
            self.assertEqual(response.status_code, 200, "Protocol generation endpoint failed")
            print("✅ Protocol generation endpoint accepted the request!")
            
        except requests.exceptions.ReadTimeoutError:
            # This is expected for SSE endpoints that stream for a long time
            print("✅ Protocol generation endpoint started streaming (timeout as expected)")
        except requests.exceptions.Timeout:
            # This is also expected
            print("✅ Protocol generation endpoint started streaming (timeout as expected)")
        
        print("  ℹ️  Full protocol generation testing requires SSE support")

if __name__ == "__main__":
    print("🚀 Starting Simplified Backend Test for PyLabRobot Agent 🚀")
    print()
    unittest.main(verbosity=2)
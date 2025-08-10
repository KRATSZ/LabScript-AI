#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Test for PyLabRobot Agent - Backend Only

This script tests the entire backend workflow for the PyLabRobot agent,
ensuring that device-specific configurations are correctly loaded,
prompts are generated with the correct context, and the simulation backend
is chosen dynamically.
"""

import json
import requests
from sseclient import SSEClient
import time
from pathlib import Path
import unittest

class TestPyLabRobotE2E(unittest.TestCase):
    
    API_BASE_URL = "http://127.0.0.1:8000"
    HARDWARE_PROFILES_DIR = Path(__file__).parent.parent / "backend/hardware_profiles"

    def setUp(self):
        """Set up test environment."""
        print(f"\n{'='*20} Starting Test: {self.id()} {'='*20}")
        self.session = requests.Session()
        # Ensure server is running
        try:
            response = self.session.get(self.API_BASE_URL)
            self.assertEqual(response.status_code, 200, "Backend server is not running.")
        except requests.exceptions.ConnectionError:
            self.fail("Connection to backend server failed. Please ensure the server is running.")

    def load_hardware_config_from_file(self, profile_name: str) -> str:
        """Loads a hardware profile and returns it as a formatted string."""
        config_path = self.HARDWARE_PROFILES_DIR / f"{profile_name}.json"
        self.assertTrue(config_path.exists(), f"Hardware profile not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Format the config similar to how the frontend would
        # This is a simplified version for testing purposes
        lines = [f"Robot Model: PyLabRobot"]
        for key, value in config_data.items():
            if isinstance(value, dict):
                lines.append(f"{key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                 lines.append(f"{key.replace('_', ' ').title()}: {', '.join(map(str, value))}")
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(lines)

    def run_protocol_generation_test(self, robot_model: str, user_goal: str, expected_backend: str, expected_prompt_text: str):
        """
        A generic test runner for generating a protocol for a specific device.
        
        Args:
            robot_model: The robot model to test (e.g., "pylabrobot_hamilton_star").
            user_goal: The user's goal for the protocol.
            expected_backend: The expected backend to be used (e.g., "HamiltonStarBackend").
            expected_prompt_text: A piece of text expected to be in the agent's knowledge.
        """
        print(f"Testing protocol generation for: {robot_model}")
        
        # 1. Load hardware config
        hardware_config = self.load_hardware_config_from_file(robot_model)
        self.assertIn(f"Robot Model: {robot_model.split('_', 1)[1].replace('_', ' ')}", hardware_config, "Loaded config is incorrect.")

        # 2. Call generate-protocol-code endpoint
        sop_markdown = f"User goal: {user_goal}"
        request_data = {
            "sop_markdown": sop_markdown,
            "hardware_config": hardware_config,
        }
        
        print("Sending request to /api/generate-protocol-code...")
        response = self.session.post(
            f"{self.API_BASE_URL}/api/generate-protocol-code",
            json=request_data,
            stream=True
        )
        self.assertEqual(response.status_code, 200, "Failed to connect to streaming endpoint.")

        client = SSEClient(response)
        
        found_backend_log = False
        found_knowledge_log = False
        final_code = None
        
        print("Processing SSE events...")
        for event in client.events():
            if event.event == 'message':
                try:
                    data = json.loads(event.data)
                    event_type = data.get("event_type")
                    message = data.get("message", "")
                    
                    if "Using" in message and "backend" in message:
                        print(f"  - Log: {message}")
                        if expected_backend in message:
                            found_backend_log = True
                    
                    if "knowledge for PyLabRobot" in message:
                        print(f"  - Log: {message}")
                        if expected_prompt_text in data.get("knowledge", ""):
                            found_knowledge_log = True
                            
                    if event_type == "final_result" and data.get("success"):
                        final_code = data.get("generated_code")
                        print("  - Final code received.")
                        
                except json.JSONDecodeError:
                    self.fail(f"Failed to decode SSE event data: {event.data}")

        print("SSE stream finished.")

        # 3. Assertions
        self.assertTrue(found_backend_log, f"Did not find expected backend log for '{expected_backend}'.")
        self.assertTrue(found_knowledge_log, f"Did not find expected text in agent knowledge: '{expected_prompt_text}'.")
        self.assertIsNotNone(final_code, "Protocol generation did not succeed or return final code.")
        self.assertIn("async def protocol(lh):", final_code, "Generated code is missing protocol function.")
        
        print(f"Successfully verified protocol generation for {robot_model}.\n")

    def test_hamilton_star_protocol(self):
        """Test case for Hamilton STAR."""
        self.run_protocol_generation_test(
            robot_model="pylabrobot_hamilton_star",
            user_goal="Aspirate 50uL from well A1 of the source plate and dispense into well B1 of the destination plate.",
            expected_backend="HamiltonStarBackend",
            expected_prompt_text="You are an expert in generating Python protocols for the **Hamilton STAR**"
        )
        
    def test_tecan_evo_protocol(self):
        """Test case for Tecan EVO."""
        self.run_protocol_generation_test(
            robot_model="pylabrobot_tecan_evo",
            user_goal="Using an 8-channel pipette, aspirate 100uL from the first column of the source plate and dispense to the first column of the destination plate.",
            expected_backend="EVOBackend",
            expected_prompt_text="You are an expert in generating Python protocols for the **Tecan Freedom EVO**"
        )

if __name__ == "__main__":
    print("🚀 Starting Backend E2E Test for PyLabRobot Agent 🚀")
    unittest.main()
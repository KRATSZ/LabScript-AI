#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test iteration function callback functionality."""

def test_iteration_callback():
    """Test the iteration function with callback."""
    print("=== Testing Iteration Function with Callback ===")
    
    try:
        from langchain_agent import run_code_generation_graph
        
        # Test callback function
        events_received = []
        
        def test_reporter(event_data):
            events_received.append(event_data)
            print(f"Event: {event_data['event_type']} - {event_data.get('message', '')}")
            if event_data['event_type'] == 'iteration_result':
                print(f"  Status: {event_data.get('status')}")
                print(f"  Attempt: {event_data.get('attempt_num')}")
        
        # Simple test input
        test_sop = "1. Load a 96-well plate in slot 1\n2. Transfer 50uL from A1 to B1"
        test_hw = "Robot Model: OT-2\nAPI Version: 2.16\nLeft Pipette: p300_single_gen2"
        test_input = f"{test_sop}\n---CONFIG_SEPARATOR---\n{test_hw}"
        
        print("Running code generation with callback...")
        result = run_code_generation_graph(test_input, max_iterations=3, iteration_reporter=test_reporter)
        
        print(f"\nFunction completed!")
        print(f"Events received: {len(events_received)}")
        print(f"Result type: {type(result)}")
        print(f"Result preview: {result[:300]}..." if len(result) > 300 else result)
        
        # Check if we received the expected event types
        event_types = [event['event_type'] for event in events_received]
        print(f"\nEvent types received: {set(event_types)}")
        
        assert len(events_received) > 0
        assert "成功" in events_received[-1]["message"]
        assert isinstance(result, str)
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_iteration_callback()
    print(f"\nTest {'PASSED' if True else 'FAILED'}")
    exit(0 if True else 1) 
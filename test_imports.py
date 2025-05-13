import sys
import traceback

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Python Path: {sys.path}")

print("\nAttempting to import ChatOpenAI...")
try:
    from langchain_openai import ChatOpenAI
    print("SUCCESS: ChatOpenAI imported successfully!")
except ImportError as e:
    print(f"FAILED to import ChatOpenAI: {e}")
    traceback.print_exc()
except Exception as e_other:
    print(f"UNEXPECTED ERROR during ChatOpenAI import: {e_other}")
    traceback.print_exc()

print("\nAttempting to import agent_executor from langchain_agent...")
try:
    from langchain_agent import agent_executor
    print("SUCCESS: agent_executor imported successfully!")
except ImportError as e:
    print(f"FAILED to import agent_executor: {e}")
    traceback.print_exc()
except Exception as e_other:
    print(f"UNEXPECTED ERROR during agent_executor import: {e_other}")
    traceback.print_exc()

print("\nAttempting to import run_opentrons_simulation from opentrons_utils...")
try:
    from opentrons_utils import run_opentrons_simulation
    print("SUCCESS: run_opentrons_simulation imported successfully!")
except ImportError as e:
    print(f"FAILED to import run_opentrons_simulation: {e}")
    traceback.print_exc()
except Exception as e_other:
    print(f"UNEXPECTED ERROR during run_opentrons_simulation import: {e_other}")
    traceback.print_exc()

print("\nTest finished.") 
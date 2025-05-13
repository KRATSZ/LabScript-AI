# -*- coding: utf-8 -*-
"""Sets up the Langchain agent for Opentrons protocol generation."""
import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# Import from our other modules
from config import (
    api_key, base_url, model_name,
    VALID_LABWARE_NAMES, VALID_INSTRUMENT_NAMES, VALID_MODULE_NAMES,
    CODE_EXAMPLES
)
from opentrons_utils import run_opentrons_simulation, SimulateToolInput

# 1. LLM Setup
llm = ChatOpenAI(
    model=model_name,
    openai_api_key=api_key, # Using the hardcoded key from config
    openai_api_base=base_url, # Using the hardcoded base URL from config
    temperature=0.05, 
    streaming=True, 
)

# 2. Tool Setup
tools = [
    Tool(
        name="opentrons_simulator",
        func=run_opentrons_simulation,
        description="""Simulates Opentrons Python protocol code (API v2+) using 'opentrons_simulate'.
Input MUST be a string containing the complete, raw Python code (including imports, metadata/requirements, and run function). DO NOT wrap the code in markdown backticks (```).
Output is the simulation result (stdout/stderr). Analyze the '--- Result: ---' line and STDERR content carefully.
If the result indicates FAILURE or critical errors/tracebacks/exceptions are present in STDERR/STDOUT: you MUST revise the *entire* Python code based on the error messages and run the simulation again with the corrected code.
Repeat this process until the simulation result indicates SUCCESS or 'likely SUCCEEDED'.
If SUCCESS/likely SUCCEEDED, the code is considered valid and ready.""",
        args_schema=SimulateToolInput
    )
]

# 3. Prompt Template Definition
prompt_template_str = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format STRICTLY:

Question: the input question you must answer
# --- Add chat history to the prompt for multi-turn ---
Previous Conversation:
{chat_history}

Thought: You should always think step-by-step about the user request, plan the code, consult the provided valid names and examples, use the simulator, analyze results, and plan corrections.
Action: The action to take, MUST be exactly one of [{tool_names}]. Do NOT use brackets around the tool name.
Action Input: The input to the action. For `opentrons_simulator`, this MUST be the complete, raw Python code string ONLY. DO NOT include markdown formatting like ```python or ```.
Observation: The result of the action (the output from the `opentrons_simulator` tool).
... (this Thought/Action/Action Input/Observation sequence repeats N times)
Thought: I have received a 'Simulation SUCCEEDED' or 'Simulation likely SUCCEEDED' result. The code is validated. I will now output the final code.
Final Answer: The final answer. This MUST be ONLY the validated raw Python code block itself, starting with `from opentrons import...` or `metadata = ...` or `requirements = ...`. NO other text, NO explanations, NO apologies, NO markdown formatting (```python or ```).

Your specific task: Generate valid Opentrons Python code based on the user's request, ensuring it passes simulation using the `opentrons_simulator` tool. Adhere strictly to the provided valid names and examples.

--- CONTEXT: Valid Opentrons Information ---

Valid Labware Names (use EXACTLY these `load_name` strings):
{valid_labware}

Valid Instrument Names (use EXACTLY these `instrument_name` strings):
{valid_instruments}

Valid Module API Names (use EXACTLY these `load_module` strings for `protocol.load_module(MODULE_API_NAME, LOCATION)`):
{valid_modules}

Code Examples (Refer to these for correct syntax, API level, robot type specific details like `metadata` vs `requirements` and trash handling):
{code_examples}

--- END CONTEXT ---

User Request: {input}

Detailed Instructions for your Thought Process:
1.  Analyze User Request: Identify all requirements: actions (transfer, mix, etc.), volumes, labware types and desired names, pipette types, module types, deck slots, target robot (OT-2 or Flex), and desired API level.
    *   Default to API '2.20' if unspecified by the user or if a Flex robot is implied. Check example API levels.
    *   Flex uses `requirements = {{"robotType": "Flex", "apiLevel": "X.Y"}}` (typically API >= 2.20).
    *   OT-2 uses `metadata = {{'apiLevel': 'X.Y'}}` (e.g., '2.16', '2.20').
2.  Plan Code Generation: Outline the Python code structure. Crucially:
    *   Include `from opentrons import protocol_api` at the beginning.
    *   Define the main function as `def run(protocol: protocol_api.ProtocolContext):` including the type hint.
    *   Select **EXACT** API names for labware, instruments, and modules from the `Valid Names` lists provided.
    *   Use the correct syntax for loading items based on the `Code Examples` (e.g., `protocol.load_labware(...)`, `protocol.load_instrument(...)`, `protocol.load_module(...)`, `module_var.load_labware(...)`).
    *   For Flex, remember to `protocol.load_trash_bin(SLOT)` if needed. OT-2 uses the fixed trash in slot 12 by default and does not require explicit loading of a trash bin unless a movable trash is used (less common for basic protocols).
    *   Plan the sequence of commands (pick up tip, aspirate, dispense, drop tip, etc.) based on the user request.
3.  Generate Code: Write the complete Python code based on your plan and the provided context (valid names, examples).
4.  Prepare for Simulation: Ensure the code is a single string, starting with imports, then metadata/requirements, then the run function. Double-check that only valid API names were used and match the robot type context (e.g., Flex labware for Flex robot).
5.  Action - Simulate: Use the `opentrons_simulator` tool. The Action Input MUST be the raw code string ONLY.
6.  Analyze Observation: Read the simulation output (STDOUT, STDERR, '--- Result: ---'). Pay close attention to any lines containing 'error', 'traceback', 'exception', 'fail', 'not found', especially in STDERR after common warnings are mentally filtered.
7.  Check for Success/Failure:
    *   If '--- Result: Simulation SUCCEEDED ---' or '--- Result: Simulation likely SUCCEEDED ---': Proceed to the 'Final Answer' step. (Note: "SUCCEEDED WITH UNEXPECTED STDERR" or "COMPLETED WITH UNEXPECTED STDERR" should still be reviewed carefully for subtle issues, but might be acceptable if the core logic is fine).
    *   If '--- Result: Simulation FAILED ---' or critical errors are present: Identify the specific Python error(s) (e.g., `LabwareLoadError`, `AttributeError`, `ImportError`, `SyntaxError`, `RobotNotSupportedError`). Think step-by-step how to correct the Python code, referring back to the valid names, examples, and API documentation for the specific robot type and API level.
8.  Iterate if Failed: Go back to step 3 (Generate Corrected Code), step 4 (Prepare), step 5 (Simulate), and step 6 (Analyze) with the *corrected* code. Repeat until simulation succeeds acceptably.
9.  Final Answer: Once simulation succeeds, provide ONLY the validated raw Python code block as the Final Answer. Start the code directly.

Begin!

{agent_scratchpad}
"""

# 4. Prompt Template Creation and Formatting
prompt = PromptTemplate.from_template(prompt_template_str)
prompt = prompt.partial(
    valid_labware=", ".join(VALID_LABWARE_NAMES),
    valid_instruments=", ".join(VALID_INSTRUMENT_NAMES),
    valid_modules=", ".join(VALID_MODULE_NAMES),
    code_examples=CODE_EXAMPLES,
    tools = tools, # Include tools in the partial formatting
    tool_names = ", ".join([t.name for t in tools]) # Include tool names
)

# 5. Agent Creation
# Note: The prompt passed to create_react_agent should NOT be partially formatted yet
# with agent_scratchpad or input, as the agent handles those.
# We use the base prompt object created above.
agent = create_react_agent(llm, tools, prompt) 

# 6. Add memory for multi-turn conversation
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)

# 7. Agent Executor Creation
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True, 
    handle_parsing_errors="Format Error: Ensure your output strictly follows the Thought/Action/Action Input/Observation format. Check tool names and inputs. Remember, Action Input for the simulator must be ONLY the raw Python code.",
    max_iterations=10 
)

# We can potentially add functions here later if needed, 
# but the primary purpose is to set up and expose agent_executor.
if __name__ == '__main__':
    # This block is optional, can be used for testing the agent setup directly
    print("Langchain agent setup complete.")
    print(f"Agent Executor created: {type(agent_executor)}")
    # Example test invocation (requires user input)
    # try:
    #     test_input = "Create a simple OT-2 protocol API 2.16 to transfer 10uL from A1 to B1 of a corning_96_wellplate_360ul_flat in slot 1 using a p20_single_gen2 pipette and opentrons_96_tiprack_20ul in slot 2."
    #     print(f"\n--- Testing agent with input: ---\n{test_input}")
    #     result = agent_executor.invoke({"input": test_input})
    #     print("\n--- Agent Test Result ---")
    #     print(result)
    # except Exception as e:
    #     print(f"Agent test invocation failed: {e}") 
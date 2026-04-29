import asyncio
import os
import sys
import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import re

# Import our PyLabRobot executor
sys.path.append(os.path.join(os.path.dirname(__file__), 'pylabrobot-main', 'pylabrobot'))
from pylabrobot_executor import run_pylabrobot_protocol

# State definition for LangGraph
class GraphState(TypedDict):
    user_query: str                 # 用户原始自然语言需求
    pylabrobot_knowledge: str       # 通过提示词注入的 PyLabRobot 相关知识/文档片段
    current_protocol_code: Optional[str] # 当前 LLM 生成的 PyLabRobot 协议代码
    deck_json: Optional[str]        # 当前使用的 Deck 布局 JSON (固定)
    simulation_stdout: Optional[str]  # 上一轮模拟的 stdout
    simulation_stderr: Optional[str]  # 上一轮模拟的 stderr
    simulation_success: bool          # 上一轮模拟是否成功
    result_summary: Optional[str]   # 上一轮模拟的结果摘要
    attempts: int                     # 当前尝试次数
    max_attempts: int                 # 允许的最大尝试次数
    final_outcome: Optional[str]    # 最终结果状态

# Fixed Deck JSON - 极简版本，避免复杂的资源定义问题
FIXED_DECK_JSON = """
{
  "type": "Deck",
  "name": "simple_deck",
  "size_x": 500,
  "size_y": 400,
  "size_z": 100,
  "category": "deck",
  "parent_name": null,
  "location": {"type": "Coordinate", "x": 0, "y": 0, "z": 0},
  "children": [],
  "rotation": {"type": "Rotation", "x": 0, "y": 0, "z": 0},
  "barcode": null
}
"""

# PyLabRobot 知识库 - 包含 Few-shot 示例
PYLABROBOT_KNOWLEDGE = """
You are an expert in generating Python protocols for the PyLabRobot platform.
Your task is to write an async Python function `async def protocol(lh): ...` based on the user's request.

== PyLabRobot Key API Summary ==
- The main object is `lh` (LiquidHandler). All operations are methods of `lh`.
- All `lh` operations are asynchronous and MUST be awaited. e.g., `await lh.pick_up_tips(...)`.
- Getting resources: Use `lh.get_resource("resource_name")` to get a resource object from the deck.
- Core commands:
  - `await lh.pick_up_tips(tip_rack["A1"])`: Picks up tips from a specific spot.
  - `await lh.drop_tips(tip_rack["A1"])`: Drops tips back to a specific spot.
  - `await lh.aspirate(plate["A1"], vols=[100])`: Aspirates 100uL from well A1.
  - `await lh.dispense(plate["B1"], vols=[100])`: Dispenses 100uL into well B1.

== IMPORTANT: Deck Layout ==
- The deck layout is FIXED and simplified for demo purposes. Do NOT generate any Deck JSON.
- The deck contains no predefined resources (empty children list).
- Your protocol should focus on basic deck operations and printing information.
- Always end successful protocols with `print("--- PROTOCOL_SUCCESS ---")`.

== Example of a successful protocol ==
- User Request: "Print hello and deck information."
- Correct Python Code:
```python
async def protocol(lh):
    # Get deck information
    deck = lh.deck
    print(f"Hello! Working with deck: {deck.name}")
    print(f"Deck size: {deck.size_x} x {deck.size_y} x {deck.size_z}")
    print(f"Number of children: {len(deck.children)}")
    print("--- PROTOCOL_SUCCESS ---")
```

== Basic Operations Example ==
- User Request: "Show deck details and children."
- Correct Python Code:
```python
async def protocol(lh):
    # Access deck details
    deck = lh.deck
    print(f"Deck name: {deck.name}")
    print(f"Deck location: {deck.location}")
    
    # List available resources (may be empty)
    if deck.children:
        for child in deck.children:
            print(f"Resource: {child.name}, Type: {child.__class__.__name__}")
    else:
        print("No resources found on deck")
    
    print("--- PROTOCOL_SUCCESS ---")
```

== Important Notes ==
- Always use `await` for all lh operations
- Always pick up tips before aspirating and drop them after dispensing
- Use the exact resource names: "tip_rack_1" and "plate_1"
- Well names use format like "A1", "B2", etc.
- Volume is specified in microliters (uL)
"""

# Initialize LLM with hardcoded API settings
llm = ChatOpenAI(
    model="gemini-2.5-pro-preview-06-05",
    temperature=0.2,
    openai_api_key="sk-TnKnlDtgvZgrG9wP543180A16aA34a1a978c90333dCa8746",
    openai_api_base="https://api.pumpkinaigc.online/v1"
)

async def generate_and_simulate_node(state: GraphState) -> GraphState:
    """
    核心节点：生成协议代码并执行模拟
    """
    print(f"\n=== Attempt {state['attempts'] + 1} ===")
    
    # 构建 Prompt
    if state["attempts"] == 0:
        # 首次生成
        prompt = f"""
{state["pylabrobot_knowledge"]}

Now, based on the above information, generate the `async def protocol(lh):` Python code for the following user request:

User Request: {state["user_query"]}

Please provide ONLY the Python code for the protocol function. Do not include any explanations or markdown formatting.
"""
    else:
        # 迭代修正
        prompt = f"""
{state["pylabrobot_knowledge"]}

The previous attempt to run the protocol failed. Here are the details:

Previous Protocol Code:
```python
{state["current_protocol_code"]}
```

Simulation Results:
- Success: {state["simulation_success"]}
- Result Summary: {state["result_summary"]}
- STDOUT: {state["simulation_stdout"]}
- STDERR: {state["simulation_stderr"]}

Please analyze the error and provide a corrected `async def protocol(lh):` Python code for the original user request:

User Request: {state["user_query"]}

Focus on fixing the specific errors shown in the logs. Provide ONLY the corrected Python code.
"""

    # 调用 LLM 生成代码
    try:
        messages = [SystemMessage(content="You are a PyLabRobot protocol expert."), 
                   HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        new_protocol_code = response.content.strip()
        
        # 简单的代码清理 - 移除可能的 markdown 格式
        if new_protocol_code.startswith("```python"):
            new_protocol_code = new_protocol_code[9:]
        if new_protocol_code.endswith("```"):
            new_protocol_code = new_protocol_code[:-3]
        new_protocol_code = new_protocol_code.strip()
        
        print(f"Generated Protocol Code:\n{new_protocol_code}")
        
    except Exception as e:
        print(f"Error generating protocol: {e}")
        # 如果 LLM 调用失败，使用一个简单的默认协议
        new_protocol_code = """
async def protocol(lh):
    print("ERROR: Failed to generate protocol from LLM")
    raise Exception("LLM generation failed")
"""

    # 更新状态 - 协议代码
    state["current_protocol_code"] = new_protocol_code
    state["deck_json"] = FIXED_DECK_JSON  # 使用固定的 Deck

    # 执行模拟
    try:
        print("Executing simulation...")
        pylabrobot_project_root = os.path.join(os.path.dirname(__file__), "pylabrobot-main")
        simulation_results = await run_pylabrobot_protocol(
            new_protocol_code, 
            FIXED_DECK_JSON, 
            pylabrobot_project_root=pylabrobot_project_root
        )
        
        # 更新状态 - 模拟结果
        state["simulation_stdout"] = simulation_results["stdout"]
        state["simulation_stderr"] = simulation_results["stderr"]
        state["simulation_success"] = simulation_results["success"]
        state["result_summary"] = simulation_results["result_summary"]
        
        print(f"Simulation Success: {simulation_results['success']}")
        print(f"Result Summary: {simulation_results['result_summary']}")
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        state["simulation_stdout"] = ""
        state["simulation_stderr"] = f"Simulation execution error: {e}"
        state["simulation_success"] = False
        state["result_summary"] = f"Simulation failed: {e}"

    # 更新尝试次数
    state["attempts"] += 1
    
    return state

def should_continue_edge(state: GraphState) -> str:
    """
    条件边：判断是否继续迭代
    """
    if state["simulation_success"]:
        print("✅ Protocol successfully simulated and validated!")
        state["final_outcome"] = "Success"
        return END
    elif state["attempts"] >= state["max_attempts"]:
        print(f"❌ Max attempts ({state['max_attempts']}) reached. Protocol failed to validate.")
        state["final_outcome"] = "Max attempts reached"
        return END
    else:
        print(f"🔄 Attempt {state['attempts']} failed. Retrying...")
        return "agent_core"

# 构建 LangGraph
def create_agent():
    """
    创建并编译 LangGraph Agent
    """
    workflow = StateGraph(GraphState)
    
    # 添加节点
    workflow.add_node("agent_core", generate_and_simulate_node)
    
    # 设置入口点
    workflow.set_entry_point("agent_core")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent_core",
        should_continue_edge,
        {
            "agent_core": "agent_core",  # 继续迭代
            END: END                     # 结束
        }
    )
    
    return workflow.compile()

async def run_agent(user_query: str, max_attempts: int = 3):
    """
    运行 LangGraph Agent
    """
    # 创建 Agent
    app = create_agent()
    
    # 初始状态
    initial_state = {
        "user_query": user_query,
        "pylabrobot_knowledge": PYLABROBOT_KNOWLEDGE,
        "current_protocol_code": None,
        "deck_json": FIXED_DECK_JSON,
        "simulation_stdout": None,
        "simulation_stderr": None,
        "simulation_success": False,
        "result_summary": None,
        "attempts": 0,
        "max_attempts": max_attempts,
        "final_outcome": None
    }
    
    print(f"🚀 Starting PyLabRobot Protocol Generation Agent")
    print(f"📝 User Query: {user_query}")
    print(f"🔄 Max Attempts: {max_attempts}")
    
    # 运行 Agent
    final_state = await app.ainvoke(initial_state)
    
    print(f"\n{'='*60}")
    print(f"🏁 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Final Outcome: {final_state.get('final_outcome')}")
    print(f"Total Attempts: {final_state.get('attempts')}")
    print(f"Success: {final_state.get('simulation_success')}")
    
    if final_state.get('simulation_success'):
        print(f"\n✅ SUCCESSFUL PROTOCOL:")
        print(f"```python")
        print(final_state.get('current_protocol_code'))
        print(f"```")
    else:
        print(f"\n❌ FAILED TO GENERATE WORKING PROTOCOL")
        print(f"Last Error: {final_state.get('result_summary')}")
        if final_state.get('current_protocol_code'):
            print(f"\nLast Attempted Code:")
            print(f"```python")
            print(final_state.get('current_protocol_code'))
            print(f"```")
    
    return final_state

# 测试函数
async def main():
    """
    主测试函数
    """
    test_queries = [
        "Aspirate 50uL from well A2 of the plate, then dispense it into well C5 of the same plate.",
        "Transfer 100uL from wells A1, A2, A3 to wells B1, B2, B3 respectively using different tips.",
        "Pick up tips from A1, aspirate 200uL from plate well D4, and dispense it to well H12."
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'#'*80}")
        print(f"TEST CASE {i}")
        print(f"{'#'*80}")
        
        try:
            await run_agent(query, max_attempts=3)
        except Exception as e:
            print(f"❌ Test case {i} failed with exception: {e}")
        
        print(f"\n{'='*80}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 
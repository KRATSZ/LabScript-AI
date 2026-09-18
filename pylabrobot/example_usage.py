#!/usr/bin/env python3
"""
简单的使用示例：PyLabRobot LangGraph Agent

使用前请确保：
1. 安装依赖：pip install -r requirements.txt
2. 设置 OpenAI API Key：export OPENAI_API_KEY="your-api-key"
3. 确保 pylabrobot-main 目录在当前目录下
"""

import asyncio
import os
from pylabrobot_langgraph_agent import run_agent

async def simple_example():
    """
    简单示例：运行一个基本的液体处理协议
    """
    # API Key 已硬编码在 pylabrobot_langgraph_agent.py 中
    print("ℹ️  使用硬编码的 API 配置")
    
    # 用户查询
    user_query = "Aspirate 100uL from well A1 of the plate and dispense it to well B1 of the same plate."
    
    print("🧪 PyLabRobot Protocol Generation Demo")
    print("=" * 50)
    print(f"Query: {user_query}")
    print("=" * 50)
    
    try:
        # 运行 Agent
        result = await run_agent(user_query, max_attempts=3)
        
        if result.get('simulation_success'):
            print("\n🎉 成功生成并验证了协议！")
        else:
            print("\n😞 协议生成失败，请检查错误信息。")
            
    except Exception as e:
        print(f"❌ 运行过程中出现错误: {e}")

if __name__ == "__main__":
    asyncio.run(simple_example()) 
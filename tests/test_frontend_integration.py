#!/usr/bin/env python3
"""
前端集成测试脚本
测试前端与后端API的完整集成
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

class FrontendIntegrationTester:
    def __init__(self):
        self.session = None
        self.results = {
            "health_check": False,
            "sop_generation": False,
            "code_generation": False,
            "simulation": False,
            "tools": False,
            "sse_events": 0
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """测试健康检查端点"""
        print("🔍 测试健康检查...")
        try:
            async with self.session.get(f"{API_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查通过: {data}")
                    self.results["health_check"] = True
                else:
                    print(f"❌ 健康检查失败: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
    
    async def test_tools_endpoint(self):
        """测试工具列表端点"""
        print("🔍 测试工具列表...")
        try:
            async with self.session.get(f"{API_BASE_URL}/api/tools") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 工具列表获取成功: {len(data.get('tools', []))} 个工具")
                    self.results["tools"] = True
                else:
                    print(f"❌ 工具列表获取失败: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 工具列表异常: {e}")
    
    async def test_sop_generation(self):
        """测试SOP生成"""
        print("🔍 测试SOP生成...")
        try:
            payload = {
                "hardware_config": """Robot Model: Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: None
Use Gripper: false
Deck Layout:
  A1: opentrons_96_tiprack_1000ul
  B1: corning_96_wellplate_360ul_flat""",
                "user_goal": "我想要进行一个简单的液体转移实验，从96孔板的A1孔转移100µL液体到B1孔"
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/api/generate-sop",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        sop_length = len(data.get("sop_markdown", ""))
                        print(f"✅ SOP生成成功: {sop_length} 字符")
                        self.results["sop_generation"] = True
                        return data.get("sop_markdown")
                    else:
                        print(f"❌ SOP生成失败: {data}")
                else:
                    print(f"❌ SOP生成请求失败: HTTP {response.status}")
        except Exception as e:
            print(f"❌ SOP生成异常: {e}")
        return None
    
    async def test_code_generation_sse(self, sop_markdown: str):
        """测试代码生成SSE流"""
        print("🔍 测试代码生成 (SSE)...")
        try:
            payload = {
                "sop_markdown": sop_markdown or """# 测试协议
## 材料
- Flex机器人
- flex_1channel_1000移液器
- 96孔板

## 步骤
1. 吸取100µL液体
2. 转移到目标孔
3. 完成实验""",
                "hardware_config": """Robot Model: Flex
API Version: 2.19
Left Pipette: flex_1channel_1000"""
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/api/generate-protocol-code",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    event_count = 0
                    final_code = ""
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]  # Remove 'data: '
                                data = json.loads(data_str)
                                event_count += 1
                                
                                if data.get('event_type') == 'iteration_result' and data.get('status') == 'SUCCESS':
                                    final_code = data.get('final_code', '')
                                    
                                if event_count <= 5:  # 只打印前5个事件
                                    print(f"📡 SSE事件 {event_count}: {data.get('event_type', 'unknown')}")
                                elif event_count == 6:
                                    print("📡 ... (更多事件)")
                                    
                            except json.JSONDecodeError:
                                continue
                    
                    self.results["sse_events"] = event_count
                    if final_code:
                        print(f"✅ 代码生成成功: {event_count} 个事件, {len(final_code)} 字符代码")
                        self.results["code_generation"] = True
                        return final_code
                    else:
                        print(f"⚠️ 代码生成部分成功: {event_count} 个事件，但未获得最终代码")
                else:
                    print(f"❌ 代码生成请求失败: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 代码生成异常: {e}")
        return None
    
    async def test_simulation(self, protocol_code: str):
        """测试协议模拟"""
        print("🔍 测试协议模拟...")
        try:
            payload = {
                "protocol_code": protocol_code or """from opentrons import protocol_api

metadata = {
    'protocolName': 'Test Protocol',
    'author': 'Integration Tester',
    'description': 'Simple test protocol',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'B1')
    pipette = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])
    
    pipette.pick_up_tip()
    pipette.aspirate(100, plate.wells()[0])
    pipette.dispense(100, plate.wells()[1])
    pipette.drop_tip()
"""
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/api/simulate-protocol",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        sim_result = data.get("simulation_result", {})
                        status = "成功" if sim_result.get("success") else "失败"
                        warnings = "有警告" if sim_result.get("has_warnings") else "无警告"
                        print(f"✅ 模拟完成: {status}, {warnings}")
                        self.results["simulation"] = True
                    else:
                        print(f"❌ 模拟失败: {data}")
                else:
                    print(f"❌ 模拟请求失败: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 模拟异常: {e}")
    
    async def run_full_test(self):
        """运行完整测试套件"""
        print("🚀 开始前端集成测试...")
        print("=" * 50)
        
        start_time = time.time()
        
        # 基础连接测试
        await self.test_health_check()
        await self.test_tools_endpoint()
        
        # 工作流程测试
        sop = await self.test_sop_generation()
        code = await self.test_code_generation_sse(sop)
        await self.test_simulation(code)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 50)
        print("📊 测试结果汇总:")
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print(f"🏥 健康检查: {'✅' if self.results['health_check'] else '❌'}")
        print(f"🛠️  工具列表: {'✅' if self.results['tools'] else '❌'}")
        print(f"📝 SOP生成: {'✅' if self.results['sop_generation'] else '❌'}")
        print(f"💻 代码生成: {'✅' if self.results['code_generation'] else '❌'}")
        print(f"🧪 协议模拟: {'✅' if self.results['simulation'] else '❌'}")
        print(f"📡 SSE事件数: {self.results['sse_events']}")
        
        passed_tests = sum(1 for v in self.results.values() if v is True)
        total_tests = len([k for k, v in self.results.items() if isinstance(v, bool)])
        
        print(f"📈 通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！前端集成成功！")
            return True
        else:
            print("⚠️  部分测试失败，请检查API服务器状态")
            return False

async def main():
    """主函数"""
    print("🔧 前端集成测试工具")
    print("确保API服务器正在运行在 http://localhost:8000")
    print()
    
    async with FrontendIntegrationTester() as tester:
        success = await tester.run_full_test()
        return 0 if success else 1

if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        sys.exit(1) 
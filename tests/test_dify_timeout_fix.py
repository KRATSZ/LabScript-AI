#!/usr/bin/env python3
"""
测试Dify API超时修复
"""

import sys
import os
import pytest

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from langchain_agent import generate_sop_with_langchain

@pytest.mark.skip(reason="This test is deprecated and its purpose is now covered by other tests.")
def test_dify_timeout_fix():
    """测试Dify API超时修复"""
    print("🔍 测试Dify API超时修复...")
    
    test_input = """Robot Model: Flex
API Version: 2.20
Left Pipette: flex_1channel_1000
Right Pipette: None
Use Gripper: false
Deck Layout:
  A1: opentrons_flex_96_tiprack_1000ul
  B1: corning_96_wellplate_360ul_flat
---
我想要进行一个简单的液体转移实验，从96孔板的A1孔转移100µL液体到B1孔"""
    
    print(f"📝 测试输入: {test_input[:100]}...")
    print("⏱️ 开始调用Dify API（带超时和重试机制）...")
    
    try:
        result = generate_sop_with_langchain(test_input)
        
        if result and not result.startswith("Error:"):
            print("✅ Dify API调用成功！")
            print(f"📄 SOP长度: {len(result)} 字符")
            print(f"📄 SOP预览: {result[:200]}...")
            return True
        else:
            print("❌ Dify API调用失败")
            print(f"❌ 错误信息: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(f"❌ 异常详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_dify_timeout_fix()
    if success:
        print("\n🎉 测试通过！Dify API超时问题已修复")
    else:
        print("\n💥 测试失败，请检查网络连接或Dify API状态")
    
    sys.exit(0 if success else 1) 
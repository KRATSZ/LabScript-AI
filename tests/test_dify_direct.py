#!/usr/bin/env python3
"""
直接测试Dify API调用
"""

import os
import sys
import pytest

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from langchain_agent import generate_sop_with_langchain

@pytest.mark.skip(reason="This test is deprecated as it was for the old Dify workflow.")
def test_local_sop_generation():
    """
    测试本地SOP生成功能
    """
    test_input = """
Hardware:
Robot Model: Flex
...
User Goal:
I want to do a simple transfer.
"""
    print("🎬 开始测试本地SOP生成...")
    result = generate_sop_with_langchain(test_input)
    print("📄 生成的SOP内容:")
    print(result)

    assert result is not None
    assert "Objective" in result
    assert "Procedure" in result
    print("✅ 本地SOP生成测试成功!")

if __name__ == '__main__':
    test_local_sop_generation() 
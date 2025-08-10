#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Python执行工具是否正常工作
"""

from langchain_experimental.tools import PythonREPLTool

def test_python_executor():
    """测试Python执行工具"""
    print("初始化Python执行工具...")
    python_executor = PythonREPLTool()
    
    # 测试简单计算
    test_code = """
import math
result = math.sqrt(16) + 2
print(f"计算结果: {result}")
"""
    
    print("\n执行测试代码:")
    print(test_code)
    
    try:
        result = python_executor.run(test_code)
        assert "计算结果: 6.0" in result
        print("\n测试成功!")
    except Exception as e:
        print(f"\n执行失败: {str(e)}")

if __name__ == "__main__":
    test_python_executor() 
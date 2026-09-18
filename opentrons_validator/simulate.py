#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Opentrons脚本模拟器
用法: python simulate.py <script_file>
"""
import sys
import os

# 添加backend目录到路径 - 从opentrons_validator文件夹向上一级再进入backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from opentrons_utils import run_opentrons_simulation

def main():
    if len(sys.argv) != 2:
        print("用法: python simulate.py <script_file>")
        print("示例: python simulate.py ../论文中要用的实验脚本案例/Bradford_proteinassay.py")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    # 如果是相对路径，基于当前工作目录解析，而不是脚本所在目录
    if not os.path.isabs(script_path):
        script_path = os.path.abspath(script_path)
    
    if not os.path.exists(script_path):
        print(f"错误: 文件 '{script_path}' 不存在")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"尝试访问的文件: {script_path}")
        sys.exit(1)
    
    print(f"正在模拟脚本: {os.path.basename(script_path)}")
    print("=" * 50)
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        result = run_opentrons_simulation(code, return_structured=True)
        
        if result['success']:
            print("✅ 模拟成功!")
            if result['has_warnings']:
                print("⚠️  有警告信息:")
                print(result['error_details'])
        else:
            print("❌ 模拟失败!")
            print("错误详情:")
            print(result['error_details'])
            if result['recommendations']:
                print("\n修复建议:")
                for rec in result['recommendations']:
                    print(rec)
            sys.exit(1)
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
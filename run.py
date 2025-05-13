#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Opentrons AI 协议生成器启动脚本
"""
import os
import sys
import subprocess
import importlib.util

def check_module_installed(module_name):
    """检查模块是否已安装"""
    return importlib.util.find_spec(module_name) is not None

def check_command_exists(command):
    """检查命令是否存在"""
    try:
        subprocess.run([command, "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE,
                      check=False)
        return True
    except (FileNotFoundError, subprocess.SubprocessError):
        return False

def main():
    """主函数"""
    print("\n=== Opentrons AI 协议生成器 ===\n")
    
    # 检查必要的依赖
    missing_deps = []
    if not check_module_installed("streamlit"):
        missing_deps.append("streamlit")

    # 显示选项
    print("请选择运行模式:")
    print("1. 命令行版本 (main.py)")
    print("2. Streamlit Web界面版本 (streamlit_app.py)")
    print("3. 安装依赖")
    print("q. 退出")
    
    choice = input("\n请输入选项 [1/2/3/q]: ").strip().lower()
    
    if choice == "1" or choice == "":
        print("\n启动命令行版本...")
        try:
            subprocess.run([sys.executable, "main.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"运行出错: {e}")
        except FileNotFoundError:
            print("错误: main.py 文件不存在!")
    
    elif choice == "2":
        if not check_module_installed("streamlit"):
            print("\n错误: 未安装 streamlit 模块。请先选择选项 3 安装依赖。")
            return
            
        print("\n启动 Streamlit Web界面...")
        try:
            subprocess.run(["streamlit", "run", "streamlit_app.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"运行出错: {e}")
        except FileNotFoundError:
            print("错误: streamlit 命令不可用。请确保正确安装了 streamlit。")
    
    elif choice == "3":
        print("\n安装依赖...")
        dependencies = ["streamlit>=1.30.0"]
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + dependencies, check=True)
            print("\n依赖安装完成！请重新运行此脚本。")
        except subprocess.CalledProcessError as e:
            print(f"安装出错: {e}")
    
    elif choice == "q":
        print("\n退出程序...")
    
    else:
        print("\n无效选项，请重新运行并选择正确选项。")

if __name__ == "__main__":
    main() 
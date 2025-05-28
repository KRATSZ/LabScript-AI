#!/usr/bin/env python3
"""
Opentrons AI Protocol Generator - 主启动脚本
"""

import sys
import os
import argparse

# 指定Python解释器路径
PYTHON_EXE = "C:/Python313/python.exe"

def setup_paths():
    """设置Python路径"""
    # 添加backend目录到Python路径
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    return backend_path

def start_api_server():
    """启动API服务器"""
    print("🚀 启动Opentrons AI Protocol Generator API服务器...")
    
    backend_path = setup_paths()
    print(f"📁 Backend路径: {backend_path}")
    print(f"🐍 Python解释器: {PYTHON_EXE}")
    
    try:
        import uvicorn
        from api_server import app
        
        print("📡 服务器配置:")
        print("   - 主机: 0.0.0.0")
        print("   - 端口: 8000")
        print("   - API文档: http://localhost:8000/docs")
        print("   - 健康检查: http://localhost:8000/")
        print()
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def run_tests():
    """运行测试"""
    print("🧪 运行测试套件...")
    print(f"🐍 使用Python解释器: {PYTHON_EXE}")
    
    setup_paths()
    
    try:
        import subprocess
        result = subprocess.run([
            PYTHON_EXE, "-m", "pytest", "tests/", "-v"
        ], cwd=os.path.dirname(__file__))
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"❌ Python解释器未找到: {PYTHON_EXE}")
        print("请检查Python安装路径或安装pytest: pip install pytest")
        sys.exit(1)

def show_status():
    """显示项目状态"""
    print("📊 Opentrons AI Protocol Generator 状态")
    print("=" * 50)
    
    backend_path = setup_paths()
    
    # 检查Python解释器
    print("🐍 Python解释器:")
    if os.path.exists(PYTHON_EXE):
        print(f"   ✅ {PYTHON_EXE}")
        try:
            import subprocess
            result = subprocess.run([PYTHON_EXE, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   📋 版本: {result.stdout.strip()}")
        except:
            pass
    else:
        print(f"   ❌ {PYTHON_EXE} (未找到)")
    
    # 检查核心文件
    core_files = [
        'api_server.py',
        'langchain_agent.py', 
        'opentrons_utils.py',
        'config.py'
    ]
    
    print("\n📁 核心文件:")
    for file in core_files:
        file_path = os.path.join(backend_path, file)
        status = "✅" if os.path.exists(file_path) else "❌"
        print(f"   {status} {file}")
    
    # 检查目录结构
    directories = ['backend', 'tests', 'docs', 'scripts', 'labscriptAI-frontend']
    print("\n📂 目录结构:")
    for dir_name in directories:
        dir_path = os.path.join(os.path.dirname(__file__), dir_name)
        status = "✅" if os.path.exists(dir_path) else "❌"
        print(f"   {status} {dir_name}/")
    
    # 检查依赖
    print("\n📦 依赖检查:")
    dependencies = ['fastapi', 'uvicorn', 'langchain', 'opentrons']
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Opentrons AI Protocol Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  {PYTHON_EXE} main.py                    # 启动API服务器
  {PYTHON_EXE} main.py --test            # 运行测试
  {PYTHON_EXE} main.py --status          # 显示项目状态
        """
    )
    
    parser.add_argument(
        '--test', 
        action='store_true',
        help='运行测试套件'
    )
    
    parser.add_argument(
        '--status',
        action='store_true', 
        help='显示项目状态'
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    elif args.status:
        show_status()
    else:
        start_api_server()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Opentrons AI Protocol Generator - 主启动脚本
"""

import sys
import os
import argparse

def setup_paths():
    """设置Python路径"""
    # 添加backend目录到Python路径
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    return backend_path

def get_python_executable():
    """获取当前Python解释器路径"""
    return sys.executable

def start_api_server():
    """启动API服务器"""
    print("🚀 启动Opentrons AI Protocol Generator API服务器...")
    
    backend_path = setup_paths()
    python_exe = get_python_executable()
    print(f"📁 Backend路径: {backend_path}")
    print(f"🐍 Python解释器: {python_exe}")
    
    try:
        import uvicorn
        from api_server import app
        from config import debug, server_host, server_port

        display_host = "localhost" if server_host in {"0.0.0.0", "::"} else server_host
        
        print("📡 服务器配置:")
        print(f"   - 主机: {server_host}")
        print(f"   - 端口: {server_port}")
        print(f"   - API文档: http://{display_host}:{server_port}/docs")
        print(f"   - 健康检查: http://{display_host}:{server_port}/")
        print()
        
        uvicorn.run(
            app,
            host=server_host,
            port=server_port,
            reload=False,
            log_level="debug" if debug else "info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def run_tests():
    """运行测试"""
    print("🧪 运行测试套件...")
    python_exe = get_python_executable()
    print(f"🐍 使用Python解释器: {python_exe}")
    
    setup_paths()
    
    # 检查是否安装了 pytest
    try:
        import pytest
    except ImportError:
        print("❌ pytest 未安装，请运行: uv pip install -e \".[dev]\"")
        sys.exit(1)
    
    try:
        import subprocess
        result = subprocess.run([
            python_exe, "-m", "pytest", "tests/", "-v"
        ], cwd=os.path.dirname(__file__))
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        sys.exit(1)

def show_status():
    """显示项目状态"""
    print("📊 Opentrons AI Protocol Generator 状态")
    print("=" * 50)
    
    backend_path = setup_paths()
    python_exe = get_python_executable()
    
    # 检查Python解释器
    print("🐍 Python解释器:")
    print(f"   ✅ {python_exe}")
    try:
        import subprocess
        result = subprocess.run([python_exe, "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   📋 版本: {result.stdout.strip()}")
    except:
        pass
    
    # 检查 UV 环境
    print("\n🔧 UV 环境:")
    import shutil
    if shutil.which("uv"):
        print("   ✅ UV 已安装")
        venv_path = os.path.join(os.path.dirname(__file__), '.venv')
        if os.path.exists(venv_path):
            print("   ✅ .venv 虚拟环境存在")
        else:
            print("   ❌ .venv 虚拟环境不存在")
    else:
        print("   ❌ UV 未安装")
    
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
    dependencies = ['fastapi', 'uvicorn', 'langchain', 'opentrons', 'mcp']
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
  python main.py                    # 启动API服务器
  python main.py --test            # 运行测试
  python main.py --status          # 显示项目状态
  
UV 使用示例:
  uv run python main.py            # 使用UV运行
  uv run pytest tests/             # 使用UV运行测试
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

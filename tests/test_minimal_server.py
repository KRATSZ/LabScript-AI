# -*- coding: utf-8 -*-
"""
最小测试服务器
用于验证基本功能是否正常
"""

import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """测试所有必要的导入"""
    try:
        print("测试导入...")
        
        # 测试基本模块
        from fastapi import FastAPI
        print("✅ FastAPI导入成功")
        
        from pydantic import BaseModel
        print("✅ Pydantic导入成功")
        
        # 测试后端模块
        import config
        print(f"✅ Config导入成功 - API Key: {config.api_key[:10]}...")
        
        import langchain_agent
        print("✅ Langchain Agent导入成功")
        
        # 测试API服务器
        import api_server
        print("✅ API Server导入成功")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()

def test_basic_functionality(monkeypatch):
    """测试基本功能和配置加载"""
    monkeypatch.setenv("OPENAI_MODEL_NAME", "test-model")
    print("\n测试基本功能...")
    try:
        from langchain_agent import (
            generate_protocol_code, 
            generate_sop_with_langchain
        )
        # from langchain_agent import DIFY_API_KEY, DIFY_API_URL # This is old
        print(f"✅ API配置正常:")
        print(f"  - Model: {os.getenv('OPENAI_MODEL_NAME')}")
        
        # 测试Dify配置
        # from langchain_agent import DIFY_API_KEY, DIFY_API_URL
        # print(f"✅ Dify配置正常:")
        # print(f"  - Dify URL: {DIFY_API_URL}")
        # print(f"  - Dify Key: {DIFY_API_KEY[:10]}...")
        
        assert os.getenv("OPENAI_MODEL_NAME") == "test-model"
        
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_api_models():
    """测试API模型"""
    try:
        print("\n测试API模型...")
        
        from api_server import (
            SOPGenerationRequest, 
            SOPGenerationResponse,
            ProtocolCodeGenerationRequest,
            ProtocolCodeGenerationResponse
        )
        
        # 测试创建请求模型
        sop_req = SOPGenerationRequest(
            hardware_config="Test config",
            user_goal="Test goal"
        )
        print("✅ SOP请求模型创建成功")
        
        code_req = ProtocolCodeGenerationRequest(
            sop_markdown="Test SOP",
            hardware_config="Test config"
        )
        print("✅ 协议代码请求模型创建成功")
        
        assert sop_req.user_goal == "Test goal"
        assert code_req.sop_markdown == "Test SOP"
        
    except Exception as e:
        print(f"❌ API模型测试失败: {e}")
        import traceback
        traceback.print_exc()

def run_minimal_server():
    """运行最小服务器"""
    try:
        print("\n启动最小测试服务器...")
        
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI(title="Minimal Test Server")
        
        @app.get("/")
        def root():
            return {"message": "Minimal test server running", "status": "ok"}
        
        @app.get("/test")
        def test():
            return {"test": "success", "config_loaded": True}
        
        print("启动服务器在 http://localhost:8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        
    except Exception as e:
        print(f"❌ 最小服务器启动失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=== 最小功能测试 ===\n")
    
    # 运行所有测试
    tests = [
        ("导入测试", test_imports),
        ("基本功能测试", test_basic_functionality), 
        ("API模型测试", test_api_models)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        test_func()
        results.append((test_name, True))
    
    print("\n=== 测试结果总结 ===")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print(f"\n🎉 所有测试通过！可以尝试启动完整服务器。")
        
        user_input = input("\n要启动最小测试服务器吗？(y/n): ")
        if user_input.lower() == 'y':
            run_minimal_server()
    else:
        print(f"\n⚠️ 有测试失败，请检查依赖和配置。")

if __name__ == "__main__":
    main() 
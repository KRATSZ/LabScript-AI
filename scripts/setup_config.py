#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabscriptAI 配置设置脚本
帮助用户快速设置环境变量和配置文件
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

def get_project_root() -> Path:
    """获取项目根目录"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "setup.py").exists():
            return current
        current = current.parent
    return Path.cwd()

def create_env_file(config: Dict[str, Any], env_path: Path):
    """创建 .env 文件"""
    env_content = []
    env_content.append("# LabscriptAI 环境变量配置")
    env_content.append("# 由 setup_config.py 自动生成")
    env_content.append("")
    
    # 应用配置
    env_content.append("# 应用环境配置")
    env_content.append(f"LABSCRIPTAI_ENVIRONMENT={config.get('environment', 'development')}")
    env_content.append("")
    
    # API 配置
    env_content.append("# 主要 LLM API 配置")
    api_config = config.get('api', {})
    env_content.append(f"LABSCRIPTAI_API_KEY={api_config.get('api_key', '')}")
    env_content.append(f"LABSCRIPTAI_BASE_URL={api_config.get('base_url', 'https://api.openai.com/v1')}")
    env_content.append(f"LABSCRIPTAI_MODEL_NAME={api_config.get('model_name', 'gpt-4')}")
    env_content.append("")
    
    # DeepSeek 配置
    env_content.append("# DeepSeek API 配置")
    env_content.append(f"LABSCRIPTAI_DEEPSEEK_API_KEY={api_config.get('deepseek_api_key', '')}")
    env_content.append(f"LABSCRIPTAI_DEEPSEEK_BASE_URL={api_config.get('deepseek_base_url', 'https://api.deepseek.com/v1')}")
    env_content.append(f"LABSCRIPTAI_DEEPSEEK_MODEL={api_config.get('deepseek_model', 'deepseek-chat')}")
    env_content.append("")
    
    # 服务器配置
    env_content.append("# 服务器配置")
    server_config = config.get('server', {})
    env_content.append(f"LABSCRIPTAI_SERVER_HOST={server_config.get('host', '0.0.0.0')}")
    env_content.append(f"LABSCRIPTAI_SERVER_PORT={server_config.get('port', 8000)}")
    env_content.append(f"LABSCRIPTAI_DEBUG={str(server_config.get('debug', False)).lower()}")
    env_content.append("")
    
    # 数据库配置
    env_content.append("# 数据库配置")
    db_config = config.get('database', {})
    env_content.append(f"LABSCRIPTAI_DATABASE_URL={db_config.get('url', 'sqlite:///./labscriptai.db')}")
    env_content.append("")
    
    # 日志配置
    env_content.append("# 日志配置")
    log_config = config.get('logging', {})
    env_content.append(f"LABSCRIPTAI_LOG_LEVEL={log_config.get('level', 'INFO')}")
    if log_config.get('file_path'):
        env_content.append(f"LABSCRIPTAI_LOG_FILE_PATH={log_config['file_path']}")
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content))
    
    print(f"✅ 环境变量文件已创建: {env_path}")

def interactive_setup():
    """交互式配置设置"""
    print("🚀 LabscriptAI 配置设置向导")
    print("=" * 50)
    
    config = {}
    
    # 环境选择
    print("\n1. 选择运行环境:")
    print("   1) development (开发环境)")
    print("   2) production (生产环境)")
    print("   3) testing (测试环境)")
    
    env_choice = input("请选择环境 (1-3) [1]: ").strip() or "1"
    env_map = {"1": "development", "2": "production", "3": "testing"}
    config['environment'] = env_map.get(env_choice, "development")
    
    # API 配置
    print("\n2. API 配置:")
    api_config = {}
    
    api_key = input("请输入主要 API 密钥 (OpenAI 兼容): ").strip()
    if api_key:
        api_config['api_key'] = api_key
    
    base_url = input("请输入 API 基础URL [https://api.openai.com/v1]: ").strip()
    api_config['base_url'] = base_url or "https://api.openai.com/v1"
    
    model_name = input("请输入模型名称 [gpt-4]: ").strip()
    api_config['model_name'] = model_name or "gpt-4"
    
    # DeepSeek 配置
    print("\n3. DeepSeek API 配置 (用于快速任务，可选):")
    deepseek_key = input("请输入 DeepSeek API 密钥 (可选): ").strip()
    if deepseek_key:
        api_config['deepseek_api_key'] = deepseek_key
        
        deepseek_url = input("请输入 DeepSeek API URL [https://api.deepseek.com/v1]: ").strip()
        api_config['deepseek_base_url'] = deepseek_url or "https://api.deepseek.com/v1"
        
        deepseek_model = input("请输入 DeepSeek 模型名称 [deepseek-chat]: ").strip()
        api_config['deepseek_model'] = deepseek_model or "deepseek-chat"
    
    config['api'] = api_config
    
    # 服务器配置
    print("\n4. 服务器配置:")
    server_config = {}
    
    port = input("请输入服务器端口 [8000]: ").strip()
    try:
        server_config['port'] = int(port) if port else 8000
    except ValueError:
        server_config['port'] = 8000
    
    debug = input("是否启用调试模式? (y/N): ").strip().lower()
    server_config['debug'] = debug in ['y', 'yes', 'true']
    
    config['server'] = server_config
    
    # 数据库配置
    print("\n5. 数据库配置:")
    print("   1) SQLite (默认，适合开发和小型部署)")
    print("   2) PostgreSQL (推荐生产环境)")
    print("   3) MySQL")
    print("   4) 自定义")
    
    db_choice = input("请选择数据库类型 (1-4) [1]: ").strip() or "1"
    
    db_config = {}
    if db_choice == "1":
        db_config['url'] = "sqlite:///./labscriptai.db"
    elif db_choice == "2":
        host = input("PostgreSQL 主机 [localhost]: ").strip() or "localhost"
        port = input("PostgreSQL 端口 [5432]: ").strip() or "5432"
        user = input("PostgreSQL 用户名: ").strip()
        password = input("PostgreSQL 密码: ").strip()
        database = input("PostgreSQL 数据库名 [labscriptai]: ").strip() or "labscriptai"
        db_config['url'] = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    elif db_choice == "3":
        host = input("MySQL 主机 [localhost]: ").strip() or "localhost"
        port = input("MySQL 端口 [3306]: ").strip() or "3306"
        user = input("MySQL 用户名: ").strip()
        password = input("MySQL 密码: ").strip()
        database = input("MySQL 数据库名 [labscriptai]: ").strip() or "labscriptai"
        db_config['url'] = f"mysql://{user}:{password}@{host}:{port}/{database}"
    else:
        custom_url = input("请输入自定义数据库URL: ").strip()
        db_config['url'] = custom_url
    
    config['database'] = db_config
    
    # 日志配置
    print("\n6. 日志配置:")
    log_config = {}
    
    log_level = input("请选择日志级别 (DEBUG/INFO/WARNING/ERROR) [INFO]: ").strip().upper()
    log_config['level'] = log_level if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR'] else 'INFO'
    
    log_file = input("日志文件路径 (留空表示不写入文件): ").strip()
    if log_file:
        log_config['file_path'] = log_file
    
    config['logging'] = log_config
    
    return config

def main():
    """主函数"""
    project_root = get_project_root()
    
    print(f"项目根目录: {project_root}")
    
    # 检查是否已存在配置文件
    env_file = project_root / ".env"
    config_file = project_root / "config.json"
    
    if env_file.exists() or config_file.exists():
        print("\n⚠️  检测到已存在的配置文件:")
        if env_file.exists():
            print(f"   - {env_file}")
        if config_file.exists():
            print(f"   - {config_file}")
        
        overwrite = input("\n是否覆盖现有配置? (y/N): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("配置设置已取消。")
            return
    
    # 选择配置方式
    print("\n请选择配置方式:")
    print("1) 交互式配置 (推荐)")
    print("2) 复制示例文件")
    print("3) 退出")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == "1":
        # 交互式配置
        config = interactive_setup()
        
        # 创建 .env 文件
        create_env_file(config, env_file)
        
        # 询问是否也创建 JSON 配置文件
        create_json = input("\n是否也创建 JSON 配置文件? (y/N): ").strip().lower()
        if create_json in ['y', 'yes']:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON 配置文件已创建: {config_file}")
        
    elif choice == "2":
        # 复制示例文件
        example_env = project_root / ".env.example"
        example_config = project_root / "config.json.example"
        
        if example_env.exists():
            shutil.copy2(example_env, env_file)
            print(f"✅ 已复制示例环境文件: {env_file}")
            print("   请编辑此文件并填入实际的配置值。")
        
        if example_config.exists():
            shutil.copy2(example_config, config_file)
            print(f"✅ 已复制示例配置文件: {config_file}")
            print("   请编辑此文件并填入实际的配置值。")
    
    else:
        print("配置设置已取消。")
        return
    
    print("\n🎉 配置设置完成!")
    print("\n下一步:")
    print("1. 检查并编辑配置文件中的值")
    print("2. 运行应用程序: python -m backend.api_server")
    print("3. 访问 http://localhost:8000 查看API文档")

if __name__ == "__main__":
    main()
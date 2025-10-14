# -*- coding: utf-8 -*-
"""
统一配置管理模块
支持环境变量、配置文件和默认值的层级配置管理
"""

import os
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API相关配置"""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_retries: int = 3
    request_timeout: int = 30
    
    # DeepSeek API配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    
    # 其他API配置
    anthropic_api_key: str = ""
    google_api_key: str = ""
    figshare_token: str = ""  # 添加Figshare token支持


@dataclass
class ServerConfig:
    """服务器配置类"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1
    
    # CORS配置
    cors_origins: list = field(default_factory=lambda: ["*"])
    cors_methods: list = field(default_factory=lambda: ["*"])
    cors_headers: list = field(default_factory=lambda: ["*"])


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    url: str = "sqlite:///./labscriptai.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class LoggingConfig:
    """日志配置类"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class AppConfig:
    """应用程序总配置类"""
    # 环境配置
    environment: str = "development"  # development, production, testing
    
    # 子配置
    api: APIConfig = field(default_factory=APIConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # 其他配置
    secret_key: str = "your-secret-key-change-in-production"
    jwt_secret: str = "your-jwt-secret-change-in-production"
    jwt_expire_hours: int = 24


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None, env_prefix: str = "LABSCRIPTAI_"):
        self.config_file = config_file
        self.env_prefix = env_prefix
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """加载配置，优先级：环境变量 > 配置文件 > 默认值"""
        if self._config is not None:
            return self._config
        
        # 1. 从默认值开始
        config = AppConfig()
        
        # 2. 从配置文件加载（如果存在）
        if self.config_file and os.path.exists(self.config_file):
            try:
                config = self._load_from_file(config)
                logger.info(f"配置文件已加载: {self.config_file}")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        # 3. 从环境变量覆盖
        config = self._load_from_env(config)
        
        # 4. 验证配置
        self._validate_config(config)
        
        self._config = config
        return config
    
    def _load_from_file(self, config: AppConfig) -> AppConfig:
        """从配置文件加载"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 更新API配置
        if 'api' in data:
            api_data = data['api']
            for key, value in api_data.items():
                if hasattr(config.api, key):
                    setattr(config.api, key, value)
        
        # 更新服务器配置
        if 'server' in data:
            server_data = data['server']
            for key, value in server_data.items():
                if hasattr(config.server, key):
                    setattr(config.server, key, value)
        
        # 更新数据库配置
        if 'database' in data:
            db_data = data['database']
            for key, value in db_data.items():
                if hasattr(config.database, key):
                    setattr(config.database, key, value)
        
        # 更新日志配置
        if 'logging' in data:
            log_data = data['logging']
            for key, value in log_data.items():
                if hasattr(config.logging, key):
                    setattr(config.logging, key, value)
        
        # 更新应用配置
        for key in ['environment', 'secret_key', 'jwt_secret', 'jwt_expire_hours']:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    def _load_from_env(self, config: AppConfig) -> AppConfig:
        """从环境变量加载"""
        # API配置
        config.api.api_key = self._get_env('API_KEY', config.api.api_key)
        config.api.base_url = self._get_env('BASE_URL', config.api.base_url)
        config.api.model_name = self._get_env('MODEL_NAME', config.api.model_name)
        config.api.temperature = float(self._get_env('TEMPERATURE', str(config.api.temperature)))
        config.api.max_retries = int(self._get_env('MAX_RETRIES', str(config.api.max_retries)))
        config.api.request_timeout = int(self._get_env('REQUEST_TIMEOUT', str(config.api.request_timeout)))
        
        # DeepSeek配置
        config.api.deepseek_api_key = self._get_env('DEEPSEEK_API_KEY', config.api.deepseek_api_key)
        config.api.deepseek_base_url = self._get_env('DEEPSEEK_BASE_URL', config.api.deepseek_base_url)
        config.api.deepseek_model = self._get_env('DEEPSEEK_MODEL', config.api.deepseek_model)
        
        # 其他API配置
        config.api.anthropic_api_key = self._get_env('ANTHROPIC_API_KEY', config.api.anthropic_api_key)
        config.api.google_api_key = self._get_env('GOOGLE_API_KEY', config.api.google_api_key)
        config.api.figshare_token = self._get_env('FIGSHARE_TOKEN', config.api.figshare_token)
        
        # 服务器配置
        config.server.host = self._get_env('SERVER_HOST', config.server.host)
        config.server.port = int(self._get_env('SERVER_PORT', str(config.server.port)))
        config.server.debug = self._get_env('DEBUG', str(config.server.debug)).lower() == 'true'
        config.server.reload = self._get_env('RELOAD', str(config.server.reload)).lower() == 'true'
        config.server.workers = int(self._get_env('WORKERS', str(config.server.workers)))
        
        # 数据库配置
        config.database.url = self._get_env('DATABASE_URL', config.database.url)
        config.database.echo = self._get_env('DATABASE_ECHO', str(config.database.echo)).lower() == 'true'
        
        # 应用配置
        config.environment = self._get_env('ENVIRONMENT', config.environment)
        config.secret_key = self._get_env('SECRET_KEY', config.secret_key)
        config.jwt_secret = self._get_env('JWT_SECRET', config.jwt_secret)
        config.jwt_expire_hours = int(self._get_env('JWT_EXPIRE_HOURS', str(config.jwt_expire_hours)))
        
        # 日志配置
        config.logging.level = self._get_env('LOG_LEVEL', config.logging.level)
        config.logging.file_path = self._get_env('LOG_FILE_PATH', config.logging.file_path)
        
        return config
    
    def _get_env(self, key: str, default: str) -> str:
        """获取环境变量"""
        return os.getenv(f"{self.env_prefix}{key}", default)
    
    def _validate_config(self, config: AppConfig):
        """验证配置"""
        # 验证必需的API密钥
        if not config.api.api_key:
            logger.warning("主API密钥未设置")
        
        # 验证URL格式
        if not config.api.base_url.startswith(('http://', 'https://')):
            raise ValueError(f"无效的API基础URL: {config.api.base_url}")
        
        # 验证端口范围
        if not (1 <= config.server.port <= 65535):
            raise ValueError(f"无效的端口号: {config.server.port}")
        
        # 验证环境
        if config.environment not in ['development', 'production', 'testing']:
            logger.warning(f"未知的环境类型: {config.environment}")
    
    def save_config_template(self, file_path: str):
        """保存配置文件模板"""
        template = {
            "environment": "development",
            "secret_key": "your-secret-key-change-in-production",
            "jwt_secret": "your-jwt-secret-change-in-production",
            "jwt_expire_hours": 24,
            "api": {
                "api_key": "your-openai-api-key",
                "base_url": "https://api.openai.com/v1",
                "model_name": "gpt-4",
                "temperature": 0.0,
                "max_retries": 2,
                "request_timeout": 60,
                "deepseek_api_key": "your-deepseek-api-key",
                "deepseek_base_url": "https://api.deepseek.com/v1",
                "deepseek_model": "deepseek-chat",
                "anthropic_api_key": "",
                "google_api_key": ""
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "reload": False,
                "workers": 1,
                "cors_origins": ["*"],
                "cors_methods": ["*"],
                "cors_headers": ["*"]
            },
            "database": {
                "url": "sqlite:///./labscriptai.db",
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": null,
                "max_file_size": 10485760,
                "backup_count": 5
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        logger.info(f"配置模板已保存到: {file_path}")


# 全局配置管理器实例
config_manager = ConfigManager(
    config_file=os.getenv('LABSCRIPTAI_CONFIG_FILE', 'config.json'),
    env_prefix='LABSCRIPTAI_'
)

# 获取配置的便捷函数
def get_config() -> AppConfig:
    """获取应用配置"""
    return config_manager.load_config()


# 向后兼容的配置变量（保持现有代码可用）
def _load_legacy_config():
    """加载传统配置变量以保持向后兼容"""
    config = get_config()
    
    # 导出传统变量名
    globals().update({
        'api_key': config.api.api_key,
        'base_url': config.api.base_url,
        'model_name': config.api.model_name,
        'DEEPSEEK_API_KEY': config.api.deepseek_api_key,
        'DEEPSEEK_BASE_URL': config.api.deepseek_base_url,
        'DEEPSEEK_INTENT_MODEL': config.api.deepseek_model,
    })


# 初始化传统配置变量
_load_legacy_config()
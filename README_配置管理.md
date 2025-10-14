# LabscriptAI 配置管理快速指南

## 快速开始

### 方式一：自动配置（推荐）
```bash
# 运行配置脚本
python3 scripts/setup_config.py
```

### 方式二：手动配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，填入你的API密钥
nano .env
```

## 必需配置项

### LLM API 配置
```bash
# OpenAI 配置（主要API）
LABSCRIPTAI_API_KEY=your_openai_api_key_here
LABSCRIPTAI_BASE_URL=https://api.openai.com/v1
LABSCRIPTAI_MODEL_NAME=gpt-4

# DeepSeek 配置（用于意图识别）
LABSCRIPTAI_DEEPSEEK_API_KEY=your_deepseek_key_here
```

## 环境配置示例

### 开发环境
```bash
LABSCRIPTAI_ENVIRONMENT=development
LABSCRIPTAI_DEBUG=true
LABSCRIPTAI_LOG_LEVEL=DEBUG
```

### 生产环境
```bash
LABSCRIPTAI_ENVIRONMENT=production
LABSCRIPTAI_DEBUG=false
LABSCRIPTAI_LOG_LEVEL=INFO
LABSCRIPTAI_DATABASE_URL=postgresql://user:pass@localhost:5432/labscriptai
```

## 支持的API提供商

- **OpenAI**: 设置 `LABSCRIPTAI_API_KEY` 和 `LABSCRIPTAI_BASE_URL`
- **DeepSeek**: 设置 `LABSCRIPTAI_DEEPSEEK_API_KEY`
- **Azure OpenAI**: 设置相应的 `LABSCRIPTAI_BASE_URL`
- **本地模型**: 设置本地API的 `LABSCRIPTAI_BASE_URL`

## 配置优先级

1. 环境变量 (最高优先级)
2. `config.json` 文件
3. 默认值 (最低优先级)

## 更多信息

- 详细配置指南: [docs/配置管理指南.md](docs/配置管理指南.md)
- 常见问题: 查看文档中的故障排除部分
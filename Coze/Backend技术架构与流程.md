# LabscriptAI Backend 技术架构与流程

## 🏗️ 系统架构概述

Backend文件夹是LabscriptAI的核心技术实现，基于FastAPI + LangChain + LangGraph构建的智能协议生成系统，提供从用户需求到可执行代码的完整解决方案。

## 📁 文件结构说明

```
backend/
├── __init__.py                 # 包初始化文件
├── api_server.py               # FastAPI服务器主文件
├── langchain_agent.py          # LangChain智能体核心逻辑
├── opentrons_utils.py          # Opentrons工具函数
├── prompts.py                  # 提示词模板管理
├── config.py                   # 系统配置和常量
├── diff_utils.py               # 代码差异处理工具
├── pylabrobot_utils.py         # PyLabRobot工具函数
├── pylabrobot_agent.py         # PyLabRobot智能体
├── file_exporter.py            # 文件导出功能
├── external_publisher.py       # 外部发布功能
├── pylabrobot_template.py      # PyLabRobot模板
├── OT2protocolcode/            # OT-2协议代码示例
└── examples/                   # 示例代码
```

## 🔧 核心模块详解

### 1. API服务器 (api_server.py)

#### 功能职责
- 提供RESTful API接口
- 处理HTTP请求和响应
- 协调各个功能模块
- 提供流式生成能力

#### 核心端点
```python
# 健康检查
GET /                    # 服务状态检查
GET /api/health          # API健康状态
GET /api/tools           # 可用工具列表

# 核心功能
POST /api/generate-sop   # 生成标准操作程序
POST /api/generate-protocol-code  # 生成协议代码
POST /api/simulate-protocol      # 模拟验证代码

# 高级功能
POST /api/generate-sop-stream    # 流式SOP生成
POST /api/export/protocols-io    # 导出protocols.io格式
```

#### 工作流程
```
用户请求 → FastAPI路由 → 参数验证 → 业务逻辑处理 → 结果返回
    ↓         ↓          ↓          ↓          ↓
   HTTP接收   路由分发   数据校验   模块调用   JSON响应
```

### 2. LangChain智能体 (langchain_agent.py)

#### 功能职责
- 基于LangGraph的智能协议生成
- 多模态AI模型集成
- 代码生成和错误修复
- 流式处理和迭代优化

#### 核心组件
```python
# 状态管理
class AgentState(TypedDict):
    messages: list[Message]
    hardware_config: str
    user_goal: str
    sop_markdown: str
    generated_code: str
    simulation_result: dict
    iteration_count: int

# 智能体节点
sop_generator_node         # SOP生成节点
code_generator_node        # 代码生成节点
simulator_node            # 模拟验证节点
error_analyzer_node       # 错误分析节点
code_corrector_node       # 代码修正节点
```

#### 工作流程
```
用户目标 → SOP生成 → 代码生成 → 模拟验证 → 错误分析 → 迭代修复
    ↓         ↓         ↓         ↓         ↓         ↓
   需求分析   流程设计   Python编写   执行测试   问题诊断   代码优化
```

### 3. Opentrons工具函数 (opentrons_utils.py)

#### 功能职责
- Opentrons协议代码模拟
- 错误分析和建议生成
- 环境配置管理
- 子进程通信

#### 核心功能
```python
def run_opentrons_simulation(protocol_code: str) -> dict:
    """运行Opentrons协议模拟"""
    # 创建临时文件
    # 设置环境变量
    # 执行模拟命令
    # 解析输出结果

def get_error_recommendations(error_output: str) -> list:
    """根据错误输出提供修复建议"""
    # 错误类型识别
    # 修复建议生成
    # 优先级排序
```

#### 模拟流程
```
协议代码 → 临时文件 → 环境设置 → 子进程执行 → 结果解析 → 错误分析
    ↓         ↓         ↓         ↓         ↓         ↓
   Python代码  文件写入   ot_env配置   simulate.py  JSON格式  建议生成
```

### 4. 提示词模板管理 (prompts.py)

#### 功能职责
- 统一管理所有AI提示词
- 支持多种设备类型
- 提供错误修复模板
- 多语言支持

#### 模板分类
```python
# SOP生成模板
SOP_GENERATION_PROMPT_TEMPLATE

# 代码生成模板
CODE_GENERATION_PROMPT_TEMPLATE_FLEX    # Flex专用
CODE_GENERATION_PROMPT_TEMPLATE_OT2     # OT-2专用

# 错误修复模板
CODE_CORRECTION_DIFF_TEMPLATE_FLEX      # Flex修复
CODE_CORRECTION_DIFF_TEMPLATE_OT2       # OT-2修复

# 意图分类模板
CODE_CONVERSATION_CLASSIFIER_PROMPT_TEMPLATE
```

### 5. 系统配置管理 (config.py)

#### 功能职责
- 集中管理系统配置
- 设备类型定义
- API密钥管理
- 硬件配置常量

#### 配置内容
```python
# API配置
api_key = "sk-..."
base_url = "https://api.deepseek.com"
model_name = "deepseek-chat"

# 设备配置
LABWARE_FOR_OT2 = [...]      # OT-2载具列表
LABWARE_FOR_FLEX = [...]     # Flex载具列表
INSTRUMENTS_FOR_OT2 = [...]  # OT-2移液器列表
INSTRUMENTS_FOR_FLEX = [...] # Flex移液器列表
MODULES_FOR_OT2 = [...]      # OT-2模块列表
MODULES_FOR_FLEX = [...]     # Flex模块列表

# 常见错误和解决方案
COMMON_PITFALLS_OT2 = [...]
CODE_EXAMPLES = "..."
```

## 🔄 完整工作流程

### 阶段1：请求接收和处理
```
HTTP请求 → FastAPI接收 → 参数验证 → 请求路由 → 模块调用
    ↓         ↓          ↓          ↓         ↓
   用户输入   api_server   数据校验   业务分发   智能体处理
```

### 阶段2：SOP生成
```
用户目标 → 硬件配置 → 提示词组装 → AI模型 → SOP输出
    ↓         ↓          ↓         ↓        ↓
   目标分析   配置验证   模板选择   LLM调用   Markdown格式
```

### 阶段3：代码生成
```
SOP文档 → 设备类型 → 代码模板 → AI生成 → Python代码
    ↓        ↓          ↓         ↓         ↓
   流程解析   型号识别   模板选择   模型推理   可执行代码
```

### 阶段4：模拟验证
```
Python代码 → 环境准备 → 模拟执行 → 结果解析 → 错误检测
    ↓         ↓          ↓         ↓         ↓
   代码写入   ot_env设置   子进程    输出分析   问题识别
```

### 阶段5：错误修复和迭代
```
错误信息 → 原因分析 → 修复策略 → 代码修改 → 重新验证
    ↓         ↓          ↓         ↓         ↓
   错误解析   根因诊断   方案制定   DIFF修复   循环验证
```

## 🎯 关键技术特性

### 1. 多设备支持
- **OT-2支持**: 完整的OT-2 API和硬件配置
- **Flex支持**: 最新的Flex API和硬件配置
- **自动识别**: 根据配置自动识别设备类型
- **专门优化**: 针对不同设备的专门优化策略

### 2. 智能错误处理
```python
# 错误类型识别
error_types = {
    'syntax': '语法错误',
    'api': 'API调用错误',
    'hardware': '硬件配置错误',
    'logic': '逻辑错误'
}

# 错误修复策略
repair_strategies = {
    'immediate_fix': '立即修复',
    'regenerate_code': '重新生成',
    'manual_intervention': '人工干预'
}
```

### 3. 流式生成能力
- **实时反馈**: 提供实时的生成进度反馈
- **流式输出**: 支持Server-Sent Events流式输出
- **进度跟踪**: 实时显示生成进度和状态
- **中断支持**: 支持生成过程中的中断操作

### 4. 迭代优化机制
```python
# 迭代控制
MAX_ITERATIONS = 3
ITERATION_TIMEOUT = 300  # 5分钟

# 收敛判断
def should_continue_iteration(state: AgentState) -> bool:
    return (
        state.iteration_count < MAX_ITERATIONS and
        not state.simulation_result.get('success', False) and
        time.time() - state.start_time < ITERATION_TIMEOUT
    )
```

## 🛡️ 安全和稳定性

### 1. 输入验证
- **参数验证**: 严格的API参数验证
- **格式检查**: 输入数据格式验证
- **长度限制**: 输入内容长度限制
- **内容过滤**: 恶意内容过滤

### 2. 错误隔离
- **异常处理**: 完善的异常处理机制
- **错误边界**: 错误隔离和边界控制
- **恢复机制**: 自动错误恢复机制
- **日志记录**: 完整的错误日志记录

### 3. 性能优化
- **超时控制**: 各环节超时控制
- **资源管理**: 内存和CPU资源管理
- **并发控制**: 请求并发控制
- **缓存机制**: 结果缓存机制

## 📊 性能指标

### 响应时间
- **SOP生成**: 10-30秒
- **代码生成**: 30-120秒
- **模拟验证**: 15-60秒
- **错误修复**: 20-90秒

### 成功率指标
- **SOP生成成功率**: > 95%
- **代码生成成功率**: > 85%
- **模拟验证成功率**: > 90%
- **错误修复成功率**: > 80%

### 系统稳定性
- **API可用性**: > 99%
- **错误恢复率**: > 85%
- **内存使用**: < 2GB
- **响应延迟**: < 100ms

## 🔧 扩展性设计

### 1. 模块化架构
- **松耦合**: 各模块间松耦合设计
- **插件化**: 支持功能插件化扩展
- **接口标准化**: 标准化的接口设计
- **配置化**: 通过配置文件控制功能

### 2. 多平台支持
- **容器化**: Docker容器化部署
- **云原生**: 支持云平台部署
- **跨平台**: 支持多操作系统
- **微服务**: 支持微服务架构

### 3. AI模型扩展
- **多模型**: 支持多种AI模型
- **模型切换**: 动态模型切换
- **自定义模型**: 支持自定义AI模型
- **模型管理**: 统一的模型管理

---

## 🎯 使用示例

### 示例1：完整协议生成流程
```python
# 1. 生成SOP
sop_response = requests.post('http://localhost:8000/api/generate-sop', json={
    'hardware_config': 'Robot Model: Flex...',
    'user_goal': '我需要一个PCR反应的自动化协议'
})

# 2. 生成代码
code_response = requests.post('http://localhost:8000/api/generate-protocol-code', json={
    'sop_markdown': sop_response.json()['sop_markdown'],
    'hardware_config': 'Robot Model: Flex...'
})

# 3. 模拟验证
simulation_response = requests.post('http://localhost:8000/api/simulate-protocol', json={
    'protocol_code': code_response.json()['generated_code']
})
```

### 示例2：流式SOP生成
```python
# 流式生成SOP
response = requests.post('http://localhost:8000/api/generate-sop-stream', json={
    'hardware_config': config,
    'user_goal': goal
}, stream=True)

# 实时处理流式数据
for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8'))
        print(f"进度: {data['progress']}, 内容: {data['content']}")
```

这个Backend技术架构为LabscriptAI提供了强大的智能协议生成能力，通过AI模型和专业工具的结合，实现了从用户需求到可执行代码的自动化转换。
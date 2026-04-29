# 📚 API 接口与技术架构文档

## 🏗️ 技术架构概览

本项目采用 **双虚拟环境架构** 以解决核心库依赖冲突：

1.  **主应用环境 (`.venv`)**:
    *   运行 FastAPI, LangChain, LangGraph。
    *   处理业务逻辑、Prompt 工程、SOP 生成。
    *   **不包含** `opentrons` 库。

2.  **隔离环境 (`ot_env`)**:
    *   仅运行 Opentrons API 和模拟器。
    *   通过 `opentrons_utils.py` 中的 `subprocess` 调用进行通信。

### 技术栈
*   **Backend**: Python 3.11, FastAPI, LangGraph, Uvicorn
*   **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Monaco Editor
*   **AI Core**: LangChain, OpenAI API / Gemini API
*   **Robotics**: Opentrons API v2, PyLabRobot, pyFluent

---

## 🔗 API 端点说明

API 文档地址 (启动后端后访问):
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 核心接口

#### 1. SOP 生成 (`/api/generate-sop`)
- **Method**: `POST`
- **描述**: 基于自然语言目标和硬件配置，生成标准操作程序 (SOP) Markdown。
- **Input**: `hardware_config` (str), `user_goal` (str)

#### 2. 协议代码生成 (`/api/generate-protocol-code`)
- **Method**: `POST` (SSE Stream)
- **描述**: 生成可执行的 Python 协议代码。支持流式返回，实时推送 AI 的思考过程和模拟验证结果。
- **流程**: Code Generation -> Simulation -> Error Analysis -> Refactoring (Loop).

#### 3. 协议模拟 (`/api/simulate-protocol`)
- **Method**: `POST`
- **描述**: 调用本地模拟器验证代码。
- **Output**: `success` (bool), `raw_simulation_output` (str), `error_message` (str).

#### 4. PyLabRobot 模拟 (`/api/simulate-pylabrobot-protocol`)
- **Method**: `POST`
- **描述**: 针对 Hamilton/Tecan 等第三方平台的 PyLabRobot 代码模拟接口。

#### 5. 导出 (`/api/export/protocols-io`)
- **Method**: `POST`
- **描述**: 打包协议文件、SOP 和元数据为 ZIP，适配 protocols.io 格式。



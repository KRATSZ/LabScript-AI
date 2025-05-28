# Opentrons AI Protocol Generator
🧬 **智能化的Opentrons实验协议生成器**
通过自然语言描述实验需求，自动生成、验证和优化Opentrons机器人协议代码。
## 🆕 最新主要更新
### ✨ 功能与体验优化
1.  **代码生成流程与显示 (前端 `generate-code` 页面)**:
    *   **API模式**: 后端代码生成接口 (`/api/generate-protocol-code`) 已从旧版的SSE（服务器发送事件）彻底转换为同步HTTP请求。这意味着代码生成过程中的实时日志更新不再逐条显示，而是在整个生成过程（包括所有迭代）完成后，一次性将所有迭代日志返回给前端。
    *   **迭代日志显示**:
        *   后端 `ProtocolCodeGenerationResponse` Pydantic模型增加了 `iteration_logs: List[Dict[str, Any]]` 字段，用于收集详细的迭代信息。
        *   前端 `CodeGenerationPage.tsx` 会接收并展示这些日志，包括事件类型、尝试次数、AI的思考消息、生成的代码片段（部分）以及遇到的错误详情。
    *   **代码编辑器**: `CodeGenerationPage.tsx` 中的Monaco代码编辑器高度已增加到 `650px`，提供了更大的代码编辑和查看空间。

2.  **硬件配置传递 (前端 `configure-hardware` 页面)**:
    *   **简化流程**: 用户现在可以直接在文本输入框中提供完整的硬件配置字符串。
    *   **数据流**:
        *   `HardwareConfigPage.tsx` 允许用户在"可视化配置"和"文本配置"模式间切换。
        *   若选择"文本配置"并保存，该原始文本将通过 `AppContext` (`rawHardwareConfigText`) 直接传递。
        *   SOP生成 (`SopDefinitionPage.tsx`) 和代码生成 (`CodeGenerationPage.tsx`) 会优先使用这个原始文本配置；如果原始文本配置为空或未提供，则回退到使用通过可视化界面构建的硬件配置。
    *   **持久化**: 硬件配置（包括原始文本模式下的配置）会保存到浏览器 `localStorage`，方便下次使用。

3.  **代码生成质量优化 (后端 `langchain_agent.py`)**:
    *   **丰富上下文提示**: 借鉴了旧版 `Codegeneration.py` 的优点，向代码生成模型的提示中加入了更丰富的上下文信息，包括：
        *   有效的实验器材名称列表 (`VALID_LABWARE_NAMES`)
        *   有效的仪器名称列表 (`VALID_INSTRUMENT_NAMES`)
        *   有效的模块名称列表 (`VALID_MODULE_NAMES`)
        *   相关的代码示例 (`CODE_EXAMPLES`)
    *   **效果**: 此优化显著提高了首次代码生成的准确率，减少了不必要的迭代次数，多数情况下可以一次生成成功。

4.  **模拟结果显示优化 (前端 `simulation-results` 页面与后端 `opentrons_utils.py`)**:
    *   **结构化响应**: 后端 `/api/simulate-protocol` 端点现在返回更结构化的 `ProtocolSimulationResponse`，包含明确的字段如 `success`, `raw_simulation_output`, `error_message`, `warnings_present`, `warning_details`, `final_status_message`。
    *   **完整日志**: 移除了 `opentrons_utils.py` 中对模拟输出日志的长度截断（之前硬编码为4000字符）。前端现在可以接收并展示完整的模拟步骤日志。
    *   **前端展示**: `SimulationResultsPage.tsx` 调整了UI，以更清晰、美观的方式展示这些结构化信息和完整的原始模拟日志。

5.  **前端UI英文化**:
    *   项目内所有前端页面组件 (`labscriptAI-frontend/src/pages/`) 中的用户可见文本（如标题、按钮、提示信息、标签等）已从中文翻译为英文，以提供更国际化的用户体验。

### 🛠️ 后端API文档更新
*   `backend/api_server.py` 中 FastAPI 应用的标题、描述以及各个端点的描述性文档字符串（docstrings）已更新为英文。这确保了通过 `/docs` (Swagger UI) 和 `/redoc` (ReDoc) 自动生成的API交互文档显示为英文，与前端UI语言保持一致。

---

## ✨ 主要特性

- 🤖 **AI驱动的SOP生成** - 基于用户实验目标和硬件配置，通过Dify工作流智能生成标准操作程序 (SOP)。
- 💻 **自动代码生成与迭代优化** - 将SOP和硬件配置转换为可执行的Opentrons Python协议，并通过多轮AI迭代（结合模拟器反馈）自动检测和修复代码错误。
- 🧪 **集成模拟验证** - 集成Opentrons模拟器 (`opentrons_simulate`) 进行协议验证，提供详细的运行日志和错误反馈。
- 📝 **硬件配置灵活性** - 支持通过可视化界面或直接文本输入来定义硬件配置。
- 📜 **详尽的迭代日志** - 代码生成完成后，提供所有AI迭代尝试的详细日志，增强透明度。
- 🌐 **现代化Web界面** - React + TypeScript前端 (`labscriptAI-frontend`)，提供清晰的用户操作流程。
- 📄 **英文API文档** - 所有API端点的描述均已英文化，方便开发者理解和集成。

## 🏗️ 项目结构

```
OTCode工程师（跑通）/
├── main.py                     # 主启动脚本 (包含服务器启动、状态检查、测试运行)
├── requirements.txt            # Python依赖
├── start_backend.bat           # (Windows) 快速启动后端服务器的批处理文件
├── start_frontend.bat          # (Windows) 快速启动前端开发的批处理文件
├── .gitignore                  # Git忽略文件
│
├── backend/                    # 后端核心代码
│   ├── __init__.py
│   ├── api_server.py           # FastAPI应用，提供所有API端点
│   ├── langchain_agent.py      # LangChain智能体，负责SOP和代码生成逻辑
│   ├── opentrons_utils.py      # Opentrons模拟器和相关工具函数
│   └── config.py               # 配置文件 (包含API密钥、模型名称、有效器材列表等)
│
├── tests/                      # 测试文件 (部分已归档或待更新)
│   ├── ...
│
├── scripts/                    # 辅助脚本 (部分已整合入main.py)
│   ├── ...
│
├── docs/                       # 项目文档 (本文档及其他辅助说明)
│   ├── README.md (本文件)
│   └── ...
│
├── labscriptAI-frontend/       # React前端应用 (Vite + TypeScript + MUI)
│   ├── public/
│   ├── src/
│   │   ├── components/         # 可复用UI组件 (硬件、代码、SOP、欢迎页等)
│   │   ├── context/            # 全局应用状态 (AppContext)
│   │   ├── hooks/              # 自定义Hooks
│   │   ├── pages/              # 各页面组件 (欢迎、硬件配置、SOP定义、代码生成、模拟结果等)
│   │   ├── services/           # API服务层 (api.ts)
│   │   ├── utils/              # 工具函数 (apiTester.ts等)
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── generated_protocols/        # (可选) 生成的协议文件存放目录
└── archive/                    # 归档的旧文件或参考代码
```

## 🚀 快速开始

### 1. 环境准备
- Python (推荐 3.10+)，并配置好pip。本项目使用 `C:/Python313/python.exe` 作为示例路径。
- Node.js (推荐 LTS版本，如 18.x 或 20.x) 和 npm。

### 2. 安装依赖

```bash
# 安装Python后端依赖
# 请根据您的Python解释器路径调整
C:/Python313/python.exe -m pip install -r requirements.txt

# 安装前端依赖
cd labscriptAI-frontend
npm install
```

### 3. 配置环境变量
在项目根目录下创建或修改 `.env` 文件 (如果 `config.py` 从此处加载环境变量)，或者直接修改 `backend/config.py` 文件，填入必要的API密钥：

```python
# backend/config.py (部分示例)
# Dify API (用于SOP生成)
DIFY_API_KEY = "your-dify-api-key"  # 替换为您的Dify API Key
DIFY_API_URL = "https://api.dify.ai/v1" # Dify API基础URL
DIFY_SOP_WORKFLOW_ID = "your-dify-sop-workflow-id" # 替换为您的Dify SOP工作流ID

```
**重要**: `backend/config.py` 还包含 `VALID_LABWARE_NAMES`, `VALID_INSTRUMENT_NAMES`, `VALID_MODULE_NAMES` 和 `CODE_EXAMPLES` 等列表，这些对于提升代码生成质量至关重要，请根据您的实际可用器材和常见场景进行维护和更新。

### 4. 启动后端服务器

```bash
# 方式1: 使用主启动脚本 (推荐)
C:/Python313/python.exe main.py

# 您也可以使用其他方式，如直接运行 uvicorn:
# uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```
Windows用户可以直接双击根目录下的 `start_backend.bat`。

服务器启动后，API将在 `http://localhost:8000` 上可用。

### 5. 启动前端应用

```bash
# 进入前端目录
cd labscriptAI-frontend

# 启动开发服务器
npm run dev
```
Windows用户可以直接双击根目录下的 `start_frontend.bat`。

前端应用通常会在 `http://localhost:5173` (Vite默认端口，请根据实际情况调整) 上可用。

### 6. 访问应用

- **前端应用**: http://localhost:5173
- **API文档 (Swagger UI)**: http://localhost:8000/docs
- **API文档 (ReDoc)**: http://localhost:8000/redoc
- **API健康检查**: http://localhost:8000/
- **开发者工具 (前端页面)**: http://localhost:5173/dev-tools

## 🔧 API端点 (主要)

所有API端点的描述均已英文化，请参考 `http://localhost:8000/docs` 获取最准确和可交互的API文档。

### 1. SOP生成
- **POST** `/api/generate-sop`
- **请求体**: `SOPGenerationRequest`
  ```json
  {
    "hardware_config": "Robot Model: Flex\nAPI Version: 2.20\nLeft Pipette: flex_1channel_1000\nDeck Slot A1: opentrons_flex_96_tiprack_1000ul_hrf",
    "user_goal": "Perform a serial dilution from column 1 to column 12 of a 96 well plate."
  }
  ```
- **响应体**: `SOPGenerationResponse`
  ```json
  {
    "success": true,
    "sop_markdown": "## Protocol: Serial Dilution...",
    "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff"
  }
  ```

### 2. 协议代码生成
- **POST** `/api/generate-protocol-code`
- **请求体**: `ProtocolCodeGenerationRequest`
  ```json
  {
    "sop_markdown": "## Protocol: Serial Dilution...",
    "hardware_config": "Robot Model: Flex\nAPI Version: 2.20\nLeft Pipette: flex_1channel_1000\nDeck Slot A1: opentrons_flex_96_tiprack_1000ul_hrf"
  }
  ```
- **响应体**: `ProtocolCodeGenerationResponse`
  ```json
  {
    "success": true,
    "generated_code": "from opentrons import protocol_api\n\nmetadata = {'apiLevel': '2.20'}...",
    "attempts": 1,
    "warnings": [],
    "iteration_logs": [
      { "event_type": "llm_call_start", "attempt_num": 1, "message": "Generating code for SOP..." },
      { "event_type": "code_attempt", "attempt_num": 1, "generated_code": "...", "error_details": null },
      { "event_type": "simulation_result", "attempt_num": 1, "status": "SUCCEEDED", "stdout": "...", "stderr": "" }
    ],
    "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff"
  }
  ```

### 3. 协议模拟
- **POST** `/api/simulate-protocol`
- **请求体**: `ProtocolSimulationRequest`
  ```json
  {
    "protocol_code": "from opentrons import protocol_api\n\nmetadata = {'apiLevel': '2.20'}..."
  }
  ```
- **响应体**: `ProtocolSimulationResponse`
  ```json
  {
    "success": true,
    "raw_simulation_output": "Analyzing P300 Single-Channel GEN2 on left mount\n...",
    "error_message": null,
    "warnings_present": false,
    "warning_details": null,
    "final_status_message": "Simulation completed successfully.",
    "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff"
  }
  ```

### 4. 健康检查
- **GET** `/api/health`
  - 返回API健康状态和版本信息。
- **GET** `/`
  - 基础健康检查端点。

## 🔄 工作流程 (用户视角)

1.  **欢迎页面 (`/`)**:
    *   了解应用功能，点击 "Get Started"。

2.  **硬件配置页面 (`/configure-hardware`)**:
    *   选择机器人型号 (Flex, OT-2, PyLabRobot (实验性))。
    *   选择API版本。
    *   配置左/右移液器。
    *   (Flex) 选择是否使用夹爪 (Gripper)。
    *   通过拖拽或选择方式在虚拟Deck上配置实验器材 (Labware)。
    *   **或者**，切换到"文本配置"模式，直接粘贴或编写完整的硬件配置字符串。
    *   保存配置，进入SOP定义页面。

3.  **SOP定义页面 (`/define-sop`)**:
    *   输入实验目标或简要描述。
    *   点击 "Generate SOP with AI"，后端调用Dify（或其他SOP生成服务）生成SOP Markdown。
    *   在Markdown编辑器中查看和编辑AI生成的SOP。
    *   确认SOP后，点击 "Generate Protocol Code"。

4.  **代码生成页面 (`/generate-code`)**:
    *   系统自动将SOP和硬件配置发送到后端进行代码生成。
    *   等待AI完成代码生成和迭代优化过程。
    *   在Monaco Editor中查看生成的Python协议代码。
    *   查看详细的迭代日志，了解AI的每一步尝试和结果。
    *   如有需要，可手动编辑代码。
    *   点击 "Run Simulation"。

5.  **模拟结果页面 (`/simulation-results`)**:
    *   系统自动将当前代码发送到后端进行Opentrons模拟。
    *   查看模拟是否成功、是否有警告或错误。
    *   查看详细的模拟器原始输出日志。
    *   (可选) 如果模拟包含错误，可以返回代码编辑页面进行修改，或依赖AI的迭代能力。

6.  **动画页面 (`/animation`)**:
    * 查看协议的动画演示。

7.  **(可选) 开发者工具页面 (`/dev-tools`)**:
    *   进行API连接测试、查看系统信息等。

## 💡 未来可能的改进方向
- 更智能的SOP解析和代码生成，减少对模板的依赖。
- 支持更多类型的机器人和实验设备。
- 完善错误提示和用户引导。
- 协议动画的实际集成和展示。
- 用户账户系统和协议保存云端。

## 📚 技术栈

### 后端
- Python 3.10+
- FastAPI: 用于构建高性能API
- Uvicorn: ASGI服务器
- LangChain: 驱动AI代码生成和迭代逻辑的核心框架
- Pydantic: 数据校验和模型定义
- Opentrons API & `opentrons_simulate`: 用于协议验证
- (可能) Dify Client: 与Dify平台交互生成SOP

### 前端
- Node.js & npm
- React 18+
- Vite: 构建工具和开发服务器
- TypeScript: 类型安全
- Material-UI (MUI): UI组件库
- Monaco Editor: 代码编辑器组件
- Lucide Icons: 图标库
- Notistack: 通知/Snackbar组件
- Framer Motion: (可选) 用于动画效果

### 其他
- Git & GitHub: 版本控制
- Prettier: 代码格式化 (推荐配置并使用)

## 🤝 贡献

欢迎各种形式的贡献！如果您有任何建议、发现bug或希望添加新功能，请随时联系gaoyuanbio@qq.com，或创建Issue或Pull Request。


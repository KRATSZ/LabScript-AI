<<<<<<< HEAD
# Opentrons AI Protocol Generator
🧬 **智能化的Opentrons实验协议生成器**

## 🚀 快速启动

### 前置要求
- Python 3.11 (推荐)
- Node.js 18+ 
- uv package manager

### 启动步骤
```bash
# 1. 环境初始化
.\scripts\setup-uv.ps1

# 2. 配置环境变量
cp .env.example .env

# 3. 启动后端 API 服务器
.\.venv\Scripts\Activate.ps1
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
or
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
# 或者使用 uv run python main.py

# 4. 启动前端开发服务器
cd labscriptAI-frontend
npm install  # 首次运行
# 如果遇到依赖冲突错误，可以使用：npm install --legacy-peer-deps
npm run dev

# 5. 前端构建（生产环境）
npm run build     # 构建生产版本
npm run preview   # 预览构建结果
```

### 访问地址
- 前端界面: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 前端构建与部署
- **构建输出目录**: `labscriptAI-frontend/dist/`
- **构建命令**: `npm run build`
- **预览构建**: `npm run preview` (本地预览生产版本)
- **部署**: 将 `dist/` 目录内容部署到静态文件服务器
- **环境变量**: 项目根目录的 `.env` 统一管理前端 API、后端 LLM 和服务端口等配置

---

通过自然语言描述实验需求，自动生成、验证和优化Opentrons机器人协议代码。

## 🏗️ 技术架构

### 核心设计
- **双虚拟环境**: `.venv` (主应用) + `ot_env` (Opentrons隔离环境)
- **前后端分离**: React + TypeScript 前端 + FastAPI 后端
- **AI驱动**: LangChain + LangGraph 实现代码生成与迭代优化
- **模拟验证**: 集成 Opentrons 模拟器进行协议验证

### 依赖管理
- **Python**: `pyproject.toml` + `uv` 包管理器
- **Node.js**: `package.json` 管理前端依赖
- **环境隔离**: 解决 opentrons 包与现代库的版本冲突

### API 架构
- **RESTful API**: FastAPI 提供标准 HTTP 接口
- **数据模型**: Pydantic 确保类型安全
- **文档生成**: 自动生成 Swagger/ReDoc 文档
- **健康检查**: 内置系统状态监控

### ✨ 功能与体验优化
1.  **代码生成流程与显示 (前端 `generate-code` 页面)**:
    *   **实时流式API (SSE)**: 后端代码生成接口 (`/api/generate-protocol-code`) 采用**服务器发送事件 (Server-Sent Events, SSE)** 模式。这使得后端的 AI 思考、代码生成、模拟验证和迭代优化的每一步，都能被**实时地**推送给前端。
    *   **前端实时日志**:
        *   前端 `CodeGenerationPage.tsx` 监听这些实时事件，并动态地在界面上更新进度、展示AI的思考过程和每一次的尝试结果。
        *   最终的迭代日志（Iteration Logs）是由前端根据接收到的事件流**动态组装**而成的，而不是由后端一次性返回，提供了极佳的透明度和用户体验。
    *   **代码编辑器**: `CodeGenerationPage.tsx` 中的Monaco代码编辑器高度已增加到 `650px`，提供了更大的代码编辑和查看空间。

2.  **硬件配置传递 (前端 `configure-hardware` 页面)**:
    *   **简化流程**: 用户现在可以直接在文本输入框中提供完整的硬件配置字符串。
    *   **数据流**:
        *   `HardwareConfigPage.tsx` 允许用户在"可视化配置"和"文本配置"模式间切换。
        *   若选择"文本配置"并保存，该原始文本将通过 `AppContext` (`rawHardwareConfigText`) 直接传递。
        *   SOP生成 (`SopDefinitionPage.tsx`) 和代码生成 (`CodeGenerationPage.tsx`) 会优先使用这个原始文本配置；如果原始文本配置为空或未提供，则回退到使用通过可视化界面构建的硬件配置。
    *   **持久化**: 硬件配置（包括原始文本模式下的配置）会保存到浏览器 `localStorage`，方便下次使用。

3.  **智能化的代码生成与迭代优化 (后端 `langchain_agent.py`)**:
    *   **核心架构**: 项目采用 `LangGraph` 构建了一个循环式的代码生成与修正工作流。此流程模拟了"开发-测试-Debug"的模式，具体步骤为：
        *   **代码生成 (`generate_code_node`)**: AI根据SOP和硬件配置生成初始Python代码。
        *   **模拟验证 (`simulator_node`)**: 调用Opentrons模拟器执行生成的代码。
        *   **决策 (`should_continue`)**: 如果模拟成功，流程结束。如果失败，进入下一步。
        *   **反馈准备 (`prepare_feedback_node`)**: AI分析失败日志，生成结构化的反馈。
        *   **循环**: 将反馈传回代码生成节点，开始新一轮的修正与尝试。
    *   **关键优化点**:
        *   **动态知识库**: 为降低AI选择错误硬件的可能性，系统会根据用户选择的机器人型号（Flex或OT-2），动态地从`config.py`中筛选并提供对应的有效器材、移液器和模块列表。这极大地减少了提示词中的噪声，提高了首次生成的准确率。
        *   **高质量的修正反馈**: `prepare_feedback_node`节点经过了深度优化：
            *   **错误日志清洗**: 调用 `extract_error_from_simulation` 函数，从冗长的模拟输出中提取最核心的错误信息。
            *   **结构化反馈**: 生成的反馈包含了 **[失败分析]**, **[建议操作]**, **[错误日志]** 和 **[上次失败的代码]** 四个部分，为AI提供了完整的Debug上下文，使其能够进行更精确的修复。
        *   **清晰的提示工程**: 代码生成提示词 (`CODE_GENERATION_PROMPT_TEMPLATE`) 经过重构，能够清晰地区分 **原始SOP** 和 **后续修正反馈**，指导AI优先处理修正任务。

4.  **PyLabRobot Agent 技术架构升级 (2025-07-29)**:
    *   **专业提示词模板**: 
        *   `PYLABROBOT_CODE_GENERATION_PROMPT_TEMPLATE`: 针对PyLabRobot语法的初始代码生成模板，强制要求`async def protocol(lh):`函数封装
        *   `PYLABROBOT_CODE_CORRECTION_DIFF_PROMPT_TEMPLATE`: 基于diff的智能代码修复模板
        *   `PYLABROBOT_FORCE_REGENERATE_PROMPT_TEMPLATE`: 循环检测时的强制重生成模板
    *   **智能错误分析**: 重构`_analyze_pylabrobot_error`函数，支持结构化错误检测:
        *   `MissingProtocolFunction`: 检测缺失协议函数封装错误
        *   `PyLabRobotNotInstalled`: 环境依赖问题检测
        *   `VolumeError`, `ImportError`, `ResourceNotFoundError`等专项错误类型
    *   **混合LLM策略**: 
        *   创建任务使用Gemini-2.5-Pro（复杂推理）
        *   修复任务使用DeepSeek-V3-Fast（快速响应）
        *   动态LLM切换基于任务类型和`force_regenerate`标志
    *   **硬件配置扩展**: 
        *   新增Hamilton Vantage配置文件(`pylabrobot_hamilton_vantage.json`)
        *   支持动态设备类型检测（hamilton_star, hamilton_vantage, opentrons, tecan_evo）
        *   API端点更新显示名称映射
    *   **前端界面优化**:
        *   设备选择列表增加Hamilton Vantage选项
        *   SOP页面对话框增加清除按钮和界面美化
        *   空状态提示和视觉效果改进

5.  **模拟结果显示优化 (前端 `simulation-results` 页面与后端 `opentrons_utils.py`)**:
    *   **结构化响应**: 后端 `/api/simulate-protocol` 端点现在返回更结构化的 `ProtocolSimulationResponse`，包含明确的字段如 `success`, `raw_simulation_output`, `error_message`, `warnings_present`, `warning_details`, `final_status_message`。
    *   **完整日志**: 移除了 `opentrons_utils.py` 中对模拟输出日志的长度截断（之前硬编码为4000字符）。前端现在可以接收并展示完整的模拟步骤日志。
    *   **前端展示**: `SimulationResultsPage.tsx` 调整了UI，以更清晰、美观的方式展示这些结构化信息和完整的原始模拟日志。

6.  **前端UI英文化**:
    *   项目内所有前端页面组件 (`labscriptAI-frontend/src/pages/`) 中的用户可见文本（如标题、按钮、提示信息、标签等）已从中文翻译为英文，以提供更国际化的用户体验。

### 🛠️ 后端API文档更新
*   `backend/api_server.py` 中 FastAPI 应用的标题、描述以及各个端点的描述性文档字符串（docstrings）已更新为英文。这确保了通过 `/docs` (Swagger UI) 和 `/redoc` (ReDoc) 自动生成的API交互文档显示为英文，与前端UI语言保持一致。

### 🔧 环境与部署优化 (2025-07-02)
*   **完善了开发环境设置文档**: 根据实际部署经验，增加了详细的故障排除指南，解决了在 Windows 系统上因 Python 版本、中文路径、项目结构等问题导致的安装失败。
*   **脚本健壮性提升**: `scripts/setup-uv.ps1` 脚本已更新，会自动切换到项目根目录执行，并指定使用稳定的 Python 3.11 版本，避免了常见的编译错误和路径问题。
*   **打包配置修正**: `pyproject.toml` 文件已明确指定打包 `backend` 目录，解决了 `setuptools` 的包发现错误。

---

## ✨ 主要特性

- 🤖 **AI驱动的SOP生成** - 基于用户实验目标和硬件配置，通过本地LangChain智能生成标准操作程序 (SOP)。
- 💻 **自动代码生成与迭代优化** - 将SOP和硬件配置转换为可执行的Opentrons Python协议，并通过多轮AI迭代（结合模拟器反馈）自动检测和修复代码错误。
- 🧪 **集成模拟验证** - 集成Opentrons模拟器 (`opentrons_simulate`) 进行协议验证，提供详细的运行日志和错误反馈。
- 🤖 **PyLabRobot 实验性支持** - 新增对 PyLabRobot 平台的支持，共享同一套“生成-验证-修复”的AI工作流，提供统一的用户体验。
- 📝 **硬件配置灵活性** - 支持通过可视化界面或直接文本输入来定义硬件配置。
- 📦 **一键导出protocols.io格式** - 将生成的协议、硬件配置和SOP打包为ZIP文件，方便上传到protocols.io平台分享和发布。
- 📜 **详尽的迭代日志** - 代码生成完成后，提供所有AI迭代尝试的详细日志，增强透明度。
- 🌐 **现代化Web界面** - React + TypeScript前端 (`labscriptAI-frontend`)，提供清晰的用户操作流程。
- 📄 **英文API文档** - 所有API端点的描述均已英文化，方便开发者理解和集成。

## 📁 项目结构

```
OTCode工程师（跑通）/
├── pyproject.toml              # Python 项目配置与依赖管理
├── uv.lock                     # UV 包管理器锁文件
├── main.py                     # 多功能启动脚本 (API/测试/状态检查)
├── .python-version             # Python 版本规范 (3.11)
│
├── backend/                    # 🏗️ 后端核心
│   ├── api_server.py           # FastAPI 应用与路由定义
│   ├── langchain_agent.py      # LangGraph 工作流引擎 (Opentrons)
│   ├── pylabrobot_agent.py     # LangGraph 工作流引擎 (PyLabRobot)
│   ├── opentrons_utils.py      # Opentrons 模拟器接口
│   ├── pylabrobot_utils.py     # PyLabRobot 模拟器接口
│   ├── config.py               # 系统配置与硬件库
│   ├── prompts.py              # AI 提示词模板
│   ├── diff_utils.py           # 代码差异处理工具
│   ├── external_publisher.py   # 外部集成接口
│   └── file_exporter.py        # 文件导出功能
│
├── labscriptAI-frontend/       # 🎨 前端应用 (React + TypeScript)
│   ├── src/
│   │   ├── components/         # UI 组件库
│   │   ├── pages/              # 路由页面组件
│   │   ├── services/           # API 客户端服务
│   │   ├── context/            # 全局状态管理
│   │   └── utils/              # 前端工具函数
│   ├── package.json            # 前端依赖配置
│   └── vite.config.ts          # Vite 构建配置
│
├── scripts/                    # 🔧 自动化脚本
│   └── setup-uv.ps1            # 环境初始化脚本
│
├── .venv/                      # 🐍 主 Python 虚拟环境
├── ot_env/                     # 🔬 Opentrons 隔离环境
├── tests/                      # 🧪 测试套件
├── opentrons_validator/        # 🔍 协议验证工具
└── 论文中要用的实验脚本案例/    # 📚 参考案例库
```

## 🏛️ 项目架构概览

本项目采用了一个先进的**双虚拟环境架构**，以彻底解决核心库 (`uv` vs `opentrons`) 之间的依赖冲突，保证系统的稳定性和可维护性。

### 核心设计思想

- **环境隔离**: 主应用 (`.venv`) 和 Opentrons 模拟器 (`ot_env`) 运行在两个完全独立的环境中。
- **子进程通信**: 主应用通过安全的 `subprocess` 调用来命令 `ot_env` 执行模拟任务，而不是直接 `import` 库，从而避免依赖冲突。


### 各部分职责

*   **虚拟环境 (`.venv/` & `ot_env/`)**
    *   `.venv/`: **主应用环境**。包含了所有现代化的库，如 FastAPI (Web服务), LangChain (AI逻辑) 等。**此环境不包含 `opentrons`**。
    *   `ot_env/`: **Opentrons 隔离环境**。一个纯净的环境，其唯一目的就是安装并运行对依赖有特殊要求的 `opentrons` 包。

*   **后端 (`backend/`)**
    *   `api_server.py`: 一个 FastAPI Web 服务器，为前端界面提供标准的 HTTP API 接口（如生成SOP、生成代码等）。
    *   `langchain_agent.py`: 项目的"大脑"，封装了所有与大语言模型交互的逻辑，负责驱动SOP生成和代码的迭代生成。
    *   `opentrons_utils.py`: **关键的桥梁**。它通过**子进程 (`subprocess`)** 调用 `ot_env/` 环境来执行 Opentrons 模拟，并将结果返回给主应用。

*   前端 (`labscriptAI-frontend/`)
    *   一个独立的 React/Vite 应用，是项目的图形用户界面 (GUI)。它通过调用 `api_server.py` 提供的 API 来与后端交互。

*   **核心工具与脚本**
    *   `scripts/setup-uv.ps1`: **项目初始化脚本**。负责自动化地创建并配置上述的 `.venv` 和 `ot_env` 双虚拟环境。

## 🚀 开发环境设置

### ⚡ 核心特性
- **双虚拟环境隔离**: 解决 opentrons 依赖冲突
- **一键式初始化**: 自动化环境配置脚本
- **现代包管理**: 使用 `uv` 实现快速依赖解析
- **跨平台兼容**: 支持 Windows/macOS/Linux

本项目使用 `uv` 进行包管理，并采用双虚拟环境策略来解决 `opentrons` 包的依赖冲突问题。请严格遵循以下步骤进行设置。

> **架构核心：依赖隔离**
> - **`opentrons` 库** 依赖于旧版本的核心库（例如 `anyio<4.0`）。
> - **`uv` `FastAPI` 等现代库** 则需要新版本的核心库（例如 `anyio>=4.5`）。
> 这种冲突无法在单一环境中解决。因此，本项目的正确架构是：
> - **`.venv/`**: 主环境。它 **不包含** `opentrons`。所有核心服务（FastAPI, LangChain）在此运行。
> - **`ot_env/`**: 一个完全隔离的环境，其唯一目的是安装和运行 `opentrons`。
> - **通信方式**: 主应用通过 **子进程 (`subprocess`)** 来调用 `ot_env` 环境中的模拟器，而不是直接 `import opentrons`。


### 1. 先决条件

#### Windows 系统
- **安装 `uv`**: `uv` 是一个非常快速的 Python 包安装和解析器。请先根据其[官方文档](https://github.com/astral-sh/uv)进行安装。通常，在 Windows 上可以使用：
  ```shell
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Windows 用户关键设置**: 由于 `opentrons` 的一个依赖在处理包含非 ASCII 字符（如中文）的 Windows 用户路径时存在问题，必须设置一个全局环境变量来强制 Python 使用 UTF-8 编码。请在 **管理员权限的终端** 中运行以下命令，**然后重启你的终端或电脑**，使其生效：
  ```shell
  setx PYTHONUTF8 1 /M
  ```

#### Linux/macOS 系统
- **安装 `uv`**: 在 Linux 或 macOS 系统上，可以使用以下命令安装 `uv`：
  ```bash
  # 使用官方安装脚本
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # 或者使用 pip 安装
  pip install uv
  
  # 或者使用包管理器（Ubuntu/Debian）
  sudo apt update && sudo apt install python3-pip
  pip3 install uv
  
  # macOS 使用 Homebrew
  brew install uv
  ```
- **环境变量设置**: 安装完成后，确保 `uv` 在你的 PATH 中。如果使用官方脚本安装，通常会自动添加到 `~/.bashrc` 或 `~/.zshrc`。如果没有，请手动添加：
  ```bash
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```
- **Python 版本要求**: 确保系统安装了 Python 3.11。在 Ubuntu/Debian 系统上：
  ```bash
  sudo apt update
  sudo apt install python3.11 python3.11-venv python3.11-dev
  ```

### 2. 初始化项目

#### Windows 系统
我们提供了一个便捷的 PowerShell 脚本来完成所有环境的搭建工作。

- **运行设置脚本**: 在项目根目录下，使用 PowerShell 运行 `setup-uv.ps1` 脚本。
  ```shell
  .\scripts\setup-uv.ps1
  ```

#### Linux/macOS 系统
在 Linux 或 macOS 系统上，需要手动执行以下步骤来初始化项目：

1. **创建主虚拟环境**:
   ```bash
   # 进入项目根目录
   cd /path/to/LabscriptAI_cloud
   
   # 使用 uv 创建主虚拟环境
   uv venv .venv --python 3.11
   
   # 激活虚拟环境
   source .venv/bin/activate
   
   # 安装项目依赖
   uv pip install -e .
   ```

2. **创建 Opentrons 隔离环境**:
   ```bash
   # 创建 opentrons 专用环境
   uv venv ot_env --python 3.11
   
   # 激活 opentrons 环境
   source ot_env/bin/activate
   
   # 安装 opentrons 相关依赖
   uv pip install opentrons
   
   # 退出 opentrons 环境
   deactivate
   ```

3. **验证安装**:
   ```bash
   # 重新激活主环境
   source .venv/bin/activate
   
   # 验证安装
   python -c "import backend; print('Backend module loaded successfully')"
   ```

**环境设置说明**:
- `.venv/`: 主项目环境，包含 FastAPI、LangChain 等核心依赖。
- `ot_env/`: `opentrons` 专用隔离环境，仅包含 `opentrons` 及其特定依赖。
- 两个环境完全隔离，避免依赖冲突问题。

### 3. 如何运行

**务必先激活主虚拟环境**，所有操作都在此环境中进行。

#### Windows 系统
```powershell
# 激活主虚拟环境
.\.venv\Scripts\Activate.ps1

# 启动后端服务器
uv run python main.py

# 或者使用 uvicorn 直接启动
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

# 运行测试
pytest
```

#### Linux/macOS 系统
```bash
# 激活主虚拟环境
source .venv/bin/activate

# 启动后端服务器
uv run python main.py

# 或者使用 uvicorn 直接启动
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

# 启动前端开发服务器（需要先安装 Node.js）
cd labscriptAI-frontend
npm install  # 首次运行
# 如果遇到依赖冲突错误，可以使用：npm install --legacy-peer-deps
npm run dev

# 运行测试
pytest

# 退出虚拟环境
deactivate
```

### 4. 依赖管理

- **所有依赖项** 均在根目录的 `pyproject.toml` 文件中的 `[project.dependencies]` 部分进行管理。
- **添加新依赖**:
  1.  手动将新的包名（例如 `requests` 或 `requests==2.28.1`）添加到 `pyproject.toml` 的依赖列表中。
  2.  在已激活的 `.venv` 环境中运行以下命令来安装新的包：
      ```bash
      # Windows
      uv pip sync pyproject.toml
      
      # Linux/macOS
      uv pip install -e .
      ```

---

## 🔧 常见问题与解决方案 (Troubleshooting)

在环境设置和依赖安装过程中，您可能会遇到一些常见问题。这里提供了基于实践的解决方案。

> **注意**: 以下问题主要针对 Windows 系统。Linux/macOS 系统的常见问题请参考上面的 "Linux/macOS 系统常见问题与解决方案" 部分。

### 1. 错误: `Multiple top-level packages discovered`
- **问题**: 运行 `uv pip install -e .` 时，`setuptools` 因为在根目录找到多个文件夹（如 `backend`, `tests`, `.venv`）而感到困惑，不知道该打包哪一个。
- **解决方案**: 项目中的 `pyproject.toml` 文件已通过添加以下内容解决此问题，明确指定只有 `backend` 是需要安装的包。如果遇到类似问题，请确保配置存在：
  ```toml
  [tool.setuptools]
  packages = ["backend"]
  ```

### 2. 错误: `subprocess-exited-with-error` (编译 `numpy` 或其他库失败)
- **问题**: 这通常发生在 `pip` 尝试从源代码编译一个包时，但系统缺少 C++ 编译器（如 Visual Studio Build Tools）。最常见的原因是使用了过于新潮的 Python 版本（如 3.12+），这些版本缺少预编译的二进制包 (wheels)。
- **解决方案**: **请务_务必_使用 Python 3.11 版本**。本项目已验证 Python 3.11.x 可以顺利安装所有依赖的预编译版本，从而完全绕开编译的需要。`setup-uv.ps1` 脚本也已强制指定使用 Python 3.11。

### 3. 错误: `[WinError 2] 系统找不到指定的文件` 或安装时路径编码错误
- **问题**: 在 Windows 系统上，如果你的项目路径或用户路径包含中文字符（如 `D:\项目\app` 或 `C:\Users\张三`），某些 Python 包的安装脚本会因为编码问题而失败。
- **解决方案**: 设置一个全局环境变量，强制 Python 使用 UTF-8。请**以管理员身份**运行 PowerShell 或 CMD，执行以下命令，**然后重启电脑**使其生效：
  ```shell
  setx PYTHONUTF8 1 /M
  ```

### 4. 错误: `Failed to create virtualenv ... The directory '.venv' exists` 或 `拒绝访问`
- **问题**:
    - A) 上一次失败的安装过程在项目中留下了一个空的或损坏的 `.venv` 文件夹。
    - B) 某个程序（如你的 VS Code、终端、文件管理器）正在使用 `.venv` 文件夹，导致系统锁定它，脚本无法删除或修改。
- **解决方案**:
    - **手动删除 `.venv` 文件夹**。
    - 如果删除时提示"拒绝访问"，请**关闭所有可能占用它的程序（特别是 VS Code 和所有终端窗口）**，然后再试一次。
    - 删除后，重新运行 `.\scripts\setup-uv.ps1`。

### 5. Linux/macOS 系统常见问题与解决方案

#### 权限问题
- **问题**: 在某些 Linux 发行版上，可能遇到权限不足的问题。
- **解决方案**:
  ```bash
  # 确保当前用户对项目目录有完整权限
  sudo chown -R $USER:$USER /path/to/LabscriptAI_cloud
  chmod -R 755 /path/to/LabscriptAI_cloud
  ```

#### Python 版本问题
- **问题**: 系统默认 Python 版本不是 3.11。
- **解决方案**:
  ```bash
  # Ubuntu/Debian 安装 Python 3.11
  sudo apt update
  sudo apt install software-properties-common
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install python3.11 python3.11-venv python3.11-dev
  
  # 创建虚拟环境时指定 Python 版本
  uv venv .venv --python python3.11
  ```

#### 依赖编译问题
- **问题**: 某些包需要编译，但缺少必要的系统依赖。
- **解决方案**:
  ```bash
  # Ubuntu/Debian 安装编译工具
  sudo apt update
  sudo apt install build-essential python3.11-dev libffi-dev libssl-dev
  
  # CentOS/RHEL/Fedora
  sudo yum groupinstall "Development Tools"
  sudo yum install python3.11-devel libffi-devel openssl-devel
  ```

#### 环境变量问题
- **问题**: `uv` 命令找不到或虚拟环境激活失败。
- **解决方案**:
  ```bash
  # 检查 uv 是否在 PATH 中
  which uv
  
  # 如果没有，添加到 PATH
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  
  # 或者使用完整路径
  ~/.local/bin/uv venv .venv --python 3.11
  ```

#### 如何修改虚拟环境在终端中的提示符名称？
- **问题**: 激活虚拟环境后，终端提示符可能是乱码或文件夹全名，不够美观。
- **解决方案**:
    1. 打开虚拟环境的配置文件，例如 `.venv/pyvenv.cfg`。
    2. 在文件末尾添加一行 `prompt = 你想要的名字`，例如：
       ```cfg
       prompt = backend
       ```
    3. 保存文件，然后重新激活环境：
       ```bash
       # Linux/macOS
       deactivate
       source .venv/bin/activate
       
       # Windows
       deactivate
       .\.venv\Scripts\activate
       ```

## 🔧 API 端点

### 🔗 文档地址
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 🏥 系统健康检查
```bash
GET /                    # 基础健康检查
GET /api/health         # 详细系统状态
GET /api/tools          # 可用工具列表
```

### 1. SOP生成
- **POST** `/api/generate-sop`
- **请求体**: `SOPGenerationRequest`
  ```json
  {
    "hardware_config": "Robot Model: Flex\nAPI Version: 2.19\nLeft Pipette: flex_1channel_1000\nDeck Slot A1: opentrons_flex_96_tiprack_1000ul_hrf",
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
    "sop_markdown": "提取质粒DNA",
    "hardware_config": "Robot Model: Flex\nAPI Version: 2.19\nLeft Pipette: flex_1channel_1000\nDeck Slot A1: opentrons_flex_96_tiprack_1000ul_hrf"
  }
  ```
- **响应体**: `ProtocolCodeGenerationResponse`
  ```json
  {
    "success": true,
    "generated_code": "from opentrons import protocol_api\n\nmetadata = {'apiLevel': '2.19'}...",
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
    "protocol_code": "from opentrons import protocol_api\n\nmetadata = {'apiLevel': '2.19'}..."
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

### 3b. 协议模拟 (PyLabRobot)
- **POST** `/api/simulate-pylabrobot-protocol`
- **说明**: 模拟验证 PyLabRobot 协议代码。
- **请求体**: `PyLabRobotSimulationRequest`
  ```json
  {
    "protocol_code": "async def protocol(lh): ..."
  }
  ```
- **响应体**: `ProtocolSimulationResponse` (与Opentrons模拟共享相同结构)

### 4. protocols.io 导出
- **POST** `/api/export/protocols-io`
- **说明**: 将完整的协议信息打包成ZIP文件，方便上传到protocols.io平台分享。
- **请求体**: `ProtocolExportRequest`
  ```json
  {
    "user_goal": "Perform a serial dilution from column 1 to column 12 of a 96 well plate.",
    "hardware_config": "Robot Model: Flex\nAPI Version: 2.19\nLeft Pipette: flex_1channel_1000\nDeck Slot A1: opentrons_flex_96_tiprack_1000ul_hrf",
    "sop_markdown": "## Protocol: Serial Dilution\n\n### Steps:\n1. Load plate...",
    "generated_code": "from opentrons import protocol_api\n\nmetadata = {'apiLevel': '2.19'}..."
  }
  ```
- **响应**: ZIP文件下载 (`application/zip`)
- **包含文件**:
  - `protocol_script.py`: 可执行的Opentrons Python协议代码
  - `protocol_details.md`: 格式化的协议说明文档，包含上传到protocols.io的详细指南

### 5. 健康检查
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
    *   点击 "Generate SOP with AI"，后端调用本地LangChain生成SOP Markdown。
    *   在Markdown编辑器中查看和编辑AI生成的SOP。
    *   确认SOP后，点击 "Generate Protocol Code"。
4.  **代码生成页面 (`/generate-code`)**:
    *   系统自动将SOP和硬件配置发送到后端。**后端分发器会根据硬件配置中的机器人类型，自动选择Opentrons或PyLabRobot的AI Agent进行代码生成**。
    *   等待AI完成代码生成和迭代优化过程。
    *   在Monaco Editor中查看生成的Python协议代码。
    *   查看详细的迭代日志，了解AI的每一步尝试和结果。
    *   如有需要，可手动编辑代码。
    *   点击 "Run Simulation"。
5.  **模拟结果页面 (`/simulation-results`)**:
    *   系统自动将当前代码发送到后端进行模拟。**前端会根据当前机器人类型，调用正确的模拟API**。
    *   查看模拟是否成功、是否有警告或错误。
    *   查看详细的模拟器原始输出日志。
    *   **导出协议**: 点击 "Export for protocols.io" 按钮，系统会将完整的协议信息（用户目标、硬件配置、SOP和代码）打包成ZIP文件下载，方便上传到protocols.io平台分享。
    *   (可选) 如果模拟包含错误，可以返回代码编辑页面进行修改，或依赖AI的迭代能力。
6.  **动画页面 (`/animation`)**:
    * 查看协议的动画演示。
7.  **(可选) 开发者工具页面 (`/dev-tools`)**:
    *   进行API连接测试、查看系统信息等。

## ⚡ 性能与优化

### 🚀 架构优势
- **异步处理**: FastAPI 异步端点提供高并发能力
- **智能缓存**: LRU 缓存减少重复计算开销
- **流式响应**: 实时迭代日志提升用户体验
- **模块化设计**: 松耦合架构便于横向扩展


### 📊 资源使用
- **CPU**: 主要消耗在 AI 推理阶段
- **内存**: 典型运行占用 ~200-500MB
- **存储**: 虚拟环境 ~2-3GB
- **网络**: OpenAI API 调用频次优化

## 💡 未来可能的改进方向

- **"智能反馈"的错误覆盖**: 不断将实践中遇到的新错误类型（如`TipAttachedError`, `DeckConflictError`等）及其解决方案加入到`prepare_feedback_node`的分析逻辑中，使其能够应对更多样的失败场景。
- 更智能的SOP解析和代码生成
- 支持更多类型的机器人和实验设备。
- 完善错误提示和用户引导。
- 协议动画的实际集成和展示。
- 用户账户系统和协议保存云端（目前比较缺钱暂时没做）。

## 📚 技术栈

### 后端技术
```python
# 核心框架
FastAPI             # 高性能 Web 框架
Uvicorn            # ASGI 服务器
Pydantic           # 数据验证与序列化
# AI & 工作流
LangChain          # AI 应用开发框架  
LangGraph          # 有状态工作流引擎
OpenAI API         # 大语言模型接口
# 专业集成
Opentrons API      # 机器人协议开发
opentrons          # 协议模拟验证 (包含 opentrons_simulate 命令)
# 依赖管理
uv                 # 现代 Python 包管理器
```

### 前端技术
```typescript
// 核心框架
React 18+          // 用户界面库
TypeScript         // 类型安全的 JavaScript
Vite              // 构建工具与开发服务器

// UI & 组件
Material-UI (MUI)  // React 组件库
Monaco Editor      // 代码编辑器
Lucide React       // 图标库
Notistack         // 通知系统
// 状态管理
React Context      // 全局状态管理
```

### 开发工具
```bash
# 包管理
uv                 # Python 包管理
npm               # Node.js 包管理
# 代码质量
ESLint            # JavaScript/TypeScript 代码检查
Prettier          # 代码格式化
# 版本控制
Git               # 分布式版本控制
```

## 🤝 贡献

欢迎各种形式的贡献！如果您有任何建议、发现bug或希望添加新功能，请随时联系gaoyuanbio@qq.com，或创建Issue或Pull Request。

## 🚀 优化计划（未完成） 20250729
### 核心技术债
1.  **【后端】God Object**: `backend/langchain_agent.py` 文件接近2000行，混合了代码生成、代码编辑、SOP对话等多种Agent的逻辑，严重违反了“单一职责原则”，维护和测试成本高。
2.  **【前端】上帝组件 (God Component)**: `labscriptAI-frontend/src/pages/CodeGenerationPage.tsx` 文件超过1300行，将数据获取、业务逻辑、多重本地状态和复杂UI渲染全部耦合在一起，存在潜在的性能瓶颈，难以维护。
3.  **【后端】逻辑冗余**: `opentrons_utils.py` 和 `langchain_agent.py`升级与优化
=======
# 🚀 LabscriptAI: Autonomous Liquid-Handling Robotics Scripting for Accessible and Responsible Protein Engineering
# 🚀 LabscriptAI：用于可访问且负责任的蛋白质工程的自主液体处理机器人脚本生成框架

**Authors**: Yuan Gao# (高源), Yizhou Luo#, Wenzhuo Li#, Yunquan Lan, Han Jiang, Yongcan Chen, Xiao Yi, Lihao Fu*, Min Yang*, Tong Si*  
*State Key Laboratory for Quantitative Synthetic Biology, Shenzhen Institute of Synthetic Biology, Shenzhen Institutes of Advanced Technology, Chinese Academy of Sciences*  
*定量合成生物学重点实验室，中国科学院深圳先进技术研究院合成生物学研究所*

🌐 **Live Demo / 在线体验**: https://LabScriptAI.cn  

---

## 📖 Abstract / 摘要

**[English]**  
Laboratory automation enhances experimental throughput and reproducibility, yet widespread adoption is constrained by the expertise required for robotic programming. Here, we developed **LabscriptAI**, a multi-agent framework enabling large language models (LLMs) to autonomously generate and validate executable Python scripts for protein engineering automation. LabscriptAI automated cell-free protein synthesis (CFPS) and characterization of 298 green fluorescent protein (GFP) variants designed by 53 teams from 5 countries in a student challenge. The top variant matched the performance of extensively optimized superfolder GFP (sfGFP) while exploring a distinct sequence space. Furthermore, LabscriptAI orchestrated distributed automation across biofoundry and fume hood-enclosed systems to engineer enzyme variants utilizing formaldehyde—a sustainable but hazardous substrate—identifying a double mutant with 7-fold enhanced catalytic efficiency. The platform implements rigorous safety measures, including biosecurity screening, physical containment, and human-in-the-loop oversight, to safeguard autonomous protein engineering. LabscriptAI democratizes laboratory automation by eliminating programming barriers while promoting responsible research practices.

**[中文]**  
实验室自动化能够显著提高实验通量和可重复性，但机器人编程所需的专业知识限制了其广泛应用。为此，我们开发了 **LabscriptAI**，这是一个多智能体（Multi-agent）框架，能够赋能大语言模型（LLMs）自主生成并验证用于蛋白质工程自动化的可执行 Python 脚本。LabscriptAI 成功自动化了无细胞蛋白合成（CFPS）流程，并对来自 5 个国家 53 支学生队伍设计的 298 个绿色荧光蛋白（GFP）变体进行了表征。结果显示，表现最佳的变体在探索不同序列空间的同时，达到了经过广泛优化的超折叠 GFP（sfGFP）的性能水平。此外，LabscriptAI 还协调了跨越生物铸造厂和通风橱封闭系统的分布式自动化流程，用于工程化利用甲醛（一种可持续但有害的底物）的酶变体，最终鉴定出一个催化效率提高 7 倍的双突变体。该平台实施了严格的安全措施，包括生物安全筛查、物理遏制和“人在回路（Human-in-the-loop）”监管，以保障自主蛋白质工程的安全性。LabscriptAI 通过消除编程障碍普及了实验室自动化，同时促进了负责任的研究实践。

---

## 🧠🏗️ System Architecture / 系统架构

**[English]**  
LabscriptAI employs a **Multi-Agent Architecture** orchestrated by LangGraph, separating high-level planning from low-level code implementation.

1.  **Task Planning Agent**: Coordinates workflow processing. It translates natural language requests into structured Standard Operating Procedures (SOPs) and initiates human-in-the-loop dialogue for validation.
2.  **Code Graph Backend**: An iterative code generation engine featuring:
    *   **Coder Agent**: Generates initial Python scripts utilizing domain knowledge (RAG) and hardware profiles.
    *   **Reviewer Agent**: Validates code using platform-specific simulators (Opentrons Simulator, PyLabRobot, pyFluent).
    *   **Precise Refactoring Engine (PRE)**: Instead of regenerating entire scripts upon error, PRE analyzes simulation logs to generate targeted `SEARCH/REPLACE` patches, ensuring convergence and stability.

**[中文]**  
LabscriptAI 采用由 LangGraph 编排的**多智能体架构**，实现了高层任务规划与底层代码实现的解耦。

1.  **任务规划智能体 (Task Planning Agent)**：负责协调工作流处理。它将用户的自然语言需求转化为结构化的标准操作程序（SOP），并启动“人在回路”对话进行确认。
2.  **代码图后端 (Code Graph Backend)**：一个迭代式的代码生成引擎，包含：
    *   **编码智能体 (Coder Agent)**：利用领域知识（RAG）和硬件配置文件生成初始 Python 脚本。
    *   **审查智能体 (Reviewer Agent)**：调用平台特定的模拟器（Opentrons Simulator, PyLabRobot, pyFluent）验证代码。
    *   **精准重构引擎 (Precise Refactoring Engine, PRE)**：当验证出错时，PRE 不会重新生成整个脚本，而是分析模拟日志，生成针对性的 `SEARCH/REPLACE` 补丁，从而保证代码收敛和稳定性。

![System Architecture](Picture/MainFigure1_1115.png)

### 🎯 Precise Refactoring Engine / 精准重构引擎

**[English]**  
Traditional LLM-based code generation often struggles with "fixing one bug but introducing another" when regenerating full files. LabscriptAI's **Precise Refactoring Engine (PRE)** adopts a patching strategy. It locates the specific error block based on simulator feedback and applies a minimal edit, significantly reducing token usage and improving success rates.

**[中文]**  
传统的基于 LLM 的代码生成在重新生成整个文件时，经常会遇到“修复一个 bug 但引入另一个 bug”的问题。LabscriptAI 的 **精准重构引擎 (PRE)** 采用补丁策略。它根据模拟器的反馈定位具体的错误代码块，并应用最小化的编辑，显著减少了 Token 消耗并提高了成功率。

![Precise Refactoring Engine](Picture/修复PRE的原理和案例.png)

---

## ✨🌍 Key Features / 核心特性

### 1. Cross-Platform Support / 跨平台支持

**[English]**  
LabscriptAI is hardware-agnostic, supporting major liquid-handling platforms through unified interfaces and adapter layers:
*   **Opentrons (OT-2 & Flex)**: Native support via Opentrons Python API v2.
*   **Tecan (Fluent & EVO)**: Supported via our custom-developed **[pyFluent](pyFluent/README.md)** library, compiling Python to `.gwl` worklists.
*   **Hamilton (Vantage & STAR)**: Integrated via the open-source **PyLabRobot** driver.

**[中文]**  
LabscriptAI 具有硬件无关性，通过统一接口和适配层支持主流液体处理平台：
*   **Opentrons (OT-2 & Flex)**：通过 Opentrons Python API v2 提供原生支持。
*   **Tecan (Fluent & EVO)**：通过我们需要自研的 **[pyFluent](pyFluent/README.md)** 库支持，将 Python 代码编译为 `.gwl` 工作列表。
*   **Hamilton (Vantage & STAR)**：集成开源驱动 **PyLabRobot** 进行支持。

![Cross Platform Validation](Picture/MFigure2%20-%20副本.png)
*Figure 2: Cross-platform validation of the iGEM plate reader calibration protocol on Opentrons, Tecan Fluent, and Hamilton Vantage.*

### 2. Complex Workflow Automation / 复杂工作流自动化

**[English]**  
In the **CAPE (Critical Assessment of Protein Engineering)** competition, LabscriptAI automated the screening of 298 student-designed GFP variants. It handled complex deck layouts, multi-step dilutions, and plate reader integration.

**[中文]**  
在 **CAPE (蛋白质工程关键评估)** 竞赛中，LabscriptAI 自动化了 298 个学生设计的 GFP 变体的筛选工作。它成功处理了复杂的甲板布局、多步稀释以及酶标仪集成。

![GFP Layout](Picture/GFPFLEX自动化布局.png)

### 3. Responsible AI & Safety / 负责任的 AI 与安全

**[English]**  
*   **Biosecurity Screening**: Integration with the **IBBIS Common Mechanism** to screen DNA sequences for potential threats before synthesis.
*   **Physical Containment**: Distributed automation strategies for handling hazardous reagents (e.g., Formaldehyde) in fume hood-enclosed robots.
*   **Human-in-the-loop**: Mandatory human validation for critical SOPs and safety-sensitive operations.

**[中文]**  
*   **生物安全筛查**：集成 **IBBIS 通用机制**，在合成前对 DNA 序列进行潜在威胁筛查。
*   **物理遏制**：针对危险试剂（如甲醛），采用在通风橱封闭机器人中进行的分布式自动化策略。
*   **人在回路**：关键 SOP 和安全敏感操作强制要求人类验证。

---

## ⚙️🚀 Quick Start / 快速开始

For detailed installation instructions, please refer to [📄 Installation Guide (docs/INSTALLATION.md)](docs/INSTALLATION.md).
详细安装指南请参阅 [📄 安装文档 (docs/INSTALLATION.md)](docs/INSTALLATION.md)。

### Environment Setup / 环境配置

**[English]**  
We use a **dual-virtual-environment architecture** to isolate Opentrons dependencies (which often conflict with modern AI libraries).
**[中文]**  
我们采用**双虚拟环境架构**来隔离 Opentrons 依赖（其经常与现代 AI 库发生冲突）。

```powershell
# Windows PowerShell (One-click setup / 一键安装)
.\scripts\setup-uv.ps1
```

### Running the Application / 运行应用

1.  **Start Backend / 启动后端**:
    ```powershell
    .\.venv\Scripts\Activate.ps1
    uv run python main.py
    ```

2.  **Start Frontend / 启动前端**:
    ```bash
    cd labscriptAI-frontend
    npm run dev
    ```

3.  **Access / 访问**:
    Open your browser at **http://localhost:5173**

---

## 📚📂 Documentation / 文档资源

*   [🛠️ Installation & Troubleshooting / 安装与故障排除](docs/INSTALLATION.md)
*   [📚 API Architecture / API 架构说明](docs/API_ARCHITECTURE.md)
*   [🧪 pyFluent Library / pyFluent 库文档](pyFluent/README.md)

---

## 🔗 References & Citation / 引用

If you use LabscriptAI in your research, please cite our work, thanks!:
如果您在研究中使用了 LabscriptAI，请引用我们的工作，感谢大佬！：

> Yuan G, et al. "Autonomous liquid-handling robotics scripting through large language models enables accessible and safe protein engineering workflows." bioRxiv (2025): 2025-09.

**Key Technologies used / 关键技术:**
*   **LangGraph**: [Build resilient language agents as graphs](https://langchain-ai.github.io/langgraph/).
*   **CodeAct**: [Executable Code Actions](https://arxiv.org/abs/2402.01030).
*   **PyLabRobot**: [Hardware-agnostic interface for liquid-handling robots](https://docs.pylabrobot.org/).
*   **IBBIS**: [Common Mechanism for DNA Synthesis Screening](https://www.ibbis.org/).

---

## 📧 Contact / 联系方式
Facing code problem please contact: gaoyuanbio@qq.com

*State Key Laboratory for Quantitative Synthetic Biology, Shenzhen Institute of Synthetic Biology,CAS.*
*中国科学院深圳先进技术研究院合成生物学研究所，定量合成生物学重点实验室*
>>>>>>> upstream/main

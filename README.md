# LabScript AI

这是一个基于人工智能的工具，旨在通过自然语言交互，帮助用户快速生成和验证多种实验室自动化设备的控制脚本或协议。

## 主要功能

- **AI 驱动的脚本生成**：使用自然语言描述您的实验流程或设备操作，AI 将根据您的描述生成相应的控制脚本。
- **多平台兼容性（目标）**：
    - 当前重点支持 **Opentrons** (Flex & OT-2, 多 API 版本)。
    - 计划扩展支持 **pylabrobot** 等框架，以兼容更多类型的实验室设备。
- **模拟验证 (Opentrons)**：生成的 Opentrons 协议会通过模拟器验证，确保代码的基础正确性。
- **错误分析与建议 (Opentrons)**：当 Opentrons 模拟验证失败时，AI 会分析错误原因并提供改进建议。
- **对话式交互**：通过命令行界面与 AI 进行对话，逐步细化需求并生成脚本。
- **可扩展框架**：设计允许未来集成更多设备类型、验证工具和 AI 能力。

## 安装与运行

### 系统要求

- Python 3.8 或更高版本
- Git

### 安装步骤

1.  **克隆本仓库**
    ```bash
    git clone https://github.com/KRATSZ/LabScript-AI.git
    cd LabScript-AI
    ```

2.  **创建虚拟环境 (推荐)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\\Scripts\\activate  # Windows
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置 API 密钥**
    - 复制 `.env.example` (如果未来提供) 或手动创建 `.env` 文件。
    - 在 `.env` 文件中设置您的 `OPENAI_API_KEY`。
    ```dotenv
    OPENAI_API_KEY='your_openai_api_key_here'
    ```

### 运行应用

通过命令行启动交互式会话：
```bash
python run.py  # 或者 python main.py，取决于最终确定的入口脚本
```
应用将在您的终端中启动，您可以开始与 AI 对话来生成脚本。

## 使用方法 (命令行示例)

1.  启动应用 (`python run.py`)。
2.  AI 可能会首先询问您目标设备类型、API 版本或其他基本信息。
3.  输入您的实验需求，例如：
    > "帮我写一个 Opentrons OT-2 (API 2.16) 的协议，从试剂槽 A1 吸取 50uL 试剂，加入到 96 孔板 B2。"
    > "我想用 pylabrobot 控制一个 Hamilton STAR，执行一个简单的液体转移：从 TubeRack1 的 A1 孔取 100uL，加到 PlateCarrier1 上的 96 孔板 C3。" (未来功能)
4.  AI 会根据您的描述生成代码，并可能进行模拟验证（如果支持）。
5.  根据 AI 的反馈（成功、失败、建议）继续对话或获取最终脚本。

## 示例提问 (Opentrons 重点)

- "生成一个 Opentrons Flex (API 2.20) 方案，用 1000uL 移液器将 A1 孔的 50uL 液体转移到 B2 孔。"
- "设计一个 OT-2 (API 2.18) 实验，从源板的 A1-A6 孔吸取 100uL 液体，分别分配到目标板的 B1-B6 孔，并为每次转移更换吸头。"
- "编写一个 Opentrons 协议，实现从第一列开始，在 96 孔板中进行 1:2 的连续稀释，共稀释 6 列，每孔总体积 200uL。"

## 技术架构

本项目采用以下技术构建：

- **Python**: 主要开发语言。
- **LangChain**: 构建和管理 AI 代理、工具链和记忆的核心框架。
- **DeepSeek API**: 提供底层的自然语言处理和代码生成能力。
- **Opentrons Python API**: 用于生成和模拟验证 Opentrons 协议。
- **(未来) Pylabrobot**: 用于支持更广泛的实验室自动化设备。
- **(计划) Asyncio**: 用于提升 I/O 密集型操作（如 API 调用）的性能和响应速度 (参考未来改进)。
- **(计划) RAG (Retrieval Augmented Generation)**: 计划集成，通过检索相关文档提高生成代码的准确性和可靠性 (参考未来改进)。

### 主要文件说明

- **`main.py`**: **命令行交互界面 (CLI) 的主入口**。负责处理用户输入循环、选择机器人/API版本、调用 LangChain Agent 处理请求、显示对话历史和最终生成的代码。
- **`langchain_agent.py`**: **核心 AI 代理逻辑**。配置 LangChain Agent Executor，包括：
    - 初始化 LLM (当前配置为 DeepSeek API)。
    - 定义 `opentrons_simulator` 工具，并集成 `opentrons_utils.py` 中的模拟函数。
    - 构建复杂的 ReAct Prompt Template，包含工具使用说明、上下文（有效名称、代码示例）、格式要求和逐步思考指令。
    - 设置对话记忆 (ConversationBufferMemory)。
- **`opentrons_utils.py`**: **Opentrons 专属工具集**。主要包含 `run_opentrons_simulation` 函数，该函数：
    - 接收 Python 代码字符串。
    - 查找并执行 `opentrons_simulate` 命令行工具（处理 PATH 和常见安装位置）。
    - 将代码写入临时文件进行模拟。
    - 捕获并解析模拟器的 stdout 和 stderr，处理编码问题。
    - 返回包含模拟结果（成功/失败/日志）的字符串，供 Agent 分析。
    - 包含 `SimulateToolInput` Pydantic 模型用于 LangChain 工具的输入校验。
- **`config.py`**: **配置与知识库**。
    - 存储 API 密钥和基础 URL (当前为 DeepSeek)。
    - 定义 LLM 模型名称。
    - 包含大量的 **硬编码知识**，作为 RAG 的初步替代或补充，供 Prompt 引用：
        - `VALID_LABWARE_NAMES`
        - `VALID_INSTRUMENT_NAMES`
        - `VALID_MODULE_NAMES`
        - `CODE_EXAMPLES` (包含 OT-2 和 Flex 的代码片段)
- **`run.py`**: **启动器脚本**。提供一个简单的菜单，允许用户选择启动命令行版本 (`main.py`) 或安装依赖。是运行应用推荐的起点 (`python run.py`)。
- **`requirements.txt`**: 列出项目运行所需的 Python 依赖库 (如 `langchain-openai`, `opentrons` 等)。
- **`test_imports.py`**: **环境检查脚本**。用于快速测试核心依赖项（如 LangChain, OpenAI/DeepSeek 客户端, 本地工具模块）是否已正确安装并可以导入。
- **`.env`**: (需用户手动创建) 用于安全地存储 API 密钥等敏感信息，避免硬编码在代码中。由 `.gitignore` 排除，不上传到版本库。
- **`.gitignore`**: 定义 Git 在进行版本控制时应忽略的文件和目录（如 `__pycache__`, `venv`, `.env`, `generated_protocols` 等）。
- **`generated_protocols/`**: (通常由 `.gitignore` 排除) 建议用于存放由 AI 生成并验证通过的协议文件，便于管理。
- **`otcoder engineer.py`**: **历史遗留文件**。原项目主脚本，现已重构，仅作留档说明。

## 常见问题

**Q: 我需要安装 Opentrons App 才能使用这个工具吗？**
A: 仅使用模拟验证功能不需要完整的 Opentrons App，但需要安装 `opentrons` Python 包。实际在机器人上运行生成的协议则需要相应的 Opentrons 环境。

**Q: 支持哪些大语言模型？**
A: 当前主要基于 DeepSeek API。未来可以通过 LangChain 的抽象轻松扩展支持其他模型。

**Q: 如何添加对新设备的支持？**
A: 需要编写相应的工具函数（类似 `opentrons_utils.py`），提供代码生成模板、验证逻辑（如果可能），并将其集成到 `langchain_agent.py` 的工具集中。

**Q: 为什么生成的代码无法工作？**
A: 可能原因包括：自然语言描述不够清晰、AI 理解偏差、目标设备/API 的限制、或是 AI 生成的 Bug。请检查 AI 的错误分析（如果提供），并尝试更精确地描述您的需求。

## 未来改进方向与建议

### 1. (计划) 提升响应速度：引入异步操作 (`Asyncio`)
*   **目标**：减少用户等待时间，尤其是在调用外部大模型 API 时。
*   **核心技术**：Python 的 `asyncio` 库。
*   **实施概要**：识别 I/O 阻塞点 (如 API 调用)，利用 LangChain 的异步接口和 `asyncio` 进行重构。

### 2. (计划) 提高生成准确性：集成 RAG (Retrieval Augmented Generation)
*   **目标**：利用专业知识库（如 API 文档、最佳实践）增强大模型，生成更准确、可靠的脚本。
*   **核心技术**：检索增强生成（RAG）。
*   **实施概要**：构建包含相关文档的知识库，选择或搭建 RAG 系统（如使用 LangChain 相关组件），在生成前检索上下文信息并注入 Prompt。

### 3. 扩展设备兼容性
*   逐步集成 `pylabrobot` 或其他库，支持更多自动化平台。
*   为不同平台开发相应的代码生成模板和验证工具。

### 4. 增强交互体验
*   引入更复杂的对话管理，支持上下文修正、多轮澄清。
*   提供更结构化的输入方式（例如，表单辅助）来补充自然语言。

## 问题与反馈

如果您在使用过程中遇到任何问题，或有改进建议，请通过以下方式联系我们：

- 在 GitHub 仓库提交 Issue: [https://github.com/KRATSZ/LabScript-AI/issues](https://github.com/KRATSZ/LabScript-AI/issues)
- 发送邮件至：gaoyuanbio@qq.com

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件（如果未来添加）。

---

*本项目旨在简化各种实验室自动化脚本的创建过程，赋能研究人员更高效地利用自动化工具。* 
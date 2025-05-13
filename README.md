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

- **`run.py` / `main.py`**: 应用的命令行入口点。负责初始化环境、处理用户输入循环、调用核心 Agent。
- **`langchain_agent.py`**: 定义核心的 LangChain Agent 或 Chain。集成 LLM、工具（如代码生成、模拟验证）、记忆模块，处理用户请求的核心逻辑。
- **`opentrons_utils.py`**: 包含与 Opentrons 相关的工具函数，如协议模拟、错误分析、API 版本处理等。未来可能重构或增加类似 `pylabrobot_utils.py` 的文件。
- **`config.py`**: 存放配置信息，如 API 密钥加载逻辑、默认模型参数、支持的设备/API 列表等。
- **`requirements.txt`**: 列出项目所需的 Python 依赖库。
- **`.env`**: (需用户创建) 存储敏感信息，如 API 密钥。由 `.gitignore` 排除。
- **`.gitignore`**: 定义 Git 应忽略的文件和目录。
- **`generated_protocols/`**: (可能由 `.gitignore` 排除) 用于存放 AI 生成的协议文件。

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
# Opentrons Lab Agent Skills

[Agent Skills](https://agentskills.io) 是一种简单、开放的格式，用于为AI代理赋予新能力。此仓库包含专注于 Opentrons 的技能，可扩展 Claude 在 Opentrons OT-2 和 Flex 实验室机器人方面的能力。

## 简介

这些技能教会 Claude 如何：

- **编写和修订 Python 协议**，为 OT-2 和 Flex 机器人提供正确的台面设置、实验器皿加载、移液器配置和摄像头捕获
- **使用本地 Opentrons 运行时验证协议**，利用 Opentrons 的分析和模拟工具，以及环境就绪检查
- **通过 LAN HTTP API 控制机器人**，用于健康检查、摄像头预览、协议上传、运行创建和播放控制
- **参考经过验证的协议库**，包含 800+ 示例协议和可复用代码片段

## 包含的技能

| 技能 | 描述 | 使用场景 |
|------|------|----------|
| `opentrons-protocol-author` | 为 Opentrons 机器人起草或重构 Python 协议 | 编写新协议、编辑现有协议或审查协议代码 |
| `opentrons-simulation-repair` | 通过 simulate -> parse -> edit 循环修复协议 | 仿真报错后逐轮修复、定位最高优先级 blocker |
| `opentrons-protocol-verify` | 使用本地 Opentrons 运行时分析和模拟协议 | 检查协议是否有效、模拟执行、诊断环境问题 |
| `opentrons-robot-lan` | 通过 LAN HTTP API 与机器人交互 | 查询机器人状态、查看摄像头、上传协议、控制运行 |
| `opentrons-protocol-library` | 参考内置协议库与代码片段 | 搜索现有协议、查看协议元数据、提取参考代码片段 |

## MCP 服务器

本项目包含一个实用的 MCP 服务器 `mcp-servers/opentrons-mcp/`，提供紧凑的本地仿真和实时机器人控制工具。

### MCP 工具列表

**本地仿真工具：**
- `doctor_local_runtime` - 检查本地 Opentrons 运行时就绪状态
- `simulate_protocol` - 在本地运行协议仿真
- `parse_simulation_output` - 解析仿真输出，提取问题分类

**机器人状态工具：**
- `robot_status` / `robot_health` - 获取机器人健康状态
- `module_status` - 获取模块状态
- `get_slot_occupation` - 获取槽位占用情况
- `list_available_slots` - 列出可用槽位
- `list_tip_candidates` - 列出可用针头候选
- `suggest_next_tip_well` - 建议下一个针头位置
- `is_home_safe` - 检查是否可安全归位

**运行控制工具：**
- `create_run_context` - 创建运行上下文（维护模式）
- `load_pipette` - 加载移液器
- `load_labware` - 加载实验器皿
- `load_module` - 加载模块
- `move_labware` - 移动实验器皿
- `cleanup_motion` - 清理运动状态，归位机械臂和抓取器
- `create_run` - 创建协议运行
- `control_run` - 控制运行（播放/暂停/停止）
- `get_runs` - 获取运行列表
- `run_history` - 获取运行历史
- `get_run_status` - 获取运行状态

**协议工具：**
- `get_protocols` - 获取协议列表
- `upload_protocol` - 上传协议到机器人
- `run_protocol` - 执行协议（含本地仿真门控）
- `execute_protocol_recovery` - 执行协议恢复
- `recover_tip_pickup` - 恢复针头拾取

**错误恢复工具：**
- `reconcile_state` - 协调机器人状态
- `parse_error` - 解析错误
- `suggest_recovery_action` - 建议恢复动作

**视觉工具：**
- `camera_status` - 获取摄像头状态
- `configure_camera` - 配置摄像头
- `capture_preview_image` - 捕获预览图像
- `capture_run_image` - 捕获运行图像
- `list_data_files` - 列出数据文件
- `download_data_file` - 下载数据文件
- `analyze_image_with_kimi` - 使用 Kimi 分析图像

### 启动 MCP 服务器

```bash
cd mcp-servers/opentrons-mcp
npm install
node index.js
```

### MCP 配置示例

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js"]
    }
  }
}
```

### 仿真优先工作流

```text
1. doctor_local_runtime  # 检查环境就绪
2. simulate_protocol     # 运行本地仿真
3. parse_simulation_output  # 解析仿真输出
4. 编辑协议
5. 重复直到仿真通过
```

### run_protocol 安全门控

`run_protocol` 工具现在强制执行本地仿真门控：

```text
doctor_local_runtime → simulate_protocol → parse_simulation_output
                                                      ↓
                                          仿真通过？──否→ 阻止真机执行
                                                      ↓是
                                              开始真机执行
```

如果仿真失败，工具返回 `blocked_real_execution: true`，不会启动真机运行。

## 与 Codex 一起使用

Codex 的主入口是仓库根目录下的 `AGENTS.md`。在仓库根目录启动 Codex 时，它会同时看到：

- `AGENTS.md` 中的工作流规则
- `skills/` 中的技能说明
- `reference-code/Protocols-develop/` 中的内置参考协议库
- `examples/reference-protocols/` 中的小型可运行参考 protocol

推荐流程：

1. 先用 `search_protocols.py search` 查内置参考库
2. 用 `show` 查看候选 protocol 的 README、源码路径和元数据
3. 用 `snippet` 抽取局部代码片段
4. 参考 `examples/reference-protocols/` 或起草新协议
5. 运行 `doctor`、`analyze` 或 `simulate`
6. 只有本地验证通过后才进入 MCP 真机执行

## 与 Claude Code 一起使用

### 方式 1：项目级技能（推荐）

最简单的方法是在项目的 `skills/` 目录下保存技能。Claude Code 会自动发现以下位置的技能：

| 位置 | 作用范围 |
|------|----------|
| `<project>/skills/` | 项目特定技能（此仓库的结构） |
| `<project>/.claude/skills/` | Claude Code 原生位置 |
| `~/.claude/skills/` | 可在项目中使用的用户级技能 |

**在 Claude Code 中使用这些技能：**

1. 克隆或复制此仓库到您的项目目录
2. 确保 `skills/` 文件夹在您的工作目录中
3. 在该目录中启动 Claude Code
4. Claude 将自动发现并加载技能

当处理协议时，只需描述您的需求：

```
编写一个 OT-2 协议，将液体从 96 孔板转移到 384 孔板。
```

Claude 将自动使用 `opentrons-protocol-author` 技能。

推荐 Claude Code 工作流：

1. 先用 `opentrons-protocol-library` 查内置参考库
2. 再选择 `reference-code/Protocols-develop/` 或 `examples/reference-protocols/` 中的参考 protocol
3. 使用 `opentrons-protocol-author` 起草或改写
4. 使用 `opentrons-protocol-verify` 或 `opentrons-simulation-repair`
5. 本地通过后再调用 `opentrons-mcp`

### 方式 2：作为 Claude Code 插件安装

您可以将这些技能打包为 Claude Code 插件以便分发：

```bash
/plugin marketplace add <your-org>/opentrons-lab-agent-skills
```

或者通过将单个技能复制到 `~/.claude/skills/` 来安装。

### 方式 3：手动安装技能

将单个技能目录复制到您的 Claude Code 技能位置：

```bash
# Linux/macOS
cp -r skills/opentrons-protocol-author ~/.claude/skills/
cp -r skills/opentrons-simulation-repair ~/.claude/skills/
cp -r skills/opentrons-protocol-verify ~/.claude/skills/
cp -r skills/opentrons-robot-lan ~/.claude/skills/
cp -r skills/opentrons-protocol-library ~/.claude/skills/

# Windows
xcopy /E /I skills\opentrons-protocol-author %USERPROFILE%\.claude\skills\
```

## 在其他项目中使用此项目

有多种方式可以在您的其他项目中使用 Opentrons-Lab-Agent 的技能和 MCP 服务器。

### 方式 1：Git Submodule（推荐用于长期维护）

```bash
# 在您的项目中添加为 submodule
git submodule add https://github.com/SmartisanNaive/Opentrons-Lab-Agent.git opentrons-lab-agent

# 初始化 submodule
git submodule update --init --recursive

# 更新到最新版本
cd opentrons-lab-agent && git pull origin main && cd .. && git add opentrons-lab-agent && git commit -m "更新 opentrons-lab-agent"
```

**优点：** 可追踪版本变化，易于更新
**注意：** 需要在 `.gitmodules` 中配置技能路径

### 方式 2：直接复制 Skills 文件夹

```bash
# 在您的项目目录结构
your-project/
├── your_protocols/
├── skills/                    # 复制 skills 目录到这里
│   ├── opentrons-protocol-author/
│   ├── opentrons-simulation-repair/
│   ├── opentrons-protocol-verify/
│   ├── opentrons-robot-lan/
│   └── opentrons-protocol-library/
├── .claude/
└── pyproject.toml
```

```bash
# 克隆或复制 skills 到目标项目
cp -r /path/to/Opentrons-Lab-Agent/skills ./skills
```

### 方式 3：使用 MCP 服务器

在 Claude Code 的 MCP 配置中添加 MCP 服务器：

**macOS/Linux:** `~/.claude/settings.json` 或项目级 `.claude/mcp.json`
**Windows:** `%USERPROFILE%\.claude\settings.json`

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js"],
      "env": {
        "OPENTRONS_PYTHON": "/ABSOLUTE/PATH/TO/.venv/bin/python"
      }
    }
  }
}
```

### 方式 4：通过 uv 依赖引用

如果您使用 Python 和 uv 作为包管理器，可以创建一个包装包：

```bash
# 在 pyproject.toml 中添加
[tool.uv]
packages = [
    { path = "/path/to/Opentrons-Lab-Agent/src" }
]
```

### 方式 5：创建符号链接

```bash
# 创建符号链接而非复制
ln -s /path/to/Opentrons-Lab-Agent/skills ./skills
ln -s /path/to/Opentrons-Lab-Agent/mcp-servers ./mcp-servers
```

### 环境变量配置

无论使用哪种方式，您可能需要配置以下环境变量：

```bash
# 协议库路径（可选）
export OPENTRONS_PROTOCOL_LIBRARY_PATH="/path/to/Opentrons-Lab-Agent/reference-code/Protocols-develop"

# MCP 服务器的 Python 路径（可选）
export OPENTRONS_PYTHON="/path/to/your-project/.venv/bin/python"
```

### 快速开始

1. **克隆此仓库**
```bash
git clone https://github.com/SmartisanNaive/Opentrons-Lab-Agent.git
```

2. **在目标项目中创建 skills 目录并链接**
```bash
mkdir -p your-project/skills
ln -s /path/to/Opentrons-Lab-Agent/skills/* your-project/skills/
```

3. **启动 Claude Code**
```bash
cd your-project
claude
```

4. **使用技能**
```
编写一个 Flex 协议，进行 1:2 系列稀释。
```

## Python 环境

这些技能假设使用 `uv` 管理 Python 以实现可重现的环境。

```bash
# 创建本地虚拟环境
uv venv .venv

# 通过 uv 运行脚本
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
```

## 技能结构

每个技能都遵循 [Agent Skills 规范](https://agentskills.io/specification)：

```
skill-name/
├── SKILL.md          # 必需：元数据 + 指令
├── scripts/           # 可选：可执行代码
├── references/        # 可选：文档
├── assets/           # 可选：模板、资源
└── evals/            # 推荐：测试用例
```

`SKILL.md` 文件包含：
- **Frontmatter**：`name`、`description`、`license`、`compatibility`
- **Instructions**：Claude 的分步指导
- **References**：捆绑资源的链接

## 使用示例

### 编写协议

```
我需要一个 Flex 协议来进行系列稀释，起始 100ul 在第一个孔中，
1:2 稀释跨越 96 板的 8 个孔。
```

### 验证协议

```
检查这个协议是否有效：protocols/my_protocol.py
```

### 控制机器人

```
我的 OT-2 在 192.168.1.50。检查其健康状态并显示摄像头预览。
```

## 测试和评估

每个技能都包含 `evals/evals.json` 测试用例，遵循 [Agent Skills 评估模式](https://agentskills.io/docs/skill-creation/evaluating-skills)：

```bash
# 验证技能结构
skills-ref validate ./skills/opentrons-protocol-author
skills-ref validate ./skills/opentrons-simulation-repair
skills-ref validate ./skills/opentrons-protocol-verify
skills-ref validate ./skills/opentrons-robot-lan
skills-ref validate ./skills/opentrons-protocol-library
```

## 仓库布局

```
Opentrons-Lab-Agent/
├── mcp-servers/
│   └── opentrons-mcp/                # MCP 服务
├── examples/
│   └── reference-protocols/          # Codex / Claude Code 参考 protocol
├── reference-code/
│   └── Protocols-develop/            # 内置只读参考协议库
├── skills/
│   ├── opentrons-protocol-author/    # 协议编写技能
│   ├── opentrons-simulation-repair/  # 仿真修复技能
│   ├── opentrons-protocol-verify/    # 协议验证技能
│   ├── opentrons-robot-lan/         # 机器人 API 控制技能
│   └── opentrons-protocol-library/  # 协议知识库引用
├── src/opentrons_lab_agent/             # 辅助模块
├── tests/                               # 单元测试
├── README.md                            # 英文文档
├── README_CN.md                         # 中文文档
├── AGENTS.md                            # 跨工具代理配置
└── CONTRIBUTING.md                      # 开发指南
```

## 协议库知识库

`opentrons-protocol-library` 默认会优先使用仓库内置的 `reference-code/Protocols-develop/`。解析顺序如下：

1. `--library /path/to/Protocols-develop`
2. `OPENTRONS_PROTOCOL_LIBRARY_PATH=/path/to/Protocols-develop`
3. 仓库内 `reference-code/Protocols-develop`
4. 兼容旧工作区的同级 `../Protocols-develop`

内置参考库是只读参考资产，不属于本项目核心运行逻辑。

配置后可引用：

- **800+ 经过验证的协议**，附带 README 文档
- **协议源码**，可直接抽取可复用代码片段
- **fields.json** 参数定义
- **Cookbook.md**，当所选快照包含该文件时可直接引用
- **protolib/ 目录**中的辅助函数

### 搜索协议库

```bash
# 按关键字搜索协议
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  search "magnetic beads" "DNA cleanup"

# 查看某个 protocol 的 README、源码和元数据
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  show 00222e

# 提取聚焦片段
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  snippet 00222e serial plasma

# 列出 Cookbook 模式
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py cookbook

# 列出协议分类
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py categories
```

### 示例查询

- "是否有磁珠 DNA 清理的协议？"
- "向我展示如何实现液位跟踪"
- "找一个进行系列稀释的协议"
- "基于 CSV 的板布局的模式是什么？"
- "查看 00222e 的源码和运行时元数据"
- "从 00222e 提取和 plasma 或 serial 相关的代码片段"

## 视觉集成

本项目提供两层视觉相关功能：

**机器人端摄像头控制**（`src/opentrons_lab_agent/robot_api.py`）：
- `GET /camera` - 获取摄像头状态
- `POST /camera` - 配置摄像头
- `POST /camera/cameraSettings` - 设置摄像头参数
- `POST /camera/capturePreviewImage` - 捕获预览图像

**MCP 端视觉工具**：
- `camera_status` - 摄像头状态
- `configure_camera` - 配置摄像头
- `capture_preview_image` - 捕获预览图像
- `capture_run_image` - 捕获运行图像
- `list_data_files` - 列出数据文件
- `download_data_file` - 下载数据文件
- `analyze_image_with_kimi` - 使用 Kimi 分析图像

**设计原则**：
- 图像采集保留在机器人 MCP 端
- 图像分析在独立步骤或未来的 MCP 中进行
- 使用 `image_path` 路径而非将二进制嵌入工具输出

**当前 Flex 限制**：
- `GET /camera` 可用
- `/camera/capturePreviewImage` 当前返回 `404`
- `captureImage` 通过命令队列可成功执行
- 历史图像可通过 `dataFiles` 获取

## 真实响应示例

### `robot_status`（Flex 真机，缩写）

```json
{
  "success": true,
  "data": {
    "ready_for_physical_action": true,
    "blockers": [],
    "health_summary": {
      "robot_model": "OT-3 Standard",
      "api_version": "8.8.1",
      "robot_serial": "FLXA2020240921002"
    }
  }
}
```

### `run_protocol`（Flex 空协议验证，缩写）

```json
{
  "success": true,
  "data": {
    "final_status": "succeeded",
    "requires_attention": false,
    "final_run_history": {
      "command_counts": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
      }
    }
  },
  "run_id": "5b6cc2d2-ef50-4da6-9f9f-090fc243ccfe",
  "session_id": "5b6cc2d2-ef50-4da6-9f9f-090fc243ccfe"
}
```

### `recover_tip_pickup`（真机修复恢复，缩写）

```json
{
  "success": true,
  "data": {
    "recovered_well": "B1",
    "resume_action": {
      "data": {
        "actionType": "resume-from-recovery"
      }
    },
    "final_run_history": {
      "status": "succeeded",
      "has_ever_entered_error_recovery": true
    }
  }
}
```

### `run_protocol` 被仿真门控拦截（缩写）

```json
{
  "success": false,
  "data": {
    "blocked_real_execution": true,
    "gate_stage": "simulate_protocol",
    "parsed_simulation_output": {
      "success": false,
      "issues": [
        { "category": "SYNTAX_OR_IMPORT" }
      ]
    }
  }
}
```

### `suggest_recovery_action` 目标槽位被占用（缩写）

```json
{
  "success": true,
  "data": {
    "recovery": {
      "action": "suggest_new_destination_slot",
      "escalate_to_human": true,
      "candidate_destination_slots": [
        { "slot_name": "A2", "confidence": "low" },
        { "slot_name": "B2", "confidence": "low" },
        { "slot_name": "C2", "confidence": "low" }
      ]
    }
  }
}
```

## 本地 Opentrons 运行时假设

验证技能对本地 Opentrons 运行时就绪性采取了谨慎的态度：

- 默认检查当前 Python 环境是否可以导入 `opentrons.cli` 和 `opentrons.simulate`
- 只有在显式提供 `--workspace-root` / `--api-root` / `--shared-data-root` 时，才会进入外部源码树模式
- 在外部源码树模式下，如有需要会注入最小的 `opentrons._version` 垫片
- 缺失依赖会被明确报告，而不是假装验证成功

这确保 Claude Code 提供关于本地可以执行什么和不能执行什么的准确反馈。

## 测试

### Python 单元测试

```bash
# 运行所有单元测试
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

### MCP 服务器测试

```bash
cd mcp-servers/opentrons-mcp
npm test
```

### 技能结构验证

```bash
skills-ref validate ./skills/opentrons-protocol-author
skills-ref validate ./skills/opentrons-simulation-repair
skills-ref validate ./skills/opentrons-protocol-verify
skills-ref validate ./skills/opentrons-robot-lan
skills-ref validate ./skills/opentrons-protocol-library
```

### 协议验证命令

```bash
# 检查 Opentrons 运行时就绪状态
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor

# 分析协议
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py \
  analyze path/to/protocol.py -- --check

# 模拟协议
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py \
  simulate path/to/protocol.py
```

### 机器人 API 命令

```bash
# 健康检查
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py \
  --host 192.168.1.50 health

# 捕获摄像头预览
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py \
  --host 192.168.1.50 capture-preview --output /tmp/preview.png
```

## 贡献

请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发和验证新技能的指南。

## 许可证

MIT

## 参考资料

- [Agent Skills 规范](https://agentskills.io/specification)
- [添加技能支持](https://agentskills.io/docs/client-implementation/adding-skills-support)
- [示例技能](https://github.com/anthropics/skills)
- [Opentrons 协议 API 文档](https://docs.opentrons.com/)

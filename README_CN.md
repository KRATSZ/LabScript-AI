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

## 本地 Opentrons 运行时假设

验证技能对本地 Opentrons 运行时就绪性采取了谨慎的态度：

- 默认检查当前 Python 环境是否可以导入 `opentrons.cli` 和 `opentrons.simulate`
- 只有在显式提供 `--workspace-root` / `--api-root` / `--shared-data-root` 时，才会进入外部源码树模式
- 在外部源码树模式下，如有需要会注入最小的 `opentrons._version` 垫片
- 缺失依赖会被明确报告，而不是假装验证成功

这确保 Claude Code 提供关于本地可以执行什么和不能执行什么的准确反馈。

## 贡献

请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发和验证新技能的指南。

## 许可证

MIT

## 参考资料

- [Agent Skills 规范](https://agentskills.io/specification)
- [添加技能支持](https://agentskills.io/docs/client-implementation/adding-skills-support)
- [示例技能](https://github.com/anthropics/skills)
- [Opentrons 协议 API 文档](https://docs.opentrons.com/)

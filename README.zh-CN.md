# Opentrons-Lab-Agent

[English README](README.md)

`Opentrons-Lab-Agent` 是一个面向 Claude Code 的插件式仓库，封装了与 Opentrons 相关的 Agent Skills，主要覆盖三类工作：

- 编写和修改 Python Protocol
- 检查本地 Opentrons 运行环境是否可以执行 protocol analyze / simulate
- 通过局域网 HTTP API 控制 OT-2 或 Flex 机器人，包括相机相关操作

本仓库遵循 Anthropic 公开的 skills 组织方式：每个 skill 都是独立目录，包含 `SKILL.md`，并可按需附带 `scripts/`、`references/`、`assets/`。仓库同时包含 `.claude-plugin/plugin.json`，因此也可以作为 Claude Code 的插件根目录使用。

## Python 环境

本项目默认使用 `uv` 管理 Python 虚拟环境。

- 使用 `uv venv .venv` 创建本地虚拟环境
- 使用 `uv run ...` 执行命令
- 除非你是在排查环境问题，否则不要混用系统 Python 或 `pip install`

如果你确实需要显式激活解释器，请使用 `uv` 创建出的 `.venv`；但本文档中的示例默认都采用 `uv run`。

## 包含的 Skills

- `skills/opentrons-protocol-author`
  - 用于起草、重构和修改 Opentrons Python Protocol。
  - 提供 OT-2 / Flex 的 protocol 模板，以及 metadata、runtime parameters、`capture_image()` 等简明参考。
- `skills/opentrons-protocol-verify`
  - 对本地 `opentrons` analyze / simulate 入口做包装。
  - 会先检查环境，再决定是否真正执行验证，避免把失败环境误报成“已验证”。
- `skills/opentrons-robot-lan`
  - 通过 Opentrons HTTP API 与局域网内机器人通信。
  - 覆盖 health、camera、preview capture、protocol upload、analysis、run 创建和 run action。

## 仓库结构

```text
Opentrons-Lab-Agent/
├── .claude-plugin/plugin.json
├── skills/
│   ├── opentrons-protocol-author/
│   ├── opentrons-protocol-verify/
│   └── opentrons-robot-lan/
├── src/opentrons_lab_agent/
└── tests/
```

## 在 Claude Code 中使用

这个仓库本身已经是 Claude Code 友好的插件结构：

- 插件元数据在 `.claude-plugin/plugin.json`
- skills 在 `skills/`
- Python 辅助代码在 `src/`

如果你通过 Claude Code 的插件方式分发，这个仓库已经符合对应结构。如果你更倾向于直接安装 skills，也可以把 `skills/` 下的各个目录单独复制到你的 Claude Code skills 目录中。

## 本地 Opentrons 运行环境假设

`opentrons-protocol-verify` 这个 skill 的设计是“保守且诚实”的。

它假设当前工作区里可能 vendored 了一份 Opentrons 源码，但这份源码不一定已经被安装成可直接运行的 Python 包。在当前工作区快照里，已有的 `opentrons/` 目录包含 `api/`、`api-client/` 和 `shared-data/`，但并不是一套完整可运行的本地开发环境。因此：

- 验证脚本会在运行时注入一个最小的 `opentrons._version` 模块
- 脚本会先检查 `opentrons.cli` 和 `opentrons.simulate` 是否真的可导入
- 如果缺少第三方依赖或必要的 sibling package，它会明确报错，而不会伪装成“验证通过”

这样做的目的，是让 Claude Code 明确区分“代码看起来合理”和“已经真实验证成功”。

## 示例命令

### 检查本地 analyze / simulate 是否可用

```bash
uv venv .venv
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
```

### 执行 protocol analyze

```bash
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py analyze path/to/protocol.py -- --check
```

### 查询局域网机器人状态

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
```

### 上传 protocol 并创建 analysis

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 upload-protocol path/to/protocol.py
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 analyze-protocol <protocol-id>
```

## 本仓库映射到的 Opentrons 源码入口

这些 skills 是基于当前工作区里已有的 Opentrons 源码入口编写的：

- protocol analyze 入口：`opentrons/api/src/opentrons/cli/analyze.py`
- protocol simulate 入口：`opentrons/api/src/opentrons/simulate.py`
- Python protocol 的相机方法：`opentrons/api/src/opentrons/protocol_api/protocol_context.py`
- HTTP API client 封装：`opentrons/api-client/src/`

## 测试

辅助模块附带了不依赖真实机器人的轻量测试：

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

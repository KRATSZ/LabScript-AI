# Plan: Package Opentrons-Lab-Agent as Distributable Claude Code Plugin

## Context

Opentrons-Lab-Agent 是一个 Claude Code 插件，包含 45+ MCP 工具、7 个 skills、YOLO 视觉检测和机器人控制能力。当前它依赖硬编码的相对路径和手动 Python 环境配置，无法作为可分发的插件直接使用。目标是将它打包为：**clone 即可用、首次调用视觉工具时自动安装依赖** 的 Claude Code 插件。

---

## Step 1: 创建集中路径解析模块 `lib/paths.js`

**新建**: `mcp-servers/opentrons-mcp/lib/paths.js`

提供单一来源的路径解析，所有模块通过它获取路径：

- `resolvePluginRoot()` — 优先使用 `CLAUDE_PLUGIN_ROOT` / `OPENTRONS_PLUGIN_ROOT` 环境变量，fallback 到 `__dirname` 相对路径（开发模式）
- `resolvePythonCandidates()` — Python 解释器查找链：`OPENTRONS_PYTHON` -> 插件内 `.venv` -> 仓库 `.venv` -> 系统 `python3`/`python`
- 导出常量：`PLUGIN_ROOT`, `SCRIPTS_DIR`, `WEIGHTS_DIR`, `DATA_DIR`, `ARTIFACTS_DIR`, `SESSION_STATE_DIR`, `RESULT_LOG_DIR`

---

## Step 2: 打包 YOLO 模型权重

**操作**: 复制权重文件到 `mcp-servers/opentrons-mcp/weights/`

```
mcp-servers/opentrons-mcp/weights/
  deck_v2_best.pt      # 从 labagentyolo/runs/detect/deck_v2/weights/best.pt 复制
  deck_pilot_best.pt   # 从 labagentyolo/runs/detect/deck_pilot/weights/best.pt 复制
```

修改 `.gitignore`：移除 `weights/` 全局忽略，改为忽略 `runs/` 和 `mcp-servers/opentrons-mcp/.venv/`

---

## Step 3: 更新 Python 视觉脚本路径解析

**修改**: `mcp-servers/opentrons-mcp/scripts/vision_check.py`

- 移除 `_REPO_ROOT = Path(__file__).resolve().parents[3]`（line 35）
- 新增 `_BUNDLED_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"`
- 重写 `_default_weights_chain()`（lines 38-58）：
  1. 环境变量 `OPENTRONS_DECK_YOLO_WEIGHTS`
  2. **打包权重** `weights/deck_v2_best.pt`, `weights/deck_pilot_best.pt`
  3. 向后兼容：兄弟仓库 `labagentyolo` 路径
  4. YOLOE fallback

---

## Step 4: 创建 Python 依赖自动引导模块

**新建**: `mcp-servers/opentrons-mcp/lib/python-bootstrap.js`

- `bootstrapVisionVenv()` — 检测 Python 可用性，自动创建 venv 并安装 `ultralytics` + `opencv-python-headless`
- 使用 marker file（`.opentrons-vision-ready`）避免重复安装
- 优先使用 `uv pip`，fallback 到标准 `pip`
- 结果缓存：首次引导后记住结果，不再重复检查

---

## Step 5: 更新 JS 模块使用集中路径

每个模块的改动模式相同：移除 `__filename`/`__dirname` 计算，改为从 `paths.js` 导入。

| 文件 | 改动 |
|------|------|
| `lib/vision-check.js` (lines 5-9, 40-74) | 导入 `SCRIPTS_DIR`, `resolvePythonCandidates`；集成 `ensureVisionPython` 自动引导；添加 graceful degradation |
| `lib/simulation.js` (lines 6-9, 46-78) | 导入 `SCRIPTS_DIR`, `resolvePythonCandidates`；替换 Python 候选列表 |
| `lib/health-check.js` (lines 7-8, 28, 57-63) | 导入 `PLUGIN_ROOT`, `resolvePythonCandidates`；替换 `PROJECT_ROOT` |
| `lib/state.js` (lines 6-8) | 导入 `SESSION_STATE_DIR` 替换 `__dirname` 计算 |
| `lib/result-log.js` (lines 8-10) | 导入 `RESULT_LOG_DIR` 替换 `__dirname` 计算 |
| `lib/authoring-tools.js` (lines 5-6, 47) | 导入 `PLUGIN_ROOT` 替换 `__dirname` 计算 |
| `index.js` (lines 103-130) | 导入 `PLUGIN_ROOT`, `ARTIFACTS_DIR`；移除 `resolveCameraArtifactRoot()` 和兄弟仓库 fallback |

---

## Step 6: 视觉工具优雅降级

**修改**: `lib/vision-check.js` 的 `runVisionCheck()` 函数

在调用 Python 之前：
1. 调用 `ensureVisionPython()` 尝试自动引导
2. 如果引导失败，返回结构化的降级响应（而非抛异常），包含安装指引
3. 其他非视觉工具（机器人控制、协议编写等）完全不受影响

---

## Step 7: 更新健康检查报告

**修改**: `lib/health-check.js` 的 `buildHealthCheck()`

添加 `vision_bootstrap` 状态字段，报告自动引导的结果。

---

## 验证方案

1. **路径解析验证**: 在非仓库目录下运行 `node -e "import('./lib/paths.js').then(m => console.log(m))"` 确认 `PLUGIN_ROOT` 正确
2. **权重解析验证**: 运行 `python3 -c "import vision_check; print(vision_check._default_weights_chain())"` 确认指向打包权重
3. **自动引导验证**: 删除 `.venv`，调用 `vision_check` 工具，确认自动创建 venv 并安装依赖
4. **优雅降级验证**: 在无 Python 环境下启动 MCP server，确认非视觉工具正常工作
5. **现有测试**: `cd mcp-servers/opentrons-mcp && npm test` 确认不破坏现有功能
6. **Claude Code 插件安装测试**: 通过 `/install-plugin` 安装后验证工具可用

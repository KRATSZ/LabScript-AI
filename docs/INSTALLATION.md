# 🔧 安装与环境配置指南

## ⚡ 前置要求
- **操作系统**: Windows 10/11 (推荐), macOS, Linux
- **Python**: 3.11 (必需，用于避免依赖编译问题)
- **Node.js**: 18+
- **包管理器**: [uv](https://github.com/astral-sh/uv) (用于快速 Python 依赖管理)

## 🚀 快速启动步骤

### 1. 环境初始化
本项目使用 `uv` 进行包管理，并采用**双虚拟环境架构** (`.venv` 和 `ot_env`) 来解决 Opentrons 旧版依赖与现代 AI 框架的冲突。

我们提供了一键安装脚本：

```powershell
# 在项目根目录下运行
.\scripts\setup-uv.ps1
```

该脚本会自动：
1. 检查 `uv` 是否安装。
2. 创建 `.venv` (主应用环境) 和 `ot_env` (Opentrons 隔离环境)。
3. 安装所有 Python 依赖。

### 2. 启动后端服务
**务必先激活主虚拟环境**：

```powershell
.\.venv\Scripts\Activate.ps1
```

启动后端 API 服务器：
```powershell
# 方式 A: 使用 uv 运行启动脚本
uv run python main.py

# 方式 B: 直接使用 uvicorn (开发模式)
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
```

### 3. 启动前端界面
新建一个终端窗口：
```bash
cd labscriptAI-frontend
npm install  # 仅首次运行需要
npm run dev
```

访问地址：http://localhost:5173

---

## 🔧 常见问题与解决方案 (Troubleshooting)

### 1. Windows 路径编码错误 (`[WinError 2]`)
**现象**: 安装时提示系统找不到文件，或因中文字符导致路径解析失败。
**解决**: 设置全局环境变量强制 Python 使用 UTF-8。以管理员身份运行 PowerShell：
```powershell
setx PYTHONUTF8 1 /M
# 设置后需重启电脑生效
```

### 2. 依赖编译失败 (`subprocess-exited-with-error`)
**现象**: 安装 numpy 等库时尝试编译源代码但失败。
**解决**: 确保使用 **Python 3.11**。高版本 (3.12+) 可能缺少部分库的预编译 Wheel 包。

### 3. 虚拟环境创建失败
**现象**: 提示目录已存在或拒绝访问。
**解决**: 手动删除 `.venv` 和 `ot_env` 文件夹（确保关闭 VS Code 或占用这些文件夹的终端），然后重新运行 `setup-uv.ps1`。

### 4. 终端提示符显示问题
如果想修改虚拟环境激活后的提示符名称，修改 `.venv/pyvenv.cfg`：
```cfg
prompt = LabscriptAI
```



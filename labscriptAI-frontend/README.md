# LabScript AI - 实验室自动化平台

LabScript AI 是一个基于 AI 的实验室自动化平台，帮助科学家和实验室技术人员使用 Opentrons 机器人自动化他们的实验流程。该平台可以将自然语言描述转换为精确的 Python 代码，并在 Opentrons 机器人上执行。

## 主要功能

- 🤖 自然语言转实验流程
- 🧪 支持 Opentrons OT-2 和 Flex 机器人
- 📝 AI 驱动的 SOP 生成
- 💻 自动 Python 代码生成
- 🔄 实验流程模拟和验证
- 🎥 3D 实验流程动画预览

## 数据流

1.  **硬件配置**:
    -   用户在 `HardwareConfigPage` 页面选择硬件配置。
    -   前端将配置信息通过 `AppContext` 存储。
2.  **SOP 定义**:
    -   用户在 `SopDefinitionPage` 页面定义 SOP。
    -   用户可以手动编写或使用 AI 生成。
    -   SOP 内容通过 `AppContext` 存储。
3.  **代码生成**:
    -   用户在 `CodeGenerationPage` 页面生成 Python 代码。
    -   前端将硬件配置和 SOP 内容发送到 `/api/generate-code` 端点。
    -   后端返回生成的代码，前端通过 `AppContext` 存储。
4.  **模拟**:
    -   用户在 `SimulationResultsPage` 页面模拟实验流程。
    -   前端将 Python 代码发送到 `/api/simulate` 端点。
    -   后端返回模拟结果，前端通过 `AppContext` 存储。
5.  **动画**:
    -   用户在 `AnimationPage` 页面查看 Opentrons 动画预览。
    -   主前端直接渲染 `web/opentrons-protocol-visualizer-web-slim` 中的 visualizer 组件。
    -   前端将生成的 Python protocol code 提交到主后端 `/api/visualizer/analyze/start`，再轮询 `/api/visualizer/analyze/jobs/{job_id}` 获取 playback analysis。
    -   动画页面不再依赖独立的 visualizer dev server。



## 项目结构

```
/
├── eslint.config.js        # ESLint 配置文件
├── index.html             # HTML 入口文件
├── package.json           # 项目依赖和脚本
├── postcss.config.js      # PostCSS 配置文件
├── README.md              # 项目说明文档
├── src                    # 源代码目录
│   ├── App.tsx            # 应用主组件
│   ├── components         # React 组件目录
│   │   ├── code           # 代码查看器组件
│   │   │   └── CodeViewer.tsx
│   │   ├── hardware       # 硬件配置相关组件
│   │   │   ├── DeckLayout.tsx
│   │   │   └── LabwareLibrary.tsx
│   │   ├── sop            # SOP 定义相关组件
│   │   │   ├── MarkdownEditor.tsx
│   │   │   └── MarkdownStyles.css
│   │   ├── welcome        # 欢迎页面组件
│   │   │   └── FeatureCard.tsx
│   │   ├── Layout.tsx         # 布局组件
│   │   └── StepProgress.tsx   # 步骤进度条组件
│   ├── context            # React Context
│   │   └── AppContext.tsx
│   ├── index.css          # 全局 CSS 样式
│   ├── main.tsx           # React 应用入口
│   ├── pages              # 页面组件目录
│   │   ├── AnimationPage.tsx
│   │   ├── CodeGenerationPage.tsx
│   │   ├── HardwareConfigPage.tsx
│   │   ├── SimulationResultsPage.tsx
│   │   ├── SopDefinitionPage.tsx
│   │   └── WelcomePage.tsx
│   ├── theme.ts           # Material UI 主题配置
│   ├── utils              # 实用工具函数
│   │   └── sampleData.ts
│   ├── vite-env.d.ts      # Vite 环境变量定义
│   └── types              # 类型定义
│       └── index.d.ts     # 全局类型定义
├── tailwind.config.js   # Tailwind CSS 配置文件
├── tsconfig.json          # TypeScript 配置文件
├── tsconfig.node.json     # Node.js TypeScript 配置文件
└── vite.config.ts       # Vite 配置文件

```

## 快速开始

1. 克隆仓库
2. 在项目根目录复制环境变量模板: `cp .env.example .env`
3. 安装依赖: `npm install`
4. 启动开发服务器: `npm run dev`
5. 如需动画预览，同时启动主后端 `uv run python main.py`，动画分析接口已并入主服务。

前端会从项目根目录 `.env` 读取 `VITE_API_BASE_URL` 等配置。

## API 集成指南

### 1. 实验流程生成 API

**目的**: 将用户描述转换为结构化实验流程

**后端要求**:
- 基于 OpenAI GPT-4 或类似模型
- 输入: 用户目标描述、硬件配置信息
- 输出: 结构化的 Markdown 格式 SOP
- 端点: `/api/generate-protocol`

**请求格式**:
```typescript
interface HardwareConfig {
  robotModel: 'Flex' | 'OT-2';
  apiVersion: string;
  leftPipette: string | null;
  rightPipette: string | null;
  useGripper: boolean;
  deckLayout: Record<string, LabwareItem | null>;
}

interface GenerateProtocolRequest {
  config: HardwareConfig;
  goal: string;
}
```

**响应格式**:
```typescript
interface GenerateProtocolResponse {
  sop: string;  // Markdown 格式的 SOP
  metadata: {
    estimatedTime: number;  // 预计执行时间（分钟）
    requiredLabware: string[];  // 所需耗材列表
    warnings: string[];  // 潜在问题警告
  };
}
```

### 2. 代码生成 API

**目的**: 将 SOP 转换为 Opentrons Python 代码

**后端要求**:
- 专门训练的代码生成模型
- 输入: SOP 内容、硬件配置
- 输出: Python 代码、代码结构说明
- 端点: `/api/generate-code`

**请求格式**:
```typescript
interface GenerateCodeRequest {
  sop: string;
  config: HardwareConfig;
}
```

**响应格式**:
```typescript
interface GenerateCodeResponse {
  code: string;  // Python 代码
  structure: {
    imports: string[];
    functions: Array<{
      name: string;
      description: string;
      parameters: Array<{
        name: string;
        type: string;
        description: string;
      }>;
    }>;
  };
}
```

### 3. 模拟 API

**目的**: 验证生成的实验流程

**后端要求**:
- Opentrons 协议模拟器集成
- 输入: Python 代码
- 输出: 模拟结果、错误检测、优化建议
- 端点: `/api/simulate`

**请求格式**:
```typescript
interface SimulateRequest {
  code: string;
  config: HardwareConfig;
}
```

**响应格式**:
```typescript
interface SimulationResponse {
  status: 'success' | 'warning' | 'error';
  message: string;
  details: string;
  suggestions: string[];
  metrics: {
    estimatedTime: number;
    tipUsage: number;
    liquidTransfers: number;
    steps: number;
  };
  log: Array<{
    time: string;
    message: string;
    type: 'info' | 'warning' | 'error';
  }>;
}
```

### 4. 动画生成 API

**目的**: 创建实验流程的 3D 可视化

**后端要求**:
- Three.js 渲染服务
- 输入: 模拟结果数据
- 输出: 动画关键帧数据
- 端点: `/api/animate`

**请求格式**:
```typescript
interface AnimationRequest {
  simulationResult: SimulationResponse;
}
```

**响应格式**:
```typescript
interface AnimationResponse {
  frames: Array<{
    timestamp: number;
    pipettePosition: {
      x: number;
      y: number;
      z: number;
    };
    action: string;
    details: Record<string, any>;
  }>;
  duration: number;
  steps: Array<{
    name: string;
    description: string;
    startFrame: number;
    endFrame: number;
  }>;
}
```

### 5. 数据存储 API

**目的**: 保存和管理用户的实验流程

**后端要求**:
- PostgreSQL 数据库
- 用户认证和授权
- 实验流程版本控制
- 端点: `/api/protocols`

**数据模型**:
```sql
-- 实验流程表
CREATE TABLE protocols (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  title TEXT NOT NULL,
  description TEXT,
  hardware_config JSONB,
  sop TEXT,
  python_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 版本控制表
CREATE TABLE protocol_versions (
  id UUID PRIMARY KEY,
  protocol_id UUID REFERENCES protocols(id),
  version INT,
  changes TEXT,
  sop TEXT,
  python_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**API 端点**:

1. 创建新实验流程:
```typescript
POST /api/protocols
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": string;
  "description": string;
  "hardwareConfig": HardwareConfig;
  "sop": string;
  "pythonCode": string;
}
```

2. 获取实验流程列表:
```typescript
GET /api/protocols
Authorization: Bearer <token>

Response:
{
  "protocols": Array<{
    "id": string;
    "title": string;
    "description": string;
    "createdAt": string;
    "updatedAt": string;
  }>;
}
```

3. 获取特定实验流程:
```typescript
GET /api/protocols/:id
Authorization: Bearer <token>

Response:
{
  "id": string;
  "title": string;
  "description": string;
  "hardwareConfig": HardwareConfig;
  "sop": string;
  "pythonCode": string;
  "versions": Array<{
    "version": number;
    "changes": string;
    "createdAt": string;
  }>;
}
```

## 环境变量

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# 协议生成 API
PROTOCOL_API_URL=your_protocol_api_url
PROTOCOL_API_KEY=your_protocol_api_key

# 模拟服务配置
SIMULATION_API_URL=your_simulation_api_url
SIMULATION_API_KEY=your_simulation_api_key

# 动画服务配置
ANIMATION_API_URL=your_animation_api_url
ANIMATION_API_KEY=your_animation_api_key

# 数据库配置
DATABASE_URL=your_database_url
```

## 贡献指南

1. Fork 仓库
2. 创建功能分支: `git checkout -b feature/新功能`
3. 提交更改: `git commit -m '添加新功能'`
4. 推送分支: `git push origin feature/新功能`
5. 提交 Pull Request

## 开源协议

基于 MIT 协议开源。详见 `LICENSE` 文件。

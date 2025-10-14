# 智能实验室系统架构 UML 图

## 🏗️ 整体架构图

```plantuml
@startuml SmartLab_Architecture

!theme plain
skinparam nodesep 50
skinparam ranksep 80

package "前端层 - XiaoZhi ESP32" {
    component "ESP32主控" as ESP32
    component "SSD1306 OLED显示屏" as OLED
    component "MAX98357A音频放大" as Audio
    component "INMP441麦克风" as Microphone
    component "ULN2003驱动板" as Driver
    component "ASR PRO语音识别" as ASR
}

package "后端服务层" {
    component "XiaoZhi Server" as XiaoZhiServer
    component "本地GPU语音服务" as GPUService
}

package "中间件层" {
    component "MCP服务器" as MCPServer
    component "Coze Agent平台" as CozePlatform
}

package "设备层" {
    component "ONVIF摄像头" as Camera
    component "Opentrons移液机器人" as Opentrons
    component "其他IoT设备" as IoTDevices
}

' 前端硬件连接
ESP32 --> OLED : I2C通信
ESP32 --> Audio : I2S音频输出
ESP32 --> Microphone : I2S音频输入
ESP32 --> Driver : 步进电机控制
ESP32 --> ASR : 语音识别处理

' 前端到后端连接
ESP32 --> XiaoZhiServer : WiFi/网络通信
XiaoZhiServer --> GPUService : 语音转文本请求
GPUService --> XiaoZhiServer : 识别结果返回

' 后端到中间件连接
XiaoZhiServer --> MCPServer : 本地MCP连接
XiaoZhiServer --> CozePlatform : 远程Agent调用

' MCP服务器到设备连接
MCPServer --> Camera : ONVIF协议控制
MCPServer --> Opentrons : 移液机器人控制
MCPServer --> IoTDevices : IoT设备管理

' Coze平台服务
CozePlatform --> XiaoZhiServer : LLM Agent服务
note right: 意图识别、SOP生成、Python脚本生成

@enduml
```

## 🔄 数据流程图

```plantuml
@startuml Data_Flow_Diagram

!theme plain
skinparam nodesep 40
skinparam ranksep 60

title 智能实验室数据流程图

actor "用户" as User
participant "ESP32前端" as Frontend
participant "XiaoZhi Server" as Backend
participant "GPU语音服务" as GPU
participant "Coze Agent" as Coze
participant "MCP服务器" as MCP
participant "Opentrons机器人" as Robot
participant "ONVIF摄像头" as Camera

' 用户交互流程
User -> Frontend: 语音指令
Frontend -> Frontend: ASR PRO语音识别
Frontend -> Backend: 发送文本指令

' 语音处理流程
Backend -> GPU: 语音转文本
GPU -> Backend: 返回识别文本

' Agent处理流程
Backend -> Coze: 发送用户指令
Coze -> Coze: 意图识别
Coze -> Coze: SOP生成
Coze -> Coze: Python脚本生成
Coze -> Backend: 返回生成的脚本

' 设备控制流程
Backend -> MCP: 发送控制指令
MCP -> Robot: Opentrons控制
MCP -> Camera: 摄像头控制

Robot -> MCP: 执行状态
Camera -> MCP: 视频流
MCP -> Backend: 设备状态反馈

' 结果返回流程
Backend -> Frontend: 处理结果
Frontend -> User: OLED显示/音频反馈

@enduml
```

## 🎯 系统组件图

```plantuml
@startuml Component_Diagram

!theme plain
skinparam nodesep 40

title 系统组件关系图

package "前端硬件组件" {
    component "ESP32开发板" as ESP32 {
        component "WiFi模块" as WiFi
        component "GPIO控制" as GPIO
        component "I2C接口" as I2C
        component "I2S接口" as I2S
    }

    component "显示模块" as Display {
        component "SSD1306 OLED" as OLED
        component "显示驱动" as DisplayDriver
    }

    component "音频模块" as Audio {
        component "INMP441麦克风" as Mic
        component "MAX98357A放大器" as Amp
        component "ASR PRO芯片" as ASR
    }

    component "电机控制" as Motor {
        component "ULN2003驱动板" as ULN2003
        component "步进电机" as Stepper
    }
}

package "后端服务组件" {
    component "XiaoZhi Server" as Server {
        component "Web服务器" as WebServer
        component "WebSocket服务" as WebSocket
        component "RESTful API" as RESTAPI
        component "设备管理器" as DeviceManager
    }

    component "GPU加速服务" as GPU {
        component "语音识别" as STT
        component "图像识别" as ImageRec
        component "CUDA加速" as CUDA
    }
}

package "中间件组件" {
    component "MCP服务器" as MCP {
        component "协议适配器" as ProtocolAdapter
        component "设备代理" as DeviceProxy
        component "消息队列" as MessageQueue
    }

    component "Coze Agent平台" as Coze {
        component "LLM模型" as LLM
        component "意图识别" as Intent
        component "SOP生成器" as SOP
        component "代码生成器" as CodeGen
    }
}

package "外部设备" {
    component "实验室设备" as LabDevices {
        component "Opentrons OT-2" as OT2
        component "Opentrons Flex" as Flex
        component "ONVIF摄像头" as ONVIF
        component "传感器" as Sensors
    }
}

' 硬件连接
ESP32.I2S --> Mic
ESP32.I2S --> Amp
ESP32.I2C --> OLED
ESP32.GPIO --> ULN2003
ESP32.WiFi --> Server.WebServer

' 服务连接
Server.WebSocket --> GPU.STT
Server.RESTAPI --> MCP.ProtocolAdapter
Server.DeviceManager --> Coze.Intent

' 中间件到设备
MCP.DeviceProxy --> OT2
MCP.DeviceProxy --> Flex
MCP.DeviceProxy --> ONVIF
MCP.DeviceProxy --> Sensors

' Coze内部流程
Coze.Intent --> Coze.SOP
Coze.SOP --> Coze.CodeGen
Coze.CodeGen --> Server.DeviceManager

@enduml
```

## 🔧 部署架构图

```plantuml
@startuml Deployment_Architecture

!theme plain
skinparam nodesep 50

title 系统部署架构图

node "前端设备" as Frontend {
    component "ESP32开发板" as ESP32
    component "OLED显示屏" as OLED
    component "音频模块" as AudioModule
    component "麦克风模块" as MicModule
    component "电机驱动板" as DriverBoard
}

node "本地服务器" as LocalServer {
    component "XiaoZhi Server" as XiaoZhiService
    component "GPU服务器" as GPUServer
    component "MCP服务器" as MCPService
}

cloud "云平台" as Cloud {
    component "Coze Agent平台" as CozeAgent
}

node "实验室设备" as LabEquipment {
    component "Opentrons机器人" as OpentronsRobot
    component "ONVIF摄像头" as IPCamera
    component "其他IoT设备" as IoTDevices
}

' 网络连接
Frontend --> LocalServer : WiFi/以太网
LocalServer --> Cloud : HTTPS/API调用
LocalServer --> LabEquipment : LAN/串口

' 内部连接
ESP32 --> OLED : I2C
ESP32 --> AudioModule : I2S
ESP32 --> MicModule : I2S
ESP32 --> DriverBoard : GPIO

XiaoZhiService --> GPUServer : 本地网络调用
XiaoZhiService --> MCPService : 本地进程通信
MCPService --> Opentrons Robot : TCP/IP
MCPService --> IPCamera : RTSP/ONVIF
MCPService --> IoTDevices : MQTT/HTTP

@enduml
```

## 📊 状态图

```plantuml
@startuml State_Diagram

!theme plain
skinparam nodesep 40

title 系统状态转换图

state "待机状态" as Idle {
    [*] --> Idle
    Idle --> Listening : 用户唤醒
}

state "监听状态" as Listening {
    Listening --> Processing : 接收到指令
    Listening --> Idle : 超时无输入
}

state "处理状态" as Processing {
    state "语音识别" as STT
    state "意图分析" as IntentAnalysis
    state "SOP生成" as SOPGeneration
    state "代码生成" as CodeGeneration
    state "设备控制" as DeviceControl

    [*] --> STT
    STT --> IntentAnalysis : 识别完成
    IntentAnalysis --> SOPGeneration : 意图确认
    SOPGeneration --> CodeGeneration : SOP生成完成
    CodeGeneration --> DeviceControl : 代码生成完成
    DeviceControl --> [*] : 控制完成
}

state "执行状态" as Executing {
    Executing --> Monitoring : 开始执行
}

state "监控状态" as Monitoring {
    Monitoring --> Executing : 调整参数
    Monitoring --> Complete : 执行完成
    Monitoring --> Error : 执行异常
}

state "完成状态" as Complete {
    Complete --> Idle : 返回待机
}

state "错误状态" as Error {
    Error --> Processing : 错误恢复
    Error --> Idle : 重置系统
}

Listening --> Processing
Processing --> Executing
Executing --> Monitoring

@enduml
```

## 🔄 序列图 - 完整工作流程

```plantuml
@startuml Complete_Workflow_Sequence

!theme plain
skinparam nodesep 40

title 完整工作流程序列图

actor "用户" as User
participant "ESP32前端" as ESP32
participant "XiaoZhi Server" as Server
participant "GPU语音服务" as GPU
participant "Coze Agent" as Coze
participant "MCP服务器" as MCP
participant "Opentrons机器人" as Robot

User -> ESP32: 语音唤醒词激活
ESP32 -> ESP32: ASR PRO语音识别
ESP32 -> Server: 发送识别到的文本

Server -> GPU: 语音转文本请求 (如果需要)
GPU -> Server: 返回精确文本

Server -> Coze: 发送用户指令和上下文
Coze -> Coze: 意图识别
Coze -> Coze: 实验需求分析
Coze -> Coze: SOP生成
Coze -> Coze: Opentrons Python代码生成
Coze -> Server: 返回生成的代码和执行计划

Server -> MCP: 发送设备控制指令
MCP -> Robot: 发送Python脚本执行
Robot -> Robot: 执行实验协议
Robot -> MCP: 实时执行状态
MCP -> Server: 设备状态反馈
Server -> ESP32: 处理结果
ESP32 -> User: OLED显示结果 + 音频反馈

alt 执行过程异常
    Robot -> MCP: 错误报告
    MCP -> Server: 错误信息
    Server -> Coze: 错误分析请求
    Coze -> Coze: 错误诊断
    Coze -> Coze: 修复策略生成
    Coze -> Server: 修复方案
    Server -> MCP: 修复指令
    MCP -> Robot: 执行修复
end

@enduml
```

这些UML图完整展示了智能实验室系统的架构设计，涵盖了从硬件层到应用层的完整技术栈，以及各组件之间的交互关系和数据流程。
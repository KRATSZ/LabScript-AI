# LabscriptAI Agent 流程 UML 图

## 🎯 整体架构图

```plantuml
@startuml LabscriptAI_Agent_Architecture

!theme plain
skinparam nodesep 50
skinparam ranksep 100

package "用户交互层" {
    actor User
    component "Coze Agent" as CozeAgent
}

package "意图识别层" {
    component "意图识别器" as IntentRecognizer
    database "意图规则库" as IntentRules
}

package "业务处理层" {
    component "日常对话模块" as ChatModule
    component "设备控制模块" as DeviceControlModule
    component "代码生成模块" as CodeGenerationModule
}

package "Coze执行层" {
    component "Coze工作流" as CozeWorkflow
    component "Coze Agent" as CozeAgent
    component "设备控制插件" as DevicePlugin
}

package "硬件层" {
    component "OT-2 机器人" as OT2
    component "Flex 机器人" as Flex
}

package "存储层" {
    database "配置库" as ConfigDB
    database "协议库" as ProtocolDB
    database "日志库" as LogDB
}

' 用户交互流程
User --> CozeAgent : 自然语言输入
CozeAgent --> IntentRecognizer : 意图识别请求
IntentRecognizer --> IntentRules : 查询规则
IntentRules --> IntentRecognizer : 返回匹配规则
IntentRecognizer --> CozeAgent : 意图识别结果

' 意图路由
CozeAgent --> ChatModule : 日常闲聊
CozeAgent --> DeviceControlModule : 设备控制
CozeAgent --> CodeGenerationModule : 代码生成

' 业务处理流程
ChatModule --> User : 系统介绍和指导

DeviceControlModule --> CozeWorkflow : 设备控制请求
CozeWorkflow --> CozeAgent : 协议处理
CozeAgent --> DevicePlugin : 设备通信
DevicePlugin --> OT2 : OT-2控制
DevicePlugin --> Flex : Flex控制

CodeGenerationModule --> CozeWorkflow : 代码生成请求
CozeWorkflow --> CozeAgent : 协议生成
CozeAgent --> CozeAgent : 迭代优化
CozeAgent --> DevicePlugin : 代码验证

' 数据存储访问
CozeWorkflow --> ConfigDB : 硬件配置
CozeAgent --> ProtocolDB : 协议模板
CozeWorkflow --> LogDB : 操作日志

@enduml
```

## 🔄 详细流程图

```plantuml
@startuml LabscriptAI_Detailed_Flow

!theme plain
skinparam nodesep 30
skinparam ranksep 40

title LabscriptAI Agent 详细处理流程

actor User
participant "Coze Agent" as Coze
participant "意图识别" as Intent
participant "路由分发" as Router
participant "日常对话" as Chat
participant "设备控制" as Device
participant "代码生成" as Code
participant "Coze工作流" as CozeWorkflow
participant "Coze Agent Backend" as CozeAgent
participant "Coze设备插件" as DevicePlugin
database "设备" as Hardware

' 主流程
User -> Coze: 用户输入
activate Coze
Coze -> Intent: 意图识别
activate Intent

alt 日常闲聊
    Intent -> Router: 日常闲聊意图
    Router -> Chat: 处理日常对话
    Chat -> Coze: 返回对话结果
elseif 设备控制
    Intent -> Router: 设备控制意图
    Router -> Device: 设备控制处理
    Device -> CozeWorkflow: 控制请求
    CozeWorkflow -> CozeAgent: 协议处理
    CozeAgent -> DevicePlugin: 设备通信
    DevicePlugin -> Hardware: 执行操作
    Hardware -> DevicePlugin: 执行结果
    DevicePlugin -> CozeAgent: 状态反馈
    CozeAgent -> CozeWorkflow: 处理结果
    CozeWorkflow -> Device: 控制结果
    Device -> Coze: 返回控制结果
elseif 代码生成
    Intent -> Router: 代码生成意图
    Router -> Code: 代码生成处理
    Code -> CozeWorkflow: 生成请求
    CozeWorkflow -> CozeAgent: 协议生成
    activate CozeAgent

    loop 迭代优化
        CozeAgent -> CozeAgent: SOP生成
        CozeAgent -> CozeAgent: 代码生成
        CozeAgent -> DevicePlugin: 代码验证
        DevicePlugin -> CozeAgent: 验证结果
    end

    CozeAgent -> CozeWorkflow: 生成结果
    deactivate CozeAgent
    CozeWorkflow -> Code: 代码结果
    Code -> Coze: 返回代码结果
else 结束聊天
    Intent -> Router: 结束聊天意图
    Router -> Coze: 结束对话
end

deactivate Intent
Coze -> User: 返回处理结果
deactivate Coze

@enduml
```

## 🎯 意图识别流程图

```plantuml
@startuml Intent_Recognition_Flow

!theme plain
skinparam nodesep 40
skinparam ranksep 50

title 意图识别处理流程

start

:用户输入;

if (包含结束聊天关键词?) then (是)
    :返回"结束聊天"意图;
    stop
endif

if (包含日期时间问题?) then (是)
    :返回"日常闲聊"意图;
    stop
endif

if (包含设备控制关键词?) then (是)
    :返回"设备控制"意图;
    stop
endif

if (包含代码生成关键词?) then (是)
    :返回"代码生成"意图;
    stop
endif

if (包含日常闲聊关键词或输入简短?) then (是)
    :返回"日常闲聊"意图;
    stop
endif

:默认返回"日常闲聊"意图;

stop

@enduml
```

## 🔧 代码生成流程图

```plantuml
@startuml Code_Generation_Flow

!theme plain
skinparam nodesep 30
skinparam ranksep 40

title 代码生成详细流程

start

:接收用户需求;
:分析硬件配置;

:生成SOP文档;
note right: 标准操作程序

:生成Python代码;
note right: 根据设备类型选择模板

:代码模拟验证;
note right: Coze设备插件验证

if (验证成功?) then (是)
    :返回成功结果;
    stop
else (否)
    :分析错误类型;

    if (超过最大迭代次数?) then (是)
        :返回深度错误分析;
        stop
    else (否)
        :执行错误修复;
        note right: Coze Agent智能修复
    endif
endif

:重新生成代码;
:再次验证;

stop

@enduml
```

## 🤖 设备控制流程图

```plantuml
@startuml Device_Control_Flow

!theme plain
skinparam nodesep 30
skinparam ranksep 40

title 设备控制处理流程

start

:接收控制指令;

:设备类型识别;
note right: OT-2 或 Flex

:Coze设备连接;
note right: Coze设备控制协议

if (连接成功?) then (是)
    :发送控制指令;

    if (指令执行成功?) then (是)
        :返回执行结果;
        note right: 状态和结果
    else (否)
        :错误处理;
        :返回错误信息;
    endif
else (否)
    :连接错误处理;
    :返回连接失败信息;
endif

stop

@enduml
```

## 🔄 系统状态图

```plantuml
@startuml System_State_Diagram

!theme plain
skinparam nodesep 50

title LabscriptAI 系统状态图

state "待机状态" as Idle {
    [*] --> Idle
    Idle --> Listening : 用户连接
}

state "监听状态" as Listening {
    Listening --> Processing : 接收输入
}

state "处理状态" as Processing {
    state "意图识别" as IntentRecog
    state "业务处理" as Business
    state "结果生成" as ResultGen

    [*] --> IntentRecog
    IntentRecog --> Business : 识别完成
    Business --> ResultGen : 处理完成
    ResultGen --> [*] : 生成完成
}

state "错误处理" as ErrorHandling {
    [*] --> ErrorHandling
    ErrorHandling --> [*] : 错误修复
}

state "结束状态" as Ended {
    [*] --> Ended
    Ended --> [*] : 会话结束
}

Listening --> Processing
Processing --> ErrorHandling : 出现错误
Processing --> Listening : 处理完成
Processing --> Ended : 用户结束会话
ErrorHandling --> Processing : 错误修复完成

@enduml
```

## 📊 组件交互图

```plantuml
@startuml Component_Interaction

!theme plain
skinparam nodesep 40

title 组件交互关系图

component "用户" as User
component "Coze Agent" as Coze
component "意图识别器" as Intent
component "路由器" as Router
component "日常对话模块" as Chat
component "设备控制模块" as Device
component "代码生成模块" as Code
component "Coze工作流" as CozeWorkflow
component "Coze Agent" as CozeAgentBackend
component "Coze设备插件" as DevicePlugin
component "OT-2" as OT2
component "Flex" as Flex

interface "意图识别接口" as IIntent
interface "处理接口" as IProcess
interface "API接口" as IAPI
interface "设备接口" as IDevice

User -up- IIntent
Coze -up- IIntent
Intent -up- IIntent

Intent -right- IProcess
Router -up- IProcess
Chat -up- IProcess
Device -up- IProcess
Code -up- IProcess

Device -right- IProcess
Code -right- IProcess
CozeWorkflow -up- IProcess

CozeWorkflow -right- CozeAgentBackend
CozeAgentBackend -right- DevicePlugin

DevicePlugin -down- IDevice
OT2 -up- IDevice
Flex -up- IDevice

User --> Coze : 1. 输入
Coze --> Intent : 2. 识别意图
Intent --> Router : 3. 路由请求
Router --> Chat : 4a. 日常对话
Router --> Device : 4b. 设备控制
Router --> Code : 4c. 代码生成

Device --> CozeWorkflow : 5b. 设备请求
Code --> CozeWorkflow : 5c. 生成请求

CozeWorkflow --> CozeAgentBackend : 6. 业务处理
CozeAgentBackend --> DevicePlugin : 7. 设备调用

DevicePlugin --> OT2 : 8a. OT-2控制
DevicePlugin --> Flex : 8b. Flex控制

OT2 --> DevicePlugin : 9a. OT-2结果
Flex --> DevicePlugin : 9b. Flex结果

DevicePlugin --> CozeAgentBackend : 10. 设备结果
CozeAgentBackend --> CozeWorkflow : 11. 处理结果
CozeWorkflow --> Device/Code : 12. 业务结果
Device/Code --> Router : 13. 模块结果
Router --> Intent : 14. 路由结果
Intent --> Coze : 15. 识别结果
Coze --> User : 16. 响应

@enduml
```

## 🎯 时序图

```plantuml
@startuml LabscriptAI_Sequence_Diagram

!theme plain
skinparam nodesep 40

title LabscriptAI 时序图 (代码生成场景)

actor User
participant "Coze Agent" as Coze
participant "意图识别" as Intent
participant "路由器" as Router
participant "代码生成模块" as CodeGen
participant "Coze工作流" as CozeWorkflow
participant "Coze Agent" as CozeAgentBackend
participant "Coze设备插件" as DevicePlugin
participant "OT-2/Flex" as Device

User -> Coze: "我需要一个PCR协议"
Coze -> Intent: 意图识别请求
Intent -> Coze: 代码生成意图
Coze -> Router: 路由请求
Router -> CodeGen: 处理代码生成
CodeGen -> CozeWorkflow: 生成请求
CozeWorkflow -> CozeAgentBackend: SOP生成请求
CozeAgentBackend --> CozeAgentBackend: 生成SOP文档
CozeAgentBackend --> CozeAgentBackend: 生成Python代码
CozeAgentBackend --> DevicePlugin: 代码验证请求
DevicePlugin -> Device: 模拟执行
Device --> DevicePlugin: 执行结果
DevicePlugin --> CozeAgentBackend: 验证结果

alt 验证成功
    CozeAgentBackend -> CozeWorkflow: 成功结果
    CozeWorkflow -> CodeGen: 代码生成完成
    CodeGen -> Router: 处理完成
    Router -> Coze: 路由结果
    Coze -> Intent: 最终结果
    Intent -> Coze: 结果确认
    Coze -> User: 返回生成的代码
else 验证失败
    CozeAgentBackend --> CozeAgentBackend: 错误分析
    CozeAgentBackend --> CozeAgentBackend: 代码修复
    CozeAgentBackend --> DevicePlugin: 重新验证
    DevicePlugin -> Device: 再次执行
    Device --> DevicePlugin: 新的结果
    DevicePlugin --> CozeAgentBackend: 验证结果
    CozeAgentBackend --> CozeWorkflow: 修复后结果
    CozeWorkflow -> CodeGen: 最终代码
    CodeGen -> Router: 完成处理
    Router -> Coze: 成功结果
    Coze -> User: 返回修复后的代码
end

@enduml
```

这些UML图完整展示了LabscriptAI Agent的架构设计、处理流程和组件交互关系，为系统设计和实现提供了清晰的视觉指导。
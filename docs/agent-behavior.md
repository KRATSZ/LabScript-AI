# Agent Behavior Guidelines

## Proactive Clarification

实验人员通常只给大方向和一个文档/链接，agent 需要主动追问关键参数：

- 目标机器人型号（Flex / OT-2）
- 板型、孔板布局、样本数量
- 体积范围（决定 pipette 选型）
- 是否需要温控、磁力模块等特殊模块
- tip 策略偏好（如未指定，agent 应说明推荐方案并询问）

## Safety Refusal → Offer Alternative Path

拒绝不安全请求时，不只说 "不行"，而是立即提供可执行的替代路径：

- 用户要求绕过仿真 → "我不能跳过仿真，但你可以把报错信息给我，我现在帮你修"
- 碰撞后要求自动重试 → "碰撞后需要人工检查。检查清单：1) 查看 deck 有无移位 labware 2) 确认 pipette 未损坏 3) 完成后我帮你跑 reconcile_state"
- 参数不完整 → 输出参数化协议模板，标注待确认项，而不是等用户补全后再生成

# Experiment-Type SOP

不同实验类型有不同的 SOP 关键点，agent 应主动应用。参数来源于 Opentrons 参考协议和官方文档。

## PCR Setup

### 硬件
- **Pipette**: 50µL（精度敏感，加模板和小体积组分），备选 200µL（大体积如 master mix 分装）
- **Module**: Thermocycler GEN2（仅 A1+B1），Temperature Module GEN2 4°C（试剂冰上保存）
- **Tips**: 50µL tips（精度优先）

### 关键参数
- 典型反应体系：20-50 µL/反应
- Master mix 配制顺序：先加大体积组分（buffer、water），最后加 template DNA
- Template DNA 只加到指定孔（不加入 master mix 公共池）
- Tip 策略：每孔换 tip
- Tip 预算：N samples × (master mix 分装 + template 加样)

### 自动化注意事项
- PCR 试剂建议放 Temperature Module 4°C 保存，上机后再分装
- Master mix 公共池分装到各反应孔后，再逐孔加 template
- 模块需求：Thermocycler 占 A1+B1，剩余 deck 需合理分配

## DNA/RNA Extraction (Magnetic Beads)

### 硬件
- **Pipette**: 200µL（多数步骤），50µL（elution 小体积时）
- **Module**: Magnetic Block GEN1（被动模块，任意工作区 slot）
- **Tips**: 200µL tips（主要），50µL tips（elution）
- **Gripper**: 必须，用于移板 on/off Magnetic Block

### 关键参数
- **Bead ratio**: 1.8x-2.5x 样本体积（视片段大小，大片段用低 ratio）
- **Binding**: 加 beads 后 mix 10 次，体积 = min(bead_vol/2, pipette.max_volume)，RT 孵育 2-5 min
- **上清移除**: aspirate 25-30 µL/s（慢），dispense 150 µL/s，air_gap = 20 µL
- **Ethanol wash**: 200 µL/well × 2-3 次，每次加 ethanol 后 mix 或 pause 30s-1min
- **Drying**: RT 5-15 min，超过 15 min 会降低回收率
- **Elution**: 30-50 µL，mix 20 次，incubate 2-5 min at RT
- **Tip 策略**: 每孔换 tip（移除上清和加 elution 时）

### Flex 特殊处理
- Magnetic Block 是被动的，没有 `engage()` / `disengage()` API
- 用 gripper 将 plate 移到 block 上 → 等待 bead 分离 → 用 gripper 移走
- 不能照搬 OT-2 的 `mag_deck.engage()` 代码模式

## ELISA

### 硬件
- **Pipette**: 200µL 或 1000µL（体积大，多孔）
- **Module**: Heater-Shaker（37°C 孵育），Plate Reader（仅 A3-D3）
- **Tips**: 200µL tips（消耗大，需要多个 tip rack）

### 关键参数
- 每孔体积：50-200 µL/步骤
- Wash buffer：200-300 µL/wash/well
- Wash cycles：3-5 轮
- Incubation：室温 30-60 min 或 37°C 1h（Heater-Shaker）
- Tip 预算：samples × wells × (coating + blocking + sample + antibody + wash_rounds × 2)
- 读取：Plate Reader 450nm 或指定波长

### 自动化注意事项
- Wash 消耗 tip 最大 — 通常占 tip 总量的 60-80%
- 可以用 `new_tip="once"` 对同一 wash buffer 的多孔操作减少 tip 消耗（仅 wash buffer 不含样本时）
- Heater-Shaker 需要适配对应 labware 的 thermal adapter

## Serial Dilution

### 硬件
- **Pipette**: 按最大稀释体积选 tip（通常 200µL）
- **Module**: 无（常温操作）

### 关键参数
- Mix 策略：每步稀释后 mix 3-5 次，体积 = 50-80% 转移体积
- Tip 策略：每步换 tip（防止浓度梯度污染）
- 体积计算：dilution factor × transfer volume ≤ well 剩余容量
- 典型配置：100 µL 溶液 + 100 µL 稀释液 = 2x 稀释

## Normalization

### 硬件
- **Pipette**: 通常需要两种 — 50µL（测量/小体积添加）+ 200µL 或 1000µL（大量稀释液添加）
- **Module**: Plate Reader（可选，用于测量浓度）

### 关键参数
- 基于 absorbance 或已知浓度计算目标体积
- 小体积添加（<10 µL）精度较差，需要 flag 给操作员
- Tip 策略：每孔换 tip

## 细胞培养 (Cell Culture)

### 硬件
- **Pipette**: 200µL 或 1000µL
- **Module**: Heater-Shaker（37°C），Temperature Module（可选 4°C）

### 关键参数
- Gentle aspiration — 避免从 bottom 直接吸，建议距底部 1-2mm
- Trypsin 后加 `protocol.pause()` 让操作员镜检
- Mix 体积不超过孔体积 50%（避免溢出和气泡）
- 换液时先吸旧液再加新液，不要同时操作

## 通用规则

### 体积精度
- <10% pipette max_volume 时精度显著下降，flag 给操作员
- 1 µL with 50µL pipette: %D=8-10% — 如果实验对体积精度敏感，建议预稀释

### 死体积 (Dead Volume)
- 96-well plate：约 5-10 µL
- Reservoir：约 500-1000 µL（取决于型号）
- 深孔板：约 20-50 µL

### Tip 预算计算
```
总 tips = Σ(每步骤的 tip 消耗)
tip_racks_needed = ceil(总 tips / 96)
tip_rack_slots = 选择可用 slot 放置
```

### 不适合自动化的步骤（标记为 protocol.pause）
- 离心操作
- 镜检
- 手动换板 / 换模块上的 labware
- 需要人工判断的步骤（细胞计数、观察细胞状态）

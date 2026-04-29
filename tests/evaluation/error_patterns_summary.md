# Opentrons 协议代码常见错误类型与修复方法总结

基于 Inagaki 2023 论文数据分析的 624 个错误实例

## 错误统计概览

| 错误类型 | 出现次数 | 占比 | 严重程度 |
|---------|---------|------|----------|
| API版本错误 | 498次 | 79.8% | 🔴 高 |
| 语法错误 | 175次 | 28.0% | 🟡 中 |
| 吸头管理错误 | 116次 | 18.6% | 🟡 中 |
| 体积超限错误 | 105次 | 16.8% | 🟡 中 |
| 器具未找到错误 | 15次 | 2.4% | 🟠 中高 |
| 仪器错误 | 12次 | 1.9% | 🟠 中高 |
| 槽位冲突错误 | 3次 | 0.5% | 🟢 低 |

## 详细错误分析与修复方法

### 1. API版本错误 (79.8% - 最常见)

**错误表现：**
- `apiLevel` 版本不匹配
- 使用了过时的 API 语法
- 新版本功能在旧 API 中不支持

**典型错误示例：**
```python
# 错误：使用了过时的 API
from opentrons import labware, instruments, robot

# 错误：缺少 metadata
def run():
    pass
```

**修复方法：**
```python
# 正确：使用现代 API
from opentrons import protocol_api

metadata = {
    'apiLevel': '2.13'  # 使用最新的稳定版本
}

def run(protocol: protocol_api.ProtocolContext):
    # 协议内容
    pass
```

**预防措施：**
- 始终使用最新的 `apiLevel`
- 参考官方文档的最新语法
- 避免使用 `labware.load()` 等废弃方法

---

### 2. 语法错误 (28.0%)

**错误表现：**
- Python 语法错误
- 缩进错误
- 变量名错误
- 类型错误

**典型错误示例：**
```python
# 错误：缩进问题
def run(protocol):
tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', '1')

# 错误：变量名错误
pipette.aspirate(100, source_wel)  # wel -> well

# 错误：类型错误
pipette.transfer(volume, source, dest)  # volume 未定义
```

**修复方法：**
```python
# 正确：注意缩进
def run(protocol):
    tiprack = protocol.load_labware('opentrons_96_tiprack_1000ul', '1')

# 正确：检查拼写
pipette.aspirate(100, source_well)

# 正确：定义变量
volume = 100
pipette.transfer(volume, source, dest)
```

**预防措施：**
- 使用代码编辑器的语法检查
- 仔细检查变量名拼写
- 确保正确的缩进（4个空格）

---

### 3. 吸头管理错误 (18.6%)

**错误表现：**
- 吸头用完但没有新的吸头架
- 重复使用吸头导致污染
- 吸头架配置不当

**典型错误示例：**
```python
# 错误：只配置了一个吸头架，但需要大量吸头
tip_rack = protocol.load_labware('opentrons_96_tiprack_1000ul', '1')
pipette = protocol.load_instrument('p1000_single', 'right', tip_racks=[tip_rack])

# 96次转移，但只有96个吸头
for i in range(96):
    pipette.transfer(100, source[i], dest[i])  # 会用完吸头
```

**修复方法：**
```python
# 正确：配置多个吸头架
tip_rack_1 = protocol.load_labware('opentrons_96_tiprack_1000ul', '1')
tip_rack_2 = protocol.load_labware('opentrons_96_tiprack_1000ul', '2')
pipette = protocol.load_instrument('p1000_single', 'right', 
                                  tip_racks=[tip_rack_1, tip_rack_2])

# 或者重复使用吸头（适用于相同试剂）
pipette.pick_up_tip()
for i in range(8):  # 同一个试剂的多次分配
    pipette.aspirate(100, source)
    pipette.dispense(100, dest[i])
pipette.drop_tip()
```

**预防措施：**
- 计算所需吸头数量
- 合理规划吸头架数量
- 考虑是否可以重复使用吸头

---

### 4. 体积超限错误 (16.8%)

**错误表现：**
- 吸取体积超过移液器最大容量
- 分配体积超过容器容量
- 体积计算错误

**典型错误示例：**
```python
# 错误：P1000最大容量1000µL，但要吸取1500µL
pipette_p1000.aspirate(1500, source)

# 错误：96孔板每孔最大容量通常200-300µL
pipette.transfer(500, source, plate['A1'])
```

**修复方法：**
```python
# 正确：分次吸取大体积
def transfer_large_volume(pipette, volume, source, dest):
    max_volume = pipette.max_volume
    remaining = volume
    
    while remaining > 0:
        current_volume = min(remaining, max_volume)
        pipette.transfer(current_volume, source, dest)
        remaining -= current_volume

# 或者使用更大容量的移液器
pipette_p1000 = protocol.load_instrument('p1000_single', 'right')
```

**预防措施：**
- 了解移液器的容量限制
- 了解容器的容量限制
- 实现体积检查函数

---

### 5. 器具未找到错误 (2.4%)

**错误表现：**
- 使用了不存在的器具名称
- 器具名称拼写错误
- 器具库版本不匹配

**典型错误示例：**
```python
# 错误：器具名称不存在
plate = protocol.load_labware('custom_96_wellplate_200ul', '1')
rack = protocol.load_labware('my_special_tube_rack', '2')
```

**修复方法：**
```python
# 正确：使用标准器具名称
plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
rack = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2')

# 检查可用器具
print(protocol.list_labware_definitions())
```

**预防措施：**
- 查阅官方器具库文档
- 使用 `protocol.list_labware_definitions()` 检查
- 验证器具名称拼写

---

### 6. 仪器错误 (1.9%)

**错误表现：**
- 移液器型号不存在
- 移液器挂载错误
- 移液器配置错误

**典型错误示例：**
```python
# 错误：不存在的移液器型号
pipette = protocol.load_instrument('p500_single', 'left')

# 错误：挂载位置冲突
pipette1 = protocol.load_instrument('p1000_single', 'right')
pipette2 = protocol.load_instrument('p300_single', 'right')  # 冲突
```

**修复方法：**
```python
# 正确：使用存在的移液器型号
pipette = protocol.load_instrument('p300_single_gen2', 'left')

# 正确：避免挂载冲突
pipette1 = protocol.load_instrument('p1000_single_gen2', 'right')
pipette2 = protocol.load_instrument('p300_single_gen2', 'left')
```

**预防措施：**
- 查阅支持的移液器型号列表
- 合理规划移液器挂载
- 验证移液器配置

---

### 7. 槽位冲突错误 (0.5%)

**错误表现：**
- 多个器具分配到同一个槽位
- 槽位编号错误

**典型错误示例：**
```python
# 错误：同一个槽位加载多个器具
plate1 = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
plate2 = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')  # 冲突
```

**修复方法：**
```python
# 正确：使用不同的槽位
plate1 = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
plate2 = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')

# 使用槽位管理器
used_slots = set()
def load_labware_safe(labware_type, slot):
    if slot in used_slots:
        raise ValueError(f"Slot {slot} already in use")
    used_slots.add(slot)
    return protocol.load_labware(labware_type, slot)
```

**预防措施：**
- 规划器具布局
- 使用槽位管理系统
- 检查槽位可用性

---

## 通用预防策略

### 1. 代码模板使用
创建标准的协议模板，包含：
- 正确的 API 版本声明
- 标准的器具加载模式
- 错误处理机制

### 2. 参数验证
在协议开始时验证：
- 体积范围
- 器具兼容性
- 槽位分配

### 3. 模拟测试
在实际运行前：
- 使用 `opentrons_simulate` 验证协议
- 检查错误输出
- 修复发现的问题

### 4. 分阶段开发
- 从简单协议开始
- 逐步添加复杂功能
- 每步都进行验证

### 5. 错误日志分析
- 保存详细的错误日志
- 分析常见错误模式
- 建立错误知识库

---

## 代码质量检查清单

在提交协议前检查：

- [ ] API版本是否为最新稳定版本
- [ ] 所有器具名称是否正确
- [ ] 槽位分配是否合理
- [ ] 体积是否在合理范围内
- [ ] 吸头数量是否足够
- [ ] 移液器配置是否正确
- [ ] 代码语法是否正确
- [ ] 是否有适当的错误处理

---

**注：**此总结基于对 Inagaki 2023 论文中 624 个实际错误案例的分析。建议结合最新的 Opentrons 官方文档使用。 
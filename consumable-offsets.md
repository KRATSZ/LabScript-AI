# 耗材 Offset 记忆方案

用 LabscriptAI 的记忆能力，记录**某台设备上、某个位置的某种耗材**的 XYZ 偏移；下次跑协议时自动带上。

一句话流程：

> **人确认 → 只改这一条记录 → 下次跑协议自动用上**

---

## 为什么要这样做

- 现有 `memory` 适合记笔记，但**不会自动改机械臂运动**。
- 真正影响运动的，是创建 run 时挂上的 `labwareOffsets`（MCP 已支持）。
- 所以：**记忆/台账负责存，MCP 负责在开跑时注入**。两者不要混成一条乱路径。

---

## 存什么

每一条 offset 用三样东西定位（像通讯录主键）：

| 维度 | 含义 | 例子 |
|------|------|------|
| 哪台机器 | 设备标识（见下） | health serial |
| 哪种耗材 | `definitionUri` | tip rack / 板子定义 |
| 放在哪 | `locationSequence`（槽位栈，必须是数组） | 某 slot / 模块上 |

再加：

- `vector`: `{x, y, z}`
- `enabled`: 是否启用
- `updated_at` / `source` / `note`
- 可选：最近几次 `history`（方便回滚）

> 注意：写成 `anyLocation` 的全局偏移，当前插件创建 run 时会丢掉。台账里请写**带具体槽位的位置**。

### 设备标识（已拍板）

- **Agent session** 只有 `robot_ip`，**没有** `robot_serial`；不要从 session 读。
- **已定：开跑 / 写入时从 health 现取 serial**，作为 `{device_id}`。
- 台账文件：`.labscriptai/offsets/{serial}.json`。

主键（已拍板）：**设备 serial + `definitionUri` + 槽位 `locationSequence`**。不加条码 / asset_id。

---

## 存在哪

两层分工（已拍板）：

| 层 | 路径 | 干什么 |
|----|------|--------|
| **机器真源** | `.labscriptai/offsets/{device_id}.json` | 给 MCP 读取、开跑时注入；`device_id` = health serial |
| 人读记忆 | `.labscriptai/memory/` 下的 changelog / 摘要笔记 | 记「为什么改过」 |

- **真源是 JSON 表**，按条目维护。
- **Memory 给人看、给 agent 搜索**，不要当唯一运动数据源。
- Vision 标定、夹爪临时 offset、液体 recovery 的临时 `z+1`，都不要写进这份耗材台账。
- **写入台账后同步 `POST` 到机器人 `/labwareOffsets`**，与 App 共享；冲突时仍以 workspace 台账为真源（开跑自动合并时 workspace 同 key 胜出）。

---

## 怎么用（开跑时）

### 现有行为（必须保留）

`resolveRunLabwareOffsets(robotIp, explicitOffsets)` 今天是：

| `labware_offsets` | 行为 |
|-------------------|------|
| **`undefined`（未传）** | 请求机器人 `GET /labwareOffsets`，再 prepare |
| **任意已传入值（含 `[]`）** | **整表替换**：只用显式值，**不请求**机器人，也不和别的源合并 |

因此：

- `[]` = 「我明确不要任何 offset」
- `undefined` = 「走自动解析」
- 显式传入 = **整份清单**，不是「只覆盖同 key、其余再从别处补」

### 本方案自动路径（已拍板；仅 `undefined` 时）

未传 `labware_offsets` 时，两源合并（同 key 只留一条）：

1. workspace 台账
2. 机器人 `/labwareOffsets`（兜底）

同 key：**workspace 覆盖机器人自带值**。

显式传入时：**与现在完全一致**——整表替换，不读台账、不读机器人。

```
labware_offsets === undefined
  → merge(workspace offsets, robot /labwareOffsets)   # workspace 同 key 胜出
labware_offsets === [] 或其它数组
  → 只用显式值（全替换；[] = 不要任何 offset）
```

若将来改成「显式只覆盖同 key、其余仍合并」，必须 CHANGELOG + 更新 `run_protocol` / `create_run` / `create_run_context` 文档。**默认不做这种变更。**

目标：未传参时由 MCP 自动挂上台账 + 机器人偏移，不依赖模型每次 `memory search`。

---

## 怎么更新（重点）

### 原则

**不要让 AI 用 `memory write` 整篇覆盖当唯一更新口。**  
整篇重写容易把别的耗材记录弄丢。

正确做法：**按 key 只改这一条（upsert）**——有则改，无则加，其它不动。

### 什么时候才改

只在这些情况写入：

1. 校准完成，并且人确认「按这个来」
2. 换了同类型、同槽位的物理耗材，旧 offset 不准
3. 多次 run 同一耗材同方向系统性偏差，且人确认

不要写入：

- 单次 recovery 的临时挪动
- 没确认的猜测值
- 夹爪 / 丢 tip 等临时辅助偏移

超大偏移（尤其 Z）应先告警，人确认后才能强制写入。

### 三种操作就够

| 操作 | 行为 |
|------|------|
| `upsert` | 默认；同 key 更新 vector，刷新时间与来源 |
| `disable` | 软禁用，不物理删除，方便回滚 |
| `revert` | 可选；恢复 history 里上一条 |

### 更新链路（已拍板）

```
人确认新的 xyz
  → health 取 serial
  → upsert 到 .labscriptai/offsets/{serial}.json
  → 同步写回机器人 /labwareOffsets
  → 可选：memory 追加变更说明
  → 下次 create run 且未传 labware_offsets 时自动带上
```

---

## 和现有能力的关系

| 能力 | 角色 |
|------|------|
| `memory` | 搜索/阅读变更说明；不要整表手改当真源 |
| MCP `labwareOffsets` | 开跑时真正生效的运动路径 |
| Agent session | 只有 `robot_ip` 等；**没有**可用 serial |
| Health（现取 serial） | 开跑 / 写入时解析 `{device_id}`，选哪份台账 |
| 机器人 `/labwareOffsets` | upsert 后同步写回；开跑时作自动合并兜底 |
| 本文档 | 规定何时记、何时用、何时禁止乱改 |

---

## 落地顺序

1. Health 取 serial → 读写 `.labscriptai/offsets/{serial}.json`
2. 约定 JSON 字段 + memory changelog
3. 专用 upsert（校验 + 只改一条 + **同步写回机器人** + 可选 changelog）
4. MCP：仅在 `labware_offsets === undefined` 时合并 workspace + 机器人；显式（含 `[]`）仍全替换
5. 文档：`run_protocol` 等写清 `undefined` / `[]` / 非空数组；偏离现网必须 CHANGELOG
6. 可选：`revert`、大偏移需人确认的闸门

---

## 不做的事

- 不在 protocol Python 里到处散落手动 `set_offset`
- 不用 run 日记 markdown 当唯一真源
- 不把相机标定当成 pipette 的 labware offset
- 短期不必把 `memory` 工具改成复杂数据库 API（有 JSON upsert 即可）
- 不从 agent session 读 serial

---

## 已拍板

| # | 决策 |
|---|------|
| 1 | 开跑 / 写入时从 **health 取 serial** 作为 `device_id` |
| 2 | 主键：**设备 + 定义 + 槽位**（不加 asset_id） |
| 3 | 真源：`.labscriptai/offsets/{device_id}.json` |
| 4 | upsert 后 **同步写回机器人** `/labwareOffsets` |
| 5 | 合并语义：显式 = 整表替换；仅 `undefined` 才自动合并（workspace 同 key 胜出） |

## 实现状态

已落地（MCP）：

- 台账：`.labscriptai/offsets/{serial}.json`（serial 来自 `/health`）
- 工具：
  - `record_labware_offset`（upsert / disable / revert + 写回机器人 + changelog）
  - `list_labware_offsets`（台账 / 机器人 / 合并预览 / diff）
  - `import_robot_labware_offsets`（LPC 后从机器人导入台账；默认 dry-run，`confirm=true` 才写入）
- 开跑：`resolveRunLabwareOffsets` 仅在未传 `labware_offsets` 时合并台账与机器人
- 开跑前：`preflight_run_setup` / `live_readiness_check` 检查协议声明耗材是否有 offset（默认 warn；`strict_offset_coverage` 可升为 fail）
- 文档：`labscriptai/plugins/mcp/opentrons-mcp/CHANGELOG.md`、工具参数说明


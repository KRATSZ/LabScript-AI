# LabelMe 标注说明（Opentrons 台面）

## 是否该开始标了

可以。在主仓库根目录执行：

```bash
labelme vision/data/frames/samples
```

保存时让 JSON 落在 **`vision/data/labels/`**（与图片 **同名 stem**，例如 `deck_vid1_01.json`），便于后续：

```bash
uv run python vision/scripts/labelme_to_yolo.py \
  --images vision/data/frames/samples \
  --labelme-dir vision/data/labels \
  --classes vision/data/datasets/classes.txt \
  --out vision/data/datasets/yolo
```

## 每张图要标什么

### 1. `deck_quad`（必标，一类特殊标签）

- **类型**：Polygon，**4 个顶点**。
- **Label 文本**：必须完全一致写成 **`deck_quad`**（小写、下划线）。
- **顶点顺序**（俯视台面，与 `vision_check` 一致）：**A1 → A3 → D3 → D1** 顺时针。
- **作用**：定 deck 平面，后面可用脚本把物体框中心映射到 slot；**不会**进 YOLO 训练标签（`labelme_to_yolo.py` 会忽略不在 `classes.txt` 里的名字）。
- **兼容旧标注**：历史上若 `deck_quad` 画成了多点 polygon，导出 sidecar 时会尽量自动提取 4 个角点；但**新标注仍然统一按 4 点**，这样最稳定。

### 2. 台面上的物体（检测类）

Label 必须 **与 `vision/data/datasets/classes.txt` 某一行完全一致**（区分大小写）：

| Label | 含义 |
|--------|------|
| `tiprack_50` | 50 µL 规格枪头盒 |
| `tiprack_200` | 200 µL 规格枪头盒 |
| `tiprack_1000` | 1000 µL（1 mL）规格枪头盒 |
| `plate` | 孔板（96 等） |
| `reservoir` | 储液槽 |
| `module` | 模块（温控、震荡等大块） |
| `trash_bin` | 台面废料口 / 黑色垃圾位 |

- 用 **rectangle** 即可；透视大时用 **polygon** 包紧外轮廓也行。
- **空槽**：不画框。

## 三种 tip rack 怎么区分

训练目标是 **「视觉可分的型号」**，不是抽象体积数字。建议按下面顺序判断（结合你实验室真实耗材）：

1. **物理尺寸（俯视）**
   - **1000 µL** 盒通常 **更「厚」、占地更大或孔阵更疏**（依品牌略有差异）。
   - **50 µL** 盒往往 **更扁、孔更密**。
   - **200 µL** 介于两者之间的情况最常见。

2. **颜色 / 标签贴纸**
   若你们现场 **固定配色**（例如黄=50、蓝=200、紫=1000），优先按 **你们 SOP** 记一张对照表，标的时候对照表 + 看图。

3. **不确定时**
   - **宁可标成「最可能」的一类**，也不要发明新 label。
   - 若完全无法判断：**不标该盒** 或只标 `deck_quad` 后在 `notes` 里说明（不要写进 YOLO 类名）。

标完前 10～20 张后，建议 **同一台相机、同类布局** 下快速过一遍，看三类是否 **混淆最多的一对**，再微调你的「区分规则」写进本文件。

## 与 MCP `vision_check` 的关系

当前 MCP 侧 canonical 仍是 **`tiprack` 一个桶**。你训出 **三档 tiprack** 后，推理后处理里可以把
`tiprack_50` / `tiprack_200` / `tiprack_1000` **映射回** `tiprack` 做 slot 校验，或以后扩展 MCP 输出细分型号。

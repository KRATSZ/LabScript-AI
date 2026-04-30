# 数据集现状与首次训练技术计划

生成说明：根据 `vision/data/frames/samples` 下「图片 stem ↔ 同名 `.json`」自动统计。

## 1. 当前样本统计（`vision/data/frames/samples`）

| 项目 | 数量 |
|------|------|
| 图片总数（`.jpg` / `.jpeg` 等） | **45** |
| 已标注（存在同名 `deck_*.json`） | **23** |
| 未标注（无同名 JSON） | **22** |

### 1.1 未标注列表（22 张）

当前无 LabelMe JSON，**不会**进入 `labelme_to_yolo` 的带框训练集，除非作为**纯背景图**（无 `.txt` 标签文件）参与 YOLO 训练。

- `deck_mvp_03` … `deck_mvp_12`、`deck_mvp_15`（缺号：已标的有 01,02,08,13,14）
- `deck_vid1_04.jpg`
- `deck_vid2_01.jpg`, `deck_vid2_05.jpg`, **`deck_vid2_07.jpg`**, `deck_vid2_08.jpg` … `deck_vid2_10.jpg`
- `deck_vid3_03.jpg`, `deck_vid3_05.jpg`, `deck_vid3_08.jpg` … `deck_vid3_10.jpg`

**负样本约定**：若仅保留 **`deck_vid2_07.jpg`** 作为负样本，其余 **21 张**建议移到 `data/frames/unused/`（或 `holdout/`），避免「无 JSON 却被当成要学习的背景」与「误混入未审核图」混淆。

### 1.2 已标注列表（23 张）

均含 `shapes`；类别均在 `vision/data/datasets/classes.txt` + `deck_quad` 内，**无未知 label**。

### 1.3 质检：`deck_quad` 缺失

| 文件 | 说明 |
|------|------|
| **`deck_vid1_05.json`** | **无 `deck_quad` 多边形**。若依赖角点做 slot 映射，应补标；仅训 YOLO 检测仍可训练，但与其它张标注规范不一致。 |

**建议**：在 LabelMe 打开 `deck_vid1_05`，补一个 `deck_quad`（A1→A3→D3→D1 顺时针）后保存。

---

## 2. 类别与转换约定

- **训练用类**（`classes.txt`，共 8 类）：`tiprack_50`, `tiprack_200`, `tiprack_1000`, `plate`, `reservoir`, `module`, `trash_bin`。
- **`deck_quad`**：仅几何元数据；`vision/scripts/labelme_to_yolo.py` **不写入** YOLO `.txt`。

---

## 3. 首次训练前：具体技术步骤（按顺序）

### 步骤 A — 数据整理（推荐执行）

1. 创建目录：`data/frames/unused/`（或 `holdout/`）。
2. 将「未标注且不作为负样本」的图片 **移出** `samples/`（上表除 `deck_vid2_07.jpg` 外 21 张）。
3. **保留** `deck_vid2_07.jpg` 在 `samples/` 且 **不要**为其创建 JSON → YOLO 中作为 **background / 负样本**（无对应 `labels/*.txt` 或空文件，视 Ultralytics 数据加载行为而定，一般无 txt 即表示该图无目标）。
4. （可选）将 LabelMe JSON 统一复制/移动到 `data/labels/`，与图片分离；**或**保持现状（JSON 与图同在 `samples/`），转换时 `--labelme-dir` 指向 `samples/`。

### 步骤 B — 补标与一致性

1. 为 **`deck_vid1_05`** 补 `deck_quad`。
2. 抽查 2～3 张：`deck_quad` 是否包住 **整幅 12 槽外轮廓四角**（非槽位中心点），顺序 A1→A3→D3→D1。

### 步骤 C — LabelMe → YOLO

在主仓库根目录。**`--labelme-dir`** 必须与 LabelMe JSON 所在目录一致（推荐 JSON 单独放在 `vision/data/labels/`，与图片同名 stem；若 JSON 与 JPEG 同放在 `vision/data/frames/samples/`，则两参数都指向 `vision/data/frames/samples`）。详见 `vision/README.md` 与 `vision/docs/LABELME.md`。

本 pilot 批次若 JSON 仅在 `samples/`：

```bash
uv run python vision/scripts/labelme_to_yolo.py \
  --images vision/data/frames/samples \
  --labelme-dir vision/data/frames/samples \
  --classes vision/data/datasets/classes.txt \
  --out vision/data/datasets/yolo_pilot
```

### 步骤 D — 划分 train/val（数据少时的做法）

- **极简**：全部 22 张有标图进 `train`，另手动复制 2～3 张到 `images/val` 及对应 `labels/val`（需同步改 `dataset.yaml` 或目录结构）。
- **或**：先 **不划分**，整集训练 + 用 **未参与训练的 holdout 图**（已移到 `unused/`）日后做人工看框。

当前 `labelme_to_yolo.py` 默认只写 `images/train` 与 `labels/train`；若要 val，需小改脚本或训练前手工拆目录。

### 步骤 E — 训练命令（Ultralytics）

在已生成 `vision/data/datasets/yolo_pilot/dataset.yaml` 后：

```bash
uv run yolo detect train model=vision/models/weights/yolov8n.pt data=vision/data/datasets/yolo_pilot/dataset.yaml epochs=100 imgsz=640 batch=4 name=deck_pilot
```

（`batch` 按显存调整；数据极少时注意过拟合，可加大 `degrees`/`scale` 等增强，或尽快补数据。）

### 步骤 F — 验证

1. `yolo predict` 在 `deck_vid2_07.jpg` 上应 **尽量无框** 或极低置信度。
2. 在 1～2 张 holdout 或 val 图上肉眼看框是否合理。

---

## 4. 与本仓库脚本的对应关系

| 脚本 | 作用 |
|------|------|
| `vision/scripts/labelme_to_yolo.py` | JSON → YOLO txt + `dataset.yaml` |
| `vision/scripts/sample_frames.py` | 视频抽帧（后续扩数据） |
| `vision/docs/LABELME.md` | 标注规范 |

---

## 5. 已执行（pilot 一次）

- `scripts/organize_pilot_samples.py`：21 张无 JSON 移至 `data/frames/unused/`；保留 `deck_vid2_07.jpg`；随机 5 张复制到 `data/frames/predict_probe/`。
- `labelme_to_yolo.py`：`vision/data/datasets/yolo_pilot/`（23 有标 + 1 负样本）；`dataset.yaml` 中 `val: images/train`（无独立 val，满足 Ultralytics 校验）。
- 训练：`vision/runs/detect/deck_pilot/weights/best.pt`（100 epochs，MPS）。
- 预测：`vision/runs/detect/predict_pilot/`（5 张探针）、`vision/runs/detect/predict_negative/`（`deck_vid2_07` 无检出）。

## 6. 后续可再做

1. 继续标注 `unused/` 中图片，再跑转换与微调。
2. 真正划分 `val` 时：复制部分图到 `images/val` + `labels/val`，并把 `dataset.yaml` 的 `val` 指过去。

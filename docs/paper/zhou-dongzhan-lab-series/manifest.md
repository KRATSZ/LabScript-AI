# 周东展（Dongzhan Zhou）Lab 系列论文集

上海 AI Lab AI for Science 中心 · 实验室具身智能 / 湿实验自动化相关预印本（2025–2026）。

PDF 来源：[arXiv](https://arxiv.org/) 官方 PDF 链接。`docs/paper/2605.07306v3.pdf` 为同篇 BioProVLA 的早期副本，本目录内为最新版。

## 建议阅读顺序

| 顺序 | 文件 | arXiv | 一句话 |
|------|------|-------|--------|
| 0 | `2506.19613_Intelligent-Science-Laboratory-Position.pdf` | [2506.19613](https://arxiv.org/abs/2506.19613) | Position：智能实验室 = 认知 AI + 具身 AI |
| 1 | `2505.22634_LabUtopia.pdf` | [2505.22634](https://arxiv.org/abs/2505.22634) | **LabUtopia**：Isaac Sim 高保真化学实验室仿真 + 五级 LabBench |
| 2 | `2605.02288_LabBuilder.pdf` | [2605.02288](https://arxiv.org/abs/2605.02288) | **LabBuilder**：自然语言实验需求 → 安全可执行的 3D 实验室布局 |
| 3 | `2606.12936_Pipette.pdf` | [2606.12936](https://arxiv.org/abs/2606.12936) | **Pipette**：湿实验室机器人仿真平台、基准与数据增广 |
| 4 | `2606.01777_Trans2Occ.pdf` | [2606.01777](https://arxiv.org/abs/2606.01777) | **Trans2Occ**：单目 RGB → 体素占用 → 透明器皿抓取 |
| 5 | `2606.13578_LabVLA.pdf` | [2606.13578](https://arxiv.org/abs/2606.13578) | **LabVLA**：协议驱动 VLA（RoboGenesis 数据 + LabUtopia 评测） |
| 6 | `2605.07306_BioProVLA-Agent.pdf` | [2605.07306](https://arxiv.org/abs/2605.07306) | **BioProVLA**：生物湿实验多智能体 + AugSmolVLA 闭环 |
| 7 | `2604.05484_CoEnv.pdf` | [2604.05484](https://arxiv.org/abs/2604.05484) | **CoEnv**：组合式环境驱动的具身多智能体协作 |
| 8 | `2505.16938_InternAgent.pdf` | [2505.16938](https://arxiv.org/abs/2505.16938) | **InternAgent**：假设 → 验证闭环的「科学家智能体」系统 |

## 与 LabscriptAI 的对照

| 维度 | 本系列（Zhou / 上海 AI Lab） | LabscriptAI（本仓库） |
|------|------------------------------|------------------------|
| 执行体 | 通用臂 / 仿真 VLA | Opentrons Flex 液移工作站 |
| 任务接口 | 自然语言协议 / 布局规范 | NL → Python 协议代码 |
| 感知难点 | 透明器皿、化学场景 | 协议正确性、运行时恢复 |
| 评测 | LabUtopia / Pipette 仿真 | flex15 / hardnest / runtime recovery |

## 相关链接

- 作者 Scholar：<https://scholar.google.com/citations?user=Ox6SxpoAAAAJ>
- LabUtopia 主页：<https://rui-li023.github.io/labutopia-site/>
- LabVLA 代码：<https://github.com/zjunlp/LabVLA>

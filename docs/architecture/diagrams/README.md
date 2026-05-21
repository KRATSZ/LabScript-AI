# Diagrams (SVG)

Vector diagrams for **Opentrons-Lab-Agent** layout and flows. Labels are in **English** for reliable rendering in all viewers. Style: **white background**, **blue–gray** palette (slate text `#64748b` / `#475569`, accents `#2563eb` / `#dbeafe`). **Emoji** on diagrams are hints only (e.g. 🎯 default entry, 🛡️ simulation gate, 🔄 restart path).

| File | What it shows |
|------|----------------|
| [architecture-layers.svg](architecture-layers.svg) | Five layers: Plugin, Skills, MCP, persisted state, optional vision |
| [experiment-happy-path.svg](experiment-happy-path.svg) | Five steps: intent → plan → code+iteration → live execution → complete |
| [skills-routing.svg](skills-routing.svg) | Default entry `experiment-run` vs common satellites vs dashed on-demand skills |
| [recovery-and-restart.svg](recovery-and-restart.svg) | Left: live recovery chain; Right: `safe_next_action` / `restart_review` after restart |

**中文概要：** 架构分层、主实验路径、技能路由（默认 vs 按需）、运行中恢复 vs 重启后对账。文字说明见 [`../architecture.md`](../architecture.md) 与 [`../../rules/workflows.md`](../../rules/workflows.md)。

Open any `.svg` in a browser or VS Code preview.

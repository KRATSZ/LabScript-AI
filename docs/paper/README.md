# Paper materials

Manuscript and related reading copies for LabscriptAI. **Not** runtime policy.

## Canonical working draft

| Role | Path |
|------|------|
| **Source of truth** | [`.laipaper/main0714.md`](.laipaper/main0714.md) |
| Supersedes | removed `.paper/main0706.md` / older laipaper snapshots |

Edit the markdown. Do not treat Word/PDF exports as canonical.

## Tracked vs local-only

| Kind | In git? | Location |
|------|---------|----------|
| Working manuscript (`.md`) | **Yes** | `.laipaper/main0714.md` |
| Reference paper manifests + md extracts | **Yes** | `.laipaper/reference_papers/manifest.md`, `…/md/*.md` |
| Zhou lab-series manifest | **Yes** | `zhou-dongzhan-lab-series/manifest.md` |
| This README | **Yes** | `docs/paper/README.md` |
| Word / PDF manuscript drafts | **No** (gitignored) | `.laipaper/archive/` (local exports) |
| Reference / related-work PDFs | **No** (gitignored) | `.laipaper/reference_papers/*.pdf`, `zhou-dongzhan-lab-series/*.pdf`, `2605.07306v3.pdf` |
| Editor marker files (`.figure-*-done`, etc.) | **No** | `.laipaper/` |

Binary policy: **md is source of truth; do not commit multi-MB docx/pdf drafts.** Re-download reference PDFs from arXiv using the manifests if needed.

## Layout

```
docs/paper/
├── README.md                          ← this file
├── .laipaper/
│   ├── main0714.md                    ← canonical draft
│   ├── archive/                       ← local docx/pdf exports (gitignored)
│   └── reference_papers/              ← LLM-agent / RAG related work
│       ├── manifest.md
│       ├── md/                        ← text extracts (tracked)
│       └── *.pdf                      ← local copies (gitignored)
├── zhou-dongzhan-lab-series/          ← Zhou / 上海 AI Lab lab-AI series
│   ├── manifest.md
│   └── *.pdf                          ← local copies (gitignored)
└── 2605.07306v3.pdf                   ← older BioProVLA copy; prefer series PDF (gitignored)
```

## Reference paper locations (do not mass-move)

Two sibling collections; keep both paths (already cited in manifests):

1. **`.laipaper/reference_papers/`** — general LLM-agent / RAG / preference / code-action set (see its `manifest.md`).
2. **`zhou-dongzhan-lab-series/`** — wet-lab / embodied lab-AI preprints (see its `manifest.md`). `2605.07306v3.pdf` at `docs/paper/` root is an older BioProVLA duplicate; the series copy is preferred.

## Reproducibility pointers

Methods / LLM-stack notes in `docs/reproducibility/` should cite `.laipaper/main0714.md`, not the removed `.paper/main0706.md`.

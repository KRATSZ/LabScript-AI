# External materials index

The manuscript repository intentionally contains product code only. Research
materials and evaluation outputs are preserved inside this project directory,
but outside Git tracking, at:

```text
Opentrons-Lab-Agent-materials/
```

The archive keeps the original directory names where practical:

- `docs/` — paper drafts, supplements, Commec data, iGEM data, FASTA files,
  and contamination-check research material.
- `docs/paper/.laipaper/main0812.md` — preserved paper draft.
- `docs/paper/supplyment/commec/` — preserved Commec screening material.
- `docs/research/contamination_check/` — preserved contamination-check
  tasks and supporting material.
- `benchmarks/` — 90-question evaluation runners, scoring code, and reports.
- `evaluation/90-question/tests/` — LLM acceptance-test harnesses removed from
  the product test suite.
- `evaluation/90-question/docs/` — preserved QA authoring/runtime documents.
- `runs/` — generated run histories and execution records.
- `liquid class.rar` — preserved binary archive.
- `generated/` — generated pressure-trace artifacts removed from the package.
- `legacy/removed-manuscript/` — removed MCP/Claude metadata and source docs.
- `legacy/loose-files/` — loose generated protocol and local macOS metadata.
- `legacy/` — other pre-manuscript local trees retained for reference.

The archive has its own `README.md` with the move date and a complete mapping.
It is deliberately ignored and not versioned in this repository; back it up
separately when moving this worktree to another machine.

# LabScript-AI protocol forum (sample)

Local **sample** of a protocol-pack board. Not production. No extra auth. Not wired into `labscriptai/webdemo`.

## Framework

[Astro official Blog starter](https://github.com/withastro/astro/tree/main/examples/blog) (`npm create astro@latest -- --template blog`), which is based on [Bear Blog](https://github.com/HermanMartinus/bearblog/) CSS (MIT).

Posts are Astro [content collections](https://docs.astro.build/en/guides/content-collections/). Votes are stored in the browser (`localStorage`). Downvote must pick **crash**, **leak**, or **error**.

## Run locally

```bash
cd labscriptai/forum
npm install
npm run dev
```

Open http://127.0.0.1:4321

Binds **127.0.0.1:4321** only. Do not deploy.

```bash
cd labscriptai/forum && npm test
```

## Seeded packs

Three fake posts under `src/content/protocols/`. Each has **device + deck + SOP + script**:

| Post | Device | Hardware? |
| --- | --- | --- |
| 50 µL A1 → B1 | OT-2 | marked ran on hardware |
| 20 µL PCR mix × 8 | Hamilton STAR | sim; seeded **leak** downvote |
| 50 µL serial dilution | Tecan Fluent | sim / not run |

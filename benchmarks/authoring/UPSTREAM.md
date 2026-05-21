# Authoring Benchmark Upstream Sources

## Inagaki 2023 GPT-4 OT-2

- Upstream repository: https://github.com/labauto/Inagaki_2023_GPT4OT2
- Repository: `labauto/Inagaki_2023_GPT4OT2`
- Commit: `0ef14a3a83254a7bd0eb908e28810ee8583f7fdc`
- License: MIT
- Used in: `T001-T055`
- Source path: `question_and_answer`
- Local derived manifest: `benchmarks/authoring/tasks.yaml` (`schema_version: "0.2"`)

The authoring benchmark manifest is a single frozen file. Tasks `T001-T055` are derived from the upstream question set and retain stable task IDs for continuity analysis; `T056-T090` are project-authored extensions with a structured `spec:` block (sample count, reagents, controls, expected risk flags) for machine validation and the same numbered-step prompt style as the legacy tasks. Document attribution fields and any surface-form rewrites needed after contamination analysis in manifest notes or revision logs when you change wording.

Upstream is MIT-licensed; no separate author permission artifact is required for redistribution under those terms. If you later add non-MIT derived material, document it here.

## License Text

```text
MIT License

Copyright (c) 2023 jst-robot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

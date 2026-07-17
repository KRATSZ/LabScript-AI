# FP composite vs BoB composite — definition audit, gap analysis, and recommendation

**Question from authors:** "正文用的是 FP 还是 BoB？我们需要去掉一个。"
**Answer (headline):** Keep **BoB composite** as the single headline authoring-quality metric in the main-text Table 1 and S2A. Drop the **FP** column from Table 1 and S2A. **S1 (scaffold ablation) is the one exception that keeps both**, because the FP→BoB gap *is* the scaffold-contribution signal.

---

## 1. Definitions (with code citations)

Both metrics are "composite" = the same four gates evaluated on the final submitted package. They differ **only** in whether repair/retry is allowed before the package is scored.

### 1.1 The four gates (shared by FP and BoB)

`analyze_authoring_run.py` computes the per-task composite flag `task_pass`:

```129:134:src/labscriptai/benchmark/analyze_authoring_run.py
        row["task_pass"] = bool(
            row["simulation_ok"]
            and row["validator_ok"]
            and row["semantic_ok"]
            and row["param_sweep_ok"]
        )
```

So **composite pass = `simulation_ok` ∧ `validator_ok` ∧ `semantic_ok` ∧ `param_sweep_ok`**. The individual gate fields are populated at `analyze_authoring_run.py:109-120` (`simulation_ok`, `validator_ok`, `semantic_ok`, `param_sweep_ok`, plus `first_pass_simulation_ok` at line 111). This four-gate definition is the one the paper footnote restates (`paper_execution_plan.md:209`: "FP/BoB = composite pass（sim ∧ validator ∧ semantic ∧ param_sweep）").

### 1.2 FP composite — first-shot, no-repair, four gates

Implemented in `_first_pass_count`:

```273:308:scripts/build_table1_v2.py
def _first_pass_count(summary: dict[str, Any], analysis: dict[str, Any], total: int) -> int | None:
    if not analysis:
        value = summary.get("first_pass_simulation_pass_count")
        if value is None:
            return None
        return int(value)
    gen_by_task = {
        str(record.get("task_id")): int(record.get("generation_attempts", 0))
        for record in summary.get("records", [])
        if isinstance(record, dict) and record.get("task_id")
    }
    count = 0
    saw_rows = False
    for item in analysis.get("per_task", []):
        if not isinstance(item, dict):
            continue
        saw_rows = True
        task_id = str(item.get("task_id"))
        if gen_by_task.get(task_id, 99) != 1:
            continue
        if int(item.get("simulation_repair_attempts", 0)) != 0:
            continue
        if not item.get("first_pass_simulation_ok"):
            continue
        if (
            item.get("simulation_ok")
            and item.get("validator_ok")
            and item.get("semantic_ok")
            and item.get("param_sweep_ok")
        ):
            count += 1
    if saw_rows:
        return count
    if total:
        return int(summary.get("first_pass_simulation_pass_count", 0))
    return None
```

**Boolean condition for a task to count toward FP composite** (lines 291-303):

- `generation_attempts == 1` (line 291) — single generation attempt, no generation retry;
- `simulation_repair_attempts == 0` (line 293) — no simulation-repair loop invocations;
- `first_pass_simulation_ok` (line 295) — the first simulation run passed;
- **and** all four gates `simulation_ok ∧ validator_ok ∧ semantic_ok ∧ param_sweep_ok` (lines 297-302).

**What it measures:** first-shot reliability — "did the very first submitted package pass all four gates with no repair and no retry." It is a cost/efficiency signal, not a capability signal.

> ⚠️ **Naming hazard (see §4).** When `analysis` is missing, `_first_pass_count` falls back to `summary["first_pass_simulation_pass_count"]` (lines 275-278 and 307). That fallback is **simulation-only** (`first_pass_simulation_ok`, counted at `analyze_authoring_run.py:154-155`), *not* the four-gate composite. So a single "FP" column can silently flip from "first-pass composite" to "first-pass sim pass" depending on whether `analysis/attribution-summary.json` exists. This is the FP = first-pass-sim-only vs FP = first-pass-composite collision the authors asked about.

### 1.3 BoB composite — budget-bound final package, four gates

In `build_table()`:

```421:421:scripts/build_table1_v2.py
        final_pass = int(analysis.get("task_pass_count", 0)) if analysis else None
```

`task_pass_count` is the count of `task_pass` rows (`analyze_authoring_run.py:177`), i.e. the four-gate composite evaluated on the **final** package, with no constraint on `generation_attempts` or `simulation_repair_attempts`. Repair and retry are allowed within the unified budget (`benchmark_taxonomy.md:250-256`: `max_attempts ≤ 8`, `max_wall_time_sec ≤ 1800`, `max_output_tokens ≤ 24000`, `max_tool_calls ≤ 80`; "最终 `best_of_budget_success` 只看预算内最后一个通过最低自动检查的 package").

**What it measures:** within a matched budget, did the system deliver a final package that passes all four gates. This is the capability/deliverable signal — exactly the paper's claim of "可运行、可审查、可由人类 setup 的协议包" (`benchmark_taxonomy.md:1-3`, `paper_execution_plan.md:64`).

### 1.4 Relationship: BoB ≥ FP, always

FP adds three extra conjuncts on top of the BoB four gates (`generation_attempts==1`, `simulation_repair_attempts==0`, `first_pass_simulation_ok`). Therefore any task counted in FP is necessarily counted in BoB, so **BoB ≥ FP** on every row. The gap `BoB − FP` is exactly the set of tasks the system could **not** pass first-shot but **did** pass after repair/retry within budget — i.e. the measured value of the repair/retry machinery.

---

## 2. Audit — where FP / BoB appear in the repo

| Location | FP present? | BoB present? | Which is the headline? | Note |
| --- | --- | --- | --- | --- |
| `benchmark_taxonomy.md:23` | yes ("FP") | yes ("BoB") | both stated equally | "正文 Table 1 显示 `FP` / `BoB`（composite）" — asserts main text shows both |
| `paper_execution_plan.md:75` | yes | yes | — | "Authoring FP/BoB（Table 1、S1）" — groups both under Table 1 and S1 |
| `paper_execution_plan.md:195-204` (§8.1 Table 1 cols) | **yes** ("Authoring FP‡") | **yes** ("Authoring BoB‡") | **BoB** | LabscriptAI row shows `TBD (56§)` in *both* columns, but footnote § (`:213`) states "56 为 freeze composite **BoB** 占位" — 56 is the BoB placeholder; the FP cell is TBD |
| `paper_execution_plan.md:209` (§8.1 footnote ‡) | yes | yes | — | defines both identically as the four-gate composite |
| `paper_execution_plan.md:219-225` (§8.2 S1) | yes ("Composite FP†") | yes ("Composite BoB") | **BoB** | all rows have real BoB values (23/45/56); **all FP† cells are TBD** |
| `paper_execution_plan.md:233-237` (§8.2 S2A) | yes ("FP composite") | yes ("Composite") | **BoB** | "Composite" column filled; "FP composite" column is TBD |
| `paper_execution_plan.md:311` (§12 验收) | yes | yes | **BoB for Table 1; FP for S1** | "SI 编号表 … **S1 含 FP composite**" — FP composite's designated home is S1, not Table 1 |
| `paper_deliverables.md:53` (export checklist) | yes | — | — | "S1: FP composite aggregated from freeze runs" — FP composite tied to S1 |
| `paper_deliverables.md:36` (claim boundary) | — | yes | BoB | "Table1 / S1 authoring: labscriptai-authoring-light only" |
| `authoring_benchmark_results.md:9` | — | **yes** | **BoB 62/90** | "LabscriptAI anchor … BoB **62/90**, Sim **89/90**" — the documented Table 1 headline number is BoB |
| `authoring_benchmark_results.md:10` | — | yes | BoB | S1 = "direct 23/90 · fix-loop 45/90 · LabscriptAI 56/90 composite" (the BoB/composite column) |
| `authoring_benchmark_results.md:14` | **TODO** | yes | BoB | "Before freeze export: aggregate **FP composite** (first attempt) … for S1 **and Table 1** LabscriptAI row" — FP composite is a **planned, not-yet-filled** column |
| `authoring_benchmark_results.md:363` | — | yes | **BoB** | "LabscriptAI light is clearly strongest: `56/90` composite" — narrative headline = composite/BoB |
| `runs/table1_v2_combined_summary.md:9` (filled table) | **yes** (FP col) | **yes** (BoB col) | both filled | the actual artifact carries both `FP` and `BoB` columns, plus a separate `Sim` column (sim-only) |
| `scripts/build_table1_v2.py:409` (emitted columns) | **yes** ("FP") | **yes** ("FinalPass") | both | `build_table()` emits both an `FP` and a `FinalPass` column; **FinalPass == BoB** (line 421 reads `task_pass_count`) |
| `docs/research/dashboards/status.html:428` | yes (47/66) | yes (56/66) | **BoB** | "External 66 unified py-only 当前 BoB；FP 现是 47/66，能做泛化旁证，**不是正文胜负手**" — explicitly says FP is **not** the main-text deciding metric |
| `docs/research/dashboards/status.html:619` | yes | yes | — | "列要克制：FP、BoB、Expert、Runtime、Memory、Cost" — dashboard still lists both for Table 1 (the inconsistency to fix) |

### What the main text actually relies on

- The **headline authoring-quality number is BoB composite**: 62/90 for the flash anchor (`authoring_benchmark_results.md:9`), historically 56/90 (`paper_execution_plan.md:213`, `authoring_benchmark_results.md:363`). The narrative ("clearly strongest: 56/90 composite") is told in BoB.
- **FP composite was never actually filled into Table 1.** Every FP cell in §8.1 and §8.2 is `TBD`, and `authoring_benchmark_results.md:14` lists aggregating FP composite as a pre-freeze TODO. The acceptance criteria (`paper_execution_plan.md:311`) and export checklist (`paper_deliverables.md:53`) assign FP composite's home to **S1**, not Table 1.
- The repo itself states FP "不是正文胜负手" (`status.html:428`) — FP is side-evidence, not the main-text deciding metric.

**Conclusion of audit:** the main text's primary authoring-quality metric is **BoB composite**. FP composite is (a) proposed as a column in Table 1 but never populated, (b) explicitly designated to S1, and (c) explicitly labeled not-the-headline. Dropping FP from Table 1 is therefore low-risk — it removes a column that was TBD anyway.

---

## 3. Gap analysis (BoB − FP), quantified

### 3.1 External 66 (`runs/table1_v2_combined_summary.md:24-25`)

| Row | FP | BoB | Gap (BoB−FP) | What the gap reveals |
| --- | ---: | ---: | ---: | --- |
| DeepSeek LLM-only (Run A, Direct) | 29/66 | 31/66 | **+2** | retry=2 rescued 2 tasks (3.0% of N) |
| LabscriptAI agent (Run B) | 47/66 | 56/66 | **+9** | scaffold repair rescued 9 tasks (13.6% of N; 9/19 = 47% of FP-fails rescued) |

Run B's gap (+9) is 4.5× Run A's (+2). The gap is the direct, quantified value of the LabscriptAI repair/retry scaffold on unseen community protocols.

### 3.2 Main 90 anchor rows (`runs/table1_v2_combined_summary.md:11-25`)

| Row | FP | BoB | Gap | Repair capability |
| --- | ---: | ---: | ---: | --- |
| DeepSeek LLM-only | 38 | 39 | +1 | retry=2 (light) |
| GPT-4 + fix-loop (Inagaki) | 28 | 38 | **+10** | fix-loop repair≤3 (heavy) |
| OpentronsAI (web chat) | 51 | 51 | **0** | none (single session) |
| LabscriptAI flash | 61 | 62 | +1 | repair≤3, but FP already high |
| LabscriptAI Opus 4.8 | 52 | 60 | **+8** | repair≤3, FP weaker → rescue |
| GPT-5.5 direct | 32 | 36 | +4 | retry |
| Gemini 3.5 Flash direct | 39 | 42 | +3 | retry |
| Claude Opus 4.8 direct | 49 | 54 | +5 | retry |
| Codex native | 45 | 45 | 0 | none (no sim repair) |
| Claude Code A (GLM) | 22 | 22 | 0 | none |
| Claude Code A (Opus) | 12 | 12 | 0 | none |
| Claude Code B open | 15 | 15 | 0 | none |

### 3.3 What each metric reveals

- **BoB** answers the capability question: "within a matched budget, does the system deliver a runnable, reviewable package?" It is the level playing field — every system gets the same budget and the same four gates, regardless of whether it *can* repair.
- **FP** answers the efficiency question: "did it pass first-shot with no repair?" It conflates "can't produce a correct package" with "needed one repair" — a system that repairs on attempt 2 is scored as FP-fail even though its final package is correct.
- **The gap is informative only for repair-capable systems.** Rows with no repair capability (OpentronsAI, Codex native, all Claude Code configs) have **gap = 0**, so FP and BoB are **identical** — carrying both columns is pure redundancy for them. The gap only means something where a scaffold exercises repair (LabscriptAI, Inagaki fix-loop, LLM-only with retry).
- Therefore the gap is a **scaffold-ablation signal**, and its natural home is **S1**, not the systems-comparison Table 1.

---

## 4. Naming collisions to fix (consistency)

The authors asked whether FP/BoB terminology is used inconsistently. It is, in three ways:

1. **BoB has many names.** `build_table1_v2.py:409` calls the column **"FinalPass"**; `runs/table1_v2_combined_summary.md:9` calls it **"BoB"**; `paper_execution_plan.md:219` calls it **"Composite BoB"**; `authoring_benchmark_results.md` calls it **"Composite task pass"**. Same metric, four names.
   → **Fix:** standardize on **"BoB"** (or "Composite (BoB)") everywhere; rename the `build_table1_v2.py` column `FinalPass` → `BoB`.

2. **"FP" is two different metrics.** `paper_execution_plan.md:209` defines "FP" as the **four-gate first-shot composite**. But `_first_pass_count`'s fallback (`build_table1_v2.py:275-278` and `:307`) returns `first_pass_simulation_pass_count`, which is **simulation-only** (`analyze_authoring_run.py:154-155`, field `first_pass_simulation_ok` at `:111`) — *not* the four-gate composite. The combined summary even carries a separate **"Sim"** column (`table1_v2_combined_summary.md:9`) for the sim-only pass. So "FP" can mean either "first-pass composite (4-gate)" or "first-pass sim pass" depending on data availability.
   → **Fix:** the FP column must **always** be the four-gate composite; when `analysis` is missing it should emit **NA**, never the sim-only fallback. The sim-only first-pass number belongs in the separate `Sim` column / S1 footnote (`paper_execution_plan.md:225`: "Sim pass（38/80/85）仅作 S1 脚注"), not under the FP label.

3. **Two "first-pass" definitions in the taxonomy.** `benchmark_taxonomy.md:124` defines `first_pass_success` as `simulation_pass ∧ package_complete ∧ deterministic checks` (deterministic checks per §4 lines 116-122 = deck/reagent/tips/manifest + no critical failure — i.e. **validator-style**, no semantic/param_sweep). But `paper_execution_plan.md:209` defines "FP composite" as `sim ∧ validator ∧ semantic ∧ param_sweep`. These are **different** (the taxonomy §4 version omits semantic_ok and param_sweep_ok).
   → **Fix:** align `benchmark_taxonomy.md:124` to the four-gate composite (add `semantic_ok ∧ param_sweep_ok`), or explicitly relabel the §4 notion as "first-pass deterministic" and reserve "FP composite" for the four-gate version the code actually computes. The code's four-gate version is the de facto standard.

---

## 5. Recommendation

### 5.1 Keep **BoB composite** as the single headline metric in Table 1 and S2A

Reasons:

1. **Matched-budget fair comparison.** BoB is the only metric that puts all systems — frontier LLMs, coding agents, the official tool, the literature fix-loop, and LabscriptAI — on the same footing (same four gates, same unified budget). FP penalizes systems for *exercising* their repair capability: a system that repairs on attempt 2 is FP-fail despite a correct final package. Across systems with heterogeneous repair capability (LabscriptAI agent has repair; OpentronsAI / Claude Code / Codex do not), FP is not an apples-to-apples capability comparison. BoB is.

2. **It matches the paper's actual claim.** The paper claims LabscriptAI "produces runnable, reviewable packages" (`paper_execution_plan.md:64`; `benchmark_taxonomy.md:1-3`) — a property of the **final delivered package**, not of the first shot. BoB measures exactly that. FP measures first-shot reliability, which is a cost story (handled by the Tokens/task, attempts, and Cost columns), not the capability headline.

3. **Reviewer defensibility.** Under BoB, LabscriptAI flash 62/90 vs Claude Code 12/90 is a same-budget, same-gates comparison — hard to attack. Under FP as headline, a reviewer can argue the metric punishes repair (the scaffold's whole point) and ask "why not let baselines repair too?" — the baselines that *can* repair (Inagaki fix-loop +10, LLM-only retry, frontier direct retry) already do, and show their own FP→BoB gap, so BoB is the level field. Reporting FP as headline would also *understate* LabscriptAI and invite "you're hiding your repair loop's contribution" objections.

4. **It is what the paper already does.** Every filled headline number is BoB; every FP cell is TBD; the repo states FP "不是正文胜负手." Dropping FP from Table 1 codifies the existing practice rather than changing the story.

### 5.2 S1 (scaffold ablation) is the exception — keep BOTH FP and BoB

**Yes, S1 should keep both.** S1's purpose is "证明 scaffold 贡献，非模型红利" (`paper_execution_plan.md:47`). The scaffold's contribution *is* its repair/retry/memory machinery, and that contribution is quantified by the **FP→BoB gap**. Without FP, S1 cannot show what the scaffold adds over a no-repair direct baseline (Direct: 23/90 BoB; Direct + fix-loop: 45/90; LabscriptAI: 56/90 — and the FP column shows how much of each is first-shot vs repaired). Keeping both in S1 is not inconsistency; it is purposeful, because the gap is the ablation effect size. This is also exactly where `paper_execution_plan.md:311` and `paper_deliverables.md:53` assign FP composite.

### 5.3 Concrete columns to drop / keep

- **Main-text Table 1** (`paper_execution_plan.md:195`): drop the **"Authoring FP‡"** column. Keep **"Authoring BoB‡"** as the single authoring-quality column. (Keep Expert, Runtime, Memory, Cost as already planned; Sim stays out of the main table per §8.1.) Update the §8.1 footnote to define only BoB.
- **Table S2A** (`paper_execution_plan.md:233`): drop the **"FP composite"** column. Keep **"Composite"** (= BoB) as the single pass-rate column, alongside Package/Manifest/Setup-card/Tokens. S2A is generalization side-evidence (`status.html:1101`: "external 66 只能当泛化旁证，不能靠旧数字把它写成主文胜负手"); a single matched-budget composite is the right side-evidence metric.
- **Table S1** (`paper_execution_plan.md:219`): **keep both** "Composite BoB" and "Composite FP†", plus the broken-out Validator / Semantic / Param sweep columns. This is the one table where the FP→BoB delta carries the signal. (Fill the FP† cells — they are currently all TBD per `paper_execution_plan.md:225` and `authoring_benchmark_results.md:14`.)
- **`scripts/build_table1_v2.py`**: the script currently emits both `FP` and `FinalPass` (`build_table1_v2.py:409`). For the main-table build, drop the `FP` column and rename `FinalPass` → `BoB`. (S1 is built separately from freeze-run analysis, so this does not affect S1's both-columns layout.)
- **Naming cleanup (§4):** rename `FinalPass`→`BoB` in the builder; make `_first_pass_count` return NA (not the sim-only fallback) when `analysis` is missing; align `benchmark_taxonomy.md:124` to the four-gate composite so "FP" means exactly one thing.

---

## 6. Ready-to-paste table note (for Table 1 and S2A)

> **Authoring quality (BoB composite).** Authoring pass rate is the **best-of-budget composite (BoB)**: the fraction of tasks whose final submitted package, produced within the unified budget (≤8 attempts, ≤30 min wall time, ≤24k output tokens, ≤80 tool calls; `benchmark_taxonomy.md` §7), simultaneously satisfies four deterministic gates — `simulation_ok` (Opentrons simulator/analyze passes), `validator_ok` (package three-piece complete; deck/reagent/tip/manifest consistent; no critical failure), `semantic_ok` (semantic validator), and `param_sweep_ok` (parameter-sweep validator). The four gates are computed per task in `analyze_authoring_run.py` (`task_pass = simulation_ok ∧ validator_ok ∧ semantic_ok ∧ param_sweep_ok`) and aggregated as `task_pass_count`. All systems are evaluated under the same task set, same budget, same gates, and same blind expert panel; systems that lack a repair/retry loop (e.g. the official web tool, native coding agents without simulator access) are scored identically — BoB credits a correct final package regardless of whether it was produced first-shot or after repair. First-shot (no-repair) reliability and the repair contribution are reported separately in the scaffold-ablation table (Table S1) as the FP composite and the FP→BoB gap. LabscriptAI authoring numbers are from `labscriptai-authoring-light`, not `labscriptai-full` end-to-end.

---

## 7. Summary

- **Keep BoB composite** as the single headline authoring-quality metric in **Table 1** and **S2A**; drop the FP column there.
- **S1 keeps both** FP and BoB — the gap is the scaffold-ablation signal.
- The main text already relies on BoB (62/90 flash anchor; 56/90 historically); FP was never filled into Table 1 and the repo itself calls FP "不是正文胜负手." Dropping FP from the main table codifies existing practice.
- Fix three naming collisions: `FinalPass`→`BoB`; FP fallback must not silently degrade to sim-only; align `benchmark_taxonomy.md:124` to the four-gate composite.

#!/usr/bin/env python3
"""Extract every available metric (overall + per-subset) for the External 66
S2A supplementary table, from the two frozen py-only runs.

Writes:
  supplementary/table_s2a_external66_data.json
  supplementary/table_s2a_external66_data.csv
  supplementary/table_s2a_external66_data.md

Read-only on run artifacts.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNS = {
    "A_direct": {
        "label": "Direct (LLM-only, DeepSeek-V4-Pro)",
        "root": ROOT / "runs/table1_v2_external66_llm_only_py_official_deepseek",
    },
    "B_agent": {
        "label": "LabscriptAI authoring (light)",
        "root": ROOT / "runs/table1_v2_external66_unified_py_official_deepseek_pure",
    },
}

PRO_PRICE = {"input": 0.435, "output": 0.87}  # deepseek-v4-pro USD per 1M tokens


def subset_of(tid: str) -> str:
    t = str(tid)
    if t.startswith("EOPL"):
        return "EOPL"
    if t.startswith("EOPEN"):
        return "EOPEN"
    if t.startswith("EPLR"):
        return "EPLR"
    return "OTHER"


SUBSET_ORDER = ("EOPL", "EOPEN", "EPLR")
SUBSET_NAMES = {
    "EOPL": "Opentrons Protocol Library",
    "EOPEN": "OpenPlant source-strict",
    "EPLR": "PyLabRobot-style",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(v) -> int:
    if isinstance(v, bool) or v is None:
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def record_final_provider_error(rec: dict) -> bool:
    if rec.get("error"):
        return True
    for k, v in rec.items():
        if k.endswith("_returncode") and v is not None and as_int(v) != 0:
            return True
    return as_int(rec.get("provider_error_count")) > 0 and as_int(rec.get("total_tokens")) <= 0


def four_gates(item: dict) -> bool:
    return bool(
        item.get("simulation_ok")
        and item.get("validator_ok")
        and item.get("semantic_ok")
        and item.get("param_sweep_ok")
    )


def is_fp(item: dict) -> bool:
    return (
        as_int(item.get("generation_attempts")) == 1
        and as_int(item.get("simulation_repair_attempts")) == 0
        and bool(item.get("first_pass_simulation_ok"))
        and four_gates(item)
    )


def extract_run(runkey: str) -> dict:
    root = RUNS[runkey]["root"]
    summary = load(root / "summary.json")
    analysis = load(root / "analysis" / "attribution-summary.json")
    review = load(root / "expert_review" / "review-summary.json")

    # per-task analysis map
    a_by_task = {str(it.get("task_id")): it for it in analysis.get("per_task", []) if isinstance(it, dict) and it.get("task_id")}
    # per-task token / provider map from summary records
    rec_by_task = {str(r.get("task_id")): r for r in summary.get("records", []) if isinstance(r, dict) and r.get("task_id")}

    # per-task expert review map (detect task_id field)
    rev_per = review.get("per_task", [])
    rev_by_task = {}
    rev_taskid_key = None
    if rev_per:
        sample = rev_per[0] if isinstance(rev_per[0], dict) else {}
        for cand in ("task_id", "id", "task"):
            if cand in sample:
                rev_taskid_key = cand
                break
    if rev_taskid_key:
        for it in rev_per:
            if isinstance(it, dict) and it.get(rev_taskid_key) and it.get("ok") is not False:
                rev_by_task[str(it.get(rev_taskid_key))] = it

    # detect per-task trace field in analysis
    trace_key = None
    if a_by_task:
        sample_a = next(iter(a_by_task.values()))
        for cand in ("trace_present", "trace_ok", "has_trace", "trace"):
            if cand in sample_a:
                trace_key = cand
                break

    subsets = {s: [] for s in SUBSET_ORDER}
    other = []
    for tid, it in a_by_task.items():
        s = subset_of(tid)
        (subsets[s] if s in subsets else other).append((tid, it))

    def subset_metrics(tids_items):
        n = len(tids_items)
        fp = sum(1 for _, it in tids_items if is_fp(it))
        bob = sum(1 for _, it in tids_items if four_gates(it))
        sim = sum(1 for _, it in tids_items if it.get("simulation_ok"))
        val = sum(1 for _, it in tids_items if it.get("validator_ok"))
        sem = sum(1 for _, it in tids_items if it.get("semantic_ok"))
        psw = sum(1 for _, it in tids_items if it.get("param_sweep_ok"))

        in_tok = sum(as_int(rec_by_task.get(tid, {}).get("input_tokens")) for tid, _ in tids_items)
        out_tok = sum(as_int(rec_by_task.get(tid, {}).get("output_tokens")) for tid, _ in tids_items)
        tot_tok = in_tok + out_tok
        tok_per_task = (tot_tok / n) if n else None
        cost_total = (in_tok * PRO_PRICE["input"] + out_tok * PRO_PRICE["output"]) / 1_000_000
        cost_per_task = (cost_total / n) if n else None

        # expert
        ex_scores = []
        sub_dims = defaultdict(list)
        for tid, _ in tids_items:
            r = rev_by_task.get(tid)
            if not r:
                continue
            e = r.get("expert_score_mean")
            if isinstance(e, (int, float)):
                ex_scores.append(float(e))
            for dim in ("task_alignment_score", "biological_reasonableness_score",
                        "liquid_handling_quality_score", "safety_control_score", "code_quality_score"):
                v = r.get(dim)
                if isinstance(v, (int, float)):
                    sub_dims[dim].append(float(v))
        expert_mean = (sum(ex_scores) / len(ex_scores)) if ex_scores else None

        # trace
        if trace_key:
            trace = sum(1 for _, it in tids_items if it.get(trace_key))
        else:
            trace = None

        # repair distribution
        repair_dist = defaultdict(int)
        for _, it in tids_items:
            repair_dist[as_int(it.get("simulation_repair_attempts"))] += 1

        return {
            "n": n,
            "fp_composite": fp,
            "bob_composite": bob,
            "sim_pass": sim,
            "validator_pass": val,
            "semantic_pass": sem,
            "param_sweep_pass": psw,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "total_tokens": tot_tok,
            "tokens_per_task": tok_per_task,
            "cost_total_usd": cost_total,
            "cost_per_task_usd": cost_per_task,
            "expert_mean": expert_mean,
            "expert_n": len(ex_scores),
            "expert_subdims": {k: (sum(v) / len(v)) for k, v in sub_dims.items()} if sub_dims else {},
            "trace_present": trace,
            "repair_distribution": dict(sorted(repair_dist.items())),
        }

    overall = subset_metrics([(tid, it) for s in SUBSET_ORDER for tid, it in subsets[s]] + other)
    sub_out = {s: subset_metrics(subsets[s]) for s in SUBSET_ORDER}

    # top-level scalars (overall only)
    top = {
        "provider_events": as_int(summary.get("provider_error_count")),
        "final_api_fail": sum(1 for r in summary.get("records", []) if isinstance(r, dict) and record_final_provider_error(r)),
        "tool_calls": as_int(summary.get("tool_calls")),
        "simulator_calls": as_int(summary.get("simulator_calls")),
        "package_complete": as_int(summary.get("package_complete_count")),
        "trace_present_count_toplevel": as_int(analysis.get("trace_present_count")),
        "model_id": "deepseek-v4-pro",
    }
    # Overall trace is authoritative from the top-level count (per-task trace field
    # is not present in analysis per_task, so per-subset trace stays None/NA).
    if overall.get("trace_present") is None:
        overall["trace_present"] = top["trace_present_count_toplevel"]

    return {
        "label": RUNS[runkey]["label"],
        "root": str(root.relative_to(ROOT)),
        "source_paths": {
            "summary": str((root / "summary.json").relative_to(ROOT)),
            "analysis": str((root / "analysis" / "attribution-summary.json").relative_to(ROOT)),
            "review": str((root / "expert_review" / "review-summary.json").relative_to(ROOT)),
        },
        "overall": overall,
        "subsets": sub_out,
        "top_level": top,
        "review_taskid_key": rev_taskid_key,
        "trace_per_task_key": trace_key,
    }


def main() -> int:
    out_dir = ROOT / "supplementary"
    out_dir.mkdir(parents=True, exist_ok=True)

    data = {"runs": {}, "subset_names": SUBSET_NAMES, "pricing": {"model": "deepseek-v4-pro", "usd_per_m": PRO_PRICE}}
    for runkey in RUNS:
        data["runs"][runkey] = extract_run(runkey)

    # JSON
    (out_dir / "table_s2a_external66_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    # CSV (tidy long)
    rows = []
    for runkey, rd in data["runs"].items():
        for scope_name, scope_obj in [("ALL", rd["overall"])] + [(s, rd["subsets"][s]) for s in SUBSET_ORDER]:
            for metric in ("n", "fp_composite", "bob_composite", "sim_pass", "validator_pass",
                           "semantic_pass", "param_sweep_pass", "input_tokens", "output_tokens",
                           "total_tokens", "tokens_per_task", "cost_total_usd", "cost_per_task_usd",
                           "expert_mean", "expert_n", "trace_present"):
                v = scope_obj.get(metric)
                rows.append({"run": runkey, "subset": scope_name, "metric": metric,
                             "value": "" if v is None else v})
            for dim, v in scope_obj.get("expert_subdims", {}).items():
                rows.append({"run": runkey, "subset": scope_name, "metric": dim, "value": v})
            for k, v in scope_obj.get("repair_distribution", {}).items():
                rows.append({"run": runkey, "subset": scope_name, "metric": f"repair_{k}", "value": v})
        for metric in ("provider_events", "final_api_fail", "tool_calls", "simulator_calls",
                       "package_complete", "trace_present_count_toplevel", "model_id"):
            rows.append({"run": runkey, "subset": "ALL", "metric": metric,
                         "value": rd["top_level"].get(metric)})
    with (out_dir / "table_s2a_external66_data.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["run", "subset", "metric", "value"])
        w.writeheader()
        w.writerows(rows)

    # MD
    lines = ["# External 66 (S2A) raw data extract", "",
             f"Base model: deepseek-v4-pro | pricing input ${PRO_PRICE['input']}/M, output ${PRO_PRICE['output']}/M", ""]
    for runkey, rd in data["runs"].items():
        lines += [f"## {rd['label']} (`{rd['root']}`)", "",
                  f"review task_id key: `{rd['review_taskid_key']}` | per-task trace key: `{rd['trace_per_task_key']}`", ""]
        # overall table
        o = rd["overall"]
        t = rd["top_level"]
        o_ex = f"{o['expert_mean']:.2f}" if o["expert_mean"] is not None else "NA"
        o_tpt = f"{o['tokens_per_task']:.0f}" if o["tokens_per_task"] is not None else "NA"
        o_cpt = f"${o['cost_per_task_usd']:.4f}" if o["cost_per_task_usd"] is not None else "NA"
        o_tr = o["trace_present"] if o["trace_present"] is not None else "NA"
        lines += ["### Overall (n=66)", "",
                  "| N | FP | BoB | Sim | Val | Sem | PSW | Expert | Tok/task | $/task | Provider | FinalAPIfail | ToolCalls | SimCalls | Trace |",
                  "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
                  f"| {o['n']} | {o['fp_composite']}/{o['n']} | {o['bob_composite']}/{o['n']} | {o['sim_pass']}/{o['n']} | {o['validator_pass']}/{o['n']} | {o['semantic_pass']}/{o['n']} | {o['param_sweep_pass']}/{o['n']} | {o_ex} | {o_tpt} | {o_cpt} | {t['provider_events']} | {t['final_api_fail']} | {t['tool_calls']} | {t['simulator_calls']} | {o_tr} |",
                  ]
        # expert subdims
        if o.get("expert_subdims"):
            d = o["expert_subdims"]
            lines += ["", "Expert sub-dimensions (overall, mean/5): "
                      f"alignment={d.get('task_alignment_score'):.2f}, bio={d.get('biological_reasonableness_score'):.2f}, "
                      f"liquid={d.get('liquid_handling_quality_score'):.2f}, safety={d.get('safety_control_score'):.2f}, "
                      f"code={d.get('code_quality_score'):.2f}"]
        # subset table
        lines += ["", "### Per-subset", "",
                  "| Subset | n | FP | BoB | Sim | Val | Sem | PSW | Expert | Tok/task | $/task | Trace |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for s in SUBSET_ORDER:
            sb = rd["subsets"][s]
            ex = f"{sb['expert_mean']:.2f}" if sb["expert_mean"] is not None else "NA"
            tr = sb["trace_present"] if sb["trace_present"] is not None else "NA"
            tpt = f"{sb['tokens_per_task']:.0f}" if sb["tokens_per_task"] is not None else "NA"
            cpt = f"${sb['cost_per_task_usd']:.4f}" if sb["cost_per_task_usd"] is not None else "NA"
            lines.append(f"| {s} ({SUBSET_NAMES[s]}) | {sb['n']} | {sb['fp_composite']}/{sb['n']} | {sb['bob_composite']}/{sb['n']} | {sb['sim_pass']}/{sb['n']} | {sb['validator_pass']}/{sb['n']} | {sb['semantic_pass']}/{sb['n']} | {sb['param_sweep_pass']}/{sb['n']} | {ex} | {tpt} | {cpt} | {tr} |")
        # repair distribution
        lines += ["", "Repair distribution (simulation_repair_attempts -> #tasks):"]
        for s in ["ALL"] + list(SUBSET_ORDER):
            obj = o if s == "ALL" else rd["subsets"][s]
            dist = obj.get("repair_distribution", {})
            lines.append(f"  - {s}: {dict(sorted(dist.items()))}")
        lines.append("")

    # Verification against anchors
    anchors = {
        "A_direct": dict(N=66, FP=29, BoB=31, Sim=34, Val=34, Sem=58, PSW=63, Expert=3.78,
                         total_tokens=349542, tok_per_task=5296, provider=2, final_fail=0,
                         tool_calls=0, sim_calls=66, trace=0),
        "B_agent": dict(N=66, FP=47, BoB=56, Sim=60, Val=60, Sem=64, PSW=64, Expert=4.31,
                        total_tokens=4580307, tok_per_task=69399, provider=3, final_fail=0,
                        tool_calls=538, sim_calls=215, trace=66),
    }
    lines += ["## Verification against known anchors", ""]
    ok_all = True
    for runkey, exp in anchors.items():
        o = data["runs"][runkey]["overall"]
        t = data["runs"][runkey]["top_level"]
        got = dict(N=o["n"], FP=o["fp_composite"], BoB=o["bob_composite"], Sim=o["sim_pass"],
                   Val=o["validator_pass"], Sem=o["semantic_pass"], PSW=o["param_sweep_pass"],
                   Expert=round(o["expert_mean"], 2) if o["expert_mean"] else None,
                   total_tokens=o["total_tokens"], tok_per_task=round(o["tokens_per_task"]),
                   provider=t["provider_events"], final_fail=t["final_api_fail"],
                   tool_calls=t["tool_calls"], sim_calls=t["simulator_calls"],
                   trace=o["trace_present"] if o["trace_present"] is not None else None)
        mism = {k: (exp[k], got[k]) for k in exp if got.get(k) != exp[k]}
        status = "OK" if not mism else f"MISMATCH: {mism}"
        if mism:
            ok_all = False
        lines.append(f"- {runkey}: {status}")
    lines.append(f"\nAll anchors match: {ok_all}")

    (out_dir / "table_s2a_external66_data.md").write_text("\n".join(lines), encoding="utf-8")

    # Console summary
    for runkey in RUNS:
        o = data["runs"][runkey]["overall"]
        t = data["runs"][runkey]["top_level"]
        ex = f"{o['expert_mean']:.2f}" if o["expert_mean"] is not None else "NA"
        tpt = f"{o['tokens_per_task']:.0f}" if o["tokens_per_task"] is not None else "NA"
        cpt = f"{o['cost_per_task_usd']:.4f}" if o["cost_per_task_usd"] is not None else "NA"
        tr = o["trace_present"] if o["trace_present"] is not None else "NA"
        print(f"{runkey}: N={o['n']} FP={o['fp_composite']} BoB={o['bob_composite']} "
              f"Sim={o['sim_pass']} Val={o['validator_pass']} Sem={o['semantic_pass']} "
              f"PSW={o['param_sweep_pass']} Expert={ex} "
              f"tok/task={tpt} $/task=${cpt} "
              f"prov={t['provider_events']} fail={t['final_api_fail']} tools={t['tool_calls']} "
              f"simcalls={t['simulator_calls']} trace={tr}")
        for s in SUBSET_ORDER:
            sb = data["runs"][runkey]["subsets"][s]
            sx = f"{sb['expert_mean']:.2f}" if sb["expert_mean"] is not None else "NA"
            stpt = f"{sb['tokens_per_task']:.0f}" if sb["tokens_per_task"] is not None else "NA"
            print(f"  {s}: n={sb['n']} FP={sb['fp_composite']} BoB={sb['bob_composite']} "
                  f"Sim={sb['sim_pass']} Val={sb['validator_pass']} Sem={sb['semantic_pass']} "
                  f"PSW={sb['param_sweep_pass']} Expert={sx} tok/task={stpt}")
    print(f"\nAnchors match: {ok_all}")
    print(f"Wrote: {out_dir/'table_s2a_external66_data.json'}")
    print(f"Wrote: {out_dir/'table_s2a_external66_data.csv'}")
    print(f"Wrote: {out_dir/'table_s2a_external66_data.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

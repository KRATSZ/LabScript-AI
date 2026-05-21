"""Contamination probes for the authoring benchmark task text.

The probe intentionally uses only the Python standard library so it can run in
clean reproduction environments. API keys are read from environment variables;
do not put keys in task manifests, result files, or command lines.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .tasks import AuthoringTask, load_authoring_tasks

DEFAULT_TASKS = Path("benchmarks/authoring/tasks.yaml")
DEFAULT_OUTPUT = Path("benchmarks/authoring/contamination_report.json")
DEEPSEEK_SMOKE_OUTPUT = Path("benchmarks/authoring/contamination_report.deepseek_smoke.json")
DEEPSEEK_SMOKE_TASK_IDS = ("T001", "T013", "T039", "T056", "T064", "T086")
DEFAULT_CANARY_TASKS = ("T056", "T057", "T058", "T059", "T060")
CANARY_PREFIX = "NBT_CANARY_20260515"

# Legacy prompts share this boilerplate; verbatim prefix must skip it or all 55 collide.
LEGACY_PROMPT_BOILERPLATE = (
    "Can you write a Python script that does the following experiment?\n"
)


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    base_url: str
    api_key_env: str

    @property
    def api_key(self) -> str:
        value = os.environ.get(self.api_key_env)
        if not value:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        return value


def parse_model_config(value: str) -> ModelConfig:
    """Parse `model_id,base_url,api_key_env` CLI values."""

    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3 or not all(parts):
        raise argparse.ArgumentTypeError(
            "model config must be: model_id,base_url,api_key_env"
        )
    return ModelConfig(model_id=parts[0], base_url=parts[1], api_key_env=parts[2])


def _chat_endpoint(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    return f"{url}/chat/completions"


def chat_completion(
    model: ModelConfig,
    messages: Sequence[dict[str, str]],
    *,
    max_tokens: int = 160,
    temperature: float = 0.0,
    timeout_sec: int = 120,
) -> str:
    payload: dict[str, Any] = {
        "model": model.model_id,
        "messages": list(messages),
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    # DeepSeek V4 default "thinking" leaves assistant `content` empty; disable for parseable text.
    if "deepseek" in model.base_url.lower() or "deepseek" in model.model_id.lower():
        payload["thinking"] = {"type": "disabled"}
    request = urllib.request.Request(
        _chat_endpoint(model.base_url),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {model.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{model.model_id} request failed: {exc.code} {detail}") from exc
    msg = data["choices"][0]["message"]
    text = msg.get("content")
    if not (isinstance(text, str) and text.strip()) and isinstance(msg.get("reasoning_content"), str):
        text = msg.get("reasoning_content")
    return str(text or "").strip()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+", text.lower())


def rouge_l_f1(candidate: str, reference: str) -> float:
    cand = _tokens(candidate)
    ref = _tokens(reference)
    if not cand or not ref:
        return 0.0
    previous = [0] * (len(ref) + 1)
    for cand_token in cand:
        current = [0]
        for index, ref_token in enumerate(ref, start=1):
            if cand_token == ref_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    lcs = previous[-1]
    precision = lcs / len(cand)
    recall = lcs / len(ref)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def canary_token(task_id: str) -> str:
    return f"{CANARY_PREFIX}_{task_id}_Q7K9M2"


def inject_canary(text: str, task_id: str) -> str:
    token = canary_token(task_id)
    insert_at = min(75, max(0, len(text)))
    return f"{text[:insert_at]} {token} {text[insert_at:]}"


def _strip_legacy_boilerplate_for_verbatim(text: str, source: str) -> str:
    if source != "legacy_55":
        return text
    if text.startswith(LEGACY_PROMPT_BOILERPLATE):
        return text[len(LEGACY_PROMPT_BOILERPLATE) :]
    return text


def verbatim_completion_probe(
    model: ModelConfig, task_text: str, *, source: str
) -> tuple[str, float]:
    body = _strip_legacy_boilerplate_for_verbatim(task_text, source)
    prefix = body[:50]
    reference = body[50:150]
    completion = chat_completion(
        model,
        [
            {
                "role": "system",
                "content": "Complete the benchmark question text exactly. Return only the continuation.",
            },
            {"role": "user", "content": prefix},
        ],
        max_tokens=120,
        temperature=0.0,
    )
    return completion, rouge_l_f1(completion, reference)


def source_attribution_probe(model: ModelConfig, task_text: str) -> tuple[str, bool]:
    response = chat_completion(
        model,
        [
            {
                "role": "system",
                "content": (
                    "Answer whether you have seen this exact benchmark question before. "
                    "If yes, name the source. Be conservative and do not guess."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Have you seen this benchmark question before? If yes, name the source.\n\n"
                    f"{task_text}"
                ),
            },
        ],
        max_tokens=120,
        temperature=0.0,
    )
    lowered = response.lower()
    source_terms = ("inagaki", "gpt4ot2", "gpt-4 ot-2", "labauto", "opentrons benchmark")
    negative_terms = ("no", "not seen", "do not recognize", "don't recognize", "cannot identify")
    hit = any(term in lowered for term in source_terms) and not any(
        term in lowered for term in negative_terms
    )
    return response, hit


def task_text_for_probe(task: AuthoringTask, canary_task_ids: set[str]) -> str:
    if task.task_id in canary_task_ids:
        return inject_canary(task.prompt, task.task_id)
    return task.prompt


def run_probe(
    tasks: Sequence[AuthoringTask],
    models: Sequence[ModelConfig],
    *,
    canary_task_ids: set[str],
    sleep_sec: float,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model in models:
        for task in tasks:
            probe_text = task_text_for_probe(task, canary_task_ids)
            completion, rouge_l = verbatim_completion_probe(
                model, probe_text, source=task.source
            )
            attribution_response, attribution_hit = source_attribution_probe(model, task.prompt)
            token = canary_token(task.task_id)
            records.append(
                {
                    "task_id": task.task_id,
                    "model_id": model.model_id,
                    "verbatim_rougeL": rouge_l,
                    "attribution_hit": attribution_hit,
                    "canary_hit": task.task_id in canary_task_ids and token in completion,
                    "source": task.source,
                    "canary_token": token if task.task_id in canary_task_ids else None,
                    "attribution_response": attribution_response,
                }
            )
            if sleep_sec:
                time.sleep(sleep_sec)
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run authoring benchmark contamination probes")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--deepseek-smoke",
        action="store_true",
        help=(
            "Run a fixed 6-task smoke set on DeepSeek OpenAI-compatible API "
            "(deepseek-v4-pro, https://api.deepseek.com, env DEEPSEEK_API_KEY). "
            "Writes contamination_report.deepseek_smoke.json unless --output is set."
        ),
    )
    parser.add_argument(
        "--model",
        action="append",
        type=parse_model_config,
        default=None,
        help="Model config as model_id,base_url,api_key_env (repeatable). Not used with --deepseek-smoke.",
    )
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-sec", type=float, default=0.0)
    parser.add_argument(
        "--canary-task-id",
        action="append",
        default=list(DEFAULT_CANARY_TASKS),
        help="New task IDs to probe with injected canary strings",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.deepseek_smoke:
        if not os.environ.get("DEEPSEEK_API_KEY"):
            print(
                "Skipping DeepSeek smoke: set DEEPSEEK_API_KEY in the environment, then re-run with "
                "--deepseek-smoke.",
                flush=True,
            )
            return 0
        models = [
            ModelConfig(
                model_id="deepseek-v4-pro",
                base_url="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
            )
        ]
        task_ids = list(DEEPSEEK_SMOKE_TASK_IDS)
        output = args.output or DEEPSEEK_SMOKE_OUTPUT
    else:
        if not args.model:
            raise SystemExit("error: provide --model ... at least once, or use --deepseek-smoke")
        models = args.model
        task_ids = args.task_id
        output = args.output or DEFAULT_OUTPUT

    tasks = list(load_authoring_tasks(args.tasks))
    if task_ids:
        requested = set(task_ids)
        tasks = [task for task in tasks if task.task_id in requested]
    if args.limit:
        tasks = tasks[: args.limit]
    records = run_probe(
        tasks,
        models,
        canary_task_ids=set(args.canary_task_id),
        sleep_sec=args.sleep_sec,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} contamination probe records to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

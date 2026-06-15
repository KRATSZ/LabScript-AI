#!/usr/bin/env python3
"""Collect OpentronsAI web-chat responses for the authoring90 benchmark.

The collector is intentionally conservative: it stores the raw web transcript
first, extracts protocol.py only when the response text clearly contains a
Python protocol, and supports resumable runs by skipping already extracted
tasks.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "runs" / "authoring90" / "opentrons_ai_v1"
DEFAULT_PROMPTS = DEFAULT_OUT / "prompts.jsonl"
DEFAULT_URL = "https://ai.opentrons.com/#/chat"
SMOKE_TASK_IDS = (
    "T001",
    "T002",
    "T014",
    "T024",
    "T034",
    "T047",
    "T055",
    "T057",
    "T068",
    "T073",
    "T087",
    "T090",
)

REFUSAL_PATTERNS = (
    re.compile(r"\b(can(?:not|'t)|unable|won't)\b.*\b(protocol|code|assist|help)\b", re.I | re.S),
    re.compile(r"\b(safety|policy|unsupported|not supported|cannot comply)\b", re.I),
)


@dataclass(frozen=True)
class ExtractedProtocol:
    status: str
    method: str
    protocol_text: str
    reason: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_prompt_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict) or not payload.get("task_id"):
                raise ValueError(f"invalid prompt record at {path}:{line_number}")
            records.append(payload)
    return records


def parse_task_ids(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def select_prompt_records(
    records: list[dict[str, Any]],
    *,
    task_ids: tuple[str, ...] = (),
    smoke: bool = False,
    panel_path: Path | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    wanted: tuple[str, ...] = task_ids
    if smoke:
        wanted = SMOKE_TASK_IDS
    if panel_path is not None:
        payload = json.loads(panel_path.read_text(encoding="utf-8"))
        wanted = tuple(str(task_id) for task_id in payload.get("task_ids", []))
    if wanted:
        index = {str(record["task_id"]): record for record in records}
        missing = [task_id for task_id in wanted if task_id not in index]
        if missing:
            raise ValueError(f"task ids missing from prompts: {', '.join(missing)}")
        selected = [index[task_id] for task_id in wanted]
    else:
        selected = list(records)
    if limit is not None:
        selected = selected[:limit]
    return selected


def _strip_code_block(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^```[a-zA-Z0-9_.+-]*\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip() + "\n"


def looks_like_protocol(text: str) -> bool:
    stripped = text.strip()
    if "def run(" not in stripped:
        return False
    opentrons_markers = (
        "from opentrons",
        "protocol_api",
        "ProtocolContext",
        "load_labware(",
        "load_instrument(",
    )
    return any(marker in stripped for marker in opentrons_markers)


def looks_like_plain_protocol_file(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith(("from opentrons", "import opentrons", "metadata =", "requirements =")):
        return False
    return looks_like_protocol(stripped)


def looks_like_partial_protocol(text: str) -> bool:
    stripped = text.strip()
    pythonish = any(
        marker in stripped
        for marker in (
            "from opentrons",
            "protocol_api",
            "metadata =",
            "load_labware(",
            "load_instrument(",
        )
    )
    return pythonish and not looks_like_protocol(stripped)


def _code_fence_candidates(text: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for match in re.finditer(r"```([a-zA-Z0-9_.+-]*)\s*\n(.*?)```", text, re.S):
        language = match.group(1).strip().lower()
        body = _strip_code_block(match.group(2))
        candidates.append((language, body))
    return candidates


def _is_refusal(text: str) -> bool:
    if looks_like_protocol(text):
        return False
    return any(pattern.search(text) for pattern in REFUSAL_PATTERNS)


def extract_protocol_from_text(text: str) -> ExtractedProtocol:
    """Extract protocol.py without inventing missing code."""

    for language, body in _code_fence_candidates(text):
        if language and language not in {"python", "py", "protocol.py", ""}:
            continue
        if looks_like_protocol(body):
            return ExtractedProtocol("ok", "markdown_fence", body)
    for _language, body in _code_fence_candidates(text):
        if looks_like_partial_protocol(body):
            return ExtractedProtocol("partial", "markdown_fence", "", "python fence lacks def run")
    if looks_like_plain_protocol_file(text):
        return ExtractedProtocol("ok", "plain_text", text.strip() + "\n")
    if looks_like_protocol(text):
        return ExtractedProtocol(
            "partial",
            "plain_text",
            "",
            "plain text contains protocol markers but is not a clean Python file",
        )
    if looks_like_partial_protocol(text):
        return ExtractedProtocol("partial", "plain_text", "", "plain text looks incomplete")
    if _is_refusal(text):
        return ExtractedProtocol("refused", "none", "", "response appears to refuse or mark unsupported")
    return ExtractedProtocol("no_protocol", "none", "", "no complete Opentrons protocol found")


def task_raw_dir(out_dir: Path, task_id: str) -> Path:
    return out_dir / task_id / "raw"


def task_package_dir(out_dir: Path, task_id: str) -> Path:
    return out_dir / task_id / "attempt1" / "package"


def write_collection_outputs(
    *,
    out_dir: Path,
    record: dict[str, Any],
    response_text: str,
    transcript_extra: dict[str, Any] | None = None,
    meta_extra: dict[str, Any] | None = None,
) -> ExtractedProtocol:
    task_id = str(record["task_id"])
    raw_dir = task_raw_dir(out_dir, task_id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt = str(record.get("full_prompt", ""))
    (raw_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (raw_dir / "response.md").write_text(response_text, encoding="utf-8")

    extracted = extract_protocol_from_text(response_text)
    transcript = {
        "schema_version": "1.0",
        "task_id": task_id,
        "turns": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response_text},
        ],
        "extract_status": extracted.status,
        "extract_method": extracted.method,
        "extract_reason": extracted.reason,
    }
    if transcript_extra:
        transcript.update(transcript_extra)
    (raw_dir / "transcript.json").write_text(
        json.dumps(transcript, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    status = str(transcript.get("extract_status", extracted.status))
    method = str(transcript.get("extract_method", extracted.method))
    meta = {
        "schema_version": "1.0",
        "task_id": task_id,
        "collected_at": utc_now(),
        "target": DEFAULT_URL,
        "prompt_hash": record.get("prompt_hash"),
        "difficulty": record.get("difficulty"),
        "extract_status": status,
        "extract_method": method,
    }
    if meta_extra:
        meta.update(meta_extra)
    (raw_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    if extracted.status == "ok":
        package_dir = task_package_dir(out_dir, task_id)
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "protocol.py").write_text(extracted.protocol_text, encoding="utf-8")
    return extracted


def extract_existing_raw(
    *,
    out_dir: Path,
    records: list[dict[str, Any]],
    force: bool = False,
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for record in records:
        task_id = str(record["task_id"])
        protocol_path = task_package_dir(out_dir, task_id) / "protocol.py"
        if protocol_path.exists() and not force:
            statuses[task_id] = "skipped_ok"
            continue
        response_path = task_raw_dir(out_dir, task_id) / "response.md"
        if not response_path.exists():
            statuses[task_id] = "missing_response"
            continue
        fallback_response = response_path.read_text(encoding="utf-8")
        transcript_extra, meta_extra, chrome_response = _chrome_capture_extras(
            response_path.parent,
            fallback_response,
        )
        meta_extra["extract_only"] = True
        extracted = write_collection_outputs(
            out_dir=out_dir,
            record=record,
            response_text=chrome_response,
            transcript_extra=transcript_extra,
            meta_extra=meta_extra,
        )
        statuses[task_id] = extracted.status
    return statuses


def _chrome_capture_extras(
    raw_dir: Path,
    fallback_response: str,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    capture_path = raw_dir / "chrome_capture.json"
    if not capture_path.is_file():
        return {}, {}, fallback_response
    try:
        payload = json.loads(capture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, {}, fallback_response
    if not isinstance(payload, dict):
        return {}, {}, fallback_response
    capture = payload.get("capture") if isinstance(payload.get("capture"), dict) else {}
    code_block_count = int(capture.get("codeBlockCount") or 0) if capture else 0
    raw_text = str(capture.get("rawText", ""))
    response_text = _markdown_from_chrome_raw_text(raw_text) if raw_text else fallback_response
    transcript_extra = {
        "collection_attempt": int(payload.get("collection_attempt", 1) or 1),
        "ui_capture_method": "chrome_extension_dom",
        "ui_response_text_raw": raw_text,
        "extract_method_ui_source": "visible_python_code_block" if code_block_count else "assistant_text",
    }
    meta_extra = {
        "collection_attempts": transcript_extra["collection_attempt"],
        "wall_time_sec": payload.get("wall_time_sec"),
        "browser_channel": "existing_chrome_extension",
        "url": capture.get("url"),
        "page_title": capture.get("title"),
        "session_policy": payload.get("session_policy", "new_tab_chat_now_per_task"),
        "prompt_scheme": "A_flattened_py_only",
        "ui_capture_method": "chrome_extension_dom",
    }
    return transcript_extra, meta_extra, response_text


def _clean_chrome_code_lines(lines: list[str]) -> str:
    return "\n".join(line.replace("\u00a0", " ").rstrip() for line in lines).strip() + "\n"


def _markdown_from_chrome_raw_text(raw_text: str) -> str:
    """Recover a Markdown response from OpentronsAI DOM text.

    The Chrome DOM exposes the code-block language label as a plain ``PYTHON``
    line. It may also expose syntax-highlighted tokens as nested ``code``
    elements, so the already-rendered Markdown can contain accidental nested
    fences. The raw text is cleaner; use AST parsing to find the complete
    protocol block without inventing missing code.
    """

    lines = raw_text.splitlines()
    for label_index, line in enumerate(lines):
        if line.strip().upper() != "PYTHON":
            continue
        body_lines = lines[label_index + 1 :]
        for end in range(len(body_lines), 0, -1):
            candidate = _clean_chrome_code_lines(body_lines[:end])
            if not looks_like_protocol(candidate):
                continue
            try:
                ast.parse(candidate)
            except SyntaxError:
                continue
            before = "\n".join(lines[:label_index]).strip()
            after = "\n".join(body_lines[end:]).strip()
            parts = [
                before,
                "```python\n" + candidate + "```",
                after,
            ]
            return "\n\n".join(part for part in parts if part).strip() + "\n"
    return raw_text.strip() + "\n"


async def _first_visible(page: Any, selectors: list[str]) -> Any | None:
    for selector in selectors:
        locator = page.locator(selector)
        count = await locator.count()
        for index in range(count):
            item = locator.nth(index)
            try:
                if await item.is_visible():
                    return item
            except Exception:
                continue
    return None


async def _maybe_click_by_role(page: Any, names: list[str]) -> bool:
    for name in names:
        try:
            locator = page.get_by_role("button", name=re.compile(name, re.I)).first
            if await locator.count() and await locator.is_visible():
                await locator.click()
                return True
        except Exception:
            continue
    return False


async def _try_export_response(page: Any, raw_dir: Path, timeout_ms: int = 5000) -> str:
    export_names = ["export", "download", "protocol", "copy code"]
    for name in export_names:
        try:
            button = page.get_by_role("button", name=re.compile(name, re.I)).last
            if not await button.count() or not await button.is_visible():
                continue
            async with page.expect_download(timeout=timeout_ms) as download_info:
                await button.click()
            download = await download_info.value
            export_path = raw_dir / ("export-" + download.suggested_filename)
            await download.save_as(str(export_path))
            try:
                return export_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return ""
        except Exception:
            continue
    return ""


async def _assistant_text(page: Any, full_prompt: str, assistant_selector: str | None) -> str:
    selectors = []
    if assistant_selector:
        selectors.append(assistant_selector)
    selectors.extend(
        [
            "[data-message-author-role='assistant']",
            "[data-testid*='assistant']",
            "[class*='assistant']",
            "main article",
            "main [class*='message']",
        ]
    )
    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()
            texts: list[str] = []
            for index in range(count):
                item = locator.nth(index)
                if await item.is_visible():
                    text = (await item.inner_text()).strip()
                    if text and text not in texts:
                        texts.append(text)
            if texts:
                return texts[-1]
        except Exception:
            continue

    body_text = (await page.locator("body").inner_text()).strip()
    if full_prompt and full_prompt.strip() in body_text:
        return body_text.rsplit(full_prompt.strip(), 1)[-1].strip()
    return body_text


async def _fill_chat_input(page: Any, prompt: str, input_selector: str | None) -> Any:
    selectors = []
    if input_selector:
        selectors.append(input_selector)
    selectors.extend(
        [
            "textarea",
            "[contenteditable='true']",
            "[role='textbox']",
            "input[type='text']",
        ]
    )
    locator = await _first_visible(page, selectors)
    if locator is None:
        raise RuntimeError("could not find a visible chat input")
    await locator.click()
    try:
        await locator.fill(prompt)
    except Exception:
        await page.keyboard.insert_text(prompt)
    return locator


async def _submit_prompt(page: Any, input_locator: Any, send_selector: str | None) -> None:
    if send_selector:
        button = await _first_visible(page, [send_selector])
        if button is not None:
            await button.click()
            return
    if await _maybe_click_by_role(page, ["send", "submit", "run"]):
        return
    await input_locator.press("Enter")


async def _wait_for_stable_response(
    page: Any,
    *,
    before_text: str,
    timeout_sec: int,
    stable_sec: int,
) -> None:
    deadline = time.monotonic() + timeout_sec
    last_text = ""
    last_change = time.monotonic()
    saw_growth = False
    while time.monotonic() < deadline:
        body_text = await page.locator("body").inner_text()
        if len(body_text) > len(before_text) + 40:
            saw_growth = True
        if body_text != last_text:
            last_text = body_text
            last_change = time.monotonic()
        if saw_growth and time.monotonic() - last_change >= stable_sec:
            return
        await page.wait_for_timeout(1000)
    raise TimeoutError(f"response did not stabilize within {timeout_sec}s")


async def collect_with_playwright(args: argparse.Namespace, records: list[dict[str, Any]]) -> dict[str, str]:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover - depends on local environment.
        raise SystemExit(
            "Playwright is not installed. Install it in this environment, then rerun this script."
        ) from exc

    statuses: dict[str, str] = {}
    out_dir = args.out_dir.resolve()
    profile_dir = args.user_data_dir.resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(profile_dir),
            channel=args.browser_channel,
            headless=args.headless,
            accept_downloads=True,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(args.url, wait_until="domcontentloaded", timeout=args.nav_timeout_sec * 1000)

        for record in records:
            task_id = str(record["task_id"])
            protocol_path = task_package_dir(out_dir, task_id) / "protocol.py"
            transcript_path = task_raw_dir(out_dir, task_id) / "transcript.json"
            if args.resume and protocol_path.exists() and transcript_path.exists():
                statuses[task_id] = "skipped_ok"
                continue

            attempts = args.max_retries + 1
            last_error = ""
            for attempt in range(1, attempts + 1):
                raw_dir = task_raw_dir(out_dir, task_id)
                screenshots_dir = raw_dir / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                started = time.monotonic()
                try:
                    await page.goto(args.url, wait_until="domcontentloaded", timeout=args.nav_timeout_sec * 1000)
                    await _maybe_click_by_role(page, ["new chat", "new conversation", "start new", "clear"])
                    await page.wait_for_timeout(1000)
                    before_text = await page.locator("body").inner_text()
                    await page.screenshot(path=str(screenshots_dir / f"attempt{attempt}-before.png"), full_page=True)
                    input_locator = await _fill_chat_input(page, str(record["full_prompt"]), args.input_selector)
                    await _submit_prompt(page, input_locator, args.send_selector)
                    await _wait_for_stable_response(
                        page,
                        before_text=before_text,
                        timeout_sec=args.timeout_sec,
                        stable_sec=args.stable_sec,
                    )
                    await page.screenshot(path=str(screenshots_dir / f"attempt{attempt}-after.png"), full_page=True)
                    response_text = await _assistant_text(page, str(record["full_prompt"]), args.assistant_selector)
                    extracted = extract_protocol_from_text(response_text)
                    if extracted.status != "ok" and args.try_export:
                        exported = await _try_export_response(page, raw_dir)
                        if exported:
                            exported_extract = extract_protocol_from_text(exported)
                            if exported_extract.status == "ok":
                                response_text = exported
                                extracted = exported_extract
                    extracted = write_collection_outputs(
                        out_dir=out_dir,
                        record=record,
                        response_text=response_text,
                        transcript_extra={"collection_attempt": attempt},
                        meta_extra={
                            "collection_attempts": attempt,
                            "wall_time_sec": time.monotonic() - started,
                            "browser_channel": args.browser_channel,
                            "url": page.url,
                            "session_policy": "new_chat_per_task",
                            "prompt_scheme": "A_flattened_py_only",
                        },
                    )
                    statuses[task_id] = extracted.status
                    break
                except Exception as exc:  # pragma: no cover - live UI behavior.
                    last_error = f"{type(exc).__name__}: {exc}"
                    await page.screenshot(path=str(screenshots_dir / f"attempt{attempt}-error.png"), full_page=True)
                    if attempt >= attempts:
                        write_collection_outputs(
                            out_dir=out_dir,
                            record=record,
                            response_text="",
                            transcript_extra={
                                "collection_attempt": attempt,
                                "extract_status": "timeout",
                                "extract_method": "none",
                            },
                            meta_extra={
                                "collection_attempts": attempt,
                                "wall_time_sec": time.monotonic() - started,
                                "browser_channel": args.browser_channel,
                                "url": page.url,
                                "collection_error": last_error,
                            },
                        )
                        statuses[task_id] = "timeout"
                await page.wait_for_timeout(int(random.uniform(args.sleep_min_sec, args.sleep_max_sec) * 1000))

        await context.close()
    return statuses


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--task-ids")
    parser.add_argument("--smoke", action="store_true", help="Use the 12-task smoke subset.")
    parser.add_argument("--panel", type=Path, help="Use task_ids from a panel JSON manifest.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--extract-only", action="store_true", help="Re-extract protocol.py from raw response.md files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing extracted protocol.py in extract-only mode.")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--user-data-dir", type=Path, default=DEFAULT_OUT / "browser_profile")
    parser.add_argument("--browser-channel", default="chrome")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--input-selector")
    parser.add_argument("--send-selector")
    parser.add_argument("--assistant-selector")
    parser.add_argument("--try-export", action="store_true")
    parser.add_argument("--timeout-sec", type=int, default=240)
    parser.add_argument("--nav-timeout-sec", type=int, default=60)
    parser.add_argument("--stable-sec", type=int, default=8)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--sleep-min-sec", type=float, default=5.0)
    parser.add_argument("--sleep-max-sec", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.sleep_max_sec < args.sleep_min_sec:
        parser.error("--sleep-max-sec must be >= --sleep-min-sec")

    records = select_prompt_records(
        load_prompt_records(args.prompts),
        task_ids=parse_task_ids(args.task_ids),
        smoke=args.smoke,
        panel_path=args.panel,
        limit=args.limit,
    )
    if args.dry_run:
        print("\n".join(str(record["task_id"]) for record in records))
        return 0
    if args.extract_only:
        statuses = extract_existing_raw(out_dir=args.out_dir.resolve(), records=records, force=args.force)
    else:
        statuses = asyncio.run(collect_with_playwright(args, records))
    print(json.dumps(statuses, indent=2, ensure_ascii=False))
    failed = {task_id: status for task_id, status in statuses.items() if status not in {"ok", "skipped_ok"}}
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

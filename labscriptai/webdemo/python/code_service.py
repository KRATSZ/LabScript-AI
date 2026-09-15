#!/usr/bin/env python3
"""OT code/analyze service on 127.0.0.1:8010. Started by webdemo `npm run dev`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any, Iterator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

HOST = "127.0.0.1"
PORT = int(os.environ.get("LABSCRIPTAI_CODE_PORT") or 8010)
WEBDEMO_ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and os.environ.get(key) in (None, ""):
            os.environ[key] = value


_load_env_file(WEBDEMO_ROOT / ".env")

app = FastAPI(title="LabscriptAI code service", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ANALYZE_JOBS: dict[str, dict[str, Any]] = {}
_ANALYZE_LOCK = Lock()
_ANALYZE_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ot-analyze")


class CodeGenRequest(BaseModel):
    sop_markdown: str = ""
    hardware_config: str = ""
    robot_model: str = "OT-2"


class SimulateRequest(BaseModel):
    protocol_code: str


class ConverseRequest(BaseModel):
    original_code: str = ""
    user_instruction: str = ""


def _deepseek() -> tuple[str, str, str]:
    key = (
        os.environ.get("LABSCRIPTAI_DEEPSEEK_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or ""
    )
    base = (
        os.environ.get("LABSCRIPTAI_DEEPSEEK_BASE_URL")
        or os.environ.get("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    ).rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    model = (
        os.environ.get("LABSCRIPTAI_DEEPSEEK_MODEL")
        or os.environ.get("DEEPSEEK_MODEL")
        or "deepseek-flash"
    )
    return key, base, model


def _chat_stream(messages: list[dict[str, str]]) -> Iterator[tuple[str, str]]:
    import urllib.request

    key, base, model = _deepseek()
    if not key:
        raise RuntimeError("DeepSeek key missing for code generation")
    body = json.dumps(
        {"model": model, "stream": True, "messages": messages}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=360) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            choices = data.get("choices") or []
            delta = (choices[0] or {}).get("delta") or {} if choices else {}
            thinking = delta.get("reasoning_content") or delta.get("reasoning") or ""
            content = delta.get("content") or ""
            if thinking:
                yield "thinking", str(thinking)
            if content:
                yield "content", str(content)


def _code_prompt(sop: str, hardware: str, robot: str) -> str:
    return (
        f"Write an Opentrons protocol_api Python script for {robot}.\n"
        "Return only Python. metadata + requirements with apiLevel. def run(protocol).\n"
        "Use the hardware config exactly (pipettes, slots, labware).\n\n"
        f"Hardware:\n{hardware}\n\nSOP:\n{sop}\n"
    )


def _extract_python(text: str) -> str:
    fence = text.find("```")
    if fence < 0:
        return text.strip()
    rest = text[fence + 3 :]
    if rest.lower().startswith("python"):
        rest = rest.split("\n", 1)[-1]
    end = rest.find("```")
    return (rest[:end] if end >= 0 else rest).strip()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "running", "service": "labscriptai-code", "bind": f"{HOST}:{PORT}"}


@app.post("/api/generate-protocol-code")
def generate_protocol_code(request: CodeGenRequest) -> StreamingResponse:
    def events() -> Iterator[bytes]:
        try:
            chunks: list[str] = []
            for kind, token in _chat_stream(
                [
                    {
                        "role": "user",
                        "content": _code_prompt(
                            request.sop_markdown, request.hardware_config, request.robot_model
                        ),
                    }
                ]
            ):
                if kind == "thinking":
                    yield f"data: {json.dumps({'event_type': 'thinking', 'token': token})}\n\n".encode()
                else:
                    chunks.append(token)
            code = _extract_python("".join(chunks))
            yield f"data: {json.dumps({'generated_code': code, 'final_code': code})}\n\n".encode()
            yield b'data: {"event_type": "stream_complete"}\n\n'
        except Exception as exc:
            yield f"data: {json.dumps({'event_type': 'error', 'message': str(exc)})}\n\n".encode()

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/api/converse-code")
def converse_code(request: ConverseRequest) -> dict[str, str]:
    prompt = (
        "Edit this Opentrons protocol. Return only Python.\n\n"
        f"Instruction:\n{request.user_instruction}\n\n"
        f"Code:\n{request.original_code}\n"
    )
    chunks: list[str] = []
    for kind, token in _chat_stream([{"role": "user", "content": prompt}]):
        if kind == "content":
            chunks.append(token)
    return {"type": "edit", "content": _extract_python("".join(chunks))}


def simulate_protocol_code(code: str) -> dict[str, Any]:
    try:
        from io import StringIO

        from opentrons.simulate import simulate

        simulate(StringIO(code))
        return {
            "success": True,
            "raw_simulation_output": "ok",
            "final_status_message": "Simulation passed.",
        }
    except Exception as exc:
        return {
            "success": False,
            "raw_simulation_output": str(exc),
            "error_message": str(exc),
            "final_status_message": "sim_failed",
        }


@app.post("/api/simulate-protocol")
def simulate_protocol(request: SimulateRequest) -> dict[str, Any]:
    return simulate_protocol_code(request.protocol_code)


def analyze_protocol_code(code: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        proto = Path(tmp) / "protocol.py"
        out = Path(tmp) / "analyze.json"
        proto.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "opentrons.cli",
                "analyze",
                str(proto),
                "--json-output",
                str(out),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        if not out.is_file():
            return {
                "commands": [],
                "errors": [result.stderr.strip() or result.stdout.strip() or "analyze produced no JSON"],
            }
        payload = json.loads(out.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {"commands": [], "errors": ["analyze JSON was not an object"]}
        return payload


def _job_snapshot(job: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": job["id"], "status": job["status"]}
    if "result" in job:
        payload["result"] = job["result"]
    if "error" in job:
        payload["error"] = job["error"]
    return payload


def start_analyze_job(code: str) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    job: dict[str, Any] = {"id": job_id, "status": "queued"}
    with _ANALYZE_LOCK:
        _ANALYZE_JOBS[job_id] = job

    def run() -> None:
        with _ANALYZE_LOCK:
            current = _ANALYZE_JOBS.get(job_id)
            if current is not None:
                current["status"] = "running"
        try:
            result = analyze_protocol_code(code)
            with _ANALYZE_LOCK:
                stored = _ANALYZE_JOBS.get(job_id)
                if stored is None:
                    return
                stored["status"] = "succeeded"
                stored["result"] = result
        except Exception as exc:  # noqa: BLE001 — job status, not a crash
            with _ANALYZE_LOCK:
                stored = _ANALYZE_JOBS.get(job_id)
                if stored is None:
                    return
                stored["status"] = "failed"
                stored["error"] = str(exc)

    queued = _job_snapshot(job)
    _ANALYZE_POOL.submit(run)
    return queued


def get_analyze_job(job_id: str) -> dict[str, Any] | None:
    with _ANALYZE_LOCK:
        job = _ANALYZE_JOBS.get(job_id)
        return _job_snapshot(job) if job else None


@app.post("/api/visualizer/analyze")
async def visualizer_analyze(protocol: UploadFile = File(...)) -> JSONResponse:
    raw = await protocol.read()
    code = raw.decode("utf-8", errors="replace")
    return JSONResponse(analyze_protocol_code(code))


@app.post("/api/visualizer/analyze/start")
async def visualizer_analyze_start(protocol: UploadFile = File(...)) -> dict[str, Any]:
    raw = await protocol.read()
    code = raw.decode("utf-8", errors="replace")
    return start_analyze_job(code)


@app.get("/jobs/{job_id}")
@app.get("/api/visualizer/jobs/{job_id}")
def visualizer_job(job_id: str) -> dict[str, Any]:
    job = get_analyze_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown_job")
    return job


class PlrVisualizerRequest(BaseModel):
    plan: dict[str, Any]
    robot: str = ""


@app.post("/api/plr/visualizer/start")
def plr_visualizer_start(request: PlrVisualizerRequest) -> dict[str, Any]:
    from plr_visualizer import start_plr_visualizer

    return start_plr_visualizer(request.plan, request.robot)


@app.post("/api/plr/visualizer/stop")
def plr_visualizer_stop() -> dict[str, Any]:
    from plr_visualizer import stop_plr_visualizer

    return stop_plr_visualizer()


@app.get("/api/plr/visualizer/status")
def plr_visualizer_status() -> dict[str, Any]:
    from plr_visualizer import plr_visualizer_status as status

    return status()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()

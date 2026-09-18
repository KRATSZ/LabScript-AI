"""FastAPI application for protocol upload and analysis."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from protocol_visualizer_web.analyze_job import sync_analyze_from_uploads
from protocol_visualizer_web.jobs import get_job, job_to_response, start_job

# Local dev: explicit origins instead of *. Production: set PV_CORS_ORIGINS to your frontend URL(s).
_DEFAULT_CORS = "http://127.0.0.1:5177,http://localhost:5177"

app = FastAPI(title="Protocol Visualizer API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.environ.get("PV_CORS_ORIGINS", _DEFAULT_CORS).split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


async def _read_named_files(files: list[UploadFile] | None) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    if not files:
        return out
    for f in files:
        if f.filename:
            out.append((f.filename, await f.read()))
    return out


def _run_sync_analyze(
    protocol_filename: str,
    protocol_content: bytes,
    labware_files: list[tuple[str, bytes]],
    rtp_csv_files: list[tuple[str, bytes]],
    rtp_values: str | None,
    rtp_files_map: str | None,
    check: bool,
) -> dict[str, Any]:
    try:
        return sync_analyze_from_uploads(
            protocol_filename,
            protocol_content,
            labware_files,
            rtp_csv_files,
            rtp_values,
            rtp_files_map,
            check,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=504, detail="Analysis timed out") from e


@app.post("/api/analyze")
async def analyze_protocol(
    protocol: Annotated[UploadFile, File(description="Main protocol .py or .json file")],
    labware: list[UploadFile] | None = File(None),
    rtp_csv: list[UploadFile] | None = File(None),
    rtp_values: Annotated[str | None, Form()] = None,
    rtp_files_map: Annotated[str | None, Form()] = None,
    check: Annotated[bool, Form()] = False,
) -> JSONResponse:
    """
    Synchronous analyze (may hit proxy timeouts on large protocols).
    Prefer POST /api/analyze/start + polling for long runs.
    """
    if protocol.filename is None:
        raise HTTPException(status_code=400, detail="Missing filename on protocol upload")

    content = await protocol.read()
    labware_files = await _read_named_files(labware)
    rtp_csv_files = await _read_named_files(rtp_csv)

    result = await asyncio.to_thread(
        _run_sync_analyze,
        protocol.filename,
        content,
        labware_files,
        rtp_csv_files,
        rtp_values,
        rtp_files_map,
        check,
    )
    return JSONResponse(content=result)


@app.post("/api/analyze/start")
async def analyze_protocol_start(
    protocol: Annotated[UploadFile, File(description="Main protocol .py or .json file")],
    labware: list[UploadFile] | None = File(None),
    rtp_csv: list[UploadFile] | None = File(None),
    rtp_values: Annotated[str | None, Form()] = None,
    rtp_files_map: Annotated[str | None, Form()] = None,
    check: Annotated[bool, Form()] = False,
) -> dict[str, str]:
    """Enqueue analysis; poll GET /api/analyze/jobs/{job_id} until completed or failed."""
    if protocol.filename is None:
        raise HTTPException(status_code=400, detail="Missing filename on protocol upload")

    content = await protocol.read()
    labware_files = await _read_named_files(labware)
    rtp_csv_files = await _read_named_files(rtp_csv)

    # Fail fast on obvious JSON mistakes (same validation as worker).
    if rtp_values and rtp_values.strip():
        try:
            v = json.loads(rtp_values)
            if not isinstance(v, dict):
                raise ValueError("rtp_values must be a JSON object")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON for rtp_values: {e}"
            ) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    if rtp_files_map and rtp_files_map.strip():
        try:
            v = json.loads(rtp_files_map)
            if not isinstance(v, dict):
                raise ValueError("rtp_files_map must be a JSON object")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON for rtp_files_map: {e}"
            ) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    if rtp_csv_files and not (rtp_files_map and rtp_files_map.strip()):
        raise HTTPException(
            status_code=400,
            detail="rtp_files_map is required when uploading RTP CSV files "
            '(e.g. {"liquids": "liquids.csv"} matching the uploaded file name)',
        )

    fname = protocol.filename

    async def _work() -> dict[str, Any]:
        return await asyncio.to_thread(
            sync_analyze_from_uploads,
            fname,
            content,
            labware_files,
            rtp_csv_files,
            rtp_values,
            rtp_files_map,
            check,
        )

    job_id = await start_job(lambda: _work())
    return {"job_id": job_id}


@app.get("/api/analyze/jobs/{job_id}")
async def analyze_job_status(job_id: str) -> JSONResponse:
    rec = get_job(job_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return JSONResponse(content=job_to_response(rec))

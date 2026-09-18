"""In-memory async analysis jobs (local / single-process)."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from collections.abc import Callable, Coroutine
from typing import Any

MAX_JOBS = 200


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobRecord:
    status: JobStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    created: float = field(default_factory=time.monotonic)


_jobs: dict[str, JobRecord] = {}
_lock = asyncio.Lock()


def _evict_oldest() -> None:
    if len(_jobs) <= MAX_JOBS:
        return
    # Drop oldest ~half of overflow
    overflow = len(_jobs) - MAX_JOBS + 50
    ordered = sorted(_jobs.items(), key=lambda kv: kv[1].created)
    for job_id, _ in ordered[:overflow]:
        _jobs.pop(job_id, None)


async def start_job(
    get_coro: Callable[[], Coroutine[Any, Any, dict[str, Any]]],
) -> str:
    job_id = str(uuid.uuid4())
    async with _lock:
        _evict_oldest()
        _jobs[job_id] = JobRecord(status=JobStatus.PENDING)

    async def _runner() -> None:
        async with _lock:
            rec = _jobs.get(job_id)
            if rec is None:
                return
            rec.status = JobStatus.RUNNING
        try:
            result = await get_coro()
        except Exception as e:
            async with _lock:
                rec = _jobs.get(job_id)
                if rec is not None:
                    rec.status = JobStatus.FAILED
                    rec.error = str(e)
            return
        async with _lock:
            rec = _jobs.get(job_id)
            if rec is not None:
                rec.status = JobStatus.COMPLETED
                rec.result = result

    asyncio.create_task(_runner())
    return job_id


def get_job(job_id: str) -> JobRecord | None:
    return _jobs.get(job_id)


def job_to_response(rec: JobRecord) -> dict[str, Any]:
    body: dict[str, Any] = {"status": rec.status.value}
    if rec.status == JobStatus.COMPLETED and rec.result is not None:
        body["result"] = rec.result
    if rec.status == JobStatus.FAILED and rec.error is not None:
        body["error"] = rec.error
    return body

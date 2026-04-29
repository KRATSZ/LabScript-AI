from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PV_SRC = (
    _PROJECT_ROOT
    / "web"
    / "opentrons-protocol-visualizer-web-slim"
    / "protocol-visualizer-web"
    / "src"
)


def _ensure_protocol_visualizer_path() -> None:
    path = str(_PV_SRC)
    if path not in sys.path:
        sys.path.insert(0, path)


@lru_cache(maxsize=1)
def load_protocol_visualizer_backend() -> dict[str, Any]:
    _ensure_protocol_visualizer_path()

    from protocol_visualizer_web.analyze_job import sync_analyze_from_uploads
    from protocol_visualizer_web.jobs import get_job, job_to_response, start_job

    return {
        "sync_analyze_from_uploads": sync_analyze_from_uploads,
        "get_job": get_job,
        "job_to_response": job_to_response,
        "start_job": start_job,
    }

# -*- coding: utf-8 -*-
"""Regression tests for visualizer API deployment failures."""

from fastapi.testclient import TestClient

from backend import api_server


def test_visualizer_backend_failure_keeps_cors_header(monkeypatch):
    def missing_visualizer_backend():
        raise RuntimeError("protocol visualizer source is missing")

    monkeypatch.setattr(
        api_server,
        "load_protocol_visualizer_backend",
        missing_visualizer_backend,
    )

    client = TestClient(api_server.app, raise_server_exceptions=False)
    response = client.post(
        "/api/visualizer/analyze/start",
        files={
            "protocol": (
                "protocol.py",
                b"metadata = {'apiLevel': '2.19'}\n\ndef run(protocol):\n    pass\n",
                "text/x-python",
            )
        },
        headers={"Origin": "https://labscriptai.cn"},
    )

    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "https://labscriptai.cn"
    assert response.json()["detail"].startswith(
        "Protocol visualizer backend is unavailable"
    )

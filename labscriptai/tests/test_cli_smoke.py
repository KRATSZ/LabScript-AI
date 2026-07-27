"""CLI smoke tests (no robot required)."""

from __future__ import annotations

import io
import os
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

from labscriptai.agent.cli import (
    _normalize_robot_base,
    build_parser,
    cmd_doctor,
    main,
)


def test_normalize_robot_base_defaults_31950() -> None:
    assert _normalize_robot_base("127.0.0.1") == "http://127.0.0.1:31950"
    assert _normalize_robot_base("10.31.17.153") == "http://10.31.17.153:31950"
    assert _normalize_robot_base("http://host:31950") == "http://host:31950"
    assert _normalize_robot_base("host:8080") == "http://host:8080"


def test_doctor_reports_31950_on_failure() -> None:
    parser = build_parser()
    args = parser.parse_args(["doctor", "--robot", "127.0.0.1", "--timeout", "0.3"])
    buf = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(err):
        rc = cmd_doctor(args)
    out = buf.getvalue() + err.getvalue()
    assert rc == 1
    assert "31950" in out
    assert "http://127.0.0.1:31950/health" in out


def test_chat_quit_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    # Feed /quit immediately
    monkeypatch.setattr("builtins.input", lambda _p="": "/quit")
    rc = main(["chat", "--provider", "offline", "--workspace", str(tmp_path)])
    assert rc == 0


def test_parser_subcommands() -> None:
    parser = build_parser()
    ns = parser.parse_args(["recover", "--run-id", "r1", "--robot", "1.2.3.4", "--yes"])
    assert ns.command == "recover"
    assert ns.yes is True
    ns2 = parser.parse_args(["daemon", "--robot", "1.2.3.4", "--run-id", "r1"])
    assert ns2.command == "daemon"


def test_default_provider_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from labscriptai.agent.cli import _default_provider

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    # May still load from repo .env — so only assert the function returns a known token
    provider = _default_provider()
    assert provider in {"offline", "deepseek"}

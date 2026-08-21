"""CLI smoke tests (no robot required)."""

from __future__ import annotations

import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

from labscriptai.agent.cli import (
    NPM_INSTALL_HINT,
    _normalize_robot_base,
    _parse_node_major,
    build_parser,
    check_deepseek_key,
    check_index_js,
    check_node,
    check_node_modules,
    check_opentrons,
    cmd_doctor,
    collect_doctor_checks,
    format_doctor_report,
    main,
)


def test_normalize_robot_base_defaults_31950() -> None:
    assert _normalize_robot_base("127.0.0.1") == "http://127.0.0.1:31950"
    assert _normalize_robot_base("10.31.17.153") == "http://10.31.17.153:31950"
    assert _normalize_robot_base("http://host:31950") == "http://host:31950"
    assert _normalize_robot_base("host:8080") == "http://host:8080"


def test_parse_node_major() -> None:
    assert _parse_node_major("v18.20.4") == 18
    assert _parse_node_major("v20.11.0") == 20
    assert _parse_node_major("16.0.0") == 16
    assert _parse_node_major("not-a-version") is None


def test_check_node_missing() -> None:
    status, detail = check_node(which=lambda _name: None)
    assert status == "FAIL"
    assert "not found" in detail


def test_check_node_too_old() -> None:
    class _Done:
        stdout = "v16.20.2\n"
        stderr = ""

    status, detail = check_node(which=lambda _name: "/usr/bin/node", run=lambda *_a, **_k: _Done())
    assert status == "FAIL"
    assert "16" in detail


def test_check_node_ok() -> None:
    class _Done:
        stdout = "v22.14.0\n"
        stderr = ""

    status, detail = check_node(which=lambda _name: "/usr/bin/node", run=lambda *_a, **_k: _Done())
    assert status == "OK"
    assert "v22.14.0" in detail


def test_check_node_modules_and_index(tmp_path: Path) -> None:
    assert check_node_modules(tmp_path)[0] == "FAIL"
    (tmp_path / "node_modules").mkdir()
    assert check_node_modules(tmp_path)[0] == "OK"
    assert check_index_js(tmp_path)[0] == "FAIL"
    (tmp_path / "index.js").write_text("// backend\n", encoding="utf-8")
    assert check_index_js(tmp_path)[0] == "OK"


def test_check_deepseek_key_present_absent() -> None:
    status, detail = check_deepseek_key({"DEEPSEEK_API_KEY": "sk-secret-do-not-print"})
    assert status == "OK"
    assert "sk-secret-do-not-print" not in detail
    assert "set" in detail
    status, detail = check_deepseek_key({})
    assert status == "WARN"
    assert "absent" in detail


def test_check_opentrons_missing_message() -> None:
    def _boom(_name: str) -> None:
        raise ModuleNotFoundError(_name)

    status, detail = check_opentrons(import_module=_boom, run_helper=False)
    assert status == "WARN"
    assert "SimPass/LogicPass unavailable" in detail
    assert "Node+npm" in detail


def test_collect_doctor_skips_robot_without_ip(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "index.js").write_text("x", encoding="utf-8")
    rows = collect_doctor_checks(
        robot=None,
        mcp_dir=tmp_path,
        environ={},
        check_node_fn=lambda: ("OK", "v22.0.0 (>= 18)"),
        check_opentrons_fn=lambda: ("WARN", "SimPass/LogicPass unavailable"),
        check_robot_fn=lambda _robot, timeout=2.0: ("SKIP", "pass --robot IP"),
    )
    by_name = {name: (status, detail) for status, name, detail in rows}
    assert by_name["robot"][0] == "SKIP"
    assert by_name["node"][0] == "OK"
    assert by_name["DEEPSEEK_API_KEY"][0] == "WARN"
    report = format_doctor_report(rows)
    assert "npm install" not in report
    assert "labscriptai chat" in report
    assert "FAIL: pass --robot IP (or set ROBOT_IP)" not in report


def test_format_doctor_report_prints_npm_install() -> None:
    report = format_doctor_report(
        [
            ("FAIL", "node", "node not found on PATH (need Node >= 18)"),
            ("FAIL", "node_modules", "missing /tmp/node_modules"),
            ("OK", "index.js", "/tmp/index.js"),
            ("WARN", "DEEPSEEK_API_KEY", "absent"),
            ("WARN", "opentrons", "SimPass/LogicPass unavailable until opentrons is installed"),
            ("SKIP", "robot", "pass --robot IP to probe http://IP:31950/health"),
        ]
    )
    assert NPM_INSTALL_HINT in report
    assert "cd labscriptai/plugins/mcp/opentrons-mcp && npm install" in report
    assert "FAIL: node, node_modules" in report


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


def test_doctor_without_robot_prints_toolchain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROBOT_IP", raising=False)
    monkeypatch.delenv("LABSCRIPTAI_ROBOT_IP", raising=False)
    parser = build_parser()
    args = parser.parse_args(["doctor", "--timeout", "0.3"])
    buf = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(err):
        rc = cmd_doctor(args)
    out = buf.getvalue() + err.getvalue()
    assert rc != 2
    assert "node" in out.lower()
    assert "DEEPSEEK_API_KEY" in out
    assert "index.js" in out
    assert "pass --robot" in out or "SKIP" in out
    assert "FAIL: pass --robot IP" not in out
    assert "npm install" in out or "node_modules" in out


def test_doctor_missing_node_prints_npm_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ROBOT_IP", raising=False)
    monkeypatch.delenv("LABSCRIPTAI_ROBOT_IP", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr("labscriptai.agent.cli._load_dotenv_for_doctor", lambda: None)
    monkeypatch.setattr(
        "labscriptai.agent.cli.check_node",
        lambda **_k: ("FAIL", "node not found on PATH (need Node >= 18)"),
    )
    monkeypatch.setattr("labscriptai.agent.cli._vendored_mcp_dir", lambda: tmp_path)
    monkeypatch.setattr(
        "labscriptai.agent.cli.check_opentrons",
        lambda **_k: (
            "WARN",
            "SimPass/LogicPass unavailable until opentrons is installed in this interpreter; "
            "chat robot backend still needs Node+npm",
        ),
    )
    parser = build_parser()
    args = parser.parse_args(["doctor"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_doctor(args)
    out = buf.getvalue()
    assert rc == 1
    assert NPM_INSTALL_HINT in out


def test_doctor_does_not_print_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "sk-super-secret-doctor-key"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    monkeypatch.delenv("ROBOT_IP", raising=False)
    monkeypatch.delenv("LABSCRIPTAI_ROBOT_IP", raising=False)
    monkeypatch.setattr("labscriptai.agent.cli._load_dotenv_for_doctor", lambda: None)
    monkeypatch.setattr(
        "labscriptai.agent.cli.check_node", lambda **_k: ("OK", "v22.0.0 (>= 18)")
    )
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "index.js").write_text("x", encoding="utf-8")
    monkeypatch.setattr("labscriptai.agent.cli._vendored_mcp_dir", lambda: tmp_path)
    monkeypatch.setattr(
        "labscriptai.agent.cli.check_opentrons",
        lambda **_k: ("WARN", "SimPass/LogicPass unavailable"),
    )
    parser = build_parser()
    args = parser.parse_args(["doctor"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_doctor(args)
    out = buf.getvalue()
    assert secret not in out
    assert "DEEPSEEK_API_KEY" in out
    assert "set" in out
    assert rc == 0


def test_doctor_help_mentions_toolchain() -> None:
    parser = build_parser()
    doctor = None
    for action in parser._subparsers._group_actions:  # type: ignore[attr-defined]
        doctor = action.choices.get("doctor")  # type: ignore[union-attr]
        if doctor is not None:
            break
    assert doctor is not None
    text = doctor.format_help()
    assert "health check" in text.lower() or "Node" in text or "toolchain" in text.lower()
    assert "--robot" in text


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


def test_default_provider_is_deepseek() -> None:
    from labscriptai.agent.cli import _default_provider

    assert _default_provider() == "deepseek"


def test_chat_missing_api_key_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from labscriptai.agent import llm as llm_mod

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(llm_mod, "_load_package_dotenv", lambda: None)
    err = io.StringIO()
    with redirect_stderr(err):
        rc = main(["chat", "--workspace", str(tmp_path)])
    assert rc != 0
    assert "DEEPSEEK_API_KEY" in err.getvalue()

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "eval_logicpass.py"
PYTHONPATH = str(ROOT)


def run_cli(payload: dict, extra_env: dict[str, str] | None = None) -> dict:
    env = {**os.environ, "PYTHONPATH": PYTHONPATH}
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


class EvalLogicpassTests(unittest.TestCase):
    def test_missing_analyze_is_unevaluable(self) -> None:
        out = run_cli({})
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(out["logic_pass"])
        self.assertFalse(out["final_pass_v2"])

    def test_invalid_json_exits_zero(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not-json",
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONPATH": PYTHONPATH},
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        out = json.loads(completed.stdout)
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(out["logic_pass"])
        self.assertFalse(out["final_pass_v2"])

    def test_import_failure_is_unevaluable(self) -> None:
        out = run_cli({}, extra_env={"PYTHONPATH": "/tmp/webdemo-empty-path"})
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(out["logic_pass"])
        self.assertFalse(out["final_pass_v2"])
        self.assertEqual(out.get("reason"), "logicpass_package_missing")

    def test_fab_projection_never_true_on_unevaluable(self) -> None:
        out = run_cli({})
        lit = (
            bool(out.get("sim_pass"))
            and out.get("outcome") == "pass"
            and out.get("logic_pass") is True
        )
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(lit)

    def test_package_import_works_from_repo_root(self) -> None:
        sys.path.insert(0, PYTHONPATH)
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json

        adapter = load_analyze_json(payload={"commands": []}, protocol_path=None)
        result = evaluate_logicpass(sim_pass=True, adapter=adapter)
        payload = result.to_dict()
        self.assertIn(payload["outcome"], {"pass", "fail", "unevaluable"})
        if payload["outcome"] != "pass":
            self.assertFalse(payload["logic_pass"])


if __name__ == "__main__":
    unittest.main()

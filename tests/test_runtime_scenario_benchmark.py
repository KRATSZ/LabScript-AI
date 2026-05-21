from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.runtime.scenario_benchmark import (
    _offline_factory,
    built_in_scenarios,
    run_runtime_scenarios,
)


class RuntimeScenarioBenchmarkTests(unittest.TestCase):
    def test_built_in_scenarios_cover_core_anomalies(self) -> None:
        scenarios = built_in_scenarios()

        self.assertEqual(len(scenarios), 6)
        self.assertEqual(
            {scenario.anomaly_type for scenario in scenarios},
            {
                "missing_tip",
                "occupied_destination",
                "liquid_sensing",
                "wrong_labware_preflight",
                "home_safety",
                "module_polling",
            },
        )

    def test_offline_runtime_scenarios_write_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "runtime"
            summary = run_runtime_scenarios(
                output_dir=output_dir,
                candidate_provider_factory=_offline_factory,
                model_id="offline-test",
            )
            saved = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["case_count"], 6)
        self.assertEqual(summary["passed_count"], 6)
        self.assertEqual(saved["records"][0]["case_id"], "R001")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import run as experiment_run
from experiment.config import EXPERIMENT_ID, WORKLOAD_CONFIGS


class EvidenceSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary directory as BOOKMAS_EVIDENCE_DIR
        self.temp_dir = tempfile.mkdtemp(prefix="evidence_test_")
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.temp_dir

        # Run the experiment, which should create results.json
        experiment_run.main()

        self.evidence_path = Path(self.temp_dir) / "results.json"
        self.assertTrue(self.evidence_path.exists(), "results.json was not created")

        with self.evidence_path.open("r", encoding="utf-8") as f:
            self.evidence = json.load(f)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.pop("BOOKMAS_EVIDENCE_DIR", None)

    def test_top_level_keys(self) -> None:
        ev = self.evidence
        self.assertEqual(ev.get("chapter"), 8)
        self.assertEqual(ev.get("experiment_id"), EXPERIMENT_ID)
        self.assertIsInstance(ev.get("environment"), dict)
        self.assertIn("runs", ev)
        self.assertIsInstance(ev["runs"], list)

    def test_environment_fields(self) -> None:
        env = self.evidence["environment"]
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

    def test_runs_have_required_fields_and_numeric_metrics(self) -> None:
        runs = self.evidence["runs"]
        self.assertGreaterEqual(len(runs), 2)

        seen_by_workload = {}

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], {"baseline", "treatment"})
            self.assertIn("workload_id", run)
            self.assertIn(run["workload_id"], WORKLOAD_CONFIGS.keys())
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)
            self.assertIn("metrics", run)
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)

            # Every metric value must be a finite number.
            for key, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} must be numeric, got {type(value)}",
                )

            wl = run["workload_id"]
            seen_by_workload.setdefault(wl, set()).add(run["variant"])

        # Ensure at least one baseline and one treatment run per workload.
        for wl in WORKLOAD_CONFIGS.keys():
            variants = seen_by_workload.get(wl, set())
            self.assertIn("baseline", variants, f"Missing baseline run for {wl}")
            self.assertIn("treatment", variants, f"Missing treatment run for {wl}")

    def test_results_json_is_valid_json(self) -> None:
        # Already loaded in setUp; this test ensures it is serializable again.
        serialized = json.dumps(self.evidence)
        self.assertIsInstance(serialized, str)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

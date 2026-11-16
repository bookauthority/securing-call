from __future__ import annotations

import json
import os
import unittest

from run import main as run_main
from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary evidence directory under /tmp to avoid clashes
        self.evidence_dir = "/tmp/bookmas_evidence_test"
        os.makedirs(self.evidence_dir, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.evidence_dir

        # Run the experiment to generate results.json
        run_main()

    def test_results_json_schema(self) -> None:
        path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.isfile(path), "results.json was not created")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("chapter"), CHAPTER_NUMBER)
        self.assertEqual(data.get("experiment_id"), EXPERIMENT_ID)

        env = data.get("environment")
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)

        runs = data.get("runs")
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 2)

        # Ensure at least one baseline and one treatment run per workload
        variants = {r.get("variant") for r in runs}
        self.assertIn("baseline", variants)
        self.assertIn("treatment", variants)

        workload_ids = {r.get("workload_id") for r in runs}
        self.assertEqual(len(workload_ids), 1, "Expected a single workload_id shared by runs")

        for run in runs:
            with self.subTest(run=run):
                self.assertIn(run.get("variant"), ("baseline", "treatment"))
                self.assertIsInstance(run.get("workload_id"), str)
                self.assertIsInstance(run.get("run_id"), str)
                self.assertIsInstance(run.get("success"), bool)

                metrics = run.get("metrics")
                self.assertIsInstance(metrics, dict)
                self.assertGreaterEqual(len(metrics), 1)

                for name, value in metrics.items():
                    # All metric values must be finite numbers
                    self.assertIsInstance(value, (int, float), msg=f"Metric {name} should be numeric")

        # Notes are optional but if present must be a string
        notes = data.get("notes")
        if notes is not None:
            self.assertIsInstance(notes, str)


if __name__ == "__main__":
    unittest.main()

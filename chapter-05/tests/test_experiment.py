import json
import os
import tempfile
import unittest
from typing import Any, Dict, List

import run as run_module
from experiment.experiment import WORKLOAD_IDS


class EvidenceSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        # Run the experiment into a temporary evidence directory
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.tmpdir.name
        run_module.main()
        self.evidence_path = os.path.join(self.tmpdir.name, "results.json")

    def tearDown(self) -> None:
        # Clean up temp directory
        self.tmpdir.cleanup()
        if "BOOKMAS_EVIDENCE_DIR" in os.environ:
            del os.environ["BOOKMAS_EVIDENCE_DIR"]

    def _load_evidence(self) -> Dict[str, Any]:
        self.assertTrue(os.path.isfile(self.evidence_path), "Evidence file not found")
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_top_level_schema(self) -> None:
        evidence = self._load_evidence()
        self.assertIn("chapter", evidence)
        self.assertIsInstance(evidence["chapter"], int)
        self.assertIn("experiment_id", evidence)
        self.assertIsInstance(evidence["experiment_id"], str)
        self.assertEqual(evidence["chapter"], 5)
        self.assertEqual(evidence["experiment_id"], "exp-ch5-baseline-synth-voice-det-v1")

        self.assertIn("environment", evidence)
        self.assertIsInstance(evidence["environment"], dict)
        env = evidence["environment"]
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

        self.assertIn("runs", evidence)
        self.assertIsInstance(evidence["runs"], list)

    def test_runs_schema_and_metrics(self) -> None:
        evidence = self._load_evidence()
        runs: List[Dict[str, Any]] = evidence["runs"]
        self.assertGreaterEqual(len(runs), 2)

        # Track variants per workload to ensure baseline and treatment exist
        workload_variants: Dict[str, set] = {wid: set() for wid in WORKLOAD_IDS}

        for run in runs:
            # Required fields
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            self.assertIn(run["workload_id"], WORKLOAD_IDS)
            self.assertIn(run["variant"], {"baseline", "treatment"})
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)

            workload_variants[run["workload_id"]].add(run["variant"])

            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            # At least one metric per run
            self.assertGreaterEqual(len(metrics), 1)
            for name, value in metrics.items():
                # Metric values must be finite JSON numbers
                self.assertIsInstance(value, (int, float), msg=f"Metric {name} is not numeric")

        # Ensure at least one baseline and one treatment run per workload
        for wid in WORKLOAD_IDS:
            self.assertIn("baseline", workload_variants[wid], msg=f"Missing baseline for {wid}")
            self.assertIn("treatment", workload_variants[wid], msg=f"Missing treatment for {wid}")


if __name__ == "__main__":
    unittest.main()

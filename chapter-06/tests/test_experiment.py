import json
import os
import tempfile
import unittest


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _run_experiment(self) -> str:
        evidence_dir = self.tmpdir.name
        os.environ["BOOKMAS_EVIDENCE_DIR"] = evidence_dir
        # Importing run.py and calling main directly (no subprocess).
        import importlib

        run_module = importlib.import_module("run")
        importlib.reload(run_module)
        run_module.main()
        return os.path.join(evidence_dir, "results.json")

    def test_evidence_file_schema(self) -> None:
        evidence_path = self._run_experiment()
        self.assertTrue(os.path.exists(evidence_path), "results.json should exist")

        with open(evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertEqual(data["chapter"], 6)
        self.assertEqual(data["experiment_id"], "chap6-beyond-baseline-detectors-ensembles-v1")

        # Environment
        env = data["environment"]
        self.assertIsInstance(env.get("os", ""), str)
        self.assertIsInstance(env.get("python", ""), str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        # Track workloads and variants to ensure coverage.
        workload_variant = {}

        for run in runs:
            # Required per-run fields
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            variant = run["variant"]
            workload_id = run["workload_id"]
            run_id = run["run_id"]
            success = run["success"]
            metrics = run["metrics"]

            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIsInstance(workload_id, str)
            self.assertIsInstance(run_id, str)
            self.assertIsInstance(success, bool)
            self.assertIsInstance(metrics, dict)
            self.assertGreater(len(metrics), 0)

            # Ensure metrics are numeric
            for k, v in metrics.items():
                self.assertIsInstance(
                    v, (int, float), f"Metric {k} must be numeric, got {type(v)}"
                )

            workload_variant.setdefault(workload_id, set()).add(variant)

        # Ensure each workload has at least one baseline and one treatment run.
        required_workloads = [
            "WL1_base_domain_eval",
            "WL2_new_language_eval",
            "WL3_new_channel_eval",
            "WL4_adversarial_tools_eval",
            "WL5_cost_latency_benchmark",
        ]
        for wid in required_workloads:
            self.assertIn(wid, workload_variant, f"Missing runs for workload {wid}")
            variants = workload_variant[wid]
            self.assertIn("baseline", variants, f"Missing baseline for {wid}")
            self.assertIn("treatment", variants, f"Missing treatment for {wid}")


if __name__ == "__main__":
    unittest.main()

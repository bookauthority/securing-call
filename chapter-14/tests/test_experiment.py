import json
import os
import tempfile
import unittest


class TestExperimentRun(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure we run the real experiment into a temp evidence dir
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.tmpdir.name

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_run_produces_valid_evidence(self) -> None:
        import run as experiment_run

        # Execute main to produce evidence
        experiment_run.main()

        evidence_path = os.path.join(self.tmpdir.name, "results.json")
        self.assertTrue(os.path.exists(evidence_path), "results.json not created")

        with open(evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertEqual(data.get("chapter"), 14)
        self.assertEqual(
            data.get("experiment_id"), "exp-14-stress-redteam-adversarial-eval-v1"
        )
        self.assertIn("environment", data)
        self.assertIn("runs", data)
        self.assertIsInstance(data["runs"], list)

        # Environment substructure
        env = data["environment"]
        self.assertIsInstance(env.get("os"), str)
        self.assertIsInstance(env.get("python"), str)

        # Check per-workload baseline and treatment presence
        workloads = {"wl-01", "wl-02", "wl-03", "wl-04"}
        seen = {(r["variant"], r["workload_id"]) for r in data["runs"]}
        for wid in workloads:
            self.assertIn(("baseline", wid), seen)
            self.assertIn(("treatment", wid), seen)

        # Schema for each run
        for run in data["runs"]:
            self.assertIn(run["variant"], ("baseline", "treatment"))
            self.assertIn(run["workload_id"], workloads)
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)
            self.assertIn("metrics", run)
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            # All metric values must be numbers (int or float)
            for key, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} has non-numeric value {value!r}",
                )

        # Ensure at least one shared metric name across runs for comparability
        metric_name_sets = [set(r["metrics"].keys()) for r in data["runs"]]
        shared = set.intersection(*metric_name_sets)
        self.assertTrue(
            len(shared) >= 1,
            "Expected at least one shared metric key across all runs",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

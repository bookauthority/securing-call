import json
import unittest
from pathlib import Path

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID, WL1_ID, WL2_ID
from experiment.simulation import run_experiment_simulation
from experiment.evidence import build_evidence_document, write_evidence


class TestExperimentRuntimeContract(unittest.TestCase):
    def test_simulation_and_evidence_schema(self):
        # Run a full simulation
        sim_result = run_experiment_simulation()

        # Basic structure checks
        self.assertIn((WL1_ID, "baseline"), sim_result.aggregated_metrics)
        self.assertIn((WL1_ID, "treatment"), sim_result.aggregated_metrics)
        self.assertIn((WL2_ID, "baseline"), sim_result.aggregated_metrics)
        self.assertIn((WL2_ID, "treatment"), sim_result.aggregated_metrics)

        # Build evidence document
        env_info = {"os": "test-os", "python": "3.11.0"}
        evidence = build_evidence_document(
            chapter=CHAPTER_NUMBER,
            experiment_id=EXPERIMENT_ID,
            simulation_result=sim_result,
            environment_info=env_info,
        )

        # Top-level schema checks
        self.assertIsInstance(evidence, dict)
        self.assertEqual(evidence["chapter"], CHAPTER_NUMBER)
        self.assertEqual(evidence["experiment_id"], EXPERIMENT_ID)

        self.assertIn("environment", evidence)
        self.assertIsInstance(evidence["environment"], dict)
        self.assertIn("os", evidence["environment"])
        self.assertIn("python", evidence["environment"])

        self.assertIn("runs", evidence)
        self.assertIsInstance(evidence["runs"], list)
        self.assertGreaterEqual(len(evidence["runs"]), 4)  # 2 workloads x 2 arms

        # Ensure at least one baseline and one treatment run per workload
        seen = {
            (WL1_ID, "baseline"): False,
            (WL1_ID, "treatment"): False,
            (WL2_ID, "baseline"): False,
            (WL2_ID, "treatment"): False,
        }

        for run in evidence["runs"]:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], ("baseline", "treatment"))

            self.assertIn("workload_id", run)
            self.assertIn(run["workload_id"], (WL1_ID, WL2_ID))

            key = (run["workload_id"], run["variant"])
            seen[key] = True

            self.assertIn("run_id", run)
            self.assertIsInstance(run["run_id"], str)

            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)

            self.assertIn("metrics", run)
            self.assertIsInstance(run["metrics"], dict)

            # All metric values must be finite numbers (no strings, dicts, etc.)
            for mname, mval in run["metrics"].items():
                self.assertIsInstance(
                    mval,
                    (int, float),
                    msg=f"Metric {mname} must be numeric, got {type(mval)}",
                )

        for key, present in seen.items():
            self.assertTrue(present, msg=f"Missing run for {key}")

    def test_write_evidence_to_filesystem(self):
        sim_result = run_experiment_simulation()
        env_info = {"os": "test-os", "python": "3.11.0"}
        evidence = build_evidence_document(
            chapter=CHAPTER_NUMBER,
            experiment_id=EXPERIMENT_ID,
            simulation_result=sim_result,
            environment_info=env_info,
        )

        tmp_dir = Path("/tmp") / "bookmas_ch12_test"
        if not tmp_dir.exists():
            tmp_dir.mkdir(parents=True, exist_ok=True)

        write_evidence(evidence, tmp_dir)

        out_path = tmp_dir / "results.json"
        self.assertTrue(out_path.exists(), "results.json not written")

        with out_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)

        # Confirm loaded evidence has same basic shape
        self.assertEqual(loaded["chapter"], CHAPTER_NUMBER)
        self.assertEqual(loaded["experiment_id"], EXPERIMENT_ID)
        self.assertIn("runs", loaded)
        self.assertIsInstance(loaded["runs"], list)

        # Ensure metrics are numeric after roundtrip
        for run in loaded["runs"]:
            self.assertIsInstance(run.get("metrics", {}), dict)
            for mname, mval in run.get("metrics", {}).items():
                self.assertIsInstance(
                    mval,
                    (int, float),
                    msg=f"Metric {mname} must remain numeric after serialization",
                )


if __name__ == "__main__":
    unittest.main()

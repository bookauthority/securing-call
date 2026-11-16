import json
import os
import platform
import uuid
from typing import Dict, Any, List

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID, WORKLOAD_IDS
from experiment.harness import run_workload


def main() -> None:
    # Determine evidence directory from environment variable; fall back to /evidence
    # which matches the sandbox's writable location contract.
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR") or "/evidence"
    try:
        os.makedirs(evidence_dir, exist_ok=True)
    except PermissionError:
        # As a final fallback, use current directory if /evidence is not writable.
        evidence_dir = "."
        os.makedirs(evidence_dir, exist_ok=True)

    evidence_path = os.path.join(evidence_dir, "results.json")

    runs: List[Dict[str, Any]] = []

    # For each workload, run a baseline detector and a treatment (ensemble) detector.
    for workload_id in WORKLOAD_IDS:
        # Baseline: single supervised detector
        baseline_result = run_workload(
            workload_id=workload_id,
            detector_id="baseline_cnn_mfcc",
        )
        runs.append(
            {
                "variant": "baseline",
                "workload_id": workload_id,
                "run_id": f"{workload_id}-baseline-{uuid.uuid4().hex}",
                "success": True,
                "metrics": baseline_result["metrics"],
                "detector_id": "baseline_cnn_mfcc",
            }
        )

        # Treatment: representative ensemble (weighted soft voting)
        treatment_result = run_workload(
            workload_id=workload_id,
            detector_id="ensemble_weighted_soft",
        )
        runs.append(
            {
                "variant": "treatment",
                "workload_id": workload_id,
                "run_id": f"{workload_id}-treatment-{uuid.uuid4().hex}",
                "success": True,
                "metrics": treatment_result["metrics"],
                "detector_id": "ensemble_weighted_soft",
            }
        )

    evidence: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": runs,
        "notes": (
            "Synthetic, deterministic experiment skeleton for Chapter 6. "
            "Detectors and datasets are simulated to enable reproducible benchmarking "
            "without external dependencies or data. Metrics are computed from actual "
            "executed code but do not reflect real audio performance."
        ),
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

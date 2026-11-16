import json
import os
import platform
from typing import Any, Dict, List

from experiment.experiment import (
    CHAPTER_NUMBER,
    EXPERIMENT_ID,
    WORKLOAD_IDS,
    run_all_workloads,
)


def main() -> None:
    # Determine evidence output directory
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    # Run all workloads for baseline and treatment
    runs: List[Dict[str, Any]] = run_all_workloads()

    evidence: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": runs,
        "notes": (
            "Toy offline experiment using synthetic numeric data and simple "
            "classifiers to mimic baseline/treatment structure. Metrics are "
            "computed from actual execution but are not meaningful for real "
            "synthetic voice detection."
        ),
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

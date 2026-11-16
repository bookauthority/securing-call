from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass
from typing import Dict, List

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID, CONFIG_VERSION
from experiment.simulation import run_synthetic_workload


@dataclass
class RunRecord:
    variant: str
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]


def main() -> None:
    # Determine evidence directory
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    results_path = os.path.join(evidence_dir, "results.json")

    workload_id = "WL2_offline_replay_benchmark_synthetic"

    runs: List[RunRecord] = []

    # Baseline run
    baseline_metrics = run_synthetic_workload(variant="baseline", workload_id=workload_id)
    runs.append(
        RunRecord(
            variant="baseline",
            workload_id=workload_id,
            run_id="baseline-0001",
            success=True,
            metrics=baseline_metrics,
        )
    )

    # Treatment run
    treatment_metrics = run_synthetic_workload(variant="treatment", workload_id=workload_id)
    runs.append(
        RunRecord(
            variant="treatment",
            workload_id=workload_id,
            run_id="treatment-0001",
            success=True,
            metrics=treatment_metrics,
        )
    )

    # Prepare evidence object according to required schema
    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": [asdict(r) for r in runs],
        "notes": (
            "Synthetic approximation of WL2_offline_replay_benchmark. "
            "Metrics are derived from deterministic simulations of baseline and "
            "treatment authentication flows, including toy speaker verification "
            "and liveness checks. Real-world metrics such as actual fraud events "
            "and customer complaints are not measured in this offline sandbox. "
            f"config_version={CONFIG_VERSION}"
        ),
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

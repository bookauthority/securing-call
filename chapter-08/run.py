from __future__ import annotations

import json
import os
import platform
from pathlib import Path

from experiment.config import EXPERIMENT_ID, WORKLOAD_CONFIGS
from experiment.pipeline import run_baseline_workload, run_treatment_workload
from experiment.evidence_writer import build_run_id


def main() -> None:
    chapter = 8
    environment = {
        "os": platform.platform(),
        "python": platform.python_version(),
    }

    runs = []

    for workload_id, cfg in WORKLOAD_CONFIGS.items():
        # Baseline
        baseline_result = run_baseline_workload(workload_id, cfg)
        runs.append(
            {
                "variant": "baseline",
                "workload_id": workload_id,
                "run_id": build_run_id(workload_id, "baseline"),
                "success": baseline_result["success"],
                "metrics": baseline_result["metrics"],
                "mode": "baseline-batch-mode-only",
            }
        )

        # Treatment
        treatment_result = run_treatment_workload(workload_id, cfg)
        runs.append(
            {
                "variant": "treatment",
                "workload_id": workload_id,
                "run_id": build_run_id(workload_id, "treatment"),
                "success": treatment_result["success"],
                "metrics": treatment_result["metrics"],
                "mode": (
                    "treatment-streaming-mode"
                    if workload_id != "W2-latency-focused-single-call-drilldown"
                    else "control-no-detector-mode"
                ),
            }
        )

    evidence = {
        "chapter": chapter,
        "experiment_id": EXPERIMENT_ID,
        "environment": environment,
        "runs": runs,
        "notes": (
            "All numeric metrics are derived from deterministic offline "
            "simulations within this repository. Real telephony, audio, and "
            "system-level metrics (CPU, MOS, true packet loss) are not "
            "measured and therefore omitted from the metrics objects."
        ),
    }

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    out_dir = Path(evidence_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":  # pragma: no cover
    main()

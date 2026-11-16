import json
import os
import platform
from datetime import datetime, timezone

from experiment.runner import ExperimentRunner


CHAPTER_NUMBER = 14
EXPERIMENT_ID = "exp-14-stress-redteam-adversarial-eval-v1"


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", ".")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    runner = ExperimentRunner(
        chapter=CHAPTER_NUMBER,
        experiment_id=EXPERIMENT_ID,
    )

    run_results = runner.run_all()

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": [],
        "notes": (
            "Synthetic baseline vs. adversarial (treatment) evaluation over "
            "workloads wl-01..wl-04 using deterministic simulated models."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    for item in run_results:
        evidence["runs"].append(
            {
                "variant": item.variant,
                "workload_id": item.workload_id,
                "run_id": item.run_id,
                "success": item.success,
                "metrics": item.metrics,
                "notes": item.notes,
            }
        )

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

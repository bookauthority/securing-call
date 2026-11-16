import json
import os
import platform
from pathlib import Path

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID
from experiment.simulation import run_experiment_simulation
from experiment.evidence import build_evidence_document, write_evidence


def main() -> None:
    # Run the synthetic experiment simulation to get per-arm, per-workload metrics
    simulation_result = run_experiment_simulation()

    # Build evidence document following the specified contract
    evidence = build_evidence_document(
        chapter=CHAPTER_NUMBER,
        experiment_id=EXPERIMENT_ID,
        simulation_result=simulation_result,
        environment_info={
            "os": platform.platform(),
            "python": platform.python_version(),
        },
    )

    # Determine evidence directory (default /evidence)
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    write_evidence(evidence, Path(evidence_dir))

    # Also print a short summary to stdout (not part of metrics)
    print(json.dumps({
        "chapter": evidence["chapter"],
        "experiment_id": evidence["experiment_id"],
        "runs_count": len(evidence["runs"]),
        "evidence_path": str(Path(evidence_dir) / "results.json"),
    }, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .config import WL1_ID, WL2_ID
from .simulation import FullSimulationResult


def build_evidence_document(
    chapter: int,
    experiment_id: str,
    simulation_result: FullSimulationResult,
    environment_info: Dict[str, str],
) -> Dict:
    runs: List[Dict] = []

    for workload_id in (WL1_ID, WL2_ID):
        for variant in ("baseline", "treatment"):
            metrics = simulation_result.aggregated_metrics[(workload_id, variant)]

            # success indicates that the run completed and metrics were produced
            success = True

            run_id = f"{workload_id}-{variant}"
            runs.append(
                {
                    "variant": variant,
                    "workload_id": workload_id,
                    "run_id": run_id,
                    "success": bool(success),
                    "metrics": metrics,
                }
            )

    evidence: Dict = {
        "chapter": int(chapter),
        "experiment_id": experiment_id,
        "environment": {
            "os": environment_info.get("os", "unknown"),
            "python": environment_info.get("python", "unknown"),
        },
        "runs": runs,
        "notes": (
            "Synthetic simulation of voice-cloning defense experiment. "
            "Metrics are derived from in-memory simulated telemetry only; "
            "no real customer or fraud data is used."
        ),
        "environment_metadata": environment_info,
    }

    return evidence


def write_evidence(evidence: Dict, evidence_dir: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_path = evidence_dir / "results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=False)

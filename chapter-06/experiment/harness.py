from __future__ import annotations

from typing import Any, Dict

from .datasets import SyntheticDataset
from .detectors import get_detector_predictor
from .metrics import compute_all_metrics


# Detector complexity constants used for latency/throughput simulation.
_DETECTOR_COMPLEXITY = {
    "baseline_cnn_mfcc": 1.0,
    "sup_cnn_mfcc_v2": 1.1,
    "selfsup_embedding_classifier": 1.3,
    "heuristic_metadata_rule_based": 0.7,
    "external_api_detector": 1.2,
    "ensemble_majority_vote": 1.5,
    "ensemble_weighted_soft": 1.6,
    "ensemble_stacking_meta_lr": 1.8,
    "ensemble_risk_tiered_fusion": 1.4,
}


def run_workload(workload_id: str, detector_id: str) -> Dict[str, Any]:
    """Run a single detector on a synthetic dataset for a given workload.

    Returns a dict with at least a "metrics" key mapping to numeric metrics.
    """

    dataset = SyntheticDataset(workload_id=workload_id, n_samples=600)
    labels, base_features = dataset.get()

    predictor = get_detector_predictor(detector_id)
    scores = predictor(labels, base_features)

    complexity = _DETECTOR_COMPLEXITY.get(detector_id, 1.0)
    metrics = compute_all_metrics(
        labels=labels,
        scores=scores,
        workload_id=workload_id,
        detector_complexity=complexity,
    )

    return {
        "workload_id": workload_id,
        "detector_id": detector_id,
        "metrics": metrics,
    }

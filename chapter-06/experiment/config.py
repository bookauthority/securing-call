CHAPTER_NUMBER = 6
EXPERIMENT_ID = "chap6-beyond-baseline-detectors-ensembles-v1"

# Workload identifiers as specified in the experiment description.
WORKLOAD_IDS = [
    "WL1_base_domain_eval",
    "WL2_new_language_eval",
    "WL3_new_channel_eval",
    "WL4_adversarial_tools_eval",
    "WL5_cost_latency_benchmark",
]


# Detector IDs for reference (not all are used directly in run.py, but the
# harness and detectors module support them conceptually).
DETECTOR_IDS = [
    "baseline_cnn_mfcc",
    "sup_cnn_mfcc_v2",
    "selfsup_embedding_classifier",
    "heuristic_metadata_rule_based",
    "external_api_detector",
    "ensemble_majority_vote",
    "ensemble_weighted_soft",
    "ensemble_stacking_meta_lr",
    "ensemble_risk_tiered_fusion",
]

CHAPTER_NUMBER = 12
EXPERIMENT_ID = "exp-voice-defense-kpi-ch12-rolling-ab-pilot"

# Workload identifiers from the specification
WL1_ID = "WL1_retail_banking_inbound_auth_and_profile_change"
WL2_ID = "WL2_high_value_transaction_support"

WORKLOAD_IDS = [WL1_ID, WL2_ID]

# Number of synthetic calls to simulate per workload and arm.
# Kept small for fast, bounded execution in the sandbox.
CALLS_PER_ARM_WL1 = 400
CALLS_PER_ARM_WL2 = 200

# Random seed for reproducibility
RANDOM_SEED = 1205

# Synthetic scoring and fraud parameters.
# These are calibrated to express the hypothesis qualitatively
# (treatment reduces fraud with bounded handle time impact), but
# they are purely synthetic and not tied to real-world data.
SIMULATION_PARAMS = {
    "wl1": {
        "baseline": {
            "base_fraud_prob": 0.025,  # 2.5% of calls become confirmed fraud
            "voice_cloning_fraction": 0.6,  # of fraud, how many involve voice cloning
            "aht_mean": 480.0,  # seconds
            "aht_std": 60.0,
            "step_up_rate": 0.01,  # very few step-up flows
        },
        "treatment": {
            "base_fraud_prob": 0.016,  # reduced vs baseline (~36% reduction)
            "voice_cloning_fraction": 0.6,
            "aht_mean": 500.0,  # modest AHT increase (~4%)
            "aht_std": 60.0,
            "step_up_rate": 0.08,  # more step-up verification
        },
    },
    "wl2": {
        "baseline": {
            "base_fraud_prob": 0.04,
            "voice_cloning_fraction": 0.7,
            "aht_mean": 600.0,
            "aht_std": 80.0,
            "step_up_rate": 0.03,
        },
        "treatment": {
            "base_fraud_prob": 0.024,  # reduced vs baseline (~40% reduction)
            "voice_cloning_fraction": 0.7,
            "aht_mean": 630.0,
            "aht_std": 80.0,
            "step_up_rate": 0.12,
        },
    },
}

# Synthetic transaction value distribution for WL2
WL2_TRANSACTION_MIN = 5000.0
WL2_TRANSACTION_MAX = 25000.0

# Detector scoring parameters used in treatment arms
DETECTOR_CONFIG = {
    "low_mean": 0.1,
    "low_std": 0.05,
    "high_mean": 0.75,
    "high_std": 0.1,
    "high_threshold": 0.7,
}

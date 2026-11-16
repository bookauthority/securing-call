from __future__ import annotations

CHAPTER_NUMBER = 7
EXPERIMENT_ID = "exp-07-voice-verification-stepup-liveness-abtest"

# Configuration version for traceability
CONFIG_VERSION = "v1.0.0-toy-synthetic"

# Risk engine thresholds (baseline-style)
BASELINE_THRESHOLD_LOW_RISK = 0.3
BASELINE_THRESHOLD_HIGH_RISK = 0.7

# Speaker verification configuration
SPEAKER_THRESHOLD = 0.75  # normalized cosine similarity threshold in [0,1]

# Liveness configuration
LIVENESS_THRESHOLD = 0.7

# Risk fusion weights (as described qualitatively in the spec)
W_RISK = 0.6
W_SPK = 0.25
W_LIVE = 0.15

# Number of synthetic trials per variant
SYNTHETIC_CALL_COUNT = 1000

# Random seed for deterministic pseudo-randomness
GLOBAL_RANDOM_SEED = 42

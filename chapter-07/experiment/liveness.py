from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .config import LIVENESS_THRESHOLD
from .randomization import _hash_to_float


@dataclass
class LivenessOutput:
    score: float | None
    threshold: float | None
    result: str  # 'pass', 'fail_asr', 'fail_timing', 'timeout', 'error', 'not_applicable'
    challenge_type: str | None


def _base_random(key: str) -> float:
    return _hash_to_float(key.encode("utf-8"))


def simulate_liveness(
    trial_id: str,
    trial_type: str,
    enabled: bool,
    threshold: float | None = None,
) -> LivenessOutput:
    """Simulate liveness challenge outcome.

    For genuine callers we expect high scores; for synthetic/replay lower.
    """

    if not enabled:
        return LivenessOutput(score=None, threshold=None, result="not_applicable", challenge_type=None)

    if threshold is None:
        threshold = LIVENESS_THRESHOLD

    r = _base_random("live|" + trial_id)
    # Choose challenge type
    challenge_types: Tuple[str, ...] = ("random_phrase_digits", "phrase_with_substitution_change")
    cidx = int(r * len(challenge_types)) % len(challenge_types)
    challenge_type = challenge_types[cidx]

    # Derive base score patterns
    if trial_type == "genuine":
        # High score with small noise
        base = 0.85
        noise = (_base_random("n1|" + trial_id) - 0.5) * 0.1
    elif trial_type in ("impostor", "synthetic_clone", "replay"):
        # Lower base score for non-genuine
        base = 0.4
        noise = (_base_random("n2|" + trial_id) - 0.5) * 0.2
    else:
        base = 0.5
        noise = 0.0

    score = max(0.0, min(1.0, base + noise))

    # Derive some timing/ASR anomalies deterministically
    anomaly_r = _base_random("an|" + trial_id)
    if anomaly_r < 0.02:
        return LivenessOutput(score=score, threshold=threshold, result="timeout", challenge_type=challenge_type)
    elif anomaly_r < 0.04:
        return LivenessOutput(score=score, threshold=threshold, result="fail_timing", challenge_type=challenge_type)

    # Normal ASR-based outcome
    if score >= threshold:
        result = "pass"
    else:
        result = "fail_asr"

    return LivenessOutput(score=score, threshold=threshold, result=result, challenge_type=challenge_type)

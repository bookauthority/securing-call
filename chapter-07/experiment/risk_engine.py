from __future__ import annotations

from dataclasses import dataclass

from .config import (
    BASELINE_THRESHOLD_HIGH_RISK,
    BASELINE_THRESHOLD_LOW_RISK,
)
from .randomization import deterministic_random


@dataclass
class RiskResult:
    score: float
    band: str  # 'low', 'medium', 'high'


def compute_risk(account_id: str, call_id: str, experiment_id: str) -> RiskResult:
    """Compute a synthetic but deterministic risk score in [0,1]."""

    base = deterministic_random(account_id, call_id, experiment_id)
    # Slightly reshape distribution towards the middle
    score = 0.5 * base + 0.25
    score = max(0.0, min(1.0, score))

    if score < BASELINE_THRESHOLD_LOW_RISK:
        band = "low"
    elif score < BASELINE_THRESHOLD_HIGH_RISK:
        band = "medium"
    else:
        band = "high"

    return RiskResult(score=score, band=band)

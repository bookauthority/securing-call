from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SampleFeatures:
    """Lightweight representation of a call/sample.

    We don't handle real audio. Instead, we encode a few attributes that
    influence the simulated detector and verifier scores.
    """

    is_adversarial: bool
    # Difficulty from 0..1, higher means harder to detect / verify correctly.
    difficulty: float
    # Role label (e.g., 'attacker', 'customer', 'agent')
    role: str


class BaselineDetector:
    """Simulated detector evaluated on generic data.

    It has moderately good performance on average, but no special adaptation
    to the adversarial scenarios.
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def score(self, features: SampleFeatures, rng: random.Random) -> float:
        """Return a synthetic score in [0, 1] where higher means more synthetic.

        Behavior:
        - For adversarial samples: mean score 0.7 reduced by difficulty.
        - For benign samples: mean score 0.3 increased slightly by difficulty.
        - Add small Gaussian-like noise using Box-Muller based on RNG.
        """

        if features.is_adversarial:
            base = 0.7 - 0.3 * features.difficulty
        else:
            base = 0.3 + 0.2 * features.difficulty

        # Box-Muller transform for approximate Gaussian noise
        u1 = max(rng.random(), 1e-12)
        u2 = max(rng.random(), 1e-12)
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        noise = 0.05 * z0

        score = base + noise
        return min(max(score, 0.0), 1.0)

    def predict(self, features: SampleFeatures, rng: random.Random) -> Tuple[float, bool]:
        score = self.score(features, rng)
        is_synthetic = score >= self.threshold
        return score, is_synthetic


class AdversarialDetector(BaselineDetector):
    """Detector under adversarial evaluation.

    We simulate that adversarial workloads expose some brittleness:
    - For high-difficulty adversarial samples, scores are pulled down,
      increasing false negatives compared to baseline.
    - For benign samples in adversarial contexts, scores increase a bit,
      increasing false positives.
    """

    def score(self, features: SampleFeatures, rng: random.Random) -> float:  # type: ignore[override]
        score = super().score(features, rng)
        if features.is_adversarial:
            # Push scores downward for hard adversarial samples
            score -= 0.15 * features.difficulty
        else:
            # Slightly more aggressive on benign during stress testing
            score += 0.05 * features.difficulty
        return min(max(score, 0.0), 1.0)


class BaselineVerifier:
    """Simulated verification model.

    Returns scores in [0, 1] where higher means more likely to be the
    claimed speaker. For this experiment we keep it simple:
    - Adversarial samples (impersonation) tend to get lower scores.
    - Benign samples tend to get higher scores, but high difficulty
      reduces the margin.
    """

    def __init__(self, threshold: float = 0.6) -> None:
        self.threshold = threshold

    def score(self, features: SampleFeatures, rng: random.Random) -> float:
        if features.is_adversarial:
            base = 0.4 + 0.1 * (1.0 - features.difficulty)
        else:
            base = 0.8 - 0.2 * features.difficulty

        # Simple symmetric noise
        noise = (rng.random() - 0.5) * 0.1
        score = base + noise
        return min(max(score, 0.0), 1.0)

    def predict(self, features: SampleFeatures, rng: random.Random) -> Tuple[float, bool]:
        score = self.score(features, rng)
        passed = score >= self.threshold
        return score, passed


class AdversarialVerifier(BaselineVerifier):
    """Verifier behavior under adversarial stress.

    We simulate that certain adversarial attacks are more successful at
    bypassing verification, especially at high difficulty.
    """

    def score(self, features: SampleFeatures, rng: random.Random) -> float:  # type: ignore[override]
        score = super().score(features, rng)
        if features.is_adversarial:
            # Increase scores for difficult adversarial attempts, simulating
            # better cloning quality and higher bypass rate.
            score += 0.15 * features.difficulty
        return min(max(score, 0.0), 1.0)

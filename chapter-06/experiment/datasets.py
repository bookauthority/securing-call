from __future__ import annotations

import math
from typing import List, Tuple


class SyntheticDataset:
    """Deterministic synthetic dataset used in place of real audio.

    Each dataset consists of (label, feature) pairs. The "feature" is a
    one-dimensional float value roughly corresponding to a detector score
    before model-specific transformation. Labels are 0 for human, 1 for
    synthetic. For realism, we create imbalanced patterns across workloads.
    """

    def __init__(self, workload_id: str, n_samples: int = 500) -> None:
        self.workload_id = workload_id
        self.n_samples = n_samples
        self.labels, self.base_features = self._generate()

    def _generate(self) -> Tuple[List[int], List[float]]:
        labels: List[int] = []
        features: List[float] = []

        # Workload-specific synthetic difficulty and prevalence settings.
        if self.workload_id == "WL1_base_domain_eval":
            synth_ratio = 0.5
            difficulty = 0.3  # easier (better separation)
        elif self.workload_id == "WL2_new_language_eval":
            synth_ratio = 0.5
            difficulty = 0.6  # harder
        elif self.workload_id == "WL3_new_channel_eval":
            synth_ratio = 0.5
            difficulty = 0.7
        elif self.workload_id == "WL4_adversarial_tools_eval":
            synth_ratio = 0.6
            difficulty = 0.8  # hardest, adversarial
        elif self.workload_id == "WL5_cost_latency_benchmark":
            synth_ratio = 0.4
            difficulty = 0.5
        else:
            synth_ratio = 0.5
            difficulty = 0.5

        # Deterministic pseudo-random generator using simple LCG so results are
        # reproducible without relying on the random module's global state.
        seed = 0
        # Create a workload-specific seed to change distributions between them.
        for ch in self.workload_id:
            seed = (seed * 131 + ord(ch)) % 2_147_483_647

        def lcg() -> float:
            nonlocal seed
            seed = (seed * 1_103_515_245 + 12_345) % 2_147_483_647
            return seed / 2_147_483_647.0

        for i in range(self.n_samples):
            u = lcg()
            label = 1 if u < synth_ratio else 0
            labels.append(label)

            # Base feature: draw from two overlapping gaussians controlled by difficulty.
            # difficulty close to 0 => good separation; close to 1 => heavy overlap.
            # We generate synthetic/human means: 0.8 vs 0.2 when easy, converge as difficulty grows.
            mean_human = 0.2 + 0.3 * difficulty
            mean_synth = 0.8 - 0.3 * difficulty
            std = 0.1 + 0.2 * difficulty

            # Box-Muller transform from two lcg() values.
            u1 = max(lcg(), 1e-12)
            u2 = lcg()
            z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
            if label == 1:
                feature = mean_synth + std * z
            else:
                feature = mean_human + std * z
            # Clamp to [0,1] since we'll later treat this as a pseudo-score.
            feature = max(0.0, min(1.0, feature))
            features.append(feature)

        return labels, features

    def __len__(self) -> int:  # pragma: no cover - trivial
        return self.n_samples

    def get(self) -> Tuple[List[int], List[float]]:
        """Return labels and base features."""

        return list(self.labels), list(self.base_features)

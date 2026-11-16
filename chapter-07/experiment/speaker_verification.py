from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple

from .config import SPEAKER_THRESHOLD
from .randomization import _hash_to_float


@dataclass
class SpeakerVerificationOutput:
    score: float  # normalized [0,1]
    threshold: float
    result: str  # 'pass' or 'fail'


class ToySpeakerEmbeddingModel:
    """A toy deterministic speaker embedding model.

    Each speaker_id is mapped to a 2D unit vector derived from a hash. Each
    call embedding is a slightly perturbed version of the base vector.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[float, float]] = {}

    def _base_vec(self, speaker_id: str) -> Tuple[float, float]:
        if speaker_id in self._cache:
            return self._cache[speaker_id]
        # Derive angle from hash in [0, 2*pi)
        angle = 2.0 * math.pi * _hash_to_float(speaker_id.encode("utf-8"))
        x = math.cos(angle)
        y = math.sin(angle)
        self._cache[speaker_id] = (x, y)
        return x, y

    def _call_vec(self, speaker_id: str, call_id: str) -> Tuple[float, float]:
        base_x, base_y = self._base_vec(speaker_id)
        # Small deterministic perturbation based on call_id
        delta = (_hash_to_float((speaker_id + "|" + call_id).encode("utf-8")) - 0.5) * 0.1
        # Rotate by small angle delta
        angle_delta = delta
        cos_d = math.cos(angle_delta)
        sin_d = math.sin(angle_delta)
        x = base_x * cos_d - base_y * sin_d
        y = base_x * sin_d + base_y * cos_d
        # Already unit-length rotation
        return x, y

    @staticmethod
    def _cosine_similarity(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        # both are unit vectors, so denominator = 1
        return max(-1.0, min(1.0, dot))

    @staticmethod
    def _normalize(score: float) -> float:
        # Map cosine [-1,1] to [0,1]
        return (score + 1.0) / 2.0

    def verify(
        self,
        enrolled_speaker_id: str,
        claim_speaker_id: str,
        call_id: str,
        threshold: float | None = None,
    ) -> SpeakerVerificationOutput:
        if threshold is None:
            threshold = SPEAKER_THRESHOLD

        enroll_vec = self._base_vec(enrolled_speaker_id)
        call_vec = self._call_vec(claim_speaker_id, call_id)
        cos = self._cosine_similarity(enroll_vec, call_vec)
        score = self._normalize(cos)
        result = "pass" if score >= threshold else "fail"
        return SpeakerVerificationOutput(score=score, threshold=threshold, result=result)


_model_singleton: ToySpeakerEmbeddingModel | None = None


def get_speaker_model() -> ToySpeakerEmbeddingModel:
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = ToySpeakerEmbeddingModel()
    return _model_singleton

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ClassificationCounts:
    tp: int
    tn: int
    fp: int
    fn: int

    @property
    def total(self) -> int:
        return self.tp + self.tn + self.fp + self.fn


def compute_counts(ground_truth_is_adversarial: Iterable[bool], predicted_is_adversarial: Iterable[bool]) -> ClassificationCounts:
    tp = tn = fp = fn = 0
    for gt, pred in zip(ground_truth_is_adversarial, predicted_is_adversarial):
        if gt and pred:
            tp += 1
        elif (not gt) and (not pred):
            tn += 1
        elif (not gt) and pred:
            fp += 1
        elif gt and (not pred):
            fn += 1
    return ClassificationCounts(tp=tp, tn=tn, fp=fp, fn=fn)


def error_rates(counts: ClassificationCounts) -> dict:
    total = counts.total or 1
    fnr = counts.fn / (counts.fn + counts.tp or 1)
    fpr = counts.fp / (counts.fp + counts.tn or 1)
    return {
        "false_negative_rate": float(fnr),
        "false_positive_rate": float(fpr),
        "num_samples": float(total),
    }

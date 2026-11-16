from __future__ import annotations

import math
from typing import Dict, List

LabelList = List[int]
ScoreList = List[float]


def _sorted_by_score(labels: LabelList, scores: ScoreList):
    return sorted(zip(scores, labels), key=lambda x: x[0])


def auc_roc(labels: LabelList, scores: ScoreList) -> float:
    pairs = _sorted_by_score(labels, scores)
    pos = sum(l for _, l in pairs)
    neg = len(pairs) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rank_sum = 0.0
    for i, (_, l) in enumerate(pairs, start=1):
        if l == 1:
            rank_sum += i
    u = rank_sum - pos * (pos + 1) / 2.0
    auc = u / (pos * neg)
    return float(auc)


def auc_pr(labels: LabelList, scores: ScoreList) -> float:
    # Sort by descending score.
    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    tp = 0.0
    fp = 0.0
    prev_recall = 0.0
    area = 0.0
    pos = sum(labels)
    if pos == 0:
        return 0.0

    for i in indices:
        if labels[i] == 1:
            tp += 1.0
        else:
            fp += 1.0
        recall = tp / pos
        precision = tp / (tp + fp)
        area += precision * max(0.0, recall - prev_recall)
        prev_recall = recall
    return float(area)


def _binary_confusion(labels: LabelList, scores: ScoreList, threshold: float):
    tp = fp = tn = fn = 0
    for y, s in zip(labels, scores):
        pred = 1 if s >= threshold else 0
        if y == 1 and pred == 1:
            tp += 1
        elif y == 0 and pred == 1:
            fp += 1
        elif y == 0 and pred == 0:
            tn += 1
        else:
            fn += 1
    return tp, fp, tn, fn


def eer(labels: LabelList, scores: ScoreList) -> float:
    # Compute EER by sweeping a grid of thresholds.
    thresholds = [i / 200.0 for i in range(201)]  # 0..1 step 0.005
    best_diff = 1.0
    best_eer = 1.0
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return 0.5
    for t in thresholds:
        tp, fp, tn, fn = _binary_confusion(labels, scores, t)
        fpr = fp / neg if neg else 0.0
        fnr = fn / pos if pos else 0.0
        diff = abs(fpr - fnr)
        if diff < best_diff:
            best_diff = diff
            best_eer = (fpr + fnr) / 2.0
    return float(best_eer)


def fnr_at_fpr(labels: LabelList, scores: ScoreList, target_fpr: float) -> float:
    # Determine threshold that yields closest FPR >= target_fpr, then report FNR.
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return 1.0
    thresholds = [i / 1000.0 for i in range(1001)]
    best_thresh = 1.0
    best_fpr = 1.0
    for t in thresholds:
        tp, fp, tn, fn = _binary_confusion(labels, scores, t)
        fpr = fp / neg if neg else 0.0
        if fpr >= target_fpr and fpr < best_fpr:
            best_fpr = fpr
            best_thresh = t
    # If we never exceed target FPR, use maximum threshold (most conservative).
    tp, fp, tn, fn = _binary_confusion(labels, scores, best_thresh)
    fnr = fn / pos if pos else 1.0
    return float(fnr)


def simulate_latency_and_throughput(
    n_samples: int,
    workload_id: str,
    detector_complexity: float,
) -> Dict[str, float]:
    """Return synthetic latency and throughput metrics.

    We use a simple formula to ensure deterministic, bounded metrics that vary
    across workloads and between baseline/treatment.
    """

    # Base per-sample latency in ms: scale with complexity and workload.
    # Workloads later in the list are slightly heavier.
    workload_factor = {
        "WL1_base_domain_eval": 1.0,
        "WL2_new_language_eval": 1.1,
        "WL3_new_channel_eval": 1.15,
        "WL4_adversarial_tools_eval": 1.2,
        "WL5_cost_latency_benchmark": 1.3,
    }.get(workload_id, 1.0)

    base_latency = 2.0 * detector_complexity * workload_factor

    # Median and 95th percentile as simple multiples.
    latency_p50 = base_latency
    latency_p95 = base_latency * 1.5

    # Throughput in requests/second: inverse of avg latency.
    avg_latency_sec = (latency_p50 * 0.7 + latency_p95 * 0.3) / 1000.0
    throughput_rps = 1.0 / avg_latency_sec if avg_latency_sec > 0 else 0.0

    return {
        "Latency_p50": float(latency_p50),
        "Latency_p95": float(latency_p95),
        "Throughput_rps": float(throughput_rps),
    }


def compute_all_metrics(
    labels: LabelList,
    scores: ScoreList,
    workload_id: str,
    detector_complexity: float,
) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    metrics["AUC_ROC"] = auc_roc(labels, scores)
    metrics["AUC_PR"] = auc_pr(labels, scores)
    metrics["EER"] = eer(labels, scores)
    metrics["FNR_at_1pct_FPR"] = fnr_at_fpr(labels, scores, 0.01)
    metrics["FNR_at_5pct_FPR"] = fnr_at_fpr(labels, scores, 0.05)

    latency_metrics = simulate_latency_and_throughput(
        n_samples=len(labels),
        workload_id=workload_id,
        detector_complexity=detector_complexity,
    )
    metrics.update(latency_metrics)
    return metrics

from __future__ import annotations

from typing import Callable, Dict, List, Tuple


# Type annotations
LabelList = List[int]
FeatureList = List[float]
ScoreList = List[float]


class Detector:
    """Base detector interface.

    For this synthetic experiment, a Detector maps base features and labels
    to scores. Real implementations would instead inspect raw audio.
    """

    def __init__(self, detector_id: str) -> None:
        self.detector_id = detector_id

    def predict_scores(self, labels: LabelList, features: FeatureList) -> ScoreList:
        raise NotImplementedError


class BaselineCNNMFCC(Detector):
    """Simulated supervised classifier.

    Uses a simple linear + sigmoid-like transform over base features.
    """

    def __init__(self) -> None:
        super().__init__("baseline_cnn_mfcc")

    def predict_scores(self, labels: LabelList, features: FeatureList) -> ScoreList:
        scores: ScoreList = []
        for f in features:
            # Baseline is moderately well-calibrated: logistic-shaped around 0.5
            # with slight bias.
            score = 1.0 / (1.0 + pow(2.718281828, -8.0 * (f - 0.5)))
            # Small bias towards lower scores for robustness.
            score = max(0.0, min(1.0, score * 0.95 + 0.02))
            scores.append(score)
        return scores


class SupCNNMFCCV2(Detector):
    """Improved supervised model with slightly sharper separation."""

    def __init__(self) -> None:
        super().__init__("sup_cnn_mfcc_v2")

    def predict_scores(self, labels: LabelList, features: FeatureList) -> ScoreList:
        scores: ScoreList = []
        for f in features:
            # Sharper logistic and a small calibration bump.
            score = 1.0 / (1.0 + pow(2.718281828, -10.0 * (f - 0.48)))
            score = max(0.0, min(1.0, score * 0.98 + 0.01))
            scores.append(score)
        return scores


class SelfSupEmbeddingClassifier(Detector):
    """Self-supervised-style detector with different error profile."""

    def __init__(self) -> None:
        super().__init__("selfsup_embedding_classifier")

    def predict_scores(self, labels: LabelList, features: FeatureList) -> ScoreList:
        scores: ScoreList = []
        for i, f in enumerate(features):
            # More sensitive in mid-range, somewhat noisier at extremes.
            # Introduce a deterministic perturbation based on index.
            perturb = ((i * 17) % 31) / 1000.0  # deterministic small noise
            center = 0.52
            scale = 9.0
            base = 1.0 / (1.0 + pow(2.718281828, -scale * (f - center)))
            score = base + (0.05 - abs(f - center)) * 0.1 + perturb
            score = max(0.0, min(1.0, score))
            scores.append(score)
        return scores


class HeuristicMetadataRuleBased(Detector):
    """Rule-based heuristic detector.

    We emulate heuristics that are very confident for some obvious cases but
    weaker overall.
    """

    def __init__(self) -> None:
        super().__init__("heuristic_metadata_rule_based")

    def predict_scores(self, labels: LabelList, features: FeatureList) -> ScoreList:
        scores: ScoreList = []
        for f in features:
            if f > 0.8:
                score = 0.95
            elif f < 0.2:
                score = 0.05
            else:
                # Weak linear mapping in the ambiguous region.
                score = 0.3 + 0.4 * (f - 0.2) / 0.6
            score = max(0.0, min(1.0, score))
            scores.append(score)
        return scores


class ExternalAPIDetector(Detector):
    """Placeholder for a proprietary API detector.

    Since we cannot access the network here, we simulate it as a model with
    decent but slightly different calibration.
    """

    def __init__(self) -> None:
        super().__init__("external_api_detector")

    def predict_scores(self, labels: LabelList, features: FeatureList) -> ScoreList:
        scores: ScoreList = []
        for f in features:
            # Slightly more conservative, tends to avoid extreme scores.
            score = 0.2 + 0.6 * f
            score = max(0.0, min(1.0, score))
            scores.append(score)
        return scores


def get_base_detectors() -> Dict[str, Detector]:
    """Return mapping of base detector id to instance."""

    return {
        "baseline_cnn_mfcc": BaselineCNNMFCC(),
        "sup_cnn_mfcc_v2": SupCNNMFCCV2(),
        "selfsup_embedding_classifier": SelfSupEmbeddingClassifier(),
        "heuristic_metadata_rule_based": HeuristicMetadataRuleBased(),
        "external_api_detector": ExternalAPIDetector(),
    }


def majority_vote(scores_list: List[ScoreList], threshold: float = 0.5) -> ScoreList:
    n_models = len(scores_list)
    n_samples = len(scores_list[0]) if scores_list else 0
    out: ScoreList = []
    for i in range(n_samples):
        votes = 0
        for m in range(n_models):
            votes += 1 if scores_list[m][i] >= threshold else 0
        # Convert majority vote to probability-like value (0 or 1).
        out.append(1.0 if votes >= (n_models / 2.0) else 0.0)
    return out


def weighted_soft(scores_list: List[ScoreList], weights: List[float]) -> ScoreList:
    n_samples = len(scores_list[0]) if scores_list else 0
    out: ScoreList = []
    for i in range(n_samples):
        s = 0.0
        for w, scores in zip(weights, scores_list):
            s += w * scores[i]
        out.append(s)
    return out


def stacking_meta_lr(labels: LabelList, scores_list: List[ScoreList]) -> ScoreList:
    """Simple logistic regression-like meta model trained analytically.

    We fit a 1D logistic on the average score to avoid complex optimization
    while still mimicking stacking behavior.
    """

    n = len(labels)
    if n == 0:
        return []
    avg_scores = [sum(scores[i] for scores in scores_list) / len(scores_list) for i in range(n)]

    # Closed-form-inspired heuristic: compute means for positive and negative
    # and set slope accordingly.
    pos = [s for s, y in zip(avg_scores, labels) if y == 1]
    neg = [s for s, y in zip(avg_scores, labels) if y == 0]
    if not pos or not neg:
        return avg_scores

    mean_pos = sum(pos) / len(pos)
    mean_neg = sum(neg) / len(neg)
    # Avoid degenerate cases.
    if mean_pos == mean_neg:
        return avg_scores

    # Meta parameters (heuristic):
    w = 8.0 * (mean_pos - mean_neg)
    b = -w * (mean_pos + mean_neg) / 2.0

    out: ScoreList = []
    for s in avg_scores:
        z = w * s + b
        prob = 1.0 / (1.0 + pow(2.718281828, -z))
        out.append(prob)
    return out


def risk_tiered_fusion(
    scores_a: ScoreList,
    scores_b: ScoreList,
    risk_tiers: List[str],
) -> ScoreList:
    """Risk-based fusion: simple deterministic policy over two models.

    risk_tiers: one of "low", "medium", "high" for each sample.
    """

    out: ScoreList = []
    for sa, sb, tier in zip(scores_a, scores_b, risk_tiers):
        if tier == "low":
            # Use fast baseline only with relaxed threshold => scaled score.
            prob = sa * 0.9
        elif tier == "medium":
            # Require agreement to be confident human; else treat as uncertain.
            if sa < 0.5 and sb < 0.5:
                prob = max(sa, sb) * 0.8
            else:
                prob = max(sa, sb)
        else:  # high risk
            # Default more suspicious; amplify synthetic evidence.
            prob = min(1.0, max(sa, sb) * 1.1)
        out.append(prob)
    return out


def get_detector_predictor(detector_id: str) -> Callable[[LabelList, FeatureList], ScoreList]:
    """Return a callable implementing the detector/ensemble.

    This keeps `harness.run_workload` simple and makes it easy to plug in
    real models later.
    """

    base_detectors = get_base_detectors()

    if detector_id in base_detectors:
        det = base_detectors[detector_id]

        def fn(labels: LabelList, features: FeatureList) -> ScoreList:
            return det.predict_scores(labels, features)

        return fn

    # Ensemble definitions.
    if detector_id == "ensemble_majority_vote":
        def fn(labels: LabelList, features: FeatureList) -> ScoreList:
            s1 = base_detectors["baseline_cnn_mfcc"].predict_scores(labels, features)
            s2 = base_detectors["selfsup_embedding_classifier"].predict_scores(labels, features)
            s3 = base_detectors["heuristic_metadata_rule_based"].predict_scores(labels, features)
            return majority_vote([s1, s2, s3])

        return fn

    if detector_id == "ensemble_weighted_soft":
        def fn(labels: LabelList, features: FeatureList) -> ScoreList:
            s1 = base_detectors["baseline_cnn_mfcc"].predict_scores(labels, features)
            s2 = base_detectors["selfsup_embedding_classifier"].predict_scores(labels, features)
            s3 = base_detectors["heuristic_metadata_rule_based"].predict_scores(labels, features)
            s4 = base_detectors["external_api_detector"].predict_scores(labels, features)

            # Fixed non-negative weights summing to 1 to emulate validated config.
            weights = [0.35, 0.35, 0.15, 0.15]
            return weighted_soft([s1, s2, s3, s4], weights)

        return fn

    if detector_id == "ensemble_stacking_meta_lr":
        def fn(labels: LabelList, features: FeatureList) -> ScoreList:
            s1 = base_detectors["baseline_cnn_mfcc"].predict_scores(labels, features)
            s2 = base_detectors["selfsup_embedding_classifier"].predict_scores(labels, features)
            s3 = base_detectors["heuristic_metadata_rule_based"].predict_scores(labels, features)
            return stacking_meta_lr(labels, [s1, s2, s3])

        return fn

    if detector_id == "ensemble_risk_tiered_fusion":
        def fn(labels: LabelList, features: FeatureList) -> ScoreList:
            s1 = base_detectors["baseline_cnn_mfcc"].predict_scores(labels, features)
            s2 = base_detectors["selfsup_embedding_classifier"].predict_scores(labels, features)
            # Simple cyclic assignment of risk tiers.
            risk_tiers = []
            for i in range(len(features)):
                r = i % 3
                if r == 0:
                    risk_tiers.append("low")
                elif r == 1:
                    risk_tiers.append("medium")
                else:
                    risk_tiers.append("high")
            return risk_tiered_fusion(s1, s2, risk_tiers)

        return fn

    raise ValueError(f"Unknown detector_id: {detector_id}")

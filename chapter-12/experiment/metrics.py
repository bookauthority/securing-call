from __future__ import annotations

from typing import Dict, Iterable

from .config import WL2_ID
from .simulation import (
    CallRecord,
    CXSurvey,
    DetectionEvent,
    FraudOutcome,
    HumanReviewSession,
    RiskDecisionEvent,
    VerificationEvent,
    WorkloadSimulationResult,
)


def _partition_by_arm(items: Iterable, calls_by_id: Dict[str, CallRecord]):
    arms: Dict[str, list] = {"baseline": [], "treatment": []}
    for obj in items:
        call = calls_by_id.get(obj.call_id)
        if call is None:
            continue
        if call.experiment_arm not in arms:
            continue
        arms[call.experiment_arm].append(obj)
    return arms


def aggregate_metrics_for_workload(
    wl_result: WorkloadSimulationResult,
    arm: str,
) -> Dict[str, float]:
    # Filter calls by arm
    calls = [c for c in wl_result.calls if c.experiment_arm == arm]
    calls_by_id: Dict[str, CallRecord] = {c.call_id: c for c in calls}

    # Partition events by arm using calls mapping
    detection_by_arm = _partition_by_arm(wl_result.detection_events, calls_by_id)
    risk_by_arm = _partition_by_arm(wl_result.risk_decision_events, calls_by_id)
    ver_by_arm = _partition_by_arm(wl_result.verification_events, calls_by_id)
    fraud_by_arm = _partition_by_arm(wl_result.fraud_outcomes, calls_by_id)
    cx_by_arm = _partition_by_arm(wl_result.cx_surveys, calls_by_id)
    hr_by_arm = _partition_by_arm(wl_result.human_review_sessions, calls_by_id)

    detection_events = detection_by_arm[arm]
    risk_events = risk_by_arm[arm]
    ver_events = ver_by_arm[arm]
    fraud_outcomes = fraud_by_arm[arm]
    cx_surveys = cx_by_arm[arm]
    human_reviews = hr_by_arm[arm]

    num_calls = len(calls)
    metrics: Dict[str, float] = {}

    # --- successful_voice_cloning_enabled_fraud_rate ---
    if num_calls > 0:
        fraud_voice_cloning_count = sum(
            1
            for fo in fraud_outcomes
            if fo.fraud_confirmed and fo.suspected_voice_cloning_involved == "yes"
        )
        metrics["successful_voice_cloning_enabled_fraud_rate"] = (
            fraud_voice_cloning_count * 10000.0 / float(num_calls)
        )

    # --- gross_fraud_loss_rate ---
    total_loss_amount = 0.0
    total_tx_amount = 0.0
    if wl_result.workload_id == WL2_ID:
        for fo in fraud_outcomes:
            if fo.fraud_confirmed:
                total_loss_amount += fo.fraud_loss_amount
        for c in calls:
            if c.transaction_amount is not None:
                total_tx_amount += c.transaction_amount
        if total_tx_amount > 0.0:
            metrics["gross_fraud_loss_rate"] = (
                total_loss_amount / total_tx_amount * 10000.0
            )

    # --- detected_suspicious_call_rate ---
    suspicious_calls = set()
    for de in detection_events:
        if de.synthetic_voice_score >= 0.7:
            suspicious_calls.add(de.call_id)
    for re in risk_events:
        if re.decision in ("trigger_step_up_verification", "route_to_high_risk_queue"):
            suspicious_calls.add(re.call_id)
    if num_calls > 0:
        metrics["detected_suspicious_call_rate"] = (
            len(suspicious_calls) * 1000.0 / float(num_calls)
        )

    # --- step_up_verification_trigger_rate ---
    step_up_call_ids = {re.call_id for re in risk_events if re.decision == "trigger_step_up_verification"}
    if num_calls > 0:
        metrics["step_up_verification_trigger_rate"] = (
            len(step_up_call_ids) * 1000.0 / float(num_calls)
        )

    # --- step_up_verification_failure_rate ---
    step_up_attempts = 0
    step_up_fail_or_abandon = 0
    for ve in ver_events:
        if ve.outcome in ("fail", "abandon"):
            step_up_fail_or_abandon += 1
        if ve.outcome in ("fail", "abandon", "pass"):
            step_up_attempts += 1
    if step_up_attempts > 0:
        metrics["step_up_verification_failure_rate"] = (
            step_up_fail_or_abandon * 100.0 / float(step_up_attempts)
        )

    # --- average_handle_time ---
    if num_calls > 0:
        total_aht = sum(c.average_handle_time_sec for c in calls)
        metrics["average_handle_time"] = total_aht / float(num_calls)

    # --- call_abandonment_rate ---
    abandoned = sum(1 for c in calls if c.call_outcome == "abandoned")
    if num_calls > 0:
        metrics["call_abandonment_rate"] = abandoned * 100.0 / float(num_calls)

    # --- agent_escalation_rate ---
    escalated = sum(1 for c in calls if c.call_outcome == "escalated")
    if num_calls > 0:
        metrics["agent_escalation_rate"] = escalated * 1000.0 / float(num_calls)

    # --- customer_experience_score ---
    if cx_surveys:
        total_score = sum(s.score for s in cx_surveys)
        metrics["customer_experience_score"] = total_score / float(len(cx_surveys))

    # --- detector_inference_latency ---
    if detection_events:
        latencies = sorted(de.latency_ms for de in detection_events)
        n = len(latencies)

        def percentile(p: float) -> float:
            if n == 0:
                return 0.0
            k = p * (n - 1)
            f = int(k)
            c = min(f + 1, n - 1)
            if f == c:
                return latencies[f]
            d0 = latencies[f] * (c - k)
            d1 = latencies[c] * (k - f)
            return d0 + d1

        metrics["detector_inference_latency_p50"] = percentile(0.5)
        metrics["detector_inference_latency_p90"] = percentile(0.9)
        metrics["detector_inference_latency_p99"] = percentile(0.99)

    # --- human_review_workload ---
    total_review_minutes = sum(hr.review_duration_minutes for hr in human_reviews)
    if num_calls > 0:
        metrics["human_review_workload"] = (
            total_review_minutes * 1000.0 / float(num_calls)
        )

    # --- false_positive_flag_rate ---
    # Among legitimate calls that were reviewed, how many were flagged as suspicious
    legitimate_reviewed_calls = set()
    false_positive_calls = set()
    suspicious_call_ids = suspicious_calls
    for hr in human_reviews:
        call = calls_by_id.get(hr.call_id)
        if call is None:
            continue
        is_legitimate = hr.label_legitimacy == "legitimate"
        if not is_legitimate:
            continue
        legitimate_reviewed_calls.add(hr.call_id)
        if hr.call_id in suspicious_call_ids:
            false_positive_calls.add(hr.call_id)
    if legitimate_reviewed_calls:
        metrics["false_positive_flag_rate"] = (
            len(false_positive_calls) * 100.0 / float(len(legitimate_reviewed_calls))
        )

    # --- false_negative_estimate_rate ---
    fraud_confirmed_calls = {fo.call_id for fo in fraud_outcomes if fo.fraud_confirmed}
    fraud_unflagged_calls = {
        cid for cid in fraud_confirmed_calls if cid not in suspicious_call_ids
    }
    if fraud_confirmed_calls:
        metrics["false_negative_estimate_rate"] = (
            len(fraud_unflagged_calls) * 100.0 / float(len(fraud_confirmed_calls))
        )

    return metrics

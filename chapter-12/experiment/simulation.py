from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .config import (
    CALLS_PER_ARM_WL1,
    CALLS_PER_ARM_WL2,
    DETECTOR_CONFIG,
    RANDOM_SEED,
    SIMULATION_PARAMS,
    WL1_ID,
    WL2_ID,
    WL2_TRANSACTION_MAX,
    WL2_TRANSACTION_MIN,
)


@dataclass
class CallRecord:
    call_id: str
    customer_id_hash: str
    experiment_arm: str  # "baseline" or "treatment"
    workload_id: str
    timestamp_start: float
    timestamp_end: float
    queue_or_skill: str
    agent_id_hash: str
    call_outcome: str
    average_handle_time_sec: float
    transaction_amount: float | None


@dataclass
class DetectionEvent:
    detection_event_id: str
    call_id: str
    model_version: str
    synthetic_voice_score: float
    risk_band: str
    latency_ms: float
    timestamp: float


@dataclass
class RiskDecisionEvent:
    risk_decision_event_id: str
    call_id: str
    decision: str
    decision_reason_codes: List[str]
    timestamp: float


@dataclass
class VerificationEvent:
    verification_event_id: str
    call_id: str
    verification_type: str
    outcome: str
    timestamp_start: float
    timestamp_end: float


@dataclass
class FraudOutcome:
    fraud_case_id: str
    call_id: str
    fraud_confirmed: bool
    fraud_loss_amount: float
    suspected_voice_cloning_involved: str
    case_close_timestamp: float


@dataclass
class CXSurvey:
    survey_response_id: str
    call_id: str
    survey_type: str
    score: float
    timestamp: float


@dataclass
class HumanReviewSession:
    review_session_id: str
    call_id: str
    reviewer_role: str
    review_duration_minutes: float
    label_legitimacy: str
    label_voice_cloning_suspected: str
    timestamp: float


@dataclass
class WorkloadSimulationResult:
    workload_id: str
    calls: List[CallRecord]
    detection_events: List[DetectionEvent]
    risk_decision_events: List[RiskDecisionEvent]
    verification_events: List[VerificationEvent]
    fraud_outcomes: List[FraudOutcome]
    cx_surveys: List[CXSurvey]
    human_review_sessions: List[HumanReviewSession]


@dataclass
class FullSimulationResult:
    workloads: Dict[str, WorkloadSimulationResult]
    aggregated_metrics: Dict[Tuple[str, str], Dict[str, float]]


def _normal_clamped(mean: float, std: float, lo: float, hi: float) -> float:
    # Generate a normal random variable, clamped to [lo, hi]
    x = random.gauss(mean, std)
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def _draw_customer_id_hash() -> str:
    return uuid.uuid4().hex[:16]


def _draw_agent_id_hash() -> str:
    return uuid.uuid4().hex[:8]


def _draw_queue_or_skill(workload_id: str) -> str:
    if workload_id == WL1_ID:
        return random.choice(["retail_auth", "profile_change", "security_reset"])
    else:
        return random.choice(["wire_transfer", "large_payment", "cashiers_check"])


def _simulate_detector_and_risk(
    call: CallRecord,
    is_treatment: bool,
    fraud_is_voice_cloning: bool,
) -> Tuple[List[DetectionEvent], List[RiskDecisionEvent], List[VerificationEvent]]:
    detection_events: List[DetectionEvent] = []
    risk_decision_events: List[RiskDecisionEvent] = []
    verification_events: List[VerificationEvent] = []

    now = call.timestamp_start + 1.0

    if not is_treatment:
        # baseline arm: no synthetic detector effects
        decision = "allow_with_standard_controls"
        reason_codes: List[str] = ["BASELINE_FLOW"]
        event = RiskDecisionEvent(
            risk_decision_event_id=uuid.uuid4().hex,
            call_id=call.call_id,
            decision=decision,
            decision_reason_codes=reason_codes,
            timestamp=now,
        )
        risk_decision_events.append(event)
        return detection_events, risk_decision_events, verification_events

    # Treatment arm: simulate synthetic voice detector
    latency_ms = _normal_clamped(80.0, 15.0, 40.0, 200.0)

    if fraud_is_voice_cloning:
        score = _normal_clamped(
            DETECTOR_CONFIG["high_mean"],
            DETECTOR_CONFIG["high_std"],
            0.0,
            1.0,
        )
    else:
        score = _normal_clamped(
            DETECTOR_CONFIG["low_mean"],
            DETECTOR_CONFIG["low_std"],
            0.0,
            1.0,
        )

    if score >= DETECTOR_CONFIG["high_threshold"]:
        risk_band = "high"
    elif score >= 0.4:
        risk_band = "medium"
    else:
        risk_band = "low"

    det_event = DetectionEvent(
        detection_event_id=uuid.uuid4().hex,
        call_id=call.call_id,
        model_version="detector_v1",
        synthetic_voice_score=score,
        risk_band=risk_band,
        latency_ms=latency_ms,
        timestamp=now,
    )
    detection_events.append(det_event)

    # Risk orchestration logic (simplified)
    reason_codes: List[str] = []
    if risk_band == "high":
        decision = "trigger_step_up_verification"
        reason_codes.append("DETECTOR_HIGH_SCORE")
    elif risk_band == "medium":
        decision = random.choice([
            "allow_with_standard_controls",
            "trigger_step_up_verification",
        ])
        reason_codes.append("DETECTOR_MEDIUM_SCORE")
    else:
        decision = "allow_with_standard_controls"
        reason_codes.append("DETECTOR_LOW_SCORE")

    risk_event = RiskDecisionEvent(
        risk_decision_event_id=uuid.uuid4().hex,
        call_id=call.call_id,
        decision=decision,
        decision_reason_codes=reason_codes,
        timestamp=now + latency_ms / 1000.0,
    )
    risk_decision_events.append(risk_event)

    # Step-up verification flow only when decision triggers it
    if decision == "trigger_step_up_verification":
        vtype = random.choice([
            "voice_dynamic_phrase",
            "out_of_band_app",
            "sms_otp",
        ])
        vstart = risk_event.timestamp + 1.0
        vend = vstart + random.uniform(10.0, 40.0)

        # Outcome distribution: fraudsters more likely to fail or abandon
        if fraud_is_voice_cloning:
            outcome_probs = (
                ("fail", 0.45),
                ("abandon", 0.25),
                ("pass", 0.3),
            )
        else:
            outcome_probs = (
                ("pass", 0.9),
                ("fail", 0.07),
                ("abandon", 0.03),
            )

        r = random.random()
        cumulative = 0.0
        chosen_outcome = "pass"
        for val, prob in outcome_probs:
            cumulative += prob
            if r <= cumulative:
                chosen_outcome = val
                break

        ver_event = VerificationEvent(
            verification_event_id=uuid.uuid4().hex,
            call_id=call.call_id,
            verification_type=vtype,
            outcome=chosen_outcome,
            timestamp_start=vstart,
            timestamp_end=vend,
        )
        verification_events.append(ver_event)

    return detection_events, risk_decision_events, verification_events


def _simulate_single_call(
    workload_id: str,
    experiment_arm: str,
    params: Dict[str, float],
    transaction_value: float | None,
) -> Tuple[
    CallRecord,
    List[DetectionEvent],
    List[RiskDecisionEvent],
    List[VerificationEvent],
    List[FraudOutcome],
    List[CXSurvey],
    List[HumanReviewSession],
]:
    now = time.time()
    customer_id_hash = _draw_customer_id_hash()
    agent_id_hash = _draw_agent_id_hash()
    queue_or_skill = _draw_queue_or_skill(workload_id)

    # Draw handle time from a normal distribution; clamp at a small positive value
    handle_time = max(60.0, random.gauss(params["aht_mean"], params["aht_std"]))
    start_ts = now
    end_ts = now + handle_time

    # Call outcome: most calls resolved, some abandoned
    r = random.random()
    if r < 0.05:
        call_outcome = "abandoned"
    elif r < 0.1:
        call_outcome = "escalated"
    else:
        call_outcome = "resolved"

    call = CallRecord(
        call_id=uuid.uuid4().hex,
        customer_id_hash=customer_id_hash,
        experiment_arm=experiment_arm,
        workload_id=workload_id,
        timestamp_start=start_ts,
        timestamp_end=end_ts,
        queue_or_skill=queue_or_skill,
        agent_id_hash=agent_id_hash,
        call_outcome=call_outcome,
        average_handle_time_sec=handle_time,
        transaction_amount=transaction_value,
    )

    # Simulate whether this call becomes a confirmed fraud case
    base_fraud_prob = params["base_fraud_prob"]
    is_fraud = random.random() < base_fraud_prob

    fraud_is_voice_cloning = False
    fraud_outcomes: List[FraudOutcome] = []

    if is_fraud:
        fraud_is_voice_cloning = random.random() < params["voice_cloning_fraction"]

    # Detection and risk logic (treatment vs baseline)
    detection_events, risk_decision_events, verification_events = _simulate_detector_and_risk(
        call,
        is_treatment=(experiment_arm == "treatment"),
        fraud_is_voice_cloning=fraud_is_voice_cloning,
    )

    if is_fraud:
        if transaction_value is not None:
            loss_amount = transaction_value
        else:
            loss_amount = random.uniform(100.0, 1000.0)

        fraud_outcome = FraudOutcome(
            fraud_case_id=uuid.uuid4().hex,
            call_id=call.call_id,
            fraud_confirmed=True,
            fraud_loss_amount=loss_amount,
            suspected_voice_cloning_involved=(
                "yes" if fraud_is_voice_cloning else "no"
            ),
            case_close_timestamp=end_ts + random.uniform(3600.0, 72 * 3600.0),
        )
        fraud_outcomes.append(fraud_outcome)

    # CX survey: small probability of response
    cx_surveys: List[CXSurvey] = []
    if random.random() < 0.2:
        if is_fraud and fraud_is_voice_cloning:
            score_mean = 2.5
        elif experiment_arm == "treatment":
            score_mean = 3.9
        else:
            score_mean = 4.0
        score = _normal_clamped(score_mean, 0.5, 1.0, 5.0)
        cx_surveys.append(
            CXSurvey(
                survey_response_id=uuid.uuid4().hex,
                call_id=call.call_id,
                survey_type="CSAT",
                score=score,
                timestamp=end_ts + random.uniform(60.0, 600.0),
            )
        )

    # Human review: sample small fraction of calls,
    # oversampling those with fraud
    human_review_sessions: List[HumanReviewSession] = []

    base_review_prob = 0.03
    if is_fraud:
        review_prob = 0.8
    else:
        review_prob = base_review_prob

    if random.random() < review_prob:
        if is_fraud:
            legitimacy = "fraud_confirmed"
        else:
            legitimacy = "legitimate"

        if fraud_is_voice_cloning:
            voice_cloning_label = "yes"
        else:
            voice_cloning_label = "no"

        review_duration = random.uniform(2.0, 15.0)
        human_review_sessions.append(
            HumanReviewSession(
                review_session_id=uuid.uuid4().hex,
                call_id=call.call_id,
                reviewer_role="fraud_analyst" if is_fraud else "qa",
                review_duration_minutes=review_duration,
                label_legitimacy=legitimacy,
                label_voice_cloning_suspected=voice_cloning_label,
                timestamp=end_ts + random.uniform(600.0, 3600.0),
            )
        )

    return (
        call,
        detection_events,
        risk_decision_events,
        verification_events,
        fraud_outcomes,
        cx_surveys,
        human_review_sessions,
    )


def _simulate_workload(workload_id: str) -> WorkloadSimulationResult:
    if workload_id == WL1_ID:
        n_per_arm = CALLS_PER_ARM_WL1
        wl_key = "wl1"
    elif workload_id == WL2_ID:
        n_per_arm = CALLS_PER_ARM_WL2
        wl_key = "wl2"
    else:
        raise ValueError(f"Unknown workload_id: {workload_id}")

    calls: List[CallRecord] = []
    detection_events: List[DetectionEvent] = []
    risk_decision_events: List[RiskDecisionEvent] = []
    verification_events: List[VerificationEvent] = []
    fraud_outcomes: List[FraudOutcome] = []
    cx_surveys: List[CXSurvey] = []
    human_review_sessions: List[HumanReviewSession] = []

    for arm in ["baseline", "treatment"]:
        params = SIMULATION_PARAMS[wl_key][arm]

        for _ in range(n_per_arm):
            if workload_id == WL2_ID:
                transaction_value: float | None = random.uniform(
                    WL2_TRANSACTION_MIN, WL2_TRANSACTION_MAX
                )
            else:
                transaction_value = None

            (
                call,
                det_events,
                risk_events,
                ver_events,
                frauds,
                surveys,
                reviews,
            ) = _simulate_single_call(
                workload_id=workload_id,
                experiment_arm=arm,
                params=params,
                transaction_value=transaction_value,
            )

            calls.append(call)
            detection_events.extend(det_events)
            risk_decision_events.extend(risk_events)
            verification_events.extend(ver_events)
            fraud_outcomes.extend(frauds)
            cx_surveys.extend(surveys)
            human_review_sessions.extend(reviews)

    return WorkloadSimulationResult(
        workload_id=workload_id,
        calls=calls,
        detection_events=detection_events,
        risk_decision_events=risk_decision_events,
        verification_events=verification_events,
        fraud_outcomes=fraud_outcomes,
        cx_surveys=cx_surveys,
        human_review_sessions=human_review_sessions,
    )


# Import placed here to avoid circular import: metrics depends on simulation
from .metrics import aggregate_metrics_for_workload  # noqa: E402  (import after definitions)


def run_experiment_simulation() -> FullSimulationResult:
    # Seed RNG for reproducibility
    random.seed(RANDOM_SEED)

    workloads: Dict[str, WorkloadSimulationResult] = {}

    for workload_id in (WL1_ID, WL2_ID):
        workloads[workload_id] = _simulate_workload(workload_id)

    aggregated: Dict[Tuple[str, str], Dict[str, float]] = {}
    for workload_id, wl_result in workloads.items():
        for arm in ("baseline", "treatment"):
            metrics = aggregate_metrics_for_workload(wl_result, arm)
            aggregated[(workload_id, arm)] = metrics

    return FullSimulationResult(workloads=workloads, aggregated_metrics=aggregated)

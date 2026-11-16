from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, List


@dataclass
class CallRecord:
    variant: str  # 'baseline' or 'treatment'
    call_id: str
    risk_band: str  # 'low','medium','high'
    auth_time: float
    handle_time: float
    speaker_score: float | None
    speaker_threshold: float | None
    speaker_result: str | None
    liveness_score: float | None
    liveness_threshold: float | None
    liveness_result: str | None
    trial_type: str  # 'genuine','impostor','synthetic_clone','replay'


def aggregate_metrics(calls: Iterable[CallRecord]) -> dict:
    calls_list: List[CallRecord] = list(calls)
    if not calls_list:
        return {
            "call_count": 0.0,
        }

    call_count = float(len(calls_list))
    auth_times = [c.auth_time for c in calls_list]
    handle_times = [c.handle_time for c in calls_list]

    metrics: dict = {
        "call_count": call_count,
        "avg_authentication_time": float(mean(auth_times)),
        "avg_total_call_handle_time": float(mean(handle_times)),
    }

    # Speaker verification FAR/FRR for treatment only (where speaker_result is not None)
    speaker_calls = [c for c in calls_list if c.speaker_result is not None]
    if speaker_calls:
        genuine = [c for c in speaker_calls if c.trial_type == "genuine"]
        non_genuine = [c for c in speaker_calls if c.trial_type != "genuine"]

        if genuine:
            fr = sum(1 for c in genuine if c.speaker_result == "fail") / float(len(genuine))
            metrics["speaker_verification_frr"] = float(fr)
        if non_genuine:
            fa = sum(1 for c in non_genuine if c.speaker_result == "pass") / float(len(non_genuine))
            metrics["speaker_verification_far"] = float(fa)

    # Liveness challenge failure rate (exclude not_applicable)
    live_calls = [c for c in calls_list if c.liveness_result not in (None, "not_applicable")]
    if live_calls:
        fails = [
            c
            for c in live_calls
            if c.liveness_result in ("fail_asr", "fail_timing", "timeout", "error")
        ]
        rate = float(len(fails)) / float(len(live_calls))
        metrics["liveness_challenge_failure_rate"] = rate

    return metrics

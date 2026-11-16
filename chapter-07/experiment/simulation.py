from __future__ import annotations

import math
from typing import List

from .config import (
    CONFIG_VERSION,
    EXPERIMENT_ID,
    SYNTHETIC_CALL_COUNT,
    W_LIVE,
    W_RISK,
    W_SPK,
)
from .liveness import simulate_liveness
from .metrics import CallRecord, aggregate_metrics
from .risk_engine import compute_risk
from .speaker_verification import get_speaker_model


def _trial_type_from_index(idx: int) -> str:
    # Cycle through trial types in a fixed pattern
    types = ("genuine", "impostor", "synthetic_clone", "replay")
    return types[idx % len(types)]


def _simulate_single_call(variant: str, idx: int) -> CallRecord:
    """Simulate a single synthetic call.

    The simulation is deterministic based on the index.
    """

    # Derive synthetic identifiers
    account_id = f"acct_{idx % 50}"  # some accounts repeat
    call_id = f"call_{idx}"

    risk = compute_risk(account_id, call_id, EXPERIMENT_ID)
    trial_type = _trial_type_from_index(idx)

    # Baseline KBA: more questions for higher risk
    if risk.band == "low":
        kba_questions = 2
    elif risk.band == "medium":
        kba_questions = 4
    else:
        kba_questions = 6

    # Each question consumes ~1.0 second of auth time in this toy model
    base_auth_time = float(kba_questions)
    base_handle_overhead = 8.0  # seconds not directly related to auth

    speaker_score = None
    speaker_threshold = None
    speaker_result = None
    liveness_score = None
    liveness_threshold = None
    liveness_result = None

    auth_time = base_auth_time

    if variant == "baseline":
        # No speaker verification or liveness
        handle_time = base_handle_overhead + auth_time
    else:
        # Treatment: try speaker verification and possibly liveness
        model = get_speaker_model()
        enrolled_speaker_id = f"spk_{idx % 50}"  # enrollment per account-like id
        # For genuine: claimed matches enrolled; others mismatch
        if trial_type == "genuine":
            claim_speaker_id = enrolled_speaker_id
        else:
            # Another deterministic id to simulate impostor/clone/replay
            claim_speaker_id = f"spk_{(idx + 7) % 50}"

        spk = model.verify(enrolled_speaker_id, claim_speaker_id, call_id)
        speaker_score = spk.score
        speaker_threshold = spk.threshold
        speaker_result = spk.result

        # Liveness enabled for medium/high risk and when speaker passed or trial is non-genuine
        liveness_enabled = risk.band in ("medium", "high")
        live = simulate_liveness(trial_id=call_id, trial_type=trial_type, enabled=liveness_enabled)
        liveness_score = live.score
        liveness_threshold = live.threshold
        liveness_result = live.result

        # Compute combined auth risk score as in example fusion
        # Missing scores are treated as neutral (0.5)
        base_risk = risk.score
        spk_score_norm = speaker_score if speaker_score is not None else 0.5
        live_score_norm = liveness_score if liveness_score is not None else 0.5
        combined_auth_risk_score = (
            W_RISK * base_risk
            + W_SPK * (1.0 - spk_score_norm)
            + W_LIVE * (1.0 - live_score_norm)
        )

        # Use combined risk to adjust KBA questions in treatment
        # Lower combined risk reduces questions by up to 2; higher risk adds up to 2.
        adjustment = 0
        if combined_auth_risk_score < 0.3:
            adjustment = -2
        elif combined_auth_risk_score < 0.5:
            adjustment = -1
        elif combined_auth_risk_score > 0.8:
            adjustment = 2
        elif combined_auth_risk_score > 0.6:
            adjustment = 1

        adj_kba_questions = max(1, kba_questions + adjustment)

        # Additional time for voice prompts and processing
        voice_overhead = 1.5  # seconds for speaker verification IO
        if liveness_result not in (None, "not_applicable"):
            voice_overhead += 1.0  # additional time for liveness

        auth_time = float(adj_kba_questions) + voice_overhead

        handle_time = base_handle_overhead + auth_time

    return CallRecord(
        variant=variant,
        call_id=call_id,
        risk_band=risk.band,
        auth_time=auth_time,
        handle_time=handle_time,
        speaker_score=speaker_score,
        speaker_threshold=speaker_threshold,
        speaker_result=speaker_result,
        liveness_score=liveness_score,
        liveness_threshold=liveness_threshold,
        liveness_result=liveness_result,
        trial_type=trial_type,
    )


def run_synthetic_workload(variant: str, workload_id: str) -> dict:
    """Run a bounded synthetic approximation of WL2.

    Returns aggregated numeric metrics for inclusion in the evidence file.
    """

    if variant not in ("baseline", "treatment"):
        raise ValueError(f"Unknown variant: {variant}")

    calls: List[CallRecord] = []
    for idx in range(SYNTHETIC_CALL_COUNT):
        calls.append(_simulate_single_call(variant=variant, idx=idx))

    metrics = aggregate_metrics(calls)

    # Ensure all metric values are numeric floats
    out: dict = {}
    for k, v in metrics.items():
        if isinstance(v, (int, float)) and not (math.isinf(v) or math.isnan(v)):
            out[k] = float(v)
    return out

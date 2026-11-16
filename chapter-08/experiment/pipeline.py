from __future__ import annotations

import math
from typing import Dict, Any

from .simulation import generate_calls


# The simulator uses a simple model of processing latency that is
# independent of wall-clock time. We define latency in milliseconds as
# proportional to the amount of simulated work (frames/windows).


def _baseline_process_call(total_frames: int) -> float:
    """Return simulated total processing latency (ms) for a single call.

    We model the batch pipeline as O(N) over frames with a fixed cost
    per frame plus a small fixed overhead per call.
    """

    per_frame_ms = 0.02  # processing cost per frame in ms (simulated)
    overhead_ms = 5.0
    return overhead_ms + per_frame_ms * total_frames


def _treatment_process_call(total_windows: int) -> float:
    """Return total simulated processing latency (ms) for a streaming call.

    We model streaming as per-window processing with significantly
    smaller overhead per call, but more frequent per-window work.
    """

    per_window_ms = 0.15  # processing cost per window in ms
    overhead_ms = 1.0
    return overhead_ms + per_window_ms * total_windows


def _treatment_avg_window_latency_ms() -> float:
    """Return a representative per-window latency for reporting.

    This is tied to the per-window cost above. In a real system it
    would be measured end-to-end; here we expose the same constant
    used in the per-call calculation.
    """

    return 0.15


def run_baseline_workload(workload_id: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Run a baseline (batch) simulation for a workload and collect metrics.

    Metrics (all numeric):
    - calls_processed: number of calls processed.
    - avg_detection_latency_ms: average per-call batch latency.
    - total_detection_latency_ms: sum of per-call latencies.
    """

    total_latency_ms = 0.0
    total_calls = 0.0

    for concurrent in cfg["concurrent_calls"]:
        calls = generate_calls(
            concurrent=concurrent,
            avg_duration_s=cfg["avg_call_duration_s"],
            frames_per_second=cfg["frames_per_second"],
            windows_per_second=cfg["windows_per_second"],
        )
        for call in calls:
            latency_ms = _baseline_process_call(call.total_frames)
            total_latency_ms += latency_ms
            total_calls += 1.0

    avg_latency_ms = total_latency_ms / total_calls if total_calls > 0 else 0.0

    metrics = {
        "calls_processed": float(total_calls),
        "avg_detection_latency_ms": float(avg_latency_ms),
        "total_detection_latency_ms": float(total_latency_ms),
    }

    # success is True as long as we completed computations without
    # encountering impossible values.
    success = not (math.isnan(avg_latency_ms) or math.isinf(avg_latency_ms))

    return {"success": success, "metrics": metrics}


def run_treatment_workload(workload_id: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Run a treatment (streaming) simulation for a workload and collect metrics.

    Metrics (all numeric):
    - calls_processed: number of calls processed.
    - avg_window_latency_ms: average per-window latency.
    - avg_call_detection_latency_ms: average per-call cumulative detection
      latency (simulated) across windows.
    - total_detection_latency_ms: total latency across all calls.

    For the W3 workload, we apply a simple fault injection by inflating
    per-window latency for half of the calls to model degradation.
    """

    total_latency_ms = 0.0
    total_calls = 0.0

    fault_injection = bool(cfg.get("fault_injection", False))

    for concurrent in cfg["concurrent_calls"]:
        calls = generate_calls(
            concurrent=concurrent,
            avg_duration_s=cfg["avg_call_duration_s"],
            frames_per_second=cfg["frames_per_second"],
            windows_per_second=cfg["windows_per_second"],
        )
        for idx, call in enumerate(calls):
            base_latency = _treatment_process_call(call.total_windows)
            if fault_injection and (idx % 2 == 0):
                # Simulate a latency spike under failure conditions.
                base_latency *= 1.5
            total_latency_ms += base_latency
            total_calls += 1.0

    avg_call_latency_ms = total_latency_ms / total_calls if total_calls > 0 else 0.0
    avg_window_latency_ms = _treatment_avg_window_latency_ms()

    metrics = {
        "calls_processed": float(total_calls),
        "avg_window_latency_ms": float(avg_window_latency_ms),
        "avg_call_detection_latency_ms": float(avg_call_latency_ms),
        "total_detection_latency_ms": float(total_latency_ms),
    }

    success = not (
        math.isnan(avg_call_latency_ms)
        or math.isinf(avg_call_latency_ms)
        or math.isnan(avg_window_latency_ms)
        or math.isinf(avg_window_latency_ms)
    )

    return {"success": success, "metrics": metrics}

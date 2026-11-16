from __future__ import annotations

EXPERIMENT_ID = "exp-08-realtime-telephony-ivr-agent-desktop-v1"

# Lightweight configuration for three workloads. The numbers are small
# enough to run quickly in the sandbox but large enough to yield
# non-trivial, averaged metrics.

WORKLOAD_CONFIGS = {
    "W1-realistic-multi-tenant-call-simulation": {
        "concurrent_calls": [10, 20],
        "avg_call_duration_s": 30.0,
        "frames_per_second": 50,  # 20 ms frames
        "windows_per_second": 2,  # 1 s windows, 0.5 s stride
    },
    "W2-latency-focused-single-call-drilldown": {
        "concurrent_calls": [1, 5],
        "avg_call_duration_s": 20.0,
        "frames_per_second": 50,
        "windows_per_second": 2,
    },
    "W3-failure-and-degradation-scenarios": {
        "concurrent_calls": [5, 10],
        "avg_call_duration_s": 15.0,
        "frames_per_second": 50,
        "windows_per_second": 2,
        "fault_injection": True,
    },
}

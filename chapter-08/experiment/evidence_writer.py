from __future__ import annotations

import time


def build_run_id(workload_id: str, variant: str) -> str:
    """Return a stable but unique run ID string for a workload and variant.

    We combine the workload ID, variant, and a millisecond timestamp.
    Tests only rely on uniqueness, not specific formatting.
    """

    ts_ms = int(time.time() * 1000)
    safe_workload = workload_id.replace(" ", "_")
    return f"{safe_workload}-{variant}-{ts_ms}"

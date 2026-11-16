from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List


@dataclass
class SimCall:
    """Simple representation of a call in the simulator.

    Attributes
    ----------
    call_id: int
        Integer identifier for this simulated call.
    duration_s: float
        Simulated duration of the call in seconds.
    frames_per_second: int
        Number of audio frames per second (e.g., 50 for 20 ms frames).
    windows_per_second: int
        Number of analysis windows per second (e.g., 2 for 1 s windows,
        0.5 s stride).
    """

    call_id: int
    duration_s: float
    frames_per_second: int
    windows_per_second: int

    @property
    def total_frames(self) -> int:
        return int(self.duration_s * self.frames_per_second)

    @property
    def total_windows(self) -> int:
        # A simple approximation: windows_per_second * duration
        return int(self.duration_s * self.windows_per_second)


def generate_calls(
    concurrent: int,
    avg_duration_s: float,
    frames_per_second: int,
    windows_per_second: int,
) -> List[SimCall]:
    """Generate a deterministic list of SimCall objects.

    The durations are varied slightly but deterministically using a
    simple formula based on the call index. No randomness is used so
    tests are reproducible.
    """

    calls: List[SimCall] = []
    for i in range(concurrent):
        # Vary duration by up to +/- 20% deterministically.
        factor = 1.0 + 0.2 * math.sin(i + 1)
        dur = avg_duration_s * factor
        calls.append(
            SimCall(
                call_id=i,
                duration_s=dur,
                frames_per_second=frames_per_second,
                windows_per_second=windows_per_second,
            )
        )
    return calls

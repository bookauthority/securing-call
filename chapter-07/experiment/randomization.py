from __future__ import annotations

import hashlib
from typing import Tuple

from .config import GLOBAL_RANDOM_SEED


def _hash_to_float(seed_bytes: bytes) -> float:
    """Map bytes to a deterministic float in [0, 1)."""

    digest = hashlib.sha256(seed_bytes).digest()
    # Use first 8 bytes as integer
    int_val = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return (int_val % (10**12)) / float(10**12)


def deterministic_random(account_id: str, call_id: str, experiment_id: str) -> float:
    """Deterministically map identifiers to a float in [0, 1).

    This can be used for A/B assignment; here we primarily use it to derive
    pseudo-random properties (e.g., risk band, trial type) reproducibly.
    """

    seed_str = f"{GLOBAL_RANDOM_SEED}|{experiment_id}|{account_id}|{call_id}"
    return _hash_to_float(seed_str.encode("utf-8"))


def deterministic_choice(options: Tuple[str, ...], key: str) -> str:
    """Choose from options based on key in a deterministic way."""

    r = _hash_to_float((str(GLOBAL_RANDOM_SEED) + "|" + key).encode("utf-8"))
    idx = int(r * len(options)) % len(options)
    return options[idx]

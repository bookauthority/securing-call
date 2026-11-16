# Measurement, Monitoring, and KPIs for Voice Cloning Defense Programs (Chapter 12)

This self-contained Python 3.11+ project simulates a controlled experiment for:

> **Experiment ID**: `exp-voice-defense-kpi-ch12-rolling-ab-pilot`

It models baseline and treatment call flows for voice-cloning defenses, captures
telemetry in-memory, and produces a `results.json` evidence file compatible with
an external validator.

The implementation is intentionally simple and synthetic but structurally mirrors
what you would run in a real contact-center environment with voice cloning
protection, risk orchestration, and step-up verification.

## Project Layout

- `run.py` — Entry point. Runs a small, deterministic experiment simulation and
  writes `/evidence/results.json` (or `$BOOKMAS_EVIDENCE_DIR/results.json`).
- `experiment/__init__.py` — Package marker.
- `experiment/config.py` — Constants and configuration for the experiment.
- `experiment/simulation.py` — Core simulation logic for baseline and treatment
  arms across workloads.
- `experiment/metrics.py` — Telemetry aggregation and KPI computation.
- `experiment/evidence.py` — Evidence file assembly and writing utilities.
- `tests/test_experiment.py` — Unit tests validating the runtime contract and
  basic invariants.
- `requirements.txt` — Empty of third-party runtime deps (standard library only).

## What This Project Demonstrates

The code focuses on:

- **12.1 / 12.2 – Metrics model**
  - Simulates key metrics such as:
    - `successful_voice_cloning_enabled_fraud_rate`
    - `gross_fraud_loss_rate`
    - `detected_suspicious_call_rate`
    - `step_up_verification_trigger_rate`
    - `average_handle_time`
  - Uses per-call telemetry to compute metrics separately for baseline and
    treatment, per workload.

- **12.3 – Telemetry pipelines**
  - Implements in-memory event tables corresponding to the `evidence_schema`:
    - `calls`, `detection_events`, `risk_decision_events`, `verification_events`,
      `fraud_outcomes`, `cx_surveys`, and `human_review_sessions`.
  - Simulates how detector scores and risk decisions are logged.

- **12.4 – Dashboard inputs**
  - The computed metrics dictionary is exactly what you would feed into
    dashboards for risk, operations, and executives (fraud, CX, workload).

- **12.5 – Experiments and rollout**
  - Models:
    - WL1: retail banking inbound authentication and profile changes.
    - WL2: high-value transaction support.
  - Applies deterministic randomization by hashed `customer_id_hash` for WL1 and
  per-call sampling for WL2 to emulate A/B / pilot style rollouts.

- **12.6 / 12.7 / 12.8 – Interpretation and governance**
  - Treatment logic includes slightly improved security at some cost to
    operational metrics (e.g., more step-up verification, minor handle time
    impact), giving realistic trade-offs for governance and investment decisions.

## Assumptions & Limitations

- **Synthetic data only**: No access to real audio, fraud systems, or contact
  center platforms. All metrics are derived from pseudo-randomly generated call
  trajectories seeded for reproducibility.
- **No real-time dashboards**: Instead, an evidence JSON file captures metric
  values suitable for offline inspection and plotting.
- **Offline sandbox**: No networking, external processes, or third-party
  libraries are used. The sandbox provides `/tmp`, `/tmp/work`, and `/evidence`
  as writable directories.

## Evidence File Runtime Contract

Running `python run.py` must produce a JSON file at:

```text
$BOOKMAS_EVIDENCE_DIR/results.json  (default: /evidence/results.json)
```

with structure:

```json
{
  "chapter": 12,
  "experiment_id": "exp-voice-defense-kpi-ch12-rolling-ab-pilot",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "WL1_retail_banking_inbound_auth_and_profile_change" | "WL2_high_value_transaction_support",
      "run_id": "...",
      "success": true,
      "metrics": {
        "some_metric_name": 0.123,
        "another_metric": 42
      }
    }
  ],
  "notes": "optional text",
  "environment_metadata": {"extra": "optional"}
}
```

Requirements:

- At least one **baseline** and one **treatment** run for **each workload**.
- All **metric values are finite numbers** (no strings, nulls, lists, or dicts).
- Additional non-metric content such as explanatory text, detailed metadata,
  or debugging info must be kept **outside** `metrics` (e.g. top-level `notes`,
  `environment_metadata`, etc.).
- Only metrics actually computed from simulated telemetry are included. The
  code does not fabricate unmeasurable values.

## How to Run

From the project root:

```bash
# 1. (Optional) Set evidence directory; default is /evidence
export BOOKMAS_EVIDENCE_DIR=/evidence

# 2. Run the experiment simulation
python run.py

# 3. Inspect the evidence artifact
cat /evidence/results.json

# 4. Run tests
python -m unittest discover -s tests -p "test_*.py"
```

## Design Notes

- **Deterministic randomness**: The simulation seeds Python's `random` module
  to keep runs reproducible and ensure tests can rely on stable expectations for
  structure and basic properties (but not specific numeric values).
- **Baseline vs Treatment**:
  - Baseline: no synthetic voice detector effects; fraud and losses are higher,
    fewer suspicious flags, minimal step-up flows.
  - Treatment: uses a simple synthetic `synthetic_voice_score` and risk logic to
    trigger more step-up verification, reducing simulated fraud probability and
    losses while slightly impacting customer experience and handle time.
- **Fair comparison**: Both variants share the same simulation code and differ
  only in controlled parameters and logic toggles.

This scaffold is designed to be adapted into a real telemetry- and KPI-driven
voice cloning defense program in production environments.

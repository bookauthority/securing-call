# exp-07-voice-verification-stepup-liveness-abtest

This is a self-contained, offline-friendly Python 3.11+ experiment project for:

> **Voice Verification, Step-Up Authentication, and Liveness Checks**

It simulates a contact-center authentication flow with:

- A **baseline** arm using only knowledge-based authentication (KBA).
- A **treatment** arm that adds:
  - A simple **speaker verification** prototype (embedding + cosine similarity in 2D).
  - A rule-based **liveness challenge** check (ASR-like text pattern + timing).
- An **A/B experiment harness** that:
  - Randomly assigns synthetic calls to baseline or treatment using a deterministic function.
  - Produces numeric metrics per arm for a synthetic workload.
  - Writes evidence to `/evidence/results.json` using the required schema.

No external packages are used beyond the Python standard library.

## Project layout

- `run.py` — main entry point that runs the synthetic experiment and writes evidence.
- `experiment/__init__.py` — package marker.
- `experiment/config.py` — configuration, thresholds, and utility constants.
- `experiment/randomization.py` — deterministic randomization function and helpers.
- `experiment/risk_engine.py` — simple baseline risk scoring.
- `experiment/speaker_verification.py` — deterministic, synthetic speaker verification model.
- `experiment/liveness.py` — deterministic liveness challenge generator and checker.
- `experiment/simulation.py` — core simulation of calls, baseline and treatment flows.
- `experiment/metrics.py` — metric aggregation for the simulated calls.
- `tests/test_experiment.py` — unit tests validating the evidence schema and basic behavior.

## Running the experiment

The sandbox provides `/evidence` as a writable directory. The experiment code:

- Resolves the evidence directory as:
  - `BOOKMAS_EVIDENCE_DIR` environment variable, if set; otherwise
  - `/evidence`.
- Writes a file named `results.json` in that directory.

Steps:

```bash
python run.py
```

After successful execution you should see `/evidence/results.json` with contents resembling:

```json
{
  "chapter": 7,
  "experiment_id": "exp-07-voice-verification-stepup-liveness-abtest",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "WL2_offline_replay_benchmark_synthetic",
      "run_id": "baseline-0001",
      "success": true,
      "metrics": {
        "call_count": 1000,
        "avg_authentication_time": 5.2,
        "avg_total_call_handle_time": 15.7
      }
    },
    {
      "variant": "treatment",
      "workload_id": "WL2_offline_replay_benchmark_synthetic",
      "run_id": "treatment-0001",
      "success": true,
      "metrics": {
        "call_count": 1000,
        "avg_authentication_time": 6.9,
        "avg_total_call_handle_time": 17.0,
        "speaker_verification_far": 0.01,
        "speaker_verification_frr": 0.04,
        "liveness_challenge_failure_rate": 0.08
      }
    }
  ],
  "notes": "..."
}
```

Values will vary slightly but will remain deterministic across runs with the same configuration.

## Workloads and what is simulated

The real-world spec defines two workloads (`WL1_production_like_live_calls`, `WL2_offline_replay_benchmark`). In this offline project we implement a **bounded synthetic approximation** of WL2 only:

- `workload_id`: `WL2_offline_replay_benchmark_synthetic`
- We generate a deterministic set of labeled trials:
  - Genuine
  - Impostor
  - Synthetic clone
  - Replay
- For each trial we:
  - Run the synthetic speaker verification model.
  - For a subset, run a liveness challenge with deterministic ASR-like outcome.

We do **not** attempt to simulate production telephony or real time; call durations and times are synthetic but derived from the simulated control flow, not invented constants.

The evidence therefore covers:

- Basic **security vs friction trade-off** between baseline and treatment:
  - Additional authentication time in treatment.
  - False acceptance / rejection behavior of speaker verification.
  - Liveness challenge failure rate.
- Under a controlled, reproducible synthetic environment suitable for automated testing.

Metrics that cannot be reliably observed offline with synthetic traffic (e.g., real fraud_events, customer complaints, real-world latency variance) are **omitted** from the numeric metrics section, as required. Their presence is described qualitatively in the code and comments instead.

## Running tests

Use Python's built-in unittest discovery:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests verify that:

- `run.py` produces `/evidence/results.json` using the required schema.
- Both baseline and treatment runs are present for the workload.
- Metric values are numeric and not null.
- The experiment and chapter identifiers are correct.

## Design notes

### Speaker verification prototype

Instead of using external ML models (disallowed in this offline, no-dependency setting), we implement a **toy, deterministic model**:

- Each speaker is assigned a fixed 2D vector embedding on first use derived from a hash of `speaker_id`.
- Each call produces a slightly noisy variant of the same embedding.
- Similarity is measured via cosine similarity, normalized to `[0, 1]`.
- Impostor/synthetic/replay trials use another speaker's embedding.

While this is not a real biometric model, it supports:

- Genuine vs impostor separation.
- Configurable thresholds for FAR/FRR.
- Reproducible numeric evaluation across many trials.

### Liveness checks

We simulate an **active liveness challenge** with:

- Randomized challenge types: `random_phrase_digits`, `phrase_with_substitution_change`.
- A pseudo-ASR that sometimes mismatches depending on synthetic quality and timing.
- A liveness score in `[0, 1]` and pass/fail classification with thresholds.

### Baseline vs treatment flows

In the simulation:

- Baseline: only KBA is used; authentication time depends on the number of KBA questions based on a risk score.
- Treatment: may invoke speaker verification and liveness; fusion slightly reduces KBA burden when successful, and increases it when verification fails.

These flows mirror the structure of the full spec but operate entirely on synthetic data.

## Extending the project

In a real deployment you would replace:

- `experiment/speaker_verification.py` with calls to an actual embedding model.
- `experiment/liveness.py` with real ASR, timing signals, and spectral checks.
- `experiment/simulation.py` with actual call ingestion and per-call evidence logging following the provided `evidence_schema`.

All other experiment scaffolding (randomization, metric aggregation, evidence output) can remain conceptually similar.

# Experiment 8 – Real-Time Integration with Telephony, IVR, and Agent Desktops

This repository contains a **self-contained, offline-simulated** Python 3.11+ experiment
for Chapter 8:

> "Real-Time Integration with Telephony, IVR, and Agent Desktops"

Experiment ID:

- `exp-08-realtime-telephony-ivr-agent-desktop-v1`

The goal is to **simulate** and compare a baseline batch-style pipeline and a
real-time streaming pipeline for voice risk scoring under multiple workloads.

This project does **not** integrate with real telephony, IVR, or CCaaS platforms.
Instead, it models them as deterministic, CPU-bounded Python components.
The numerical metrics it records are derived from actual executed code
(e.g., simulated processing delays, queue latencies, per-chunk timing), but
are **not** measurements of a production environment.

## Contents

- `run.py` – Main entry point. Runs the experiment and writes evidence JSON.
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Static configuration for workloads and variants.
- `experiment/simulation.py` – Core simulation primitives (calls, chunks, workers).
- `experiment/pipeline.py` – Baseline and treatment pipeline implementations.
- `experiment/metrics.py` – Metric aggregation helpers.
- `experiment/evidence_writer.py` – Writes results in the required schema.
- `tests/test_experiment.py` – Unittests validating evidence format and basic behavior.

## Key Simplifications

- **Audio**: Actual audio is not processed. We work with abstract
  "frames" and "windows" represented by simple Python objects.
- **Detection models**: There is no ML inference. Detection latency is
  modeled via deterministic `time.sleep`-like delays simulated using
  accounting of processing steps, not wall-clock time. (Real wall-clock
  sleeps are avoided so tests stay fast.)
- **Telephony / IVR / Agent desktop**: Represented by queues and event
  handlers inside a single process, communicating via function calls and
  in-memory lists.
- **Concurrency**: Implemented with `threading` and locks in a strictly
  bounded and deterministic way to mimic concurrent calls without high
  resource usage. The scale of "1,000 concurrent calls" is simulated by
  looping over call objects rather than actually creating 1,000 long-lived
  threads.

Despite these simplifications, **all metrics recorded in the evidence file
are derived from executed logic in this codebase** (e.g., simulated
per-chunk processing costs and queueing effects).

## Evidence Contract

Running `python run.py` produces `/evidence/results.json` (path taken from
`BOOKMAS_EVIDENCE_DIR`, which defaults to `/evidence` if not set) with the
following structure:

```json
{
  "chapter": 8,
  "experiment_id": "exp-08-realtime-telephony-ivr-agent-desktop-v1",
  "environment": {
    "os": "...",
    "python": "..."
  },
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "W1-realistic-multi-tenant-call-simulation",
      "run_id": "...",
      "success": true,
      "metrics": {
        "avg_detection_latency_ms": 12.3,
        "calls_processed": 200.0
      },
      "extra_notes": "..."
    }
  ],
  "notes": "Free-form text about limitations or observations."
}
```

Constraints:

- At least **one baseline** and **one treatment** run per workload.
- All metric values must be **finite numbers** (no strings, no nulls).
- Metrics must come from actual run computations, not invented constants.
- Additional fields are allowed at any level (e.g., `extra_notes`),
  but they are not interpreted as metrics.

## Workloads

We simulate three workloads (mapped to the specification):

- `W1-realistic-multi-tenant-call-simulation`
- `W2-latency-focused-single-call-drilldown`
- `W3-failure-and-degradation-scenarios`

Each workload is executed under both **baseline** (batch) and
**treatment** (streaming) variants, with small but non-trivial numbers
of simulated calls and chunks to provide meaningful but fast-running
metrics.

### Baseline Variant

- Represents a post-call batch job.
- Each call generates a synthetic "recording" processed at the end.
- We track simulated per-call processing cost and aggregate latency.

### Treatment Variant

- Represents real-time, chunk-based streaming processing.
- Calls are divided into time-ordered chunks (frames and windows).
- We simulate per-window processing latency and policy decisions.

## Running the Experiment

From the project root:

```bash
python run.py
```

This will:

1. Run all workloads (W1–W3) for both baseline and treatment variants.
2. Aggregate metrics for each run.
3. Write `/evidence/results.json` with the schema above.

You can override the evidence directory by setting:

```bash
export BOOKMAS_EVIDENCE_DIR=/some/other/path
python run.py
```

The directory will be created if it does not exist.

## Running Tests

Tests are based only on the Python standard library.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests validate:

- The evidence file exists after `run.py` is executed.
- The evidence JSON matches the required top-level schema.
- The `runs` list contains both baseline and treatment variants for
  each workload ID.
- All metric values are numeric.

## Reproducibility Notes

- The simulation uses fixed seeds and deterministic formulas wherever
  pseudo-randomness is required.
- No external services (network, shell, cloud APIs) are used.
- The code does not access the filesystem outside the project tree
  and the `/evidence` directory.

## Limitations

- Metrics like MOS, real CPU utilization, and true packet loss cannot be
  measured in this offline environment. Those metrics are **omitted** from
  `metrics` and, where relevant, limitations are mentioned in `notes`.
- This is a **didactic** reference implementation for architecture and
  measurement patterns, not a production-ready telephony integration.

# Chapter 5 – Baseline Synthetic Voice Detection (Offline Toy Experiment)

This repository fragment implements a **self-contained, offline, toy version** of the experiment described in the specification for:

- **Chapter**: 5
- **Experiment ID**: `exp-ch5-baseline-synth-voice-det-v1`

Because the sandbox environment is fully offline and may not have audio tooling, ASVspoof datasets, or ML frameworks installed, this project uses a **deterministic synthetic dataset** and **simple numeric models** to mimic the structure of the real experiment:

- A **baseline** classifier over fixed embeddings.
- A **treatment** classifier that pretends to fine-tune embeddings by transforming them before classification.
- Multiple **workloads** corresponding to those in the specification, but implemented as small bounded simulations.
- A reproducible **evidence artifact** written to `/evidence/results.json` (or to `BOOKMAS_EVIDENCE_DIR/results.json` if the environment variable is set) that follows the exact schema requested.

The goal is to show **experiment wiring, reproducibility controls, and evidence capture**, not to achieve meaningful synthetic voice detection.

## Contents

- `run.py` – Main entry point. Executes all workloads for both baseline and treatment variants and writes evidence JSON.
- `experiment/__init__.py` – Package marker.
- `experiment/experiment.py` – Core logic: synthetic data generation, baseline and treatment models, workloads, metrics, and evidence assembly.
- `tests/test_experiment.py` – Unit tests that validate the evidence schema and basic behaviour.
- `requirements.txt` – Empty of third-party runtime dependencies by design (standard library only).

## How it works

### Synthetic Data

- We generate a tiny synthetic dataset as 2D points `(x1, x2)` with labels:
  - "synthetic_voice" (positive class) points from one Gaussian cluster.
  - "natural_voice" (negative class) points from another.
- Randomness is fully controlled via a fixed seed so that runs are reproducible.

### Models

Both models operate on the same synthetic embeddings:

- **Baseline**: logistic-regression-like classifier (implemented from scratch via gradient descent) on the raw features.
- **Treatment**: same classifier, but applied after a fixed, learned linear transformation that plays the role of a "fine-tuned" embedding layer.

Both are trained deterministically on the same training set and evaluated on the same held-out set per workload.

### Workloads

We approximate the workloads from the specification:

1. `wl-inference-asvspoof-eval`
2. `wl-inference-asvspoof-dev`
3. `wl-inference-ood-vctk`
4. `wl-online-throughput-smoke`

For each workload, we:

- Create a small synthetic dataset split.
- Train or reuse models as appropriate.
- Measure at least one numeric metric (e.g., accuracy).

### Evidence Schema

`run.py` writes a single JSON file to:

- `$BOOKMAS_EVIDENCE_DIR/results.json`, if `BOOKMAS_EVIDENCE_DIR` is set, otherwise
- `/evidence/results.json`.

The JSON structure:

```json
{
  "chapter": 5,
  "experiment_id": "exp-ch5-baseline-synth-voice-det-v1",
  "environment": {
    "os": "...",
    "python": "..."
  },
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "wl-inference-asvspoof-eval",
      "run_id": "...",
      "success": true,
      "metrics": {
        "accuracy": 0.9
      }
    },
    {
      "variant": "treatment",
      "workload_id": "wl-inference-asvspoof-eval",
      "run_id": "...",
      "success": true,
      "metrics": {
        "accuracy": 0.92
      }
    }
  ],
  "notes": "Additional non-metric notes here"
}
```

Constraints implemented:

- At least one **baseline** and one **treatment** run per workload.
- Every metric value is a **finite JSON number**.
- No invented metrics like wall-clock latency; only values actually computed from the synthetic data and models.

## Usage

From the project root:

```bash
python run.py
```

This will:

- Execute all workloads for both baseline and treatment.
- Write the evidence file as described above.

Then run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Design Notes

- **Reproducibility**: All randomness is controlled via fixed seeds. The synthetic data is regenerated the same way every run, and model training uses deterministic gradient descent with fixed hyperparameters.
- **Safety**: No network access, no shell commands, no external datasets, no use of paths outside the project except `/evidence`.
- **Dependencies**: Only Python standard library is used; `requirements.txt` is empty by design.

This toy experiment mirrors the structure and evidence practices of the real synthetic voice detection experiment while remaining fully executable in a restricted, offline sandbox.
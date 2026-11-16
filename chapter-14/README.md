# Experiment exp-14-stress-redteam-adversarial-eval-v1

This repository contains a **self-contained, offline, Python 3.11+ experiment** that simulates baseline vs. adversarial (red-team) evaluation of a synthetic voice detection and verification stack.

The goal is to operationalize Chapter 14's ideas:

- **Baseline**: evaluation on generic, non-adversarial data.
- **Treatment**: structured adversarial evaluation using a scenario library and synthetic attack generator.

Because this environment is offline and must use only the Python standard library, we **simulate** audio, detection, and verification behavior with deterministic numeric models, while preserving:

- A clear separation between baseline and treatment.
- Scenario- and workload-level metrics.
- A governance-friendly evidence artifact at `/evidence/results.json` following the contract given in the prompt.

## Project layout

- `run.py` – Main entry point. Runs the experiment and writes evidence JSON.
- `requirements.txt` – Empty of runtime deps (standard library only).
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Encodes experiment metadata, workloads, and scenario definitions.
- `experiment/models.py` – Simulated detector and verifier models with deterministic outputs.
- `experiment/workloads.py` – Deterministic synthetic workload generation for baseline and treatment.
- `experiment/runner.py` – Orchestrates baseline and treatment runs and computes metrics.
- `experiment/metrics.py` – Metric computation utilities.
- `tests/test_experiment.py` – Unit tests ensuring schema correctness and basic behavior.

## How this approximates the chapter design

### Baseline vs. Treatment

- **Baseline**:
  - Uses `BaselineDetector` and `BaselineVerifier` on a **generic workload** per workload id (`wl-01`..`wl-04`).
  - Generic workloads have no explicit adversarial perturbations – they contain a mix of benign and synthetic-like samples, but not targeted to scenario weaknesses.

- **Treatment**:
  - Uses the same model classes but **different configuration** (`AdversarialDetector`, `AdversarialVerifier`) and **different workloads** enriched with adversarial flags and parameters.
  - Workloads draw from a simple scenario library that mimics the YAML-based scenario file discussed in the spec.

The experiment compares numeric performance indicators between baseline and treatment for each workload.

### What is and is not modeled

**Modeled (simulated numerically):**

- Workloads `wl-01`..`wl-04` with labels approximating:
  - `wl-01` – executive impersonation outbound.
  - `wl-02` – high-value customer impersonation inbound.
  - `wl-03` – agent impersonation social engineering.
  - `wl-04` – benign controls.
- Simplified adversarial flags (e.g., `is_adversarial`, `difficulty`), representing SNR, codecs, and style factors.
- Detector scores in `[0,1]` with frozen thresholds.
- Simple verification scores and pass/fail decisions.
- Aggregate metrics per variant and workload.

**Not modeled (documented limitations):**

- Real audio I/O, real TTS/voice cloning, codecs, and noise.
- Real ROC AUC or EER calculation – we only compute straightforward error rates over a fixed threshold. These more complex metrics are omitted because they would require richer score distributions and potentially external libs; including fake values would violate the evidence contract.

## Evidence schema

`run.py` writes a JSON document to `${BOOKMAS_EVIDENCE_DIR}/results.json` with this structure:

```jsonc
{
  "chapter": 14,
  "experiment_id": "exp-14-stress-redteam-adversarial-eval-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",      // or "treatment"
      "workload_id": "wl-01",     // stable per workload
      "run_id": "...",            // unique string per (variant, workload)
      "success": true,             // boolean
      "metrics": {
        "false_negative_rate": 0.1,
        "false_positive_rate": 0.05,
        "num_samples": 40
      },
      "notes": "optional textual notes outside the metrics object"
    },
    {
      "variant": "treatment",
      "workload_id": "wl-01",
      "run_id": "...",
      "success": true,
      "metrics": {
        "false_negative_rate": 0.2,
        "false_positive_rate": 0.03,
        "num_samples": 40
      }
    }
  ],
  "notes": "Global notes about the run"
}
```

Requirements satisfied:

- At least one **baseline** and one **treatment** run **per workload**.
- All metric values are **numbers**, not strings or nulls.
- Metrics are derived from actual computation over simulated data, not invented.
- Extra fields (e.g., `notes`) are outside `metrics` and are allowed.

## Determinism and fairness

- All workload generation uses fixed random seeds from `experiment/config.py` to ensure reproducibility and fair comparisons.
- Baseline and treatment workloads for a given workload id share structure but differ systematically in adversarial difficulty.

## Running the experiment

1. Ensure Python 3.11+ is available.
2. (Optional) Create and activate a virtual environment.
3. Install requirements (none beyond stdlib):

   ```bash
   pip install -r requirements.txt
   ```

4. Create an evidence directory and set `BOOKMAS_EVIDENCE_DIR`:

   ```bash
   mkdir -p /evidence
   export BOOKMAS_EVIDENCE_DIR=/evidence
   ```

5. Run the experiment:

   ```bash
   python run.py
   ```

6. Inspect the evidence:

   ```bash
   cat /evidence/results.json
   ```

## Running tests

To run the unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests verify:

- `run.py` creates `/evidence/results.json` with the required structure.
- The experiment id and chapter are correct.
- Every workload has at least one baseline and one treatment run.
- Metrics objects respect the type constraints (numeric values only).

## Extending this experiment

To bring this closer to a production adversarial evaluation harness, you could:

- Replace the simulated detector/verifier with real implementations from Chapters 5–8.
- Integrate actual audio generation and telephony channel simulation.
- Expand the metric set and add scenario-level breakdowns.
- Persist richer manifests and SUT response logs consistent with the evidence schema from the specification.

# Chapter 6 Experiment: Beyond the Baseline – Detectors and Ensembles

This repository fragment implements a **self-contained, offline-safe experiment harness** for:

> **Chapter 6 – Beyond the Baseline: Comparing Detection Strategies and Ensembles**
>
> Experiment ID: `chap6-beyond-baseline-detectors-ensembles-v1`

The goal is to provide a **minimal, reproducible skeleton** that:

- Implements a baseline vs. multiple treatment detectors and ensembles.
- Uses a **shared evaluation harness** and standardized workloads.
- Produces structured evidence under the required schema into `/evidence/results.json`.
- Uses **only Python standard library** (no external dependencies, no network IO).

Because this environment is offline and cannot access real audio, detectors are **simulated** using deterministic synthetic scores and labels. The code is nevertheless organized to mirror a realistic setup for supervised, self-supervised, heuristic detectors and ensembles, supporting fair comparisons and cost-aware analysis.

## Layout

- `run.py` – Main entrypoint. Runs all workloads, baseline and treatment variants, and writes evidence JSON.
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Central configuration for chapter, experiment ID, workloads, detector IDs.
- `experiment/datasets.py` – Synthetic, deterministic dataset generators per workload.
- `experiment/detectors.py` – Baseline and treatment detector implementations plus ensembles.
- `experiment/metrics.py` – Metric calculations (AUC-ROC, AUC-PR, EER, FNR, simple latency/throughput simulation).
- `experiment/harness.py` – Shared evaluation harness that ties together datasets, detectors, and metrics.
- `tests/test_experiment.py` – Unit tests validating the evidence schema and basic behavior.
- `requirements.txt` – Empty of runtime dependencies (standard library only).

## Running the Experiment

From the project root:

```bash
python -m unittest discover -s tests -p "test_*.py"

# Then run the experiment
export BOOKMAS_EVIDENCE_DIR=/evidence
python run.py
```

After running, you should see:

- `/evidence/results.json` – Evidence file with:
  - `chapter`: `6`
  - `experiment_id`: `chap6-beyond-baseline-detectors-ensembles-v1`
  - `environment`: OS & Python version
  - `runs`: One or more runs per workload (WL1–WL5), each including baseline and treatment variants, with numeric metrics.

## Design Notes

### Baseline vs Treatment

- **Baseline detector**: `baseline_cnn_mfcc`
  - Simulated as a single probabilistic classifier with moderate performance.
- **Treatment detectors**:
  - `sup_cnn_mfcc_v2` – Slightly improved supervised detector.
  - `selfsup_embedding_classifier` – Simulated self-supervised + head model with different error profile.
  - `heuristic_metadata_rule_based` – Rule-based detector with complementary strengths.
  - Ensembles:
    - `ensemble_majority_vote`
    - `ensemble_weighted_soft`
    - `ensemble_stacking_meta_lr`
    - `ensemble_risk_tiered_fusion`

In this offline skeleton we:

- Implement all detectors deterministically.
- Evaluate **baseline** as `baseline_cnn_mfcc` and **treatment** as `ensemble_weighted_soft` (representative ensemble) across **all workloads WL1–WL5**.
- Optionally compute internal metrics for other detectors but only baseline vs treatment are written as `variant` values in evidence (for clarity and minimalism).

### Workloads

We simulate five workloads to mirror the spec:

- `WL1_base_domain_eval`
- `WL2_new_language_eval`
- `WL3_new_channel_eval`
- `WL4_adversarial_tools_eval`
- `WL5_cost_latency_benchmark`

Each workload uses deterministic pseudo-random labels and scores (seeded by workload ID) so reruns are reproducible.

### Metrics

Implemented metrics (all numeric):

- `AUC_ROC`
- `AUC_PR`
- `EER`
- `FNR_at_1pct_FPR`
- `FNR_at_5pct_FPR`
- `Latency_p50`
- `Latency_p95`
- `Throughput_rps`

Other metrics from the long spec (e.g., compute ms, licensing cost) are **omitted** here because they cannot be meaningfully measured without real models or pricing. The harness focuses on having at least one robust numeric measurement per run.

### Evidence Schema

`run.py` writes `/evidence/results.json` (using the `BOOKMAS_EVIDENCE_DIR` env var) with this structure:

```json
{
  "chapter": 6,
  "experiment_id": "chap6-beyond-baseline-detectors-ensembles-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "WL1_base_domain_eval",
      "run_id": "<unique>",
      "success": true,
      "metrics": {"AUC_ROC": 0.9, ...}
    },
    ...
  ],
  "notes": "...optional text..."
}
```

Tests assert:

- File exists and is valid JSON.
- `chapter` and `experiment_id` are correct.
- Each `run` has required fields and at least one numeric metric.
- Each workload has at least one baseline and one treatment run.

### Extending to Real Audio

To adapt this skeleton to real detectors and datasets:

1. Replace synthetic dataset generation in `experiment/datasets.py` with manifest-driven audio loading.
2. Replace simulated detectors in `experiment/detectors.py` with real model inference code (e.g., PyTorch models, external APIs, etc.).
3. Extend `experiment/metrics.py` with additional metrics from the chapter spec.
4. Preserve the evidence-writing contract in `run.py` to keep chapter-level reproducibility intact.

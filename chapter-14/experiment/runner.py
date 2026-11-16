from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, List

from .metrics import compute_counts, error_rates
from .models import AdversarialDetector, AdversarialVerifier, BaselineDetector, BaselineVerifier
from .workloads import WorkloadSample, generate_all_workloads


@dataclass
class RunResult:
    variant: str  # "baseline" or "treatment"
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]
    notes: str = ""


class ExperimentRunner:
    """Run baseline and treatment variants across all workloads.

    Each (variant, workload_id) pair corresponds to one RunResult.
    """

    def __init__(self, chapter: int, experiment_id: str) -> None:
        self.chapter = chapter
        self.experiment_id = experiment_id

    def _run_single(self, variant: str, workload_id: str, samples: List[WorkloadSample]) -> RunResult:
        if variant == "baseline":
            detector = BaselineDetector(threshold=0.5)
            verifier = BaselineVerifier(threshold=0.6)
        else:
            detector = AdversarialDetector(threshold=0.5)
            verifier = AdversarialVerifier(threshold=0.6)

        # We use deterministic RNG per sample by seeding from sample_id hash
        import random

        detector_preds = []
        gt_adv_flags = []

        # For wl-02, we additionally track verification bypass / success rates
        wl_requires_verification = workload_id == "wl-02"
        total_legit = 0
        total_legit_pass = 0
        total_adv = 0
        total_adv_pass = 0

        for s in samples:
            # Seed RNG from sample_id to make per-sample behavior deterministic
            rng = random.Random(hash((variant, workload_id, s.sample_id)))

            d_score, d_is_synth = detector.predict(s.features, rng)
            # Reuse RNG state for verifier to keep correlation but deterministic
            v_score, v_pass = verifier.predict(s.features, rng)

            gt_adv_flags.append(s.features.is_adversarial)
            detector_preds.append(d_is_synth)

            if wl_requires_verification:
                if s.features.is_adversarial:
                    total_adv += 1
                    if v_pass:
                        total_adv_pass += 1
                else:
                    total_legit += 1
                    if v_pass:
                        total_legit_pass += 1

        counts = compute_counts(gt_adv_flags, detector_preds)
        base_metrics = error_rates(counts)

        if wl_requires_verification:
            # Avoid division by zero
            legit_rate = (total_legit_pass / total_legit) if total_legit else 0.0
            adv_bypass = (total_adv_pass / total_adv) if total_adv else 0.0
            base_metrics["verification_success_rate_legit"] = float(legit_rate)
            base_metrics["verification_bypass_rate_adversarial"] = float(adv_bypass)

        run_id = f"{variant}-{workload_id}-{uuid.uuid4().hex[:8]}"

        notes = (
            f"Variant={variant}, workload={workload_id}, "
            f"num_samples={int(base_metrics['num_samples'])}."
        )

        return RunResult(
            variant=variant,
            workload_id=workload_id,
            run_id=run_id,
            success=True,
            metrics=base_metrics,
            notes=notes,
        )

    def run_all(self) -> List[RunResult]:
        all_workloads = generate_all_workloads()
        results: List[RunResult] = []

        for workload_id, variants in all_workloads.items():
            for variant_name in ("baseline", "treatment"):
                samples = variants[variant_name]
                result = self._run_single(variant_name, workload_id, samples)
                results.append(result)

        return results

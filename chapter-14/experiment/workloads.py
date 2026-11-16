from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .config import WorkloadConfig, get_scenarios, get_workload_configs
from .models import SampleFeatures


@dataclass
class WorkloadSample:
    sample_id: str
    workload_id: str
    scenario_id: str
    features: SampleFeatures


def _assign_scenarios_for_workload(workload_id: str) -> List[str]:
    scenarios = [s for s in get_scenarios() if s.workload_id == workload_id]
    if not scenarios:
        return ["default_scenario"]
    return [s.scenario_id for s in scenarios]


def generate_baseline_workload(config: WorkloadConfig) -> List[WorkloadSample]:
    """Generate a workload with generic (non-targeted) samples.

    We still respect the adversarial_fraction to have both synthetic and
    benign-like samples, but without scenario-specific difficulty shaping.
    """

    rng = random.Random(config.seed)
    samples: List[WorkloadSample] = []
    scenario_ids = _assign_scenarios_for_workload(config.workload_id)

    for i in range(config.num_samples):
        is_adv = i < int(config.num_samples * config.adversarial_fraction)
        # Generic difficulty: centered around 0.5 with small variation
        difficulty = 0.3 + 0.4 * rng.random()
        role = "attacker" if is_adv else "customer"
        scenario_id = scenario_ids[i % len(scenario_ids)]
        sample = WorkloadSample(
            sample_id=f"{config.workload_id}_baseline_{i}",
            workload_id=config.workload_id,
            scenario_id=scenario_id,
            features=SampleFeatures(
                is_adversarial=is_adv,
                difficulty=difficulty,
                role=role,
            ),
        )
        samples.append(sample)

    return samples


def generate_treatment_workload(config: WorkloadConfig) -> List[WorkloadSample]:
    """Generate a workload with structured adversarial scenarios.

    Compared to baseline, we tie difficulty to scenario definitions and
    make adversarial samples systematically harder.
    """

    rng = random.Random(config.seed + 999)
    samples: List[WorkloadSample] = []
    scenarios = [s for s in get_scenarios() if s.workload_id == config.workload_id]

    if not scenarios:
        # Fallback to baseline-like behavior
        return generate_baseline_workload(config)

    for i in range(config.num_samples):
        is_adv = i < int(config.num_samples * config.adversarial_fraction)
        scenario = scenarios[i % len(scenarios)]

        # Difficulty tied to scenario base with some variation
        if is_adv:
            base_diff = scenario.difficulty
            difficulty = min(1.0, max(0.0, base_diff + 0.1 * (rng.random() - 0.5)))
            role = "attacker"
        else:
            base_diff = max(0.0, scenario.difficulty - 0.3)
            difficulty = min(1.0, max(0.0, base_diff + 0.1 * (rng.random() - 0.5)))
            role = "customer"
            if config.workload_id == "wl-03":
                role = "agent"

        sample = WorkloadSample(
            sample_id=f"{config.workload_id}_treatment_{i}",
            workload_id=config.workload_id,
            scenario_id=scenario.scenario_id,
            features=SampleFeatures(
                is_adversarial=is_adv,
                difficulty=difficulty,
                role=role,
            ),
        )
        samples.append(sample)

    return samples


def generate_all_workloads() -> Dict[str, Dict[str, List[WorkloadSample]]]:
    """Generate all workloads for baseline and treatment.

    Returns a dict:
        {workload_id: {"baseline": [...], "treatment": [...]}}
    """

    configs = get_workload_configs()
    result: Dict[str, Dict[str, List[WorkloadSample]]] = {}
    for workload_id, cfg in configs.items():
        result[workload_id] = {
            "baseline": generate_baseline_workload(cfg),
            "treatment": generate_treatment_workload(cfg),
        }
    return result

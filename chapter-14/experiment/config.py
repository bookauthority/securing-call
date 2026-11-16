from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


# Workload identifiers as described in the specification
WORKLOAD_IDS = ["wl-01", "wl-02", "wl-03", "wl-04"]


@dataclass(frozen=True)
class WorkloadConfig:
    workload_id: str
    num_samples: int
    adversarial_fraction: float
    seed: int


def get_workload_configs() -> Dict[str, WorkloadConfig]:
    """Return deterministic workload configs for each workload.

    These loosely align with the narrative size targets but keep counts small
    for bounded execution while still providing enough samples to compute
    meaningful error rates.
    """

    return {
        # Executive impersonation outbound
        "wl-01": WorkloadConfig(
            workload_id="wl-01",
            num_samples=80,
            adversarial_fraction=0.6,
            seed=101,
        ),
        # High-value customer impersonation inbound (verification heavy)
        "wl-02": WorkloadConfig(
            workload_id="wl-02",
            num_samples=100,
            adversarial_fraction=0.7,
            seed=202,
        ),
        # Agent impersonation social engineering
        "wl-03": WorkloadConfig(
            workload_id="wl-03",
            num_samples=90,
            adversarial_fraction=0.65,
            seed=303,
        ),
        # Benign natural control calls
        "wl-04": WorkloadConfig(
            workload_id="wl-04",
            num_samples=120,
            adversarial_fraction=0.0,
            seed=404,
        ),
    }


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    workload_id: str
    difficulty: float  # 0..1, where higher is more difficult for detectors


def get_scenarios() -> List[Scenario]:
    """Return a small scenario library approximating the YAML file.

    In a full system this would be loaded from YAML. Here we embed it directly
    to stay standard-library-only.
    """

    return [
        Scenario(
            scenario_id="exec_impersonation_urgent_wire",
            description="Executive impersonation requesting urgent outbound payment.",
            workload_id="wl-01",
            difficulty=0.8,
        ),
        Scenario(
            scenario_id="exec_impersonation_data_export",
            description="Executive impersonation requesting data export.",
            workload_id="wl-01",
            difficulty=0.7,
        ),
        Scenario(
            scenario_id="customer_impersonation_mfa_change",
            description="High-value customer impersonation to change MFA phone.",
            workload_id="wl-02",
            difficulty=0.85,
        ),
        Scenario(
            scenario_id="customer_impersonation_password_reset",
            description="High-value customer impersonation to reset password.",
            workload_id="wl-02",
            difficulty=0.75,
        ),
        Scenario(
            scenario_id="agent_impersonation_refund_scam",
            description="Agent impersonation offering fake refund.",
            workload_id="wl-03",
            difficulty=0.8,
        ),
        Scenario(
            scenario_id="agent_impersonation_upgrade_scam",
            description="Agent impersonation offering fake service upgrade.",
            workload_id="wl-03",
            difficulty=0.7,
        ),
        Scenario(
            scenario_id="benign_control_general_support",
            description="Benign natural support calls mirroring adversarial scripts.",
            workload_id="wl-04",
            difficulty=0.2,
        ),
    ]

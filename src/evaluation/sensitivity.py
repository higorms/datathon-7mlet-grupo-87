"""Analise de sensibilidade de parametros da politica bandit."""

from __future__ import annotations

from dataclasses import dataclass

from src.bandits.environment import BanditEnvironment, build_environment_from_catalog
from src.bandits.policies import ThompsonSampling, UCB1
from src.bandits.simulation import run_policy


@dataclass
class SensitivityRow:
    parameter: str
    value: str | float
    policy: str
    final_regret_mean: float
    conversion_rate: float
    optimal_arm_rate: float


def run_sensitivity_study(
    env: BanditEnvironment | None = None,
    horizon: int = 5000,
    seeds: int = 10,
) -> list[SensitivityRow]:
    """Varia horizonte, atraso, prior TS e c do UCB; retorna metricas agregadas."""
    env = env or build_environment_from_catalog()
    rows: list[SensitivityRow] = []

    # Horizonte (Thompson Sampling).
    for h in (5_000, 10_000, 20_000):
        res = run_policy(lambda: ThompsonSampling(), env, h, seeds, mean_delay=0.0)
        rows.append(
            SensitivityRow("horizon", h, res.name, res.final_regret_mean,
                           res.conversion_rate, res.optimal_arm_rate)
        )

    # Atraso medio (TS).
    for delay in (0.0, 200.0, 500.0):
        res = run_policy(lambda: ThompsonSampling(), env, horizon, seeds, mean_delay=delay)
        rows.append(
            SensitivityRow("mean_delay", delay, res.name, res.final_regret_mean,
                           res.conversion_rate, res.optimal_arm_rate)
        )

    # Prior Thompson Sampling.
    for alpha, beta in ((1.0, 1.0), (2.0, 2.0)):
        label = f"Beta({alpha:g},{beta:g})"
        res = run_policy(
            lambda a=alpha, b=beta: ThompsonSampling(prior_alpha=a, prior_beta=b,
                                                     name=f"Thompson Sampling {label}"),
            env, horizon, seeds, mean_delay=0.0,
        )
        rows.append(
            SensitivityRow("ts_prior", label, res.name, res.final_regret_mean,
                           res.conversion_rate, res.optimal_arm_rate)
        )

    # UCB c.
    for c in (0.5, 1.0, 2.0):
        res = run_policy(lambda c=c: UCB1(c=c), env, horizon, seeds, mean_delay=0.0)
        rows.append(
            SensitivityRow("ucb_c", c, res.name, res.final_regret_mean,
                           res.conversion_rate, res.optimal_arm_rate)
        )

    return rows
